---
title: CMD vs. WSL/Ubuntu – Formatierungs‑ & Aufrufregeln (inkl. Windows Terminal)
version: 2.0
tags: [wsl, windows, cmd, powershell, bash, quoting, paths, wt, encoding]
last_updated: 2025-08-17
---

# Zweck
Praxisleitfaden für Entwickler: Wie man unter **Windows** zuverlässig Kommandos in **WSL/Ubuntu** startet, mit korrektem **Quoting/Escaping**, **Pfaden**, **Encoding/EOL** und **Windows Terminal (wt.exe)**. Beispiele sind so gewählt, dass sie in Automatisierungen und GUI‑Launchern stabil funktionieren.

---

## 1) Grundmuster für Aufrufe nach WSL
Starte Linux‑Kommandos aus Windows **immer** über `wsl.exe` und übergebe dein Bash‑Kommando an eine Login‑Shell:

```cmd
wsl.exe -d Ubuntu -- bash -lc "<DEIN_BASH_BEFEHL>"
```
- `-d/--distribution` wählt die Distro, `--` trennt WSL‑Optionen vom Linux‑Kommando
- `bash -lc` stellt eine Login‑Umgebung her (lädt `.profile`, `.bashrc`, PATH, Aliases) und erzwingt konsistentes Bash‑Parsing
- Ohne `-l` werden diese Dateien NICHT geladen (non-login shell)

**Beispiel (direkt aus CMD/PS):**
```cmd
wsl -d Ubuntu -- bash -lc "echo 'hello from wsl'"
```

**Alternative für Standard-Distro:**
```cmd
wsl -- bash -lc "dein_kommando"
```

---

## 2) Pfade & Pfadkonvertierung

### Grundlagen
- **Linux/WSL:** `/`, Laufwerke gemountet unter `/mnt/c`, `/mnt/d`, …  
- **Windows:** `C:\`, Backslash als Standard‑Separator
- **Konvertierung:** `wslpath` verwenden (statt String‑Bastelei)

### wslpath Verwendung
```bash
# in WSL
wslpath -w /mnt/c/Users        # → C:\Users
wslpath -w /usr/bin            # → \\wsl$\<Distro>\usr\bin
wslpath -u "C:\Program Files"  # → /mnt/c/Program Files
wslpath -m /mnt/c/Users        # → C:/Users (mixed/Unix-style)
```

### ⚠️ WICHTIG: Leerzeichen in Pfaden
**wslpath escaped KEINE Leerzeichen automatisch!** Dies ist ein bekanntes Problem (GitHub Issues #3713, #11213).

```bash
# PROBLEM:
path=$(wslpath "C:\Program Files\MyApp")
# Ergebnis: /mnt/c/Program Files/MyApp (OHNE Escaping!)

# LÖSUNGEN:
# 1. Manuell quoten
path="$(wslpath "C:\Program Files\MyApp")"
"$path/executable"  # Korrekt gequoted

# 2. Manuell escapen
path=$(wslpath "C:\Program Files\MyApp" | sed 's/ /\\ /g')
# Ergebnis: /mnt/c/Program\ Files/MyApp

# 3. In Variablen immer mit Quotes verwenden
cd "$path"  # Nicht: cd $path
```

### Windows PATH mit Leerzeichen
WSL importiert Windows PATH automatisch, aber Pfade mit Leerzeichen können Probleme verursachen:
```bash
# Problem in $PATH sichtbar machen
echo $PATH | tr ':' '\n' | grep "Program Files"
# Zeigt: /mnt/c/Program Files/... (unescaped!)

# Workaround in .bashrc:
export PATH="$PATH"  # Quotes helfen bei direkter Verwendung
```

---

## 3) Quoting & Escaping – Unterschiede

### Bash (WSL/Ubuntu)
- **Singlequotes** `'…'` = *literal*, nichts wird expandiert
- **Doublequotes** `"…"` = Variablen/Backticks werden expandiert; `\"` für Anführungszeichen
- **Escape:** Backslash `\` vor Sonderzeichen
- **POSIX:** `$'…'` für spezielle Sequenzen (z.B. `$'\n'` für Newline)

**Beispiel:**
```bash
echo 'Literal: $HOME'     # Output: Literal: $HOME
echo "Expanded: $HOME"    # Output: Expanded: /home/user
echo "Quote: \"test\""    # Output: Quote: "test"
```

### CMD
- **Metazeichen:** `& | ( ) < > ^` 
- **Escape:** Caret `^` verwenden oder in `"…"` packen
- **Quotes:** Nur Doublequotes `"…"` verfügbar

**Beispiel:**
```cmd
echo Test ^& Echo      REM Escaped &
echo "Test & Echo"     REM Quoted
wsl echo "Test ^| cut" REM Pipe für WSL escaped
```

### PowerShell
- **Singlequotes** `'…'` = literal (keine Expansion)
- **Doublequotes** `"…"` = interpolierend (Variablen werden expandiert)
- **Escape:** Backtick `` ` `` (nicht Backslash!)
- **Stop-Parsing:** `--%%` stoppt PowerShell-Interpretation

**Beispiel:**
```powershell
echo 'Literal: $env:HOME'      # Output: Literal: $env:HOME
echo "Expanded: $env:HOME"     # Output: Expanded: C:\Users\...
echo "Quote: `"test`""         # Output: Quote: "test"
wsl --% bash -lc "echo test"  # Stop-Parsing für WSL
```

---

## 4) Windows Terminal (wt.exe) – Semikolon‑Problematik

### Das Problem
`wt.exe` nutzt das **Semikolon `;` als eigenen Befehls‑Delimiter** für Tabs/Panes. Enthält dein Bash‑Kommando `;`, interpretiert WT es falsch und versucht neue Tabs/Panes zu öffnen.

### Die Lösung: Backslash-Escaping
Semikolons **NUR für WT** mit Backslash escapen: `\;`

**Robustes WT‑Beispiel (neuer Tab mit WSL):**
```powershell
# PowerShell - Backtick für Zeilenumbruch
wt new-tab --title "Hive" `
  wsl.exe -d Ubuntu -- bash -lc 'echo ready\; read -n 1 -s -r -p "Taste…"\; echo\; exec bash -i'
```

```cmd
REM CMD - Backslash für Semikolon
wt new-tab --title "Test" wsl.exe -- bash -lc "echo start\; sleep 2\; echo end"
```

**Fallback ohne WT (klassisches Fenster):**
```cmd
cmd.exe /c start "" wsl.exe -d Ubuntu -- bash -lc "echo ready; read -n 1 -s -r; exec bash -i"
```

### Weitere WT-Spezifika
- WT wartet standardmäßig auf Windows Store Apps (anders als CMD)
- In PowerShell: `Start-Process wt` verwenden für non-blocking
- Aus WSL heraus: `cmd.exe /c wt.exe` verwenden (Execution Aliases funktionieren nicht direkt)

---

## 5) Umgebungsvariablen zwischen Windows & WSL

### WSLENV Grundlagen
**WSLENV** teilt/übersetzt Variablen zwischen Windows und WSL mit Flags:

| Flag | Bedeutung | Beispiel |
|------|-----------|----------|
| `/p` | Pfad-Übersetzung (Win↔Linux) | `MYPATH/p` |
| `/l` | Listen-Übersetzung (`;`↔`:`) | `PATHLIST/l` |
| `/u` | Nur Win→WSL | `WINONLY/u` |
| `/w` | Nur WSL→Win | `LINUXONLY/w` |

### Beispiele
```cmd
REM Windows CMD
set MYPROJECT=C:\Projects\App
set WSLENV=MYPROJECT/p
wsl echo $MYPROJECT
REM Output: /mnt/c/Projects/App
```

```bash
# WSL Bash
export DEPLOY_PATH=/home/user/deploy
export WSLENV=$WSLENV:DEPLOY_PATH/w
cmd.exe /c echo %DEPLOY_PATH%
# Output: \\wsl$\Ubuntu\home\user\deploy
```

### Kombinierte Flags
```cmd
set WSLENV=USERPROFILE/up:PATH/l
```
- `USERPROFILE` wird als Pfad übersetzt und nur nach WSL übergeben
- `PATH` wird als Liste behandelt (Separator-Konvertierung)

---

## 6) Encoding & Zeilenenden (EOL)

### Zeilenenden (EOL)
| System | EOL | Hex | Escape |
|--------|-----|-----|--------|
| Linux/Unix/WSL | **LF** | `0x0A` | `\n` |
| Windows | **CRLF** | `0x0D0A` | `\r\n` |
| Mac (alt) | **CR** | `0x0D` | `\r` |

### Git‑Konfiguration (Best Practice)
```bash
# EMPFOHLEN: .gitattributes im Repository-Root
# (überschreibt persönliche Einstellungen)
cat > .gitattributes << 'EOF'
# Automatische Normalisierung für Textdateien
* text=auto eol=lf

# Windows-spezifische Dateien behalten CRLF
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf

# Binärdateien nicht konvertieren
*.exe binary
*.dll binary
*.png binary
*.jpg binary
EOF
```

**Globale Git-Einstellungen:**
```bash
# Windows (Git Bash/CMD)
git config --global core.autocrlf true   # LF→CRLF checkout, CRLF→LF commit

# WSL/Linux/Mac
git config --global core.autocrlf input  # Keine Konversion checkout, CRLF→LF commit

# Deaktiviert (nicht empfohlen)
git config --global core.autocrlf false  # Keine Konversion
```

### `wsl.exe`‑Ausgabe Encoding

#### Das Problem
`wsl.exe` gibt standardmäßig **UTF-16LE** aus (statt UTF-8/System-Codepage):

```powershell
# Problem demonstrieren
wsl --list | Format-Hex
# Zeigt: Jeder zweite Byte ist 0x00 (UTF-16LE)
```

#### Lösungen

**1. WSL_UTF8 Environment Variable (WSL v0.64+):**
```powershell
# PowerShell
$env:WSL_UTF8 = 1
wsl --list  # Jetzt UTF-8!

# CMD
set WSL_UTF8=1
wsl --list
```

**2. PowerShell Console Encoding:**
```powershell
$prev = [Console]::OutputEncoding
[Console]::OutputEncoding = [System.Text.Encoding]::Unicode
$distros = wsl --list --quiet
[Console]::OutputEncoding = $prev
```

**3. Python robuste Lösung:**
```python
import subprocess

def get_wsl_distros():
    # WSL_UTF8 für neuere Versionen
    env = os.environ.copy()
    env['WSL_UTF8'] = '1'
    
    try:
        # Versuche mit UTF-8
        result = subprocess.run(
            ['wsl.exe', '--list', '--quiet'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            env=env
        )
        return result.stdout.splitlines()
    except UnicodeDecodeError:
        # Fallback auf UTF-16LE für ältere WSL
        raw = subprocess.check_output(['wsl.exe', '--list', '--quiet'])
        text = raw.decode('utf-16le', errors='ignore')
        # Bereinige BOM und NULL-Zeichen
        text = text.replace('\ufeff', '').replace('\x00', '')
        return [line.strip() for line in text.splitlines() if line.strip()]
```

---

## 7) Muster für `claude-flow` und andere Tools

### A) Direkt in WSL
```bash
claude-flow hive-mind spawn "####Task####" --claude --verbose
```

### B) Von Windows → WT‑Tab mit WSL
```powershell
# PowerShell mit korrektem Escaping
$task = '####Task####'
wt new-tab --title "Hive" `
  wsl -d Ubuntu -- bash -lc "claude-flow hive-mind spawn '$task' --claude --verbose\; echo\; read -n 1 -s -r\; exec bash -i"
```

### C) Fallback klassisches Fenster
```cmd
REM CMD Version
cmd /c start "Hive" wsl -d Ubuntu -- bash -lc "claude-flow hive-mind spawn '####Task####' --claude --verbose; echo; read -n 1 -s -r; exec bash -i"
```

### D) Mit Pfadkonvertierung
```powershell
# Windows-Pfad an WSL übergeben
$winPath = "C:\Projects\My Project"
$wslPath = wsl wslpath -u "$winPath"
wsl -- bash -lc "cd '$wslPath' && ls -la"
```

---

## 8) Debug‑Tipps & Häufige Fehler

### Fehlerdiagnose

| Fehler | Ursache | Lösung |
|--------|---------|---------|
| **0x80070002** | Fehlerhaftes Semikolon-Escaping in WT | `\;` statt `;` verwenden |
| **"command not found"** | Non-Login Shell (`.bashrc` nicht geladen) | `bash -lc` statt `bash -c` |
| **Kästchen/�-Zeichen** | UTF-16LE Encoding von `wsl.exe` | `WSL_UTF8=1` setzen |
| **"No such file"** bei Spaces | Unescapte Leerzeichen in Pfaden | Quotes verwenden: `"$path"` |
| **CRLF/LF Konflikte** | Falsche Git-Konfiguration | `.gitattributes` verwenden |
| **^M in Skripten** | Windows-Zeilenenden in Linux | `dos2unix` oder `sed -i 's/\r$//'` |

### Debug-Kommandos
```bash
# WSL-Version prüfen
wsl --version

# Encoding testen
wsl echo $LANG
wsl locale

# PATH-Probleme debuggen
wsl bash -lc 'echo $PATH | tr ":" "\n" | nl'

# Git EOL-Settings prüfen
wsl git config --list | grep -E "(eol|crlf)"

# WT Command-Line debuggen (zeigt geparste Argumente)
wt -w 0 new-tab --title "Debug" wsl echo "arg1\; arg2"
```

### Best Practices
1. **Immer Login-Shell** verwenden (`bash -lc`) für konsistente Umgebung
2. **Pfade mit Spaces** immer quoten oder escapen
3. **WSLENV** für Pfad-Sharing zwischen Windows/WSL nutzen
4. **.gitattributes** im Repo statt globale Git-Settings
5. **WSL_UTF8=1** in Windows-Umgebungsvariablen setzen
6. **Test-Skripte** für kritische Automatisierungen schreiben

---

## 9) Erweiterte Szenarien

### WSL aus Batch-Dateien
```batch
@echo off
setlocal enabledelayedexpansion
set "WSL_UTF8=1"
set "TASK=Complex Task & Test"

REM Quotes für CMD, dann für Bash
wsl -d Ubuntu -- bash -lc "echo '!TASK!' | sed 's/&/and/g'"
```

### PowerShell mit Here-Strings
```powershell
$script = @'
#!/bin/bash
echo "Complex multi-line"
echo "Bash script"
for i in {1..3}; do
    echo "Line $i"
done
'@

$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($script))
wsl -- bash -lc "echo '$encoded' | base64 -d | bash"
```

### Interoperabilität deaktivieren
```bash
# /etc/wsl.conf in WSL
[interop]
enabled = false            # Windows-Interop komplett aus
appendWindowsPath = false  # Windows-PATH nicht anhängen
```

---

## Changelog
- **v2.0** (2025-08-17): Umfassende Überarbeitung basierend auf aktueller Recherche
  - Ergänzt: wslpath Leerzeichen-Problem mit Workarounds
  - Ergänzt: PowerShell-spezifische Escape-Mechanismen
  - Erweitert: WSL_UTF8 für Encoding-Fixes
  - Präzisiert: Login- vs. Non-Login-Shell Unterschiede
  - Neu: Erweiterte Debug-Tipps und Best Practices