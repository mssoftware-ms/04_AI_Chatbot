# -*- coding: utf-8 -*-
"""
Claude-Flow@alpha – Befehlszeilen-Wizard (WSL) v2.2
- Tests in neuem WSL-Fenster
- Saved-Config Auto-Scan → --config ./…
- UTF-8-Locale Export
- Lesbare Einzeiler (doppelte Quotes um bash -lc)
- **Neu (2.2):** Warnung bei Projektpfaden unter /mnt/* und
  Button „Symlink‑State (ext4)“, der .hive-mind/.swarm auf ~/cf_state/<slug> verlinkt.
"""

import sys, json, shlex, subprocess, re
from pathlib import Path
from typing import List

from PySide6 import QtCore, QtWidgets, QtGui

APP_TITLE = "Claude-Flow@alpha – Befehlszeilen-Wizard (WSL) v2.2"
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

def list_wsl_distros() -> list[str]:
    try:
        raw = subprocess.check_output(["wsl.exe", "-l", "-q"])
        txt = raw.decode(errors="ignore").replace("\ufeff", "").replace("\x00", "")
        distros = [line.strip() for line in txt.splitlines() if line.strip()]
        return distros or [DEFAULT_DISTRO]
    except Exception:
        return [DEFAULT_DISTRO]

def win_to_wsl_path(win_path: str) -> str:
    if not win_path: return ""
    p = Path(win_path)
    drive = p.drive[:-1].lower() if p.drive else ""
    if drive and len(drive) == 1:
        rel = str(p).replace("\\", "/")[2:]
        return f"/mnt/{drive}{rel}"
    return str(p).replace("\\", "/")

def is_mnt_path(wsl_path: str) -> bool:
    return bool(wsl_path) and wsl_path.startswith("/mnt/")

def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "project"

def build_bash_line(project_wsl: str, commands: list[str]) -> str:
    exports = "export LANG=C.UTF-8; export LC_ALL=C.UTF-8"
    parts = [exports]
    if project_wsl:
        parts.append(f"cd '{project_wsl}'")
    parts.extend(commands)
    return " && ".join(parts)

def escape_double_quotes(s: str) -> str:
    return s.replace('"', r'\"')

def escape_for_wt_semicolons(s: str) -> str:
    return s.replace(";", r"\;")

def scan_saved_configs(project_win: str) -> list[str]:
    out = []
    if not project_win: return out
    base = Path(project_win) / ".claude-flow" / "saved-configs"
    if base.exists():
        for f in sorted(base.glob("*.json")):
            try:
                rel = str(f.relative_to(Path(project_win))).replace("\\", "/")
            except Exception:
                rel = f".claude-flow/saved-configs/{f.name}"
            out.append(rel)
    return out

def build_claude_flow_command(preset: str,
                              objective: str = "",
                              use_npx: bool = True,
                              claude: bool = False,
                              auto_spawn: bool = False,
                              execute: bool = False,
                              ui: bool = False,
                              swarm: bool = False,
                              verbose: bool = True,
                              saved_config_rel: str = "",
                              namespace: str = "",
                              extra_flags: str = "") -> str:
    base = ["npx", "claude-flow@alpha"] if use_npx else ["claude-flow"]
    flags: list[str] = []
    if verbose: flags.append("--verbose")
    if claude:  flags.append("--claude")
    if auto_spawn: flags.append("--auto-spawn")
    if execute: flags.append("--execute")
    if ui: flags.append("--ui")
    if swarm: flags.append("--swarm")
    if namespace.strip(): flags.extend(["--namespace", shlex.quote(namespace.strip())])
    if saved_config_rel.strip(): flags.extend(["--config", shlex.quote("./" + saved_config_rel.strip())])
    if extra_flags.strip(): flags.extend(extra_flags.strip().split())

    cmd: list[str] = [*base]

    if preset == "hive-mind spawn":
        arg = objective if objective else "<objective>"
        cmd.extend(["hive-mind", "spawn", shlex.quote(arg)])
        cmd.extend(flags)
    elif preset == "hive-mind init":
        cmd.extend(["hive-mind", "init"] + flags)
    elif preset == "hive-mind status":
        cmd.extend(["hive-mind", "status"] + flags)
    elif preset == "hive-mind wizard":
        cmd.extend(["hive-mind", "wizard"] + flags)
    elif preset == "start":
        cmd.extend(["start"] + flags)
    elif preset == "swarm":
        arg = objective if objective else "<objective>"
        cmd.extend(["swarm", shlex.quote(arg)] + flags)
    elif preset == "agent list":
        cmd.extend(["agent", "list"] + flags)
    elif preset == "help":
        cmd.extend(["help"])
    elif preset == "help hive-mind":
        cmd.extend(["help", "hive-mind"])
    elif preset == "raw (nur Flags)":
        cmd.extend(flags)
    else:
        cmd.extend(flags)

    return " ".join(cmd).strip()

def build_full_wsl_command(distro: str, project_wsl: str, bash_inner: str, use_windows_terminal: bool = False, new_window: bool = True) -> str:
    bash_line = build_bash_line(project_wsl, [bash_inner])
    lc_str = escape_double_quotes(bash_line)
    if use_windows_terminal:
        wt_bash = escape_for_wt_semicolons(lc_str)
        return f'wt new-tab --title "CF@alpha" wsl.exe -d "{distro}" -- bash -lc "{wt_bash}"'
    if new_window:
        tail = r' && echo -e "\n[Beenden mit Taste …]" && read -n 1 -s -r && exec bash -i'
        lc2 = escape_double_quotes(bash_line + tail)
        return f'cmd /c start "" wsl.exe -d "{distro}" -- bash -lc "{lc2}"'
    else:
        return f'wsl.exe -d "{distro}" -- bash -lc "{lc_str}"'

def build_symlink_script(project_wsl: str) -> str:
    bash = r"""
set -euo pipefail
export LANG=C.UTF-8; export LC_ALL=C.UTF-8
PROJ='{PROJECT_WSL}'
if [ ! -d "$PROJ" ]; then echo "Projektverzeichnis nicht gefunden: $PROJ"; exit 1; fi
NAME="$(basename "$PROJ")"
SLUG="$(printf "%s" "$NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')"
TARGET="$HOME/cf_state/$SLUG"
mkdir -p "$TARGET/hive" "$TARGET/swarm"
cd "$PROJ"

backup_if_needed() {
  local d="$1"
  if [ -e "$d" ] && [ ! -L "$d" ]; then
    local ts="$(date +%s)"
    mv "$d" "$d.bak.$ts"
    echo "Backup erstellt: $d.bak.$ts"
  fi
  rm -rf "$d"
}

backup_if_needed ".hive-mind"
backup_if_needed ".swarm"

ln -s "$TARGET/hive" .hive-mind
ln -s "$TARGET/swarm" .swarm

echo "Symlink-State eingerichtet:"
echo "  .hive-mind -> $TARGET/hive"
echo "  .swarm     -> $TARGET/swarm"
echo
echo "[Taste drücken, um das Fenster zu schließen]"
read -n 1 -s -r
exec bash -i
""".strip()
    return bash.replace("{PROJECT_WSL}", project_wsl)


class CmdWizard(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE); self.resize(1220, 860); self.setStyleSheet(DARK_QSS)

        cw = QtWidgets.QWidget(); self.setCentralWidget(cw)
        root = QtWidgets.QVBoxLayout(cw); root.setContentsMargins(12,12,12,8); root.setSpacing(10)

        # Project + distro
        row1 = QtWidgets.QHBoxLayout(); root.addLayout(row1)
        self.ed_project = QtWidgets.QLineEdit()
        self.btn_browse = QtWidgets.QPushButton("Browse"); self.btn_browse.setObjectName("neutral")
        self.cb_distro = QtWidgets.QComboBox(); self.cb_distro.addItems(list_wsl_distros())
        self.btn_reload = QtWidgets.QPushButton("Reload Distros"); self.btn_reload.setObjectName("neutral")
        self.lbl_wsl = QtWidgets.QLabel("WSL Path:"); self.lbl_wsl_val = QtWidgets.QLabel("-"); self.lbl_wsl_val.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        left = QtWidgets.QFormLayout(); left.addRow("Project Directory (Windows):", self.ed_project); left.addRow("", self.btn_browse); left.addRow(self.lbl_wsl, self.lbl_wsl_val)
        right = QtWidgets.QFormLayout(); right.addRow("WSL Distribution:", self.cb_distro); right.addRow("", self.btn_reload)
        row1.addLayout(left,2); row1.addSpacing(12); row1.addLayout(right,1)

        # Warnbereich
        self.warn = QtWidgets.QFrame()
        self.warn.setStyleSheet("QFrame { border: 1px solid #7c2d12; background: #1e1b16; border-radius: 8px; }")
        wlay = QtWidgets.QHBoxLayout(self.warn); wlay.setContentsMargins(10,8,10,8)
        icon = QtWidgets.QLabel("⚠️")
        txt = QtWidgets.QLabel("Projekt liegt unter /mnt/. Für zuverlässige SQLite-States empfiehlt sich ext4 (WSL-Dateisystem). "
                               "Klicke auf „Symlink‑State (ext4)“, um .hive-mind/.swarm nach ~/cf_state/<slug> zu verlinken.")
        txt.setWordWrap(True)
        self.btn_symlink = QtWidgets.QPushButton("Symlink‑State (ext4)"); self.btn_symlink.setObjectName("secondary")
        wlay.addWidget(icon); wlay.addWidget(txt, 1); wlay.addWidget(self.btn_symlink, 0)
        root.addWidget(self.warn); self.warn.hide()

        # Command preset
        grp_cmd = QtWidgets.QGroupBox("Kommando-Preset & Parameter"); root.addWidget(grp_cmd)
        gl = QtWidgets.QGridLayout(grp_cmd)

        self.cb_preset = QtWidgets.QComboBox()
        self.cb_preset.addItems(["hive-mind spawn","hive-mind init","hive-mind status","hive-mind wizard","start","swarm","agent list","help","help hive-mind","raw (nur Flags)"])

        self.ed_objective = QtWidgets.QPlainTextEdit(); self.ed_objective.setPlaceholderText("Objective/Task (nur für spawn/swarm)")
        self.ed_namespace = QtWidgets.QLineEdit()
        self.cb_saved = QtWidgets.QComboBox(); self.cb_saved.setEditable(True); self.cb_saved.setPlaceholderText(".claude-flow/saved-configs/… (optional)")
        self.ed_extra = QtWidgets.QLineEdit(); self.ed_extra.setPlaceholderText("Weitere Flags, z. B. --agents 8 --strategy parallel")

        self.chk_npx = QtWidgets.QCheckBox("npx verwenden"); self.chk_npx.setChecked(True)
        self.chk_verbose = QtWidgets.QCheckBox("--verbose"); self.chk_verbose.setChecked(True)
        self.chk_claude = QtWidgets.QCheckBox("--claude"); self.chk_auto = QtWidgets.QCheckBox("--auto-spawn"); self.chk_exec = QtWidgets.QCheckBox("--execute")
        self.chk_ui = QtWidgets.QCheckBox("--ui (start)"); self.chk_swarm = QtWidgets.QCheckBox("--swarm (start)")

        gl.addWidget(QtWidgets.QLabel("Preset:"), 0, 0); gl.addWidget(self.cb_preset, 0, 1, 1, 3)
        gl.addWidget(QtWidgets.QLabel("Objective:"), 1, 0); gl.addWidget(self.ed_objective, 1, 1, 1, 3)
        gl.addWidget(QtWidgets.QLabel("Namespace:"), 2, 0); gl.addWidget(self.ed_namespace, 2, 1)
        gl.addWidget(QtWidgets.QLabel("Saved-Config (relativ):"), 2, 2); gl.addWidget(self.cb_saved, 2, 3)
        gl.addWidget(QtWidgets.QLabel("Weitere Flags:"), 3, 0); gl.addWidget(self.ed_extra, 3, 1, 1, 3)
        gl.addWidget(self.chk_npx, 4, 0); gl.addWidget(self.chk_verbose, 4, 1); gl.addWidget(self.chk_claude, 4, 2); gl.addWidget(self.chk_auto, 4, 3)
        gl.addWidget(self.chk_exec, 5, 0); gl.addWidget(self.chk_ui, 5, 1); gl.addWidget(self.chk_swarm, 5, 2)

        # Ausgabeformat
        grp_fmt = QtWidgets.QGroupBox("Ausgabeformat (Einzeiler)"); root.addWidget(grp_fmt)
        hb = QtWidgets.QHBoxLayout(grp_fmt)
        self.rb_wsl_direct = QtWidgets.QRadioButton("WSL (direkt)"); self.rb_cmd_window = QtWidgets.QRadioButton("CMD neues Fenster")
        self.rb_wt = QtWidgets.QRadioButton("Windows Terminal (wt) – neuer Tab"); self.rb_plain_bash = QtWidgets.QRadioButton("Nur Linux-Befehl (für Bash in WSL)")
        self.rb_wsl_direct.setChecked(True)
        for r in (self.rb_wsl_direct, self.rb_cmd_window, self.rb_wt, self.rb_plain_bash): hb.addWidget(r)

        # Ergebnis
        grp_out = QtWidgets.QGroupBox("Ergebnis"); root.addWidget(grp_out)
        gv = QtWidgets.QVBoxLayout(grp_out); self.ed_output = QtWidgets.QPlainTextEdit(); self.ed_output.setReadOnly(True); self.ed_output.setMaximumHeight(160); gv.addWidget(self.ed_output)
        hb2 = QtWidgets.QHBoxLayout(); gv.addLayout(hb2)
        self.btn_build = QtWidgets.QPushButton("Befehl erzeugen"); self.btn_build.setObjectName("secondary")
        self.btn_copy = QtWidgets.QPushButton("Copy"); self.btn_copy.setObjectName("neutral")
        self.btn_save = QtWidgets.QPushButton("Als .cmd speichern"); self.btn_save.setObjectName("neutral")
        self.btn_test_help = QtWidgets.QPushButton("Test: help (neues Fenster)"); self.btn_test_help.setObjectName("neutral")
        self.btn_test_hm = QtWidgets.QPushButton("Test: help hive-mind (neues Fenster)"); self.btn_test_hm.setObjectName("neutral")
        hb2.addWidget(self.btn_build); hb2.addStretch(1); hb2.addWidget(self.btn_copy); hb2.addWidget(self.btn_save); hb2.addWidget(self.btn_test_help); hb2.addWidget(self.btn_test_hm)

        self.status = self.statusBar(); self.status.showMessage("Bereit.")

        # Signals
        self.btn_browse.clicked.connect(self.on_browse)
        self.ed_project.textChanged.connect(self.on_project_changed)
        self.btn_reload.clicked.connect(self.reload_distros)
        self.btn_build.clicked.connect(self.build_command)
        self.btn_copy.clicked.connect(self.copy_output)
        self.btn_save.clicked.connect(self.save_cmd)
        self.btn_test_help.clicked.connect(lambda: self.run_test(True, "help"))
        self.btn_test_hm.clicked.connect(lambda: self.run_test(True, "help hive-mind"))
        self.btn_symlink.clicked.connect(self.on_symlink_state)

        # Defaults
        self.settings_path = Path.home() / ".cf_cmd_wizard.json"
        self.restore_settings()
        self.on_project_changed(self.ed_project.text())

    # --- utils

    def restore_settings(self):
        if self.settings_path.exists():
            try:
                data = json.loads(self.settings_path.read_text(encoding="utf-8"))
                self.ed_project.setText(data.get("project_win", ""))
                d = data.get("distro", DEFAULT_DISTRO)
                avail = [self.cb_distro.itemText(i) for i in range(self.cb_distro.count())]
                if d in avail: self.cb_distro.setCurrentText(d)
            except Exception: pass

    def persist_settings(self):
        try:
            obj = {"project_win": self.ed_project.text().strip(), "distro": self.cb_distro.currentText().strip()}
            self.settings_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception: pass

    def on_browse(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Projektverzeichnis wählen")
        if d: self.ed_project.setText(d)

    def on_project_changed(self, txt: str):
        wsl_path = win_to_wsl_path(txt.strip())
        self.lbl_wsl_val.setText(wsl_path or "-")
        # Warnung bei /mnt/*
        show = is_mnt_path(wsl_path)
        self.warn.setVisible(show)
        # Saved-Configs scannen
        self.cb_saved.clear()
        files = scan_saved_configs(txt.strip())
        if files: self.cb_saved.addItems(files)
        else: self.cb_saved.addItem("")

    def reload_distros(self):
        self.cb_distro.clear(); self.cb_distro.addItems(list_wsl_distros()); self.status.showMessage("WSL-Distributionen aktualisiert.", 3000)

    def _gather(self):
        return {
            "preset": self.cb_preset.currentText(),
            "objective": self.ed_objective.toPlainText().strip(),
            "use_npx": True,
            "claude": self.chk_claude.isChecked(),
            "auto_spawn": self.chk_auto.isChecked(),
            "execute": self.chk_exec.isChecked(),
            "ui": self.chk_ui.isChecked(),
            "swarm": self.chk_swarm.isChecked(),
            "verbose": self.chk_verbose.isChecked(),
            "saved_config_rel": self.cb_saved.currentText().strip(),
            "namespace": self.ed_namespace.text().strip(),
            "extra_flags": self.ed_extra.text().strip(),
            "distro": self.cb_distro.currentText().strip(),
            "project_wsl": self.lbl_wsl_val.text().strip(),
        }

    def build_command(self):
        cfg = self._gather()
        bash_inner = build_claude_flow_command(**{k: cfg[k] for k in [
            "preset","objective","use_npx","claude","auto_spawn","execute","ui","swarm","verbose","saved_config_rel","namespace","extra_flags"
        ]})
        if self.rb_plain_bash.isChecked():
            full = build_bash_line(cfg["project_wsl"], [bash_inner])
            # reine Info: als Ganzes quoten, falls Leerzeichen
            if " " in full and not (full.startswith('"') or full.startswith("'")):
                full = f'"{full}"'
        elif self.rb_wt.isChecked():
            full = build_full_wsl_command(cfg["distro"], cfg["project_wsl"], bash_inner, use_windows_terminal=True, new_window=True)
        elif self.rb_cmd_window.isChecked():
            full = build_full_wsl_command(cfg["distro"], cfg["project_wsl"], bash_inner, use_windows_terminal=False, new_window=True)
        else:
            full = build_full_wsl_command(cfg["distro"], cfg["project_wsl"], bash_inner, use_windows_terminal=False, new_window=False)
        self.ed_output.setPlainText(full); self.status.showMessage("Befehl erzeugt.", 1500)

    def copy_output(self):
        QtWidgets.QApplication.clipboard().setText(self.ed_output.toPlainText().strip()); self.status.showMessage("In Zwischenablage kopiert.", 1500)

    def save_cmd(self):
        txt = self.ed_output.toPlainText().strip()
        if not txt: self.status.showMessage("Kein Befehl vorhanden.", 2000); return
        fn, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Als .cmd speichern", "claude-flow-call.cmd", "Batch (*.cmd);;Text (*.txt)")
        if not fn: return
        Path(fn).write_text(txt + "\r\n", encoding="utf-8"); self.status.showMessage("Gespeichert.", 2000)

    def run_test(self, new_window: bool, which: str):
        proj = self.lbl_wsl_val.text().strip()
        if not proj or proj == "-":
            QtWidgets.QMessageBox.warning(self, "Projektpfad fehlt", "Bitte Projektpfad setzen."); return
        inner = "npx claude-flow@alpha help" if which == "help" else "npx claude-flow@alpha help hive-mind"
        bash_line = build_bash_line(proj, [inner])
        lc2 = bash_line + r' && echo -e "\n[Beenden mit Taste …]" && read -n 1 -s -r && exec bash -i'
        # Doppel-Quotes escapen
        lc2 = escape_double_quotes(lc2)
        args = ["cmd", "/c", "start", "", "wsl.exe", "-d", self.cb_distro.currentText().strip(), "--", "bash", "-lc", lc2]
        try:
            subprocess.Popen(args, close_fds=True); self.status.showMessage(f"Test '{which}' in neuem Fenster gestartet.", 4000)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Fehler", f"Konnte neues Fenster nicht öffnen:\n{e}")

    def on_symlink_state(self):
        proj = self.lbl_wsl_val.text().strip()
        if not proj or proj == "-":
            QtWidgets.QMessageBox.warning(self, "Projektpfad fehlt", "Bitte Projektpfad setzen."); return
        # Script bauen und in neuem WSL-Fenster starten
        script = build_symlink_script(proj)
        lc = escape_double_quotes(script)
        args = ["cmd", "/c", "start", "", "wsl.exe", "-d", self.cb_distro.currentText().strip(), "--", "bash", "-lc", lc]
        try:
            subprocess.Popen(args, close_fds=True)
            self.status.showMessage("Symlink‑State‑Einrichtung in neuem Fenster gestartet.", 5000)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Fehler", f"Konnte Symlink‑Setup nicht starten:\n{e}")

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        self.persist_settings(); return super().closeEvent(e)

def main():
    app = QtWidgets.QApplication(sys.argv); app.setApplicationName(APP_TITLE)
    w = CmdWizard(); w.show(); sys.exit(app.exec())

if __name__ == "__main__":
    main()


class MCPDialog(QtWidgets.QDialog):
    """
    Generator für MCP-Befehle (Claude Code CLI). Führt NICHT aus – nur Ausgabe.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MCP-Befehle generieren (Claude Code)")
        self.resize(780, 520)
        try:
            self.setStyleSheet(DARK_QSS)
        except Exception:
            pass

        lay = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        lay.addLayout(form)

        self.cb_scope = QtWidgets.QComboBox(); self.cb_scope.addItems(["project","user"])
        self.cb_kind = QtWidgets.QComboBox(); self.cb_kind.addItems([
            "list","get","add (stdio)","add (sse)","add (http)","add-json","enableAllProjectMcpServers=true"
        ])
        self.ed_name = QtWidgets.QLineEdit(); self.ed_name.setPlaceholderText("Server-Name (z. B. github/linear)")
        self.ed_transport = QtWidgets.QLineEdit(); self.ed_transport.setPlaceholderText("SSE/HTTP: URL · stdio: Befehl")
        self.ed_args = QtWidgets.QLineEdit(); self.ed_args.setPlaceholderText("Args/Env, z. B. --env KEY=VAL -- npx -y my-mcp")
        self.chk_wsl = QtWidgets.QCheckBox("Als kompletten WSL-Einzeiler ausgeben"); self.chk_wsl.setChecked(True)
        self.ed_distro = QtWidgets.QLineEdit("Ubuntu")

        form.addRow("Scope:", self.cb_scope)
        form.addRow("Aktion:", self.cb_kind)
        form.addRow("Name:", self.ed_name)
        form.addRow("URL/Befehl:", self.ed_transport)
        form.addRow("Args/Env:", self.ed_args)
        form.addRow("WSL Distro:", self.ed_distro)
        form.addRow("", self.chk_wsl)

        self.out = QtWidgets.QPlainTextEdit(); self.out.setReadOnly(False)
        lay.addWidget(self.out, 1)

        btns = QtWidgets.QHBoxLayout(); lay.addLayout(btns)
        self.btn_build = QtWidgets.QPushButton("Befehl erzeugen"); 
        self.btn_copy = QtWidgets.QPushButton("In Zwischenablage"); 
        self.btn_close = QtWidgets.QPushButton("Schließen")
        btns.addWidget(self.btn_build); btns.addStretch(1); btns.addWidget(self.btn_copy); btns.addWidget(self.btn_close)

        self.btn_build.clicked.connect(self.on_build)
        self.btn_copy.clicked.connect(lambda: QtWidgets.QApplication.clipboard().setText(self.out.toPlainText()))
        self.btn_close.clicked.connect(self.accept)

    def build_linux(self) -> str:
        kind = self.cb_kind.currentText()
        scope = self.cb_scope.currentText()
        name = self.ed_name.text().strip()
        tr = self.ed_transport.text().strip()
        args = self.ed_args.text().strip()

        if kind == "list":
            return "claude mcp list"
        if kind == "get":
            return f"claude mcp get {name or '<name>'}"
        if kind == "add (stdio)":
            base = f"claude mcp add --scope {scope} {name or '<name>'}"
            return f"{base} {args or '-- /path/to/server'}"
        if kind == "add (sse)":
            return f"claude mcp add --scope {scope} --transport sse {name or '<name>'} {tr or 'https://example/sse'}"
        if kind == "add (http)":
            return f"claude mcp add --scope {scope} --transport http {name or '<name>'} {tr or 'https://example/http'}"
        if kind == "add-json":
            payload = '{"type":"stdio","command":"/path/to/cli","args":["--flag"],"env":{}}'
            return f"claude mcp add-json {name or 'custom'} '{payload}'"
        if kind == "enableAllProjectMcpServers=true":
            py = """python3 - <<'PY'
import json, os, pathlib
p = pathlib.Path.home()/'.claude'/'settings.json'
p.parent.mkdir(parents=True, exist_ok=True)
try:
 d = json.loads(p.read_text())
except Exception:
 d = {}
d['enableAllProjectMcpServers'] = True
p.write_text(json.dumps(d, indent=2))
print('OK: enableAllProjectMcpServers=true')
PY"""
            return py
        return ""

    def on_build(self):
        lin = self.build_linux()
        if not self.chk_wsl.isChecked():
            self.out.setPlainText(lin); return
        distro = self.ed_distro.text().strip() or "Ubuntu"
        bash = lin.replace('"', r'\"')
        wsl = f'wsl.exe -d "{distro}" -- bash -lc "{bash}"'
        self.out.setPlainText(wsl)


        # Menü → MCP-Dialog
        try:
            mb = self.menuBar()
            tools = mb.addMenu('Tools')
            act_mcp = tools.addAction('MCP-Befehle generieren…')
            act_mcp.triggered.connect(lambda: MCPDialog(self).exec())
        except Exception:
            pass
