import os
import sys
import json
import time
import tempfile
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

import numpy as np
import sounddevice as sd
import soundfile as sf

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QPlainTextEdit, QLabel, QDialog, QDialogButtonBox, QFormLayout,
    QComboBox, QLineEdit, QMessageBox
)

# ---------- stabile Defaults/Workarounds (Windows) ----------
# Symlink-Rechteprobleme vermeiden und Cache-Pfad setzen
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/hf"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# ---------------- Einstellungen ----------------

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

@dataclass
class AppSettings:
    backend: str = "openai"  # "local" | "openai"
    # OpenAI
    openai_model: str = "gpt-4o-mini-transcribe"
    openai_api_key: str = ""  # leer -> aus ENV lesen
    # Lokal (faster-whisper)
    local_model: str = "large-v3"       # oder "large-v3-turbo"
    device: str = "auto"                # "auto" | "cuda" | "cpu"
    compute_type: str = "auto"          # "auto" | "float16" | "int8" | "int8_float16" | "float32"

    @classmethod
    def load(cls) -> "AppSettings":
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**data)
        except Exception:
            return cls()

    def save(self) -> None:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

# ---------------- Audio-Aufnahme ----------------

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"

class RecordingWorker(QObject):
    started = Signal()
    stopped = Signal(str)  # Pfad zur WAV-Datei
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self._stream = None
        self._frames: List[np.ndarray] = []
        self._running = False

    @Slot()
    def start(self):
        if self._running:
            return
        self._frames = []
        try:
            self._stream = sd.InputStream(
                channels=CHANNELS,
                samplerate=SAMPLE_RATE,
                dtype=DTYPE,
                callback=self._callback,
            )
            self._stream.start()
            self._running = True
            print("[REC] start")
            self.started.emit()
        except Exception as e:
            self.error.emit(f"Audio-Start fehlgeschlagen: {e!r}")

    def _callback(self, indata, frames, time_info, status):
        if status:
            # Over-/Underruns könnten hier geloggt werden
            print(f"[REC] status: {status!s}")
        self._frames.append(indata.copy())

    @Slot()
    def stop(self):
        if not self._running:
            return
        try:
            self._stream.stop()
            self._stream.close()
        except Exception as e:
            self.error.emit(f"Audio-Stop fehlgeschlagen: {e!r}")
        finally:
            self._stream = None
            self._running = False

        # WAV schreiben
        try:
            total = sum(chunk.shape[0] for chunk in self._frames)
            print(f"[REC] stop, frames={len(self._frames)}, samples={total}")
            data = np.concatenate(self._frames, axis=0) if self._frames else np.zeros((1, CHANNELS), dtype=DTYPE)
            data = data.astype("float32", copy=False)
            fd, wav_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            sf.write(wav_path, data, SAMPLE_RATE, subtype="PCM_16")
            self.stopped.emit(wav_path)
        except Exception as e:
            self.error.emit(f"WAV-Schreiben fehlgeschlagen: {e!r}")

# ---------------- Lokal (faster-whisper) ----------------

class LocalTranscribeWorker(QObject):
    busy = Signal(bool)
    finished = Signal(object)  # dict: {"text": str, "language": Optional[str]}
    error = Signal(str)

    def __init__(self, settings: AppSettings):
        super().__init__()
        self._settings = settings
        self._model = None
        self._last_device = None
        self._last_compute = None

    @Slot(str)
    def transcribe(self, wav_path: str):
        t0 = time.time()
        try:
            self.busy.emit(True)

            device = self._decide_device(self._settings.device)
            compute = self._settings.compute_type
            if compute == "auto":
                compute = "float16" if device == "cuda" else "int8"

            # Model (re)laden, wenn Device/Compute gewechselt wurde
            if self._model is None or device != self._last_device or compute != self._last_compute:
                from faster_whisper import WhisperModel
                print(f"[STT local] load model={self._settings.local_model} device={device} compute={compute}")
                try:
                    self._model = WhisperModel(self._settings.local_model, device=device, compute_type=compute)
                except ValueError as e:
                    msg = str(e).lower()
                    if "float16" in msg or "not support efficient float16" in msg:
                        print("[STT local] fallback compute -> int8")
                        compute = "int8"
                        self._model = WhisperModel(self._settings.local_model, device=device, compute_type=compute)
                    else:
                        raise
                self._last_device = device
                self._last_compute = compute

            print(f"[STT local] transcribe: {wav_path}")
            segments, info = self._model.transcribe(
                wav_path,
                vad_filter=True,
                beam_size=5,
                condition_on_previous_text=False,
            )
            text = "".join(seg.text for seg in segments).strip()
            lang = getattr(info, "language", None)
            print(f"[STT local] done in {time.time() - t0:.2f}s, lang={lang}, chars={len(text)}")
            self.finished.emit({"text": text, "language": lang})
        except Exception as e:
            self.error.emit(f"Transkription (lokal) fehlgeschlagen: {e!r}")
        finally:
            self.busy.emit(False)
            try:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
            except Exception:
                pass

    @staticmethod
    def _decide_device(pref: str) -> str:
        if pref == "cpu":
            return "cpu"
        if pref == "cuda":
            return "cuda"
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

# ---------------- OpenAI ----------------

class OpenAITranscribeWorker(QObject):
    busy = Signal(bool)
    finished = Signal(object)  # dict: {"text": str, "language": None}
    error = Signal(str)

    def __init__(self, settings: AppSettings):
        super().__init__()
        self._settings = settings

    @Slot(str)
    def transcribe(self, wav_path: str):
        t0 = time.time()
        try:
            self.busy.emit(True)
            key = (self._settings.openai_api_key or os.environ.get("OPENAI_API_KEY") or "").strip()
            if not key:
                raise RuntimeError("Kein OpenAI API-Key gesetzt. Hinterlege ihn in den Einstellungen oder per ENV OPENAI_API_KEY.")
            from openai import OpenAI
            client = OpenAI(api_key=key)
            model = self._settings.openai_model or "gpt-4o-mini-transcribe"
            print(f"[STT openai] model={model}")
            with open(wav_path, "rb") as f:
                resp = client.audio.transcriptions.create(
                    model=model,
                    file=f,
                    response_format="text",
                )
            text = resp if isinstance(resp, str) else getattr(resp, "text", "")
            print(f"[STT openai] done in {time.time() - t0:.2f}s, chars={len(text or '')}")
            self.finished.emit({"text": (text or "").strip(), "language": None})
        except Exception as e:
            self.error.emit(f"Transkription (OpenAI) fehlgeschlagen: {e!r}")
        finally:
            self.busy.emit(False)
            try:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
            except Exception:
                pass

# ---------------- Einstellungsdialog ----------------

class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Einstellungen")
        self._settings = settings

        form = QFormLayout(self)

        self.cb_backend = QComboBox()
        self.cb_backend.addItems(["local", "openai"])
        self.cb_backend.setCurrentText(settings.backend)

        # OpenAI
        self.cb_openai_model = QComboBox()
        self.cb_openai_model.addItems([
            "gpt-4o-mini-transcribe",
            "gpt-4o-transcribe",
            "whisper-1",
        ])
        self.cb_openai_model.setCurrentText(settings.openai_model)

        self.le_api_key = QLineEdit()
        self.le_api_key.setEchoMode(QLineEdit.Password)
        self.le_api_key.setPlaceholderText("leer lassen = OPENAI_API_KEY aus ENV nutzen")
        self.le_api_key.setText(settings.openai_api_key)

        # Lokal
        self.cb_local_model = QComboBox()
        self.cb_local_model.addItems(["large-v3", "large-v3-turbo"])
        self.cb_local_model.setCurrentText(settings.local_model)

        self.cb_device = QComboBox()
        self.cb_device.addItems(["auto", "cuda", "cpu"])
        self.cb_device.setCurrentText(settings.device)

        self.cb_compute = QComboBox()
        self.cb_compute.addItems(["auto", "float16", "int8", "int8_float16", "float32"])
        self.cb_compute.setCurrentText(settings.compute_type)

        form.addRow("Backend", self.cb_backend)
        form.addRow(QLabel("— OpenAI —"))
        form.addRow("Modell", self.cb_openai_model)
        form.addRow("API-Key", self.le_api_key)
        form.addRow(QLabel("— Lokal (faster-whisper) —"))
        form.addRow("Modell", self.cb_local_model)
        form.addRow("Device", self.cb_device)
        form.addRow("Compute", self.cb_compute)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def get_settings(self) -> AppSettings:
        return AppSettings(
            backend=self.cb_backend.currentText(),
            openai_model=self.cb_openai_model.currentText(),
            openai_api_key=self.le_api_key.text(),
            local_model=self.cb_local_model.currentText(),
            device=self.cb_device.currentText(),
            compute_type=self.cb_compute.currentText(),
        )

# ---------------- Hauptfenster ----------------

class MainWindow(QWidget):
    sig_start_record = Signal()
    sig_stop_record = Signal()
    sig_transcribe_local = Signal(str)
    sig_transcribe_openai = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speech-to-Text (Lokal & OpenAI)")
        self.resize(780, 480)

        self.settings = AppSettings.load()

        self.output = QPlainTextEdit(self)
        self.output.setPlaceholderText("Hier erscheint die Transkription …")
        self.output.setReadOnly(False)

        self.status = QLabel(self)
        self.status.setWordWrap(True)

        self.btn_record = QPushButton("🎙 Aufnahme starten", self)
        self.btn_record.clicked.connect(self.toggle_recording)

        self.btn_settings = QPushButton("Einstellungen…", self)
        self.btn_settings.clicked.connect(self.open_settings)

        row = QHBoxLayout()
        row.addWidget(self.btn_record)
        row.addStretch(1)
        row.addWidget(self.btn_settings)

        layout = QVBoxLayout()
        layout.addWidget(self.output)
        layout.addWidget(self.status)
        layout.addLayout(row)
        self.setLayout(layout)

        # Threads/Worker
        self.rec_thread = QThread(self)
        self.rec_worker = RecordingWorker()
        self.rec_worker.moveToThread(self.rec_thread)
        self.rec_thread.start()

        self.local_thread = QThread(self)
        self.local_worker = LocalTranscribeWorker(self.settings)
        self.local_worker.moveToThread(self.local_thread)
        self.local_thread.start()

        self.openai_thread = QThread(self)
        self.openai_worker = OpenAITranscribeWorker(self.settings)
        self.openai_worker.moveToThread(self.openai_thread)
        self.openai_thread.start()

        # Verbindungen
        self.sig_start_record.connect(self.rec_worker.start, Qt.QueuedConnection)
        self.sig_stop_record.connect(self.rec_worker.stop, Qt.QueuedConnection)
        self.sig_transcribe_local.connect(self.local_worker.transcribe, Qt.QueuedConnection)
        self.sig_transcribe_openai.connect(self.openai_worker.transcribe, Qt.QueuedConnection)

        self.rec_worker.stopped.connect(self.on_record_stopped)
        self.rec_worker.error.connect(self.on_error)

        self.local_worker.busy.connect(self.on_busy)
        self.local_worker.finished.connect(self.on_transcribed)
        self.local_worker.error.connect(self.on_error)

        self.openai_worker.busy.connect(self.on_busy)
        self.openai_worker.finished.connect(self.on_transcribed)
        self.openai_worker.error.connect(self.on_error)

        self._recording = False
        self._update_status_ready()

    def _update_status_ready(self):
        if self.settings.backend == "openai":
            self.status.setText(f"Bereit – Backend: OpenAI ({self.settings.openai_model}).")
        else:
            self.status.setText(
                f"Bereit – Backend: Lokal (faster-whisper {self.settings.local_model}, {self.settings.compute_type}/{self.settings.device})."
            )

    @Slot()
    def toggle_recording(self):
        if not self._recording:
            self.status.setText("Aufnahme läuft … zum Stoppen erneut klicken.")
            self.btn_record.setText("⏹ Aufnahme stoppen")
            self._recording = True
            self.sig_start_record.emit()
        else:
            self.btn_record.setEnabled(False)
            self.sig_stop_record.emit()

    @Slot(str)
    def on_record_stopped(self, wav_path: str):
        if self.settings.backend == "openai":
            self.status.setText("Sende Audio an OpenAI …")
            self.sig_transcribe_openai.emit(wav_path)
        else:
            self.status.setText("Transkribiere lokal …")
            self.sig_transcribe_local.emit(wav_path)

    @Slot(bool)
    def on_busy(self, is_busy: bool):
        self.btn_record.setEnabled(not is_busy)
        if not is_busy:
            self.btn_record.setText("🎙 Aufnahme starten")
            self._recording = False

    @Slot(object)
    def on_transcribed(self, result: Dict[str, Any]):
        text = (result or {}).get("text", "") or ""
        language = (result or {}).get("language", None)
        if language:
            self.status.setText(f"Fertig. Sprache: {language}")
        else:
            self.status.setText("Fertig.")
        if text.strip():
            if self.output.toPlainText().strip():
                self.output.insertPlainText("\n")
            self.output.insertPlainText(text.strip() + "\n")
        else:
            self.output.insertPlainText("\n[Kein Text erkannt]\n")
        self._update_status_ready()

    @Slot(str)
    def on_error(self, msg: str):
        self.status.setText(f"Fehler: {msg}")
        self.btn_record.setEnabled(True)
        self.btn_record.setText("🎙 Aufnahme starten")
        self._recording = False
        self._update_status_ready()

    @Slot()
    def open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec() == QDialog.Accepted:
            self.settings = dlg.get_settings()
            self.settings.save()
            # Worker mit neuen Settings aktualisieren
            self.local_worker._settings = self.settings
            self.openai_worker._settings = self.settings
            self._update_status_ready()
            if self.settings.backend == "openai" and not (self.settings.openai_api_key.strip() or os.environ.get("OPENAI_API_KEY")):
                QMessageBox.warning(self, "Hinweis", "Kein OpenAI-API-Key gesetzt. Hinterlege ihn in den Einstellungen oder per ENV.")

    def closeEvent(self, event):
        for th in (self.rec_thread, self.local_thread, self.openai_thread):
            try:
                if th.isRunning():
                    th.quit()
                    th.wait(1000)
            except Exception:
                pass
        super().closeEvent(event)

def main():
    if sys.platform.startswith("win"):
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
