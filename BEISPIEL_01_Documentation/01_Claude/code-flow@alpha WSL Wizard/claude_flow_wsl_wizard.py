
from pathlib import Path
import sys
import os
import json
import shlex
import subprocess
from datetime import datetime

from PySide6 import QtCore, QtWidgets, QtGui

APP_TITLE = "Claude-Flow@alpha – WSL Prompt Wizard"
DEFAULT_DISTRO = "Ubuntu"

DARK_QSS = """
QWidget { background-color: #0f1218; color: #E6E6E6; font-size: 13px; }
QLineEdit, QTextEdit, QComboBox, QSpinBox, QCheckBox, QPlainTextEdit {
    background: #1a1f2b; color: #E6E6E6; border: 1px solid #2a3142; border-radius: 6px; padding: 6px;
}
QPushButton { background: #f97316; color: #111318; border: 0; border-radius: 8px; padding: 8px 12px; font-weight: 600; }
QPushButton:hover { background: #fb923c; }
QPushButton#secondary { background: #3b82f6; color: #0f1218; }
QPushButton#secondary:hover { background: #60a5fa; }
QPushButton#neutral { background: #334155; color: #E6E6E6; }
QPushButton#neutral:hover { background: #475569; }
QGroupBox { border: 1px solid #2a3142; border-radius: 8px; margin-top: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; color: #9ca3af; font-weight: 600; }
QLabel { color: #cbd5e1; }
QStatusBar { background: #0b0e13; color: #cbd5e1; }
"""

def decode_wsl_output(b: bytes) -> str:
    """Robuste Dekodierung von wsl.exe-Output."""
    if not b:
        return ""
    # BOM-sniff
    if b.startswith(b"\xff\xfe"):
        try:
            return b.decode("utf-16le", errors="replace")
        except Exception:
            pass
    if b.startswith(b"\xef\xbb\xbf"):
        try:
            return b.decode("utf-8", errors="replace")
        except Exception:
            pass
    # Heuristik: hoher Anteil NUL-Bytes -> UTF-16LE
    nul_ratio = b.count(b"\x00") / max(1, len(b))
    if nul_ratio > 0.2:
        try:
            return b.decode("utf-16le", errors="replace")
        except Exception:
            pass
    # Bevorzugt UTF-8
    try:
        return b.decode("utf-8", errors="replace")
    except Exception:
        pass
    # Fallbacks
    try:
        return b.decode("cp1252", errors="replace")
    except Exception:
        pass
    return b.decode("latin1", errors="replace")



def list_wsl_distros() -> list[str]:
    try:
        raw = subprocess.check_output(["wsl.exe", "-l", "-q"])
        txt = decode_wsl_output(raw).replace("\ufeff", "").replace("\x00", "")
        distros = [line.strip() for line in txt.splitlines() if line.strip()]
        return distros or [DEFAULT_DISTRO]
    except Exception:
        return [DEFAULT_DISTRO]

def win_to_wsl_path(win_path: str) -> str:
    if not win_path:
        return ""
    p = Path(win_path)
    drive = p.drive[:-1].lower() if p.drive else ""
    if drive and len(drive) == 1:
        rel = str(p).replace("\\", "/")[2:]
        return f"/mnt/{drive}{rel}"
    return str(p).replace("\\", "/")

def find_saved_configs(project_win: str) -> list[Path]:
    base = Path(project_win) / ".claude-flow" / "saved-configs"
    if base.exists():
        return sorted(base.glob("*.json"))
    return []

def build_spawn_command(task_text: str, saved_config_rel: str, extra_flags=None) -> str:
    flags = ["--claude", "--verbose"]
    if saved_config_rel:
        flags.extend(["--config", f"./{saved_config_rel}"])
    if extra_flags:
        flags.extend(extra_flags)
    return " ".join([
        "npx", "claude-flow@alpha", "hive-mind", "spawn",
        shlex.quote(task_text),
        *flags
    ])

def build_bash_line(project_wsl: str, commands: list[str]) -> str:
    parts = [f"cd {shlex.quote(project_wsl)}"]
    parts.extend(commands)
    return " && ".join(parts)

class WorkerThread(QtCore.QThread):
    out = QtCore.Signal(str)
    err = QtCore.Signal(str)
    done = QtCore.Signal(int)

    def __init__(self, args: list[str], parent=None):
        super().__init__(parent)
        self._args = args

    def run(self):
        try:
            proc = subprocess.Popen(
                self._args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            while True:
                if proc.stdout:
                    line = proc.stdout.readline()
                    if line:
                        self.out.emit(decode_wsl_output(line))
                if proc.stderr:
                    eline = proc.stderr.readline()
                    if eline:
                        self.err.emit(decode_wsl_output(eline))
                if proc.poll() is not None:
                    if proc.stdout:
                        rem = proc.stdout.read()
                        if rem:
                            self.out.emit(decode_wsl_output(rem))
                    if proc.stderr:
                        rem2 = proc.stderr.read()
                        if rem2:
                            self.err.emit(decode_wsl_output(rem2))
                    self.done.emit(proc.returncode or 0)
                    break
        except Exception as e:
            self.err.emit(f"[Wizard] Fehler beim Start: {e}")
            self.done.emit(1)

class PromptWizard(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(980, 720)
        self.setStyleSheet(DARK_QSS)

        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        layout = QtWidgets.QVBoxLayout(cw)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(10)

        top = QtWidgets.QHBoxLayout()
        layout.addLayout(top)

        self.ed_project = QtWidgets.QLineEdit()
        self.btn_browse = QtWidgets.QPushButton("Browse")
        self.btn_browse.setObjectName("neutral")
        self.lbl_wsl = QtWidgets.QLabel("WSL Path:")
        self.lbl_wsl_val = QtWidgets.QLabel("-")
        self.lbl_wsl_val.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.cb_distro = QtWidgets.QComboBox()
        self.cb_distro.addItems(list_wsl_distros())
        self.btn_refresh_distro = QtWidgets.QPushButton("Reload Distros")
        self.btn_refresh_distro.setObjectName("neutral")

        left = QtWidgets.QFormLayout()
        left.addRow("Project Directory (Windows):", self.ed_project)
        left.addRow("", self.btn_browse)
        left.addRow(self.lbl_wsl, self.lbl_wsl_val)

        right = QtWidgets.QFormLayout()
        right.addRow("WSL Distribution:", self.cb_distro)
        right.addRow("", self.btn_refresh_distro)

        top.addLayout(left, 2)
        top.addSpacing(12)
        top.addLayout(right, 1)

        grp_cfg = QtWidgets.QGroupBox("Saved-Config auswählen (.claude-flow/saved-configs)")
        layout.addWidget(grp_cfg)
        cfg_lay = QtWidgets.QGridLayout(grp_cfg)

        self.cb_saved = QtWidgets.QComboBox()
        self.btn_scan = QtWidgets.QPushButton("Scan")
        self.btn_scan.setObjectName("neutral")
        self.chk_mirror = QtWidgets.QCheckBox("Optional: zusätzlich nach .claude/config.json spiegeln")

        cfg_lay.addWidget(QtWidgets.QLabel("Datei:"), 0, 0)
        cfg_lay.addWidget(self.cb_saved, 0, 1)
        cfg_lay.addWidget(self.btn_scan, 0, 2)
        cfg_lay.addWidget(self.chk_mirror, 1, 1, 1, 2)

        grp_task = QtWidgets.QGroupBox("Aufgabe (Objective für hive-mind spawn)")
        layout.addWidget(grp_task)
        task_lay = QtWidgets.QVBoxLayout(grp_task)
        self.ed_task = QtWidgets.QPlainTextEdit()
        self.ed_task.setPlaceholderText("Beschreibe klar und vollständig, was der Schwarm erledigen soll …")
        task_lay.addWidget(self.ed_task)

        btns = QtWidgets.QHBoxLayout()
        layout.addLayout(btns)

        self.btn_require = QtWidgets.QPushButton("Check Requirements")
        self.btn_require.setObjectName("secondary")
        self.btn_init = QtWidgets.QPushButton("Initialize Claude-Flow")
        self.btn_init.setObjectName("secondary")
        self.btn_spawn_sync = QtWidgets.QPushButton("Spawn (same window)")
        self.btn_spawn = QtWidgets.QPushButton("Spawn (new window)")
        btns.addWidget(self.btn_require)
        btns.addWidget(self.btn_init)
        btns.addStretch(1)
        btns.addWidget(self.btn_spawn_sync)
        btns.addWidget(self.btn_spawn)

        grp_console = QtWidgets.QGroupBox("Console Output")
        layout.addWidget(grp_console, 1)
        con_lay = QtWidgets.QVBoxLayout(grp_console)
        self.txt_console = QtWidgets.QPlainTextEdit()
        self.txt_console.setReadOnly(True)
        con_lay.addWidget(self.txt_console)

        self.status = self.statusBar()
        self.status.showMessage("Bereit.")

        self.btn_browse.clicked.connect(self.on_browse)
        self.ed_project.textChanged.connect(self.on_project_changed)
        self.btn_scan.clicked.connect(self.scan_saved_configs)
        self.btn_refresh_distro.clicked.connect(self.reload_distros)
        self.btn_require.clicked.connect(self.check_requirements)
        self.btn_init.clicked.connect(self.init_cf)
        self.btn_spawn.clicked.connect(self.spawn_new_window)
        self.btn_spawn_sync.clicked.connect(self.spawn_same_window)

        self.ed_task.setPlainText(
            "Bearbeite alle offenen Issues im Ordner ./issues. Stelle sicher, dass "
            "WIRKLICH ALLE AUFGABEN inkl. Teilaufgaben abgeschlossen und getestet sind, "
            "bevor du das Issue auf closed setzt. Bei Fehlern oder unlösbaren Aufgaben: "
            "Meldung im Terminal und Issue offen lassen. Beachte description, additional "
            "und comments. Abarbeitung step by step (Issue_1.json, Issue_2.json …). "
            "Nach Abschluss state=closed setzen."
        )

        self.settings_path = Path.home() / ".cf_wizard_settings.json"
        self.restore_settings()
        self.on_project_changed(self.ed_project.text())

        self.worker = None

    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.txt_console.appendPlainText(f"[{ts}] {msg}")
        self.txt_console.verticalScrollBar().setValue(self.txt_console.verticalScrollBar().maximum())

    def restore_settings(self):
        if self.settings_path.exists():
            try:
                data = json.loads(self.settings_path.read_text(encoding="utf-8"))
                self.ed_project.setText(data.get("project_win", ""))
                distro = data.get("distro", DEFAULT_DISTRO)
                if distro in [self.cb_distro.itemText(i) for i in range(self.cb_distro.count())]:
                    self.cb_distro.setCurrentText(distro)
                else:
                    self.cb_distro.setCurrentIndex(0)
            except Exception:
                pass

    def persist_settings(self):
        data = {
            "project_win": self.ed_project.text().strip(),
            "distro": self.cb_distro.currentText().strip()
        }
        try:
            self.settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def on_browse(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Projektverzeichnis wählen")
        if d:
            self.ed_project.setText(d)

    def on_project_changed(self, txt: str):
        wsl = win_to_wsl_path(txt.strip())
        self.lbl_wsl_val.setText(wsl or "-")
        self.scan_saved_configs()

    def reload_distros(self):
        self.cb_distro.clear()
        self.cb_distro.addItems(list_wsl_distros())
        self.status.showMessage("WSL-Distributionen aktualisiert.", 3000)

    def scan_saved_configs(self):
        self.cb_saved.clear()
        p = self.ed_project.text().strip()
        files = find_saved_configs(p)
        for f in files:
            self.cb_saved.addItem(f.name, f)
        if not files:
            self.cb_saved.addItem("(keine .json gefunden)", None)

    def run_wsl_stream(self, bash_line: str):
        args = ["wsl.exe", "-d", self.cb_distro.currentText(), "--", "bash", "-lc", bash_line]
        self.log(f"$ {' '.join(args[:-1])} \"{bash_line}\"")
        self.worker = WorkerThread(args)
        self.worker.out.connect(self.log)
        self.worker.err.connect(lambda s: self.log(f"[stderr] {s}"))
        self.worker.done.connect(lambda rc: self.status.showMessage(f"Beendet (RC={rc})", 5000))
        self.worker.start()

    def run_wsl_new_window(self, bash_line: str):
        args = ["cmd", "/c", "start", "", "wsl.exe", "-d", self.cb_distro.currentText(), "--", "bash", "-lc", bash_line + ' && echo -e "\\n[Beenden mit Taste …]" && read -n 1 -s -r && exec bash -i' ]
        self.log(f"$ start WSL: {bash_line}")
        try:
            subprocess.Popen(args, close_fds=True)
            self.status.showMessage("In neuem Fenster gestartet.", 4000)
        except Exception as e:
            self.log(f"[Fehler] {e}")
            self.status.showMessage("Fehler beim Start (neues Fenster).", 4000)

    def check_requirements(self):
        proj = self.lbl_wsl_val.text().strip()
        if not proj or proj == "-":
            self.log("Bitte Projektpfad setzen.")
            return
        commands = [
            f"cd {shlex.quote(proj)}",
            "node -v || true",
            "npm -v || true",
            "npx --version || true",
            "npx claude-flow@alpha --help | head -n 20 || true"
        ]
        self.run_wsl_stream(" && ".join(commands))

    def init_cf(self):
        proj = self.lbl_wsl_val.text().strip()
        if not proj or proj == "-":
            self.log("Bitte Projektpfad setzen.")
            return
        bash_line = build_bash_line(proj, ["npx claude-flow@alpha init --force"])
        self.run_wsl_stream(bash_line)

    def spawn_same_window(self):
        proj = self.lbl_wsl_val.text().strip()
        if not proj or proj == "-":
            self.log("Bitte Projektpfad setzen.")
            return
        saved_item = self.cb_saved.currentData()
        saved_rel = ""
        if isinstance(saved_item, Path):
            try:
                saved_rel = str(Path(saved_item).relative_to(Path(self.ed_project.text().strip()))).replace("\\", "/")
            except Exception:
                saved_rel = f".claude-flow/saved-configs/{Path(saved_item).name}"

        task = self.ed_task.toPlainText().strip()
        if not task:
            self.log("Bitte Task/Objective eingeben.")
            return

        if self.chk_mirror.isChecked() and isinstance(saved_item, Path):
            try:
                dst = Path(self.ed_project.text().strip()) / ".claude" / "config.json"
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(Path(saved_item).read_text(encoding="utf-8"), encoding="utf-8")
                self.log(f"Mirrored Saved-Config → {dst}")
            except Exception as e:
                self.log(f"[Mirror fehlgeschlagen] {e}")

        cmd = build_spawn_command(task, saved_rel, extra_flags=None)
        bash_line = build_bash_line(proj, ["npx claude-flow@alpha init --force", cmd])
        self.run_wsl_stream(bash_line)

    def spawn_new_window(self):
        proj = self.lbl_wsl_val.text().strip()
        if not proj or proj == "-":
            self.log("Bitte Projektpfad setzen.")
            return
        saved_item = self.cb_saved.currentData()
        saved_rel = ""
        if isinstance(saved_item, Path):
            try:
                saved_rel = str(Path(saved_item).relative_to(Path(self.ed_project.text().strip()))).replace("\\", "/")
            except Exception:
                saved_rel = f".claude-flow/saved-configs/{Path(saved_item).name}"
        task = self.ed_task.toPlainText().strip()
        if not task:
            self.log("Bitte Task/Objective eingeben.")
            return

        if self.chk_mirror.isChecked() and isinstance(saved_item, Path):
            try:
                dst = Path(self.ed_project.text().strip()) / ".claude" / "config.json"
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(Path(saved_item).read_text(encoding="utf-8"), encoding="utf-8")
                self.log(f"Mirrored Saved-Config → {dst}")
            except Exception as e:
                self.log(f"[Mirror fehlgeschlagen] {e}")

        cmd = build_spawn_command(task, saved_rel, extra_flags=None)
        bash_line = build_bash_line(proj, ["npx claude-flow@alpha init --force", cmd])
        self.run_wsl_new_window(bash_line)

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        self.persist_settings()
        return super().closeEvent(e)

class WorkerThread(QtCore.QThread):
    out = QtCore.Signal(str)
    err = QtCore.Signal(str)
    done = QtCore.Signal(int)

    def __init__(self, args: list[str], parent=None):
        super().__init__(parent)
        self._args = args

    def run(self):
        try:
            proc = subprocess.Popen(
                self._args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            while True:
                if proc.stdout:
                    line = proc.stdout.readline()
                    if line:
                        self.out.emit(decode_wsl_output(line))
                if proc.stderr:
                    eline = proc.stderr.readline()
                    if eline:
                        self.err.emit(decode_wsl_output(eline))
                if proc.poll() is not None:
                    if proc.stdout:
                        rem = proc.stdout.read()
                        if rem:
                            self.out.emit(decode_wsl_output(rem))
                    if proc.stderr:
                        rem2 = proc.stderr.read()
                        if rem2:
                            self.err.emit(decode_wsl_output(rem2))
                    self.done.emit(proc.returncode or 0)
                    break
        except Exception as e:
            self.err.emit(f"[Wizard] Fehler beim Start: {e}")
            self.done.emit(1)

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    w = PromptWizard()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
