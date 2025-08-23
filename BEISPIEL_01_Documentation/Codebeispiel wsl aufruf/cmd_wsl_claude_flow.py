import sys
import shlex
import subprocess
import shutil
from typing import List

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QPlainTextEdit, QMessageBox
)
from PySide6.QtCore import Qt

APP_TITLE = "WSL Hive-Mind Launcher"

# ---------- Helpers ----------

def _sanitize(s: str) -> str:
    """Entfernt BOM/Nullbytes und trimmt."""
    return s.replace("\ufeff", "").replace("\x00", "").strip()

def list_wsl_distros() -> List[str]:
    """
    Liefert verfügbare WSL-Distributionen.
    WICHTIG: Die Ausgabe von `wsl.exe -l -q` ist oft UTF-16LE.
    """
    try:
        raw = subprocess.check_output(["wsl.exe", "-l", "-q"])  # Bytes!
        try:
            txt = raw.decode("utf-16le")
        except UnicodeDecodeError:
            try:
                txt = raw.decode("utf-8")
            except UnicodeDecodeError:
                txt = raw.decode("mbcs", errors="ignore")
        txt = txt.replace("\ufeff", "")
        names = []
        for line in txt.splitlines():
            s = _sanitize(line)
            if not s:
                continue
            if s.endswith("(Default)"):
                s = s.replace("(Default)", "").strip()
            names.append(s)
        return names or ["Ubuntu"]
    except Exception:
        return ["Ubuntu"]

def build_inner_command(task: str, use_claude: bool = True, verbose: bool = True) -> str:
    """
    Baut den Linux-Befehl für bash -lc.
    """
    parts = ["claude-flow", "hive-mind", "spawn", shlex.quote(task)]
    if use_claude:
        parts.append("--claude")
    if verbose:
        parts.append("--verbose")
    base = " ".join(parts)
    keep_open = (
        f"{base}; echo; echo '--- Hive-Mind Task beendet ---'; "
        f"read -n 1 -s -r -p 'Taste drücken, um die Sitzung zu beenden …'; echo; exec bash -i"
    )
    return keep_open

def _escape_for_wt(cmd: str) -> str:
    """
    Windows Terminal (wt.exe) nutzt ';' als Befehls-Trenner.
    Um zu verhindern, dass 'wt' unser bash-Kommando zerlegt,
    escapen wir Semikolons mit Backslash.
    Referenz: WT Command-Line Arguments.  # noqa
    """
    return cmd.replace(";", r"\;")

def launch_with_windows_terminal(distro: str, inner_cmd: str, title: str) -> bool:
    """
    Öffnet Windows Terminal (wt.exe) in neuem Tab und startet darin WSL:
        wt.exe new-tab --title "<Titel>" wsl.exe -d <Distro> -- bash -lc '<inner_cmd>'
    Semikolons im inner_cmd werden speziell für wt.exe ge-escaped.
    """
    wt = shutil.which("wt.exe")
    if not wt:
        return False

    distro = _sanitize(distro)
    title = _sanitize(title)

    # Nur für WT: Semikolons escapen, sonst spawnt WT mehrere Tabs/Kommandos.
    inner_cmd_wt = _escape_for_wt(inner_cmd)

    try:
        subprocess.Popen(
            [
                wt,
                "new-tab",
                "--title", title,
                "wsl.exe", "-d", distro, "--", "bash", "-lc", inner_cmd_wt
            ],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
        return True
    except Exception:
        return False

def launch_with_cmd_fallback(distro: str, inner_cmd: str, title: str) -> None:
    """
    Fallback ohne Windows Terminal:
        cmd.exe /c start "<Titel>" wsl.exe -d <Distro> -- bash -lc '<inner_cmd>'
    (Hier KEIN Semikolon-Escaping nötig.)
    """
    distro = _sanitize(distro)
    title = _sanitize(title)
    subprocess.Popen(
        [
            "cmd.exe", "/c", "start", title,
            "wsl.exe", "-d", distro, "--", "bash", "-lc", inner_cmd
        ],
        shell=False
    )

# ---------- UI ----------

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumWidth(860)
        self.setStyleSheet("""
            QWidget { background: #0f1115; color: #e6e6e6; font-size: 12pt; }
            QLineEdit, QComboBox, QPlainTextEdit { background: #171a21; border: 1px solid #2a2f3a; border-radius: 6px; padding: 6px; }
            QPushButton { background: #2463eb; border: none; border-radius: 8px; padding: 10px 14px; color: white; font-weight: 600; }
            QPushButton:hover { background: #1d4fd8; }
            QLabel { color: #e6e6e6; }
        """)

        layout = QVBoxLayout(self)

        # Row: Distro + Optionen
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("WSL-Distribution:", self))
        self.cmb_distro = QComboBox(self)
        for d in list_wsl_distros():
            self.cmb_distro.addItem(d)
        row1.addWidget(self.cmb_distro, 2)

        self.chk_claude = QCheckBox("--claude", self)
        self.chk_claude.setChecked(True)
        row1.addWidget(self.chk_claude)

        self.chk_verbose = QCheckBox("--verbose", self)
        self.chk_verbose.setChecked(True)
        row1.addWidget(self.chk_verbose)

        layout.addLayout(row1)

        # Row: Task
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Task:", self))
        self.ed_task = QLineEdit(self)
        self.ed_task.setPlaceholderText("####Task####")
        row2.addWidget(self.ed_task, 4)
        layout.addLayout(row2)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("Hive-Mind in externem WSL-Terminal starten", self)
        self.btn_start.clicked.connect(self.on_start_clicked)
        btn_row.addWidget(self.btn_start)

        self.btn_test = QPushButton("Verfügbarkeit testen", self)
        self.btn_test.clicked.connect(self.on_test_clicked)
        btn_row.addWidget(self.btn_test)

        layout.addLayout(btn_row)

        # Log
        self.log = QPlainTextEdit(self)
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Logausgaben …")
        layout.addWidget(self.log, 3)

        self.log.appendPlainText(
            "Hinweis: Bevorzugt wird Windows Terminal (wt.exe). "
            "Ohne wt.exe wird ein klassisches Terminalfenster verwendet."
        )

    def on_start_clicked(self):
        task = self.ed_task.text().strip() or "####Task####"
        distro = _sanitize(self.cmb_distro.currentText())
        inner_cmd = build_inner_command(
            task=task,
            use_claude=self.chk_claude.isChecked(),
            verbose=self.chk_verbose.isChecked()
        )
        title = f"Hive-Mind – {distro}"

        if launch_with_windows_terminal(distro, inner_cmd, title):
            self.log.appendPlainText(f"[OK] Windows Terminal gestartet (Distro: {distro}).")
            self.log.appendPlainText(f"bash -lc '{inner_cmd}'")
            return

        try:
            launch_with_cmd_fallback(distro, inner_cmd, title)
            self.log.appendPlainText(f"[OK] Klassisches Terminal gestartet (Distro: {distro}).")
            self.log.appendPlainText(f"bash -lc '{inner_cmd}'")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Start fehlgeschlagen:\n{e}")
            self.log.appendPlainText(f"[FEHLER] {e}")

    def on_test_clicked(self):
        """Prüft, ob 'claude-flow' in der gewählten Distro im PATH liegt."""
        distro = _sanitize(self.cmb_distro.currentText())
        try:
            raw = subprocess.check_output(
                ["wsl.exe", "-d", distro, "--", "bash", "-lc",
                 "command -v claude-flow >/dev/null && echo '__OK__' || echo '__MISSING__'"]
            )
            for enc in ("utf-8", "utf-16le", "mbcs"):
                try:
                    out = raw.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                out = raw.decode("utf-8", errors="ignore")
            if "__OK__" in out:
                self.log.appendPlainText(f"[CHECK] claude-flow gefunden in {distro}.")
            else:
                self.log.appendPlainText(f"[CHECK] claude-flow NICHT gefunden in {distro}.")
        except subprocess.CalledProcessError as e:
            self.log.appendPlainText(f"[CHECK] Fehler: {getattr(e, 'output', b'').decode('utf-8', 'ignore')}")
        except Exception as e:
            self.log.appendPlainText(f"[CHECK] Fehler: {e}")

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
