# WSL + SQLite „disk I/O error“ & `pyenv` nicht gefunden – Ursachen, Fixes & Best Practices

*Stand: 2025-08-16*

Diese Anleitung fasst die Hintergründe und **robusten** Abhilfen für den Fehler

```
Database issue detected, recreating... disk I/O error
✖ Failed to spawn Hive Mind swarm
Error: disk I/O error
-bash: pyenv: command not found
```

zusammen. Zielumgebung: **Windows + WSL (Ubuntu)**, Projekt unter `D:\…` → `/mnt/d/...` und **Claude-Flow@alpha**.

---

## 1) Warum passiert das? (Kurzfassung)

- **SQLite** meldet `SQLITE_IOERR` („I/O error“), wenn das Betriebssystem einen I/O‑Fehler zurückliefert. Ursache sind i. d. R. **Write/Locking‑Probleme**, defekte Journale oder Storage‑Themen (Platz, Fragmentierung, Rechte).  
- Unter **WSL** sind Windows‑Laufwerke (`/mnt/c`, `/mnt/d`) via **DrvFs** eingebunden. Microsoft empfiehlt für Linux‑Workflows, **Dateien im WSL‑Dateisystem (ext4‑VHD)** zu halten (Performance & Semantik). DrvFs ist für Interop gedacht, nicht für datenbanklastige Linux‑Workloads.
- **Fazit:** SQLite‑State auf `/mnt/*` ist fehleranfällig (Locking/IO). Leg den **State (oder das ganze Projekt)** auf **ext4**.

---

## 2) „Goldener Pfad“ (empfohlen)

### Variante A – Projekt komplett ins WSL-Dateisystem verschieben

```bash
# Im WSL (Ubuntu)
mkdir -p ~/projects
# Kopiere Projekt von /mnt/d nach ext4 (alternativ: rsync)
cp -a "/mnt/d/03_GIT/02_Python/01_AI Coding Station" ~/projects/ai-coding-station

cd ~/projects/ai-coding-station
npx claude-flow@alpha init --force
npx claude-flow@alpha hive-mind spawn "Wieviele Dateien hat die Anwendung?" --verbose --claude
```

**Vorteil:** Maximale Stabilität & Performance für DB/Locking.

### Variante B – Minimalinvasiv: Nur den **State** (DB) auf ext4 verlagern

```bash
# Ziel für State auf ext4 anlegen
mkdir -p ~/cf_state/ai_cs/{hive,swarm}

# Im Projektordner auf /mnt/d arbeiten
cd "/mnt/d/03_GIT/02_Python/01_AI Coding Station"

# ggf. defekten State entsorgen
rm -rf .hive-mind .swarm

# State-Verzeichnisse auf ext4 verlinken
ln -s ~/cf_state/ai_cs/hive .hive-mind
ln -s ~/cf_state/ai_cs/swarm .swarm

# Neu initialisieren & starten
npx claude-flow@alpha init --force
npx claude-flow@alpha hive-mind spawn "Wieviele Dateien hat die Anwendung?" --verbose --claude
```

**Effekt:** Code kann auf `/mnt/d` bleiben, **SQLite‑State** liegt zuverlässig auf ext4.

---

## 3) Alternativen / Ergänzungen (wenn `/mnt/*` unvermeidbar ist)

> **Hinweis:** Diese Optionen verbessern das Verhalten, ersetzen aber **nicht** die Robustheit von ext4.

### 3.1 `wsl.conf`: DrvFs mit `metadata` mounten

```ini
# /etc/wsl.conf
[automount]
options = "metadata,uid=1000,gid=1000,umask=022,fmask=11"
```

Danach in Windows:
```powershell
wsl --shutdown
```

### 3.2 „Hausmeister“-Checks

```bash
# Genug freier Speicher?
df -h .

# Offene Handles/Prozesse, die auf die DB zugreifen (Beispiele)
lsof | grep -i sqlite || true

# Kaputte Journale entfernen (nur wenn Session/State entbehrlich ist)
rm -rf .hive-mind .swarm
npx claude-flow@alpha init --force
```

---

## 4) `pyenv: command not found` – Installation auf Ubuntu/WSL

**Abhängigkeiten:** (für CPython‑Builds)

```bash
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
  libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils \
  tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev git
```

**pyenv installieren:**

```bash
curl -fsSL https://pyenv.run | bash
```

**Shell einrichten (Bash):**

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
exec $SHELL
pyenv --version
```

> Tipp: Bei Build‑Fehlern (z. B. SSL/Zlib) die „Common build problems“ im pyenv‑Wiki prüfen.

---

## 5) Praxis: Aufrufmuster für Claude‑Flow@alpha (WSL)

**WSL‑Einzeiler (CMD/PowerShell):**
```bat
wsl.exe -d "Ubuntu" -- bash -lc "export LANG=C.UTF-8; export LC_ALL=C.UTF-8; cd '/pfad/zum/projekt' && npx claude-flow@alpha init --force && npx claude-flow@alpha hive-mind spawn 'Wieviele Dateien hat die Anwendung?' --claude --verbose"
```

**Nur Linux‑Befehl (direkt in WSL):**
```bash
cd /pfad/zum/projekt
npx claude-flow@alpha init --force
npx claude-flow@alpha hive-mind spawn "Wieviele Dateien hat die Anwendung?" --claude --verbose
```

---

## 6) Referenzen & weiterführende Links

- **Microsoft Docs – WSL Dateisysteme & Performance:**  
  https://learn.microsoft.com/windows/wsl/filesystems
- **Microsoft Docs – `wsl.conf` & Automount‑Optionen (`metadata` etc.):**  
  https://learn.microsoft.com/windows/wsl/wsl-config
- **Microsoft Docs – File Permissions & WSL‑Metadata:**  
  https://learn.microsoft.com/windows/wsl/file-permissions
- **SQLite – Result Code `SQLITE_IOERR`:**  
  https://www.sqlite.org/rescode.html#ioerr
- **WSL‑Issue (SQLite‑Locking):**  
  https://github.com/microsoft/WSL/issues/2395
- **pyenv – Offizielle README & Installer:**  
  https://github.com/pyenv/pyenv  
  https://github.com/pyenv/pyenv-installer  
  https://github.com/pyenv/pyenv/wiki/Common-build-problems
