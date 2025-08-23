
---
title: Claude‑Flow One‑Shot aus Windows per WSL/Ubuntu (Python)
version: 1.0
tags: [wsl, python, subprocess, claude-flow, hive-mind, oneshot]
last_updated: 2025-08-16
---

# Ziel
Diese Dokumentation zeigt, wie **Claude‑Flow@alpha** im **Hive‑Mind**‑Modus
aus **Windows** heraus **in einem WSL/Ubuntu‑Fenster** per **Python** gestartet
wird – als *One‑Shot* inkl. `--verbose`, Verwendung einer **JSON‑Konfiguration**
und robuster **Quoting-/Pfad‑Regeln**. Die Struktur folgt den
Best‑Practices aus der maschinenlesbaren Doku.  fileciteturn1file0

---

## 1) Voraussetzungen
- Installationen (Node, Claude Code, Claude‑Flow) sind bereits erfolgt.
- Projektordner mit **.claude‑flow/** (Saved‑Configs) bzw. optionaler Mirror in
  **.claude/** vorhanden. Hintergrund: neuere Versionen bevorzugen
  `.claude/config.json`; ältere/Tools lesen z.T. `.claude-flow/config.json`.
  Falls nötig, Konfiguration **spiegeln**:  
  `cp .claude-flow/config.json .claude/config.json`.  fileciteturn7
- Korrekte **CLI‑Aufrufe** für `hive-mind` (Subcommand, *kein* `--mode`‑Flag) –
  z. B.:  
  `npx claude-flow@alpha hive-mind spawn "…"`  fileciteturn7turn9

---

## 2) Pfade & Quoting (Windows ↔ WSL)
- Windows‑Pfad `D:\…` ↔ WSL‑Pfad `/mnt/d/...` abbilden.
- Immer **Login‑Shell** verwenden:  
  `wsl.exe -d <Distro> -- bash -lc "<Befehle>"`  
  (stellt PATH/ENV her; konsistentes Parsing).  
- Ketten Sie Kommandos in Bash mit `&&` (statt `;`), um Abbruch bei Fehlern zu
  erzwingen und WT‑Sonderfälle zu vermeiden.

---

## 3) JSON‑Konfiguration des Schwarms
Primärquelle für die GUI/CLI ist eine **Saved‑Config** unter
`.claude-flow/saved-configs/<Name>.json`. Relevante Schlüssel u. a.:
`project.*`, `agents.selected`, `agents.queen_model`, `agents.worker_model`,
`swarm.*`, `settings.*`.  fileciteturn17

**Minimalbeispiel (`.claude-flow/saved-configs/MySwarm.json`)**
```json
{
  "project": {"name": "AI Coding Station", "namespace": "default"},
  "agents": {
    "selected": ["queen", "backend-dev", "frontend-dev", "system-architect", "tester"],
    "queen_model": "anthropic/claude-3-7",
    "worker_model": "anthropic/claude-3-7"
  },
  "swarm": {
    "topology": "mesh",
    "task": "Bearbeite alle offenen Issues im Ordner ./issues …"
  },
  "settings": {"parallelExecution": true}
}
```
Optional zusätzlich nach `.claude/config.json` spiegeln, wenn andere Tools
diesen Pfad erwarten.  fileciteturn7

---

## 4) Python‑Beispiele (One‑Shot aus Windows → WSL/Ubuntu)

### 4.1 Synchrone Ausführung (Ausgabe wird in Python gesammelt)
```python
import json, subprocess, shlex
from pathlib import Path

DISTRO = "Ubuntu"  # ggf. anpassen
PROJECT_WIN = r"D:\03_GIT\02_Python\01_AI Coding Station"
PROJECT_WSL = "/mnt/d/03_GIT/02_Python/01_AI Coding Station"

TASK = ("Bearbeite alle offenen Issues im Ordner ./issues. "
        "Stelle sicher, dass wirklich alle Aufgaben inkl. Teilaufgaben "
        "abgeschlossen und getestet sind. Bei Fehlern Meldung im Terminal, "
        "Issue offen lassen. Beachte description, additional und comments. "
        "Abarbeitung step by step; danach state=closed setzen.")

def write_json(p: Path, obj: dict) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return p

# 1) Konfiguration für Hive-Mind schreiben/aktualisieren
hivemind_cfg_win = Path(PROJECT_WIN, ".claude-flow", "saved-configs", "MySwarm.json")
write_json(hivemind_cfg_win, {
    "project": {"name": "AI Coding Station", "namespace": "default"},
    "agents": {
        "selected": ["queen","backend-dev","frontend-dev","system-architect","tester"],
        "queen_model": "anthropic/claude-3-7",
        "worker_model": "anthropic/claude-3-7"
    },
    "swarm": {"topology": "mesh", "task": TASK},
    "settings": {"parallelExecution": True}
})

# 2) One-Shot Start in WSL (im Projektverzeichnis, mit --config und --verbose)
bash_line = " && ".join([
    f"cd {shlex.quote(PROJECT_WSL)}",
    "npx claude-flow@alpha init --force",
    f"npx claude-flow@alpha hive-mind spawn {shlex.quote(TASK)} "
    f"--config ./.claude-flow/saved-configs/MySwarm.json --claude --verbose"
])

cp = subprocess.run(
    ["wsl.exe", "-d", DISTRO, "--", "bash", "-lc", bash_line],
    capture_output=True
)

# 3) Ausgabe dekodieren
def dec(x: bytes) -> str:
    for enc in ("utf-8","utf-16le","cp1252"):
        try:
            return x.decode(enc, errors="replace")
        except Exception:
            pass
    return x.decode("utf-8", errors="replace")

print("STDOUT:\n", dec(cp.stdout))
print("STDERR:\n", dec(cp.stderr))
print("RC:", cp.returncode)
```

**Warum so?**  
- `hive-mind spawn` ist der korrekte Aufrufstil in v2‑Alpha (Subcommand,
  nicht `--mode`).  fileciteturn7  
- `--config` bindet die Saved‑Config explizit ein; `--claude --verbose` für
  volle Integration/Logs.  fileciteturn9

### 4.2 Neues Fenster (klassisches `cmd /c start` → WSL)
```python
import subprocess, shlex

DISTRO = "Ubuntu"
PROJECT_WSL = "/mnt/d/03_GIT/02_Python/01_AI Coding Station"
TASK = "Bearbeite alle offenen Issues im Ordner ./issues …"

bash_line = " && ".join([
    f"cd {shlex.quote(PROJECT_WSL)}",
    "npx claude-flow@alpha init --force",
    f"npx claude-flow@alpha hive-mind spawn {shlex.quote(TASK)} "
    f"--config ./.claude-flow/saved-configs/MySwarm.json --claude --verbose",
    'echo -e "\n[Beenden mit Taste …]"',
    "read -n 1 -s -r",
    "exec bash -i"
])

subprocess.Popen(
    ["cmd", "/c", "start", "", "wsl.exe", "-d", DISTRO, "--", "bash", "-lc", bash_line],
    close_fds=True
)
```

### 4.3 Windows Terminal (neuer Tab) → WSL (optional)
```python
import subprocess, shlex

DISTRO = "Ubuntu"
PROJECT_WSL = "/mnt/d/03_GIT/02_Python/01_AI Coding Station"
TASK = "Bearbeite alle offenen Issues im Ordner ./issues …"

bash_line = " && ".join([
    f"cd {shlex.quote(PROJECT_WSL)}",
    "npx claude-flow@alpha init --force",
    f"npx claude-flow@alpha hive-mind spawn {shlex.quote(TASK)} "
    f"--config ./.claude-flow/saved-configs/MySwarm.json --claude --verbose",
    'echo -e "\n[Beenden mit Taste …]"',
    "read -n 1 -s -r",
    "exec bash -i"
])

subprocess.Popen([
    "wt", "new-tab", "--title", "Hive‑Mind",
    "wsl.exe", "-d", DISTRO, "--", "bash", "-lc", bash_line
], close_fds=True)
```

---

## 5) Beispiele für Aufgaben‑Text (Deutsch)
**Standard‑Task (Issues im Projekt bearbeiten)**  
```
Bearbeite alle offenen Issues im Ordner ./issues. Stelle sicher, dass
WIRKLICH ALLE AUFGABEN, auch Teilaufgaben, abgeschlossen und getestet sind,
bevor du ein Issue auf closed setzt. Bei Fehlern oder unlösbaren Aufgaben,
Meldung im Terminal und Issue offen lassen. Beachte description, additional
und comments. Abarbeitung step by step (Issue_1.json, Issue_2.json …).
Nach Abschluss state=closed setzen.
```
Dieser Stil ist 1:1 kompatibel mit dem in der Korrektursyntax verwendeten
One‑Shot‑Beispiel.  fileciteturn7

---

## 6) Troubleshooting (schnell)
- **„Unknown command: --mode“** → Sie nutzen v2‑Alpha: `hive-mind` ist ein
  **Subcommand**, nicht `--mode`.  fileciteturn7
- **Config wird nicht gezogen** → Pfad mit `--config` explizit angeben oder
  Konfiguration nach `.claude/config.json` spiegeln.  fileciteturn7
- **Keine/zu wenig Logs** → `--verbose` anhängen.  fileciteturn9
- **Pfadfehler** → `cd /mnt/<lw>/...`; `shlex.quote()` nutzen.
- **Fenster schließt sofort** → `read -n 1 -s -r` + `exec bash -i` ans Ende.

---

## 7) Referenz der wichtigsten Kommandos
- **Init (legt Projektstrukturen an):**  
  `npx claude-flow@alpha init --force`
- **Hive‑Mind One‑Shot:**  
  `npx claude-flow@alpha hive-mind spawn "<Task>" --claude --verbose`
- **Weitere Modi/Kommandos (Auszug):** `start --ui --swarm`, `swarm "<obj>"`,
  `hive-mind wizard`, `hive-mind status`, `memory …`  fileciteturn9

---

## 8) Appendix: Hilfsfunktionen (Pfad‑Mapping, Lesen/Speichern)

```python
import os, json
from pathlib import Path

def win_to_wsl(p: str) -> str:
    # D:\Pfad -> /mnt/d/Pfad
    if len(p) >= 2 and p[1] == ":":
        drive, rest = p[0].lower(), p[2:]
        return f"/mnt/{drive}" + rest.replace("\\","/")
    return p

def read_textfile(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
```

---

## 9) Hinweise zur Dokumentationsform
Diese Datei ist **Markdown** mit Frontmatter und klaren Abschnittstiteln,
damit LLMs sie **sauber parsen** und **splitten** können (RAG‑Einsatz).  fileciteturn1file0

