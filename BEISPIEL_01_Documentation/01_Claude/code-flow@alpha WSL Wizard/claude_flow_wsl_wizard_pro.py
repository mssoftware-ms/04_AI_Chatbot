# -*- coding: utf-8 -*-
"""
Claude-Flow@alpha – WSL Prompt Wizard (Pro)
- PySide6 GUI
- WSL oneshot spawn: `npx claude-flow@alpha hive-mind spawn ...`
- Uses .claude-flow/saved-configs/*.json
- Profiles (CRUD) stored at <Project>/.claude_flow/claude-flow-manager/command_profiles.json
- Command preview, copy to clipboard, dry-run
- Optional mirror to .claude/config.json
"""

import sys, json, shlex, subprocess, os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from PySide6 import QtCore, QtWidgets, QtGui

APP_TITLE = "Claude-Flow@alpha – WSL Prompt Wizard (Pro)"
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

# ---------- Helpers ----------

def decode_wsl_output(b: bytes) -> str:
    for enc in ("utf-16le", "utf-8", "cp1252"):
        try:
            return b.decode(enc, errors="replace")
        except Exception:
            pass
    return b.decode("utf-8", errors="replace")

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

def build_spawn_command(task_text: str, saved_config_rel: str, namespace: str = "", extra_flags: Optional[List[str]] = None) -> str:
    flags = ["--claude", "--verbose"]
    if saved_config_rel:
        flags.extend(["--config", f"./{saved_config_rel}"])
    if namespace.strip():
        flags.extend(["--namespace", shlex.quote(namespace.strip())])
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

def get_store_path(project_win: str) -> Path:
    return Path(project_win) / ".claude_flow" / "claude-flow-manager" / "command_profiles.json"

# ---------- Data Model ----------

@dataclass
class CommandProfile:
    id: str
    name: str
    task_text: str
    saved_config_rel: str
    namespace: str = ""
    extra_flags: str = ""          # space-separated e.g. "--agents 3"
    distro: str = DEFAULT_DISTRO
    open_in_new_window: bool = True
    use_windows_terminal: bool = False
    created_at: str = ""
    updated_at: str = ""

class CommandProfileStore:
    def __init__(self, json_path: Path):
        self.json_path = json_path
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.json_path.exists():
            self._write({"profiles": []})

    def _read(self) -> dict:
        try:
            return json.loads(self.json_path.read_text(encoding="utf-8"))
        except Exception:
            return {"profiles": []}

    def _write(self, obj: dict):
        tmp = self.json_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.json_path)

    def list(self) -> List[CommandProfile]:
        raw = self._read().get("profiles", [])
        items: List[CommandProfile] = []
        for p in raw:
            try:
                items.append(CommandProfile(**p))
            except TypeError:
                # backward compatibility (older structure)
                if "command" in p and "name" in p:
                    items.append(CommandProfile(
                        id=p.get("id", str(uuid4())),
                        name=p["name"],
                        task_text="",
                        saved_config_rel=p.get("saved_config_rel", ""),
                        namespace="",
                        extra_flags="",
                        distro=p.get("distro", DEFAULT_DISTRO),
                        open_in_new_window=p.get("open_in_new_window", True),
                        use_windows_terminal=p.get("use_windows_terminal", False),
                        created_at=p.get("created_at", ""),
                        updated_at=p.get("updated_at", ""),
                    ))
        return items

    def upsert(self, profile: CommandProfile):
        data = self._read()
        pl = data.setdefault("profiles", [])
        for i, p in enumerate(pl):
            if p.get("id") == profile.id:
                pl[i] = asdict(profile)
                self._write(data)
                return profile
        pl.append(asdict(profile))
        self._write(data)
        return profile

    def create(self, **kwargs) -> CommandProfile:
        now = datetime.now().isoformat()
        p = CommandProfile(
            id=kwargs.get("id") or str(uuid4()),
            name=kwargs["name"],
            task_text=kwargs.get("task_text", ""),
            saved_config_rel=kwargs.get("saved_config_rel", ""),
            namespace=kwargs.get("namespace", ""),
            extra_flags=kwargs.get("extra_flags", ""),
            distro=kwargs.get("distro", DEFAULT_DISTRO),
            open_in_new_window=kwargs.get("open_in_new_window", True),
            use_windows_terminal=kwargs.get("use_windows_terminal", False),
            created_at=now, updated_at=now
        )
        return self.upsert(p)

    def delete(self, pid: str) -> bool:
        data = self._read()
        before = len(data.get("profiles", []))
        data["profiles"] = [p for p in data.get("profiles", []) if p.get("id") != pid]
        self._write(data)
        return len(data["profiles"]) != before

    def export_to(self, dst: Path):
        dst.write_text(self.json_path.read_text(encoding="utf-8"), encoding="utf-8")

    def import_from(self, src: Path):
        data = json.loads(src.read_text(encoding="utf-8"))
        assert "profiles" in data and isinstance(data["profiles"], list)
        self._write(data)

# ---------- Profile Dialog ----------

class ProfileDialog(QtWidgets.QDialog):
    def __init__(self, parent, store: CommandProfileStore, saved_candidates: list[str], distros: list[str]):
        super().__init__(parent)
        self.setWindowTitle("Profile verwalten")
        self.resize(860, 520)
        self.setStyleSheet(DARK_QSS)
        self.store = store
        self.saved_candidates = saved_candidates
        self.distros = distros

        main = QtWidgets.QHBoxLayout(self)
        # list on left
        left = QtWidgets.QVBoxLayout()
        main.addLayout(left, 1)
        self.listw = QtWidgets.QListWidget()
        left.addWidget(self.listw, 1)
        lbtns = QtWidgets.QHBoxLayout()
        left.addLayout(lbtns)
        self.btn_add = QtWidgets.QPushButton("Neu")
        self.btn_dup = QtWidgets.QPushButton("Duplizieren")
        self.btn_del = QtWidgets.QPushButton("Löschen")
        self.btn_import = QtWidgets.QPushButton("Import …")
        self.btn_export = QtWidgets.QPushButton("Export …")
        for b in (self.btn_add, self.btn_dup, self.btn_del, self.btn_import, self.btn_export):
            b.setObjectName("neutral")
        lbtns.addWidget(self.btn_add); lbtns.addWidget(self.btn_dup); lbtns.addWidget(self.btn_del)
        lbtns.addStretch(1); lbtns.addWidget(self.btn_import); lbtns.addWidget(self.btn_export)

        # form on right
        right = QtWidgets.QFormLayout()
        main.addLayout(right, 2)

        self.ed_name = QtWidgets.QLineEdit()
        self.cb_saved = QtWidgets.QComboBox(); self.cb_saved.setEditable(True)
        self.cb_saved.addItems(self.saved_candidates)
        self.ed_task = QtWidgets.QPlainTextEdit()
        self.ed_namespace = QtWidgets.QLineEdit()
        self.ed_extra = QtWidgets.QLineEdit()
        self.cb_distro = QtWidgets.QComboBox(); self.cb_distro.addItems(self.distros)
        self.chk_newwin = QtWidgets.QCheckBox("In neuem Fenster starten")
        self.chk_newwin.setChecked(True)
        self.chk_wt = QtWidgets.QCheckBox("Windows Terminal verwenden")

        right.addRow("Name:", self.ed_name)
        right.addRow("Saved-Config (relativ):", self.cb_saved)
        right.addRow("Task (Objective):", self.ed_task)
        right.addRow("Namespace (optional):", self.ed_namespace)
        right.addRow("Weitere Flags:", self.ed_extra)
        right.addRow("WSL Distro:", self.cb_distro)
        right.addRow("", self.chk_newwin)
        right.addRow("", self.chk_wt)

        btm = QtWidgets.QHBoxLayout()
        main.addLayout(btm, 0)
        self.btn_apply = QtWidgets.QPushButton("Speichern")
        self.btn_close = QtWidgets.QPushButton("Schließen")
        self.btn_apply.setObjectName("secondary")
        btm.addStretch(1); btm.addWidget(self.btn_apply); btm.addWidget(self.btn_close)

        self.btn_add.clicked.connect(self.on_add)
        self.btn_dup.clicked.connect(self.on_dup)
        self.btn_del.clicked.connect(self.on_del)
        self.btn_import.clicked.connect(self.on_import)
        self.btn_export.clicked.connect(self.on_export)
        self.btn_apply.clicked.connect(self.on_apply)
        self.btn_close.clicked.connect(self.accept)
        self.listw.currentItemChanged.connect(self.on_sel)

        self.load()

    def load(self):
        self.listw.clear()
        self.profiles = self.store.list()
        for p in self.profiles:
            it = QtWidgets.QListWidgetItem(p.name)
            it.setData(QtCore.Qt.UserRole, p.id)
            self.listw.addItem(it)
        if self.profiles:
            self.listw.setCurrentRow(0)

    # selection -> populate
    def on_sel(self, cur: QtWidgets.QListWidgetItem, prev: QtWidgets.QListWidgetItem):
        if not cur: return
        pid = cur.data(QtCore.Qt.UserRole)
        p = next((x for x in self.profiles if x.id == pid), None)
        if not p: return
        self.ed_name.setText(p.name)
        self.cb_saved.setCurrentText(p.saved_config_rel)
        self.ed_task.setPlainText(p.task_text)
        self.ed_namespace.setText(p.namespace)
        self.ed_extra.setText(p.extra_flags)
        self.cb_distro.setCurrentText(p.distro if p.distro in self.distros else self.distros[0])
        self.chk_newwin.setChecked(p.open_in_new_window)
        self.chk_wt.setChecked(p.use_windows_terminal)

    def collect(self) -> CommandProfile:
        cur = self.listw.currentItem()
        pid = cur.data(QtCore.Qt.UserRole) if cur else str(uuid4())
        now = datetime.now().isoformat()
        p = CommandProfile(
            id=pid,
            name=self.ed_name.text().strip() or "Ohne Titel",
            task_text=self.ed_task.toPlainText().strip(),
            saved_config_rel=self.cb_saved.currentText().strip(),
            namespace=self.ed_namespace.text().strip(),
            extra_flags=self.ed_extra.text().strip(),
            distro=self.cb_distro.currentText().strip(),
            open_in_new_window=self.chk_newwin.isChecked(),
            use_windows_terminal=self.chk_wt.isChecked(),
            created_at=now, updated_at=now
        )
        return p

    def on_add(self):
        it = QtWidgets.QListWidgetItem("Neues Profil")
        pid = str(uuid4())
        it.setData(QtCore.Qt.UserRole, pid)
        self.listw.addItem(it)
        self.listw.setCurrentItem(it)
        self.ed_name.setText("Neues Profil")
        self.cb_saved.setCurrentText(".claude-flow/saved-configs/AI Coding Station.json")
        self.ed_task.setPlainText("Bearbeite alle offenen Issues im Ordner ./issues …")
        self.ed_namespace.setText("")
        self.ed_extra.setText("")
        self.chk_newwin.setChecked(True)
        self.chk_wt.setChecked(False)

    def on_dup(self):
        cur = self.listw.currentItem()
        if not cur: return
        cp = self.collect()
        cp.id = str(uuid4()); cp.name += " (Kopie)"
        self.store.upsert(cp); self.load()

    def on_del(self):
        cur = self.listw.currentItem()
        if not cur: return
        pid = cur.data(QtCore.Qt.UserRole)
        self.store.delete(pid); self.load()

    def on_apply(self):
        p = self.collect()
        self.store.upsert(p)
        self.load()

    def on_export(self):
        fn, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Profile exportieren nach …", "", "JSON (*.json)")
        if not fn: return
        self.store.export_to(Path(fn))

    def on_import(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Profile importieren …", "", "JSON (*.json)")
        if not fn: return
        try:
            self.store.import_from(Path(fn))
            self.load()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Import fehlgeschlagen", str(e))

# ---------- Main Window ----------

class MainWin(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1080, 760)
        self.setStyleSheet(DARK_QSS)

        cw = QtWidgets.QWidget(); self.setCentralWidget(cw)
        root = QtWidgets.QVBoxLayout(cw); root.setContentsMargins(12, 12, 12, 8); root.setSpacing(10)

        # Project + distro
        row1 = QtWidgets.QHBoxLayout(); root.addLayout(row1)
        self.ed_project = QtWidgets.QLineEdit()
        self.btn_browse = QtWidgets.QPushButton("Browse"); self.btn_browse.setObjectName("neutral")
        self.lbl_wsl = QtWidgets.QLabel("WSL Path:"); self.lbl_wsl_val = QtWidgets.QLabel("-")
        self.lbl_wsl_val.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.cb_distro = QtWidgets.QComboBox(); self.cb_distro.addItems(list_wsl_distros())
        self.btn_reload_dist = QtWidgets.QPushButton("Reload Distros"); self.btn_reload_dist.setObjectName("neutral")
        self.btn_mcp_list.clicked.connect(self.mcp_list)
        self.btn_mcp_add_sse.clicked.connect(self.mcp_add_sse)
        self.btn_mcp_enable.clicked.connect(self.mcp_enable)

        left = QtWidgets.QFormLayout(); left.addRow("Project Directory (Windows):", self.ed_project); left.addRow("", self.btn_browse); left.addRow(self.lbl_wsl, self.lbl_wsl_val)
        right = QtWidgets.QFormLayout(); right.addRow("WSL Distribution:", self.cb_distro); right.addRow("", self.btn_reload_dist)
        row1.addLayout(left, 2); row1.addSpacing(12); row1.add
        # MCP quick actions
        grp_mcp = QtWidgets.QGroupBox('MCP-Server (Claude Code)')
        root.addWidget(grp_mcp)
        mcp_lay = QtWidgets.QHBoxLayout(grp_mcp)
        self.btn_mcp_list = QtWidgets.QPushButton('MCP: list'); self.btn_mcp_list.setObjectName('neutral')
        self.btn_mcp_enable = QtWidgets.QPushButton('enableAllProjectMcpServers'); self.btn_mcp_enable.setObjectName('neutral')
        self.btn_mcp_add_sse = QtWidgets.QPushButton('add (SSE)'); self.btn_mcp_add_sse.setObjectName('neutral')
        mcp_lay.addWidget(self.btn_mcp_list); mcp_lay.addWidget(self.btn_mcp_add_sse); mcp_lay.addWidget(self.btn_mcp_enable); mcp_lay.addStretch(1)
Layout(right, 1)

        # Saved-config selection
        grp_saved = QtWidgets.QGroupBox("Saved-Config auswählen (.claude-flow/saved-configs)"); root.addWidget(grp_saved)
        gl = QtWidgets.QGridLayout(grp_saved)
        self.cb_saved = QtWidgets.QComboBox()
        self.btn_scan = QtWidgets.QPushButton("Scan"); self.btn_scan.setObjectName("neutral")
        self.chk_mirror = QtWidgets.QCheckBox("Optional: zusätzlich nach .claude/config.json spiegeln")
        gl.addWidget(QtWidgets.QLabel("Datei:"), 0, 0); gl.addWidget(self.cb_saved, 0, 1); gl.addWidget(self.btn_scan, 0, 2); gl.addWidget(self.chk_mirror, 1, 1, 1, 2)

        # Profiles + task
        grp_prof = QtWidgets.QGroupBox("Profile & Task"); root.addWidget(grp_prof)
        v = QtWidgets.QVBoxLayout(grp_prof)
        rowp = QtWidgets.QHBoxLayout(); v.addLayout(rowp)
        self.cb_profile = QtWidgets.QComboBox()
        self.btn_manage = QtWidgets.QPushButton("Profile …"); self.btn_manage.setObjectName("neutral")
        rowp.addWidget(QtWidgets.QLabel("Profil:")); rowp.addWidget(self.cb_profile, 1); rowp.addWidget(self.btn_manage)

        form = QtWidgets.QGridLayout(); v.addLayout(form)
        self.ed_task = QtWidgets.QPlainTextEdit(); self.ed_task.setPlaceholderText("Beschreibe klar und vollständig, was der Schwarm erledigen soll …")
        self.ed_namespace = QtWidgets.QLineEdit()
        self.ed_extra = QtWidgets.QLineEdit()
        form.addWidget(QtWidgets.QLabel("Task (Objective):"), 0, 0); form.addWidget(self.ed_task, 0, 1, 1, 2)
        form.addWidget(QtWidgets.QLabel("Namespace:"), 1, 0); form.addWidget(self.ed_namespace, 1, 1)
        form.addWidget(QtWidgets.QLabel("Weitere Flags:"), 1, 2); form.addWidget(self.ed_extra, 1, 3)

        # Preview + actions
        grp_prev = QtWidgets.QGroupBox("Preview & Aktionen"); root.addWidget(grp_prev)
        pv = QtWidgets.QGridLayout(grp_prev)
        self.txt_preview = QtWidgets.QPlainTextEdit(); self.txt_preview.setReadOnly(True); self.txt_preview.setMaximumHeight(110)
        self.btn_copy = QtWidgets.QPushButton("Copy"); self.btn_copy.setObjectName("neutral")
        self.btn_open_wsl = QtWidgets.QPushButton("Open WSL Terminal"); self.btn_open_wsl.setObjectName("neutral")
        self.chk_dry = QtWidgets.QCheckBox("Dry Run (nicht ausführen)")
        pv.addWidget(self.txt_preview, 0, 0, 1, 4)
        pv.addWidget(self.btn_copy, 1, 0); pv.addWidget(self.btn_open_wsl, 1, 1); pv.addWidget(self.chk_dry, 1, 3)

        # Buttons
        rowb = QtWidgets.QHBoxLayout(); root.addLayout(rowb)
        self.btn_require = QtWidgets.QPushButton("Check Requirements"); self.btn_require.setObjectName("secondary")
        self.btn_init = QtWidgets.QPushButton("Initialize Claude-Flow"); self.btn_init.setObjectName("secondary")
        self.btn_spawn_sync = QtWidgets.QPushButton("Spawn (same window)")
        self.btn_spawn = QtWidgets.QPushButton("Spawn (new window)")
        rowb.addWidget(self.btn_require); rowb.addWidget(self.btn_init); rowb.addStretch(1); rowb.addWidget(self.btn_spawn_sync); rowb.addWidget(self.btn_spawn)

        # Console
        grp_con = QtWidgets.QGroupBox("Console Output"); root.addWidget(grp_con, 1)
        cv = QtWidgets.QVBoxLayout(grp_con)
        self.txt_console = QtWidgets.QPlainTextEdit(); self.txt_console.setReadOnly(True)
        cv.addWidget(self.txt_console)

        self.status = self.statusBar(); self.status.showMessage("Bereit.")

        # Signals
        self.btn_browse.clicked.connect(self.on_browse)
        self.ed_project.textChanged.connect(self.on_project_changed)
        self.btn_reload_dist.clicked.connect(self.reload_distros)
        self.btn_scan.clicked.connect(self.scan_saved_configs)
        self.btn_manage.clicked.connect(self.open_profiles)
        self.cb_profile.currentIndexChanged.connect(self.on_profile_selected)
        self.ed_task.textChanged.connect(self.update_preview)
        self.ed_namespace.textChanged.connect(self.update_preview)
        self.ed_extra.textChanged.connect(self.update_preview)
        self.cb_saved.currentIndexChanged.connect(self.update_preview)

        self.btn_require.clicked.connect(self.check_requirements)
        self.btn_init.clicked.connect(self.init_cf)
        self.btn_spawn.clicked.connect(self.spawn_new_window)
        self.btn_spawn_sync.clicked.connect(self.spawn_same_window)
        self.btn_copy.clicked.connect(self.copy_preview)
        self.btn_open_wsl.clicked.connect(self.open_wsl_terminal)

        # Defaults
        self.ed_task.setPlainText(
            "Bearbeite alle offenen Issues im Ordner ./issues. Stelle sicher, dass "
            "WIRKLICH ALLE AUFGABEN inkl. Teilaufgaben abgeschlossen und getestet sind, "
            "bevor du das Issue auf closed setzt. Bei Fehlern oder unlösbaren Aufgaben: "
            "Meldung im Terminal und Issue offen lassen. Beachte description, additional "
            "und comments. Abarbeitung step by step (Issue_1.json, Issue_2.json …). "
            "Nach Abschluss state=closed setzen."
        )

        # Restore settings
        self.settings_path = Path.home() / ".cf_wizard_settings.json"
        self.restore_settings()
        self.on_project_changed(self.ed_project.text())

        self.worker = None

    # ---- Utilities ----

    def get_store(self) -> Optional[CommandProfileStore]:
        proj_win = self.ed_project.text().strip()
        if not proj_win: return None
        return CommandProfileStore(get_store_path(proj_win))

    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.txt_console.appendPlainText(f"[{ts}] {msg}")
        self.txt_console.verticalScrollBar().setValue(self.txt_console.verticalScrollBar().maximum())

    def restore_settings(self):
        if self.settings_path.exists():
            try:
                data = json.loads(self.settings_path.read_text(encoding="utf-8"))
                self.ed_project.setText(data.get("project_win", ""))
                d = data.get("distro", DEFAULT_DISTRO)
                if d in [self.cb_distro.itemText(i) for i in range(self.cb_distro.count())]:
                    self.cb_distro.setCurrentText(d)
            except Exception:
                pass

    def persist_settings(self):
        data = {"project_win": self.ed_project.text().strip(), "distro": self.cb_distro.currentText().strip()}
        try: self.settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception: pass

    def on_browse(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Projektverzeichnis wählen")
        if d: self.ed_project.setText(d)

    def on_project_changed(self, txt: str):
        wsl = win_to_wsl_path(txt.strip())
        self.lbl_wsl_val.setText(wsl or "-")
        self.scan_saved_configs()
        self.reload_profiles()
        self.update_preview()

    def reload_distros(self):
        self.cb_distro.clear(); self.cb_distro.addItems(list_wsl_distros())
        self.status.showMessage("WSL-Distributionen aktualisiert.", 3000)

    def scan_saved_configs(self):
        self.cb_saved.clear()
        files = find_saved_configs(self.ed_project.text().strip())
        for f in files: self.cb_saved.addItem(f.name, f)
        if not files: self.cb_saved.addItem("(keine .json gefunden)", None)
        self.update_preview()

    def reload_profiles(self):
        self.cb_profile.clear()
        store = self.get_store()
        if not store: return
        items = store.list()
        for p in items:
            self.cb_profile.addItem(p.name, p.id)
        if not items:
            self.cb_profile.addItem("(kein Profil)", None)

    def on_profile_selected(self, idx: int):
        pid = self.cb_profile.currentData()
        if not pid: return
        store = self.get_store()
        if not store: return
        profs = {p.id: p for p in store.list()}
        p = profs.get(pid)
        if not p: return
        # fill
        self.ed_task.setPlainText(p.task_text)
        self.ed_namespace.setText(p.namespace)
        self.ed_extra.setText(p.extra_flags)
        # try to select saved-config
        for i in range(self.cb_saved.count()):
            n = self.cb_saved.itemText(i)
            if n and n != "(keine .json gefunden)" and p.saved_config_rel.endswith(n):
                self.cb_saved.setCurrentIndex(i); break
        # distro in main window
        if p.distro in [self.cb_distro.itemText(i) for i in range(self.cb_distro.count())]:
            self.cb_distro.setCurrentText(p.distro)
        self.update_preview()

    def open_profiles(self):
        # candidate list of relative saved-configs
        proj = self.ed_project.text().strip()
        cand = []
        for p in find_saved_configs(proj):
            try:
                rel = str(Path(p).relative_to(Path(proj))).replace("\\", "/")
            except Exception:
                rel = f".claude-flow/saved-configs/{Path(p).name}"
            cand.append(rel)
        dist = [self.cb_distro.itemText(i) for i in range(self.cb_distro.count())]
        store = self.get_store()
        if not store:
            QtWidgets.QMessageBox.warning(self, "Hinweis", "Projektpfad ist leer.")
            return
        dlg = ProfileDialog(self, store, cand, dist)
        dlg.exec()
        self.reload_profiles()

    # ---- Preview + Command build ----

    def current_saved_rel(self) -> str:
        item = self.cb_saved.currentData()
        if isinstance(item, Path):
            try:
                return str(Path(item).relative_to(Path(self.ed_project.text().strip()))).replace("\\", "/")
            except Exception:
                return f".claude-flow/saved-configs/{Path(item).name}"
        return ""

    def build_preview(self) -> str:
        task = self.ed_task.toPlainText().strip()
        ns = self.ed_namespace.text().strip()
        flags = self.ed_extra.text().strip().split() if self.ed_extra.text().strip() else None
        saved_rel = self.current_saved_rel()
        cmd = build_spawn_command(task, saved_rel, namespace=ns, extra_flags=flags)
        proj_wsl = self.lbl_wsl_val.text().strip()
        bash_line = build_bash_line(proj_wsl, ["npx claude-flow@alpha init --force", cmd])
        args = ["wsl.exe", "-d", self.cb_distro.currentText(), "--", "bash", "-lc", bash_line]
        return "$ " + " ".join([*args[:-1], f'\"{bash_line}\"'])

    def update_preview(self):
        if not self.ed_project.text().strip() or self.lbl_wsl_val.text().strip() == "-":
            self.txt_preview.setPlainText("(Projektpfad fehlt)")
            return
        self.txt_preview.setPlainText(self.build_preview())

    def copy_preview(self):
        QtWidgets.QApplication.clipboard().setText(self.txt_preview.toPlainText())
        self.status.showMessage("Preview in die Zwischenablage kopiert.", 2500)

    # ---- Execution ----

    def open_wsl_terminal(self):
        proj = self.lbl_wsl_val.text().strip()
        if not proj or proj == "-":
            self.log("Bitte Projektpfad setzen."); return
        bash_line = f"cd {shlex.quote(proj)} && exec bash -i"
        args = ["cmd", "/c", "start", "", "wsl.exe", "-d", self.cb_distro.currentText(), "--", "bash", "-lc", bash_line]
        subprocess.Popen(args, close_fds=True)

    def ensure_saved_exists(self) -> bool:
        item = self.cb_saved.currentData()
        if isinstance(item, Path) and item.exists():
            return True
        QtWidgets.QMessageBox.warning(self, "Saved-Config fehlt", "Keine gültige Saved-Config gefunden.")
        return False

    def run_wsl_stream(self, bash_line: str):
        args = ["wsl.exe", "-d", self.cb_distro.currentText(), "--", "bash", "-lc", bash_line]
        self.log(f"$ {' '.join(args[:-1])} \"{bash_line}\"")
        self.worker = WorkerThread(args)
        self.worker.out.connect(self.log)
        self.worker.err.connect(lambda s: self.log(f"[stderr] {s}"))
        self.worker.done.connect(lambda rc: self.status.showMessage(f"Beendet (RC={rc})", 5000))
        self.worker.start()

    def run_wsl_new_window(self, bash_line: str):
        args = ["cmd", "/c", "start", "", "wsl.exe", "-d", self.cb_distro.currentText(), "--", "bash", "-lc", bash_line + ' && echo -e "\\n[Beenden mit Taste …]" && read -n 1 -s -r && exec bash -i']
        self.log(f"$ start WSL: {bash_line}")
        subprocess.Popen(args, close_fds=True)
        self.status.showMessage("In neuem Fenster gestartet.", 4000)

    def check_requirements(self):
        proj = self.lbl_wsl_val.text().strip()
        if not proj or proj == "-": self.log("Bitte Projektpfad setzen."); return
        cmds = [
            f"cd {shlex.quote(proj)}",
            "node -v || true",
            "npm -v || true",
            "npx --version || true",
            "npx claude-flow@alpha --help | head -n 20 || true"
        ]
        self.run_wsl_stream(" && ".join(cmds))

    def init_cf(self):
        proj = self.lbl_wsl_val.text().strip()
        if not proj or proj == "-": self.log("Bitte Projektpfad setzen."); return
        self.run_wsl_stream(build_bash_line(proj, ["npx claude-flow@alpha init --force"]))

    def spawn_same_window(self):
        if self.chk_dry.isChecked():
            self.log("[Dry-Run] Kein Start – siehe Preview."); return
        if not self.ensure_saved_exists(): return
        proj = self.lbl_wsl_val.text().strip()
        saved_rel = self.current_saved_rel()
        task = self.ed_task.toPlainText().strip()
        ns = self.ed_namespace.text().strip()
        flags = self.ed_extra.text().strip().split() if self.ed_extra.text().strip() else None
        cmd = build_spawn_command(task, saved_rel, namespace=ns, extra_flags=flags)
        bash_line = build_bash_line(proj, ["npx claude-flow@alpha init --force", cmd])
        self.run_wsl_stream(bash_line)

    def spawn_new_window(self):
        if self.chk_dry.isChecked():
            self.log("[Dry-Run] Kein Start – siehe Preview."); return
        if not self.ensure_saved_exists(): return
        proj = self.lbl_wsl_val.text().strip()
        saved_rel = self.current_saved_rel()
        task = self.ed_task.toPlainText().strip()
        ns = self.ed_namespace.text().strip()
        flags = self.ed_extra.text().strip().split() if self.ed_extra.text().strip() else None
        cmd = build_spawn_command(task, saved_rel, namespace=ns, extra_flags=flags)
        bash_line = build_bash_line(proj, ["npx claude-flow@alpha init --force", cmd])
        self.run_wsl_new_window(bash_line)

    # ---- Qt events ----

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        self.persist_settings()
        super().closeEvent(e)

# Worker thread for streaming
class WorkerThread(QtCore.QThread):
    out = QtCore.Signal(str); err = QtCore.Signal(str); done = QtCore.Signal(int)
    def __init__(self, args: list[str], parent=None):
        super().__init__(parent); self._args = args
    def run(self):
        try:
            proc = subprocess.Popen(self._args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            while True:
                if proc.stdout:
                    line = proc.stdout.readline()
                    if line: self.out.emit(decode_wsl_output(line))
                if proc.stderr:
                    el = proc.stderr.readline()
                    if el: self.err.emit(decode_wsl_output(el))
                if proc.poll() is not None:
                    if proc.stdout:
                        rem = proc.stdout.read()
                        if rem: self.out.emit(decode_wsl_output(rem))
                    if proc.stderr:
                        rem2 = proc.stderr.read()
                        if rem2: self.err.emit(decode_wsl_output(rem2))
                    self.done.emit(proc.returncode or 0); break
        except Exception as e:
            self.err.emit(f"[Wizard] Fehler beim Start: {e}")
            self.done.emit(1)

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    w = MainWin(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


    def mcp_list(self):
        proj = self.ed_project.text().strip()
        wslp = win_to_wsl_path(proj) if proj else "~"
        args = ["wsl.exe","-d",self.cb_distro.currentText(),"--","bash","-lc", f"cd {shlex.quote(wslp)} && claude mcp list || true"]
        self.run_shell(args, title="MCP list")

    def mcp_add_sse(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "MCP add (SSE)", "Name:")
        if not ok or not name: return
        url, ok2 = QtWidgets.QInputDialog.getText(self, "MCP add (SSE)", "SSE URL:")
        if not ok2 or not url: return
        proj = self.ed_project.text().strip()
        wslp = win_to_wsl_path(proj) if proj else "~"
        cmd = f"cd {shlex.quote(wslp)} && claude mcp add --scope project --transport sse {name} {url}"
        args = ["wsl.exe","-d",self.cb_distro.currentText(),"--","bash","-lc", cmd]
        self.run_shell(args, title="MCP add (SSE)")

    def mcp_enable(self):
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
        args = ["wsl.exe","-d",self.cb_distro.currentText(),"--","bash","-lc", py]
        self.run_shell(args, title="MCP setting")
