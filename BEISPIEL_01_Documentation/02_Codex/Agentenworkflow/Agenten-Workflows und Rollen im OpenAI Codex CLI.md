# Codex CLI — Praxis‑Handbuch (Stand: 17.08.2025)

Dieses Handbuch bündelt Installation, Konfiguration, Arbeitsmodi, AGENTS.md‑Leitplanken („Rollen“), Modellwahl (OpenAI, Azure), sowie lokale Nutzung (Ollama & GPT‑OSS). Es ist bewusst praxisnah gehalten, damit du Codex in echten Projekten sofort produktiv einsetzen kannst.

---

## 1) Überblick

**Codex CLI** ist ein lokaler Coding‑Agent fürs Terminal. Er kann:
- Dateien lesen/ändern (mit Sicherheits‑Sandbox).
- Shell‑Kommandos ausführen (je nach Modus mit/ohne Rückfrage).
- Projektwissen aus Dateien wie `README.md` und **`AGENTS.md`** einbeziehen.
- Mit unterschiedlichen **Modellen/Providern** arbeiten (OpenAI, Azure, OpenRouter, lokale Modelle via Ollama).

**Wichtige Konzepte auf einen Blick**
- **Approval‑Modi**: _Suggest_ (nur vorschlagen), _Auto‑Edit_ (Dateien schreiben), _Full‑Auto_ (Dateien + Kommandos).
- **Sandbox**: kontrolliert Schreibrechte/Netz und schützt dein System/Repo.
- **`AGENTS.md`**: dein „Leitplanken‑Dokument“ (Rollen/Checklisten/Build‑Kommandos). Keine echten parallelen Sub‑Agenten – ein Agent folgt deinen Regeln.
- **Modelle**: per `-m/--model` wählbar. Cloud (OpenAI/Azure) oder lokal (Ollama, z. B. GPT‑OSS‑20B).

---

## 2) Systemvoraussetzungen

- **Node.js** ≥ 20 (empfohlen via nvm).
- **Git** (empfohlen).
- **Betriebssystem**: macOS oder Linux nativ; **Windows über WSL2** (Ubuntu 20.04+/22.04+).
- Optional: **Ollama** für lokale Modelle (GPT‑OSS, Mistral, usw.).

---

## 3) Installation

### macOS / Linux
```bash
npm install -g @openai/codex
codex --version
```

### Windows (WSL2 empfohlen)
1. **WSL2 + Ubuntu** installieren (falls noch nicht vorhanden).
2. Node.js in WSL installieren (z. B. via nvm):
   ```bash
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
   source ~/.nvm/nvm.sh
   nvm install --lts
   ```
3. Codex CLI in WSL:
   ```bash
   npm install -g @openai/codex
   codex --version
   ```

> **Hinweis (Windows nativ):** Die Sandbox‑Funktionen sind nativ nicht zuverlässig. Verwende WSL2.

---

## 4) Authentifizierung

Du hast zwei bequeme Wege:

**A) ChatGPT‑Login (empfohlen für Plus/Pro)**
```bash
codex --login
```
– Öffnet den Browser zur Anmeldung. Vorteil: oft „0 Zusatzkosten“ für Interaktiv‑Sessions, da dein ChatGPT‑Abo/Guthaben genutzt wird (je nach Region/Plan).

**B) API‑Key (klassisch)**
```bash
export OPENAI_API_KEY="sk-..."
codex
```
– Nützlich für CI und serverseitige Automatisierung.

---

## 5) Schnellstart (im Projektordner)

```bash
cd /pfad/zu/deinem/projekt
codex                     # Startet interaktive TUI im Modus "Suggest"
# Alternativ:
codex --auto-edit         # Dateien automatisch schreiben, Kommandos mit Rückfrage
codex --full-auto         # Schreiben + Kommandos autonom (Sandbox, standardmäßig ohne Netz)
```

> **Best Practice:** Starte in **Suggest**, prüfe Vorschläge, steigere die Autonomie schrittweise.

---

## 6) Arbeitsmodi & Sandbox

### 6.1 Approval‑Modi
- **Suggest (Default):** Änderungen/Befehle werden vorgeschlagen, **nichts** wird ausgeführt, bis du zustimmst.
- **Auto‑Edit:** Dateien dürfen geschrieben werden; **Shell‑Kommandos** werden weiterhin zur Freigabe vorgelegt.
- **Full‑Auto:** Dateien **und** Kommandos dürfen autonom ausgeführt werden (in einer Sandbox ohne Netz, sofern nicht explizit erlaubt).

Umschalten per Flag (`--suggest`/`--auto-edit`/`--full-auto`) oder innerhalb der Session (z. B. Befehl `/mode`).

### 6.2 Sandbox‑Modi (Beispiele)
- `read-only` – nur lesen, keine Dateischreibzugriffe.
- `workspace-write` – im Projektordner schreiben, kein Netzwerk.
- `full-access` – Vollzugriff (nur in isolierten Containern/VMs nutzen).

**Empfehlung:** Für echte Repos **workspace‑write** + konservative Approval‑Policy.

---

## 7) Konfiguration (`~/.codex/config.toml`)

Globale Voreinstellungen und **Profile** legst du in einer TOML an. Beispiel mit drei sinnvollen Profilen:

```toml
# ~/.codex/config.toml

# Globale Defaults
model = "gpt-4.1"                # beliebiges Responses‑API‑Modell
approval_policy = "on-request"   # fragt bei riskanten Aktionen
sandbox_mode = "workspace-write" # schreibt nur im Workspace
disable_response_storage = false # ZDR (Zero Data Retention) bei Bedarf: true

[profiles.full_auto]
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[profiles.readonly]
approval_policy = "always"       # immer fragen
sandbox_mode = "read-only"

# Lokaler Betrieb über Ollama (GPT‑OSS o.ä.)
[model_providers.oss]
name = "Open Source"
base_url = "http://localhost:11434/v1"

[profiles.ollama_local]
model_provider = "oss"
model = "gpt-oss:20b"            # oder gpt-oss:120b, mistral, llama3, ...
sandbox_mode = "workspace-write"
approval_policy = "on-request"

# Azure‑Beispiel
[model_providers.azure]
name = "Azure"
base_url = "https://<RESOURCE>.openai.azure.com/openai"
env_key = "AZURE_OPENAI_API_KEY"
query_params = { api-version = "2025-04-01-preview" }
wire_api = "responses"           # Chat/Responses API

[profiles.azure_gpt4]
model_provider = "azure"
model = "<DEPLOYMENT_NAME>"      # Azure-Deployment-Name
sandbox_mode = "workspace-write"
approval_policy = "on-request"
```

**Nutzung der Profile**
```bash
codex --profile ollama_local
codex --profile azure_gpt4 -m <DEPLOYMENT_NAME>   # explizit überschreiben
```

---

## 8) `AGENTS.md` — Leitplanken & Rollen (à la „Claude Flow“)

Codex nutzt **eine Agent‑Instanz**. Parallele Sub‑Agenten sind **nicht** eingebaut. Du kannst jedoch mit **`AGENTS.md`** klare **Rollen/Checklisten** definieren, die Codex befolgt. Codex **merged** automatisch:
1. `~/.codex/AGENTS.md` (global)  
2. `<repo>/AGENTS.md` (Projekt‑Root)  
3. `<cwd>/AGENTS.md` (aktuelles Verzeichnis)

### 8.1 Beispiel‑Struktur (Python & Flutter)

```markdown
# AGENTS.md — Projektleitfaden

## Grundregeln
- Kleine, reversible Schritte; nach jeder Änderung Lint/Tests.
- Keine Netz‑/Git‑Remote‑Aktionen ohne expliziten Auftrag.
- Respektiere .editorconfig, pyproject.toml, pubspec.yaml.

## Build/Test Kommandos
### Python
- Lint: `ruff check .`
- Format: `black .`
- Typen (optional): `mypy .`
- Tests: `pytest -q --maxfail=1 --disable-warnings`
- Coverage: `pytest --cov --cov-report=term-missing`

### Flutter
- `flutter pub get`
- `flutter analyze`
- `dart format .`
- `flutter test`

## Rollen (Leitplanken)
- **Executor**: führt Aufgaben in Schritten aus (lesen → ändern → testen).
- **Validator**: prüft `ruff`, `black --check`, `pytest`, `flutter analyze/test`.
- **Debugger**: minimaler Repro, Hypothesen, Fix, Retest.
- **Formatter**: setzt Formatierung konsequent um.
- **Doc‑Generator**: README/CHANGELOG aktualisieren.

## Abbruchkriterien
- Wenn Tests/Analyse rot → stoppen und Bericht liefern.
```

> **Tipp:** Halte `AGENTS.md` kurz + projektbezogen. Nutze **globale** `~/.codex/AGENTS.md` für allgemeine Regeln und **repo‑lokal** nur das Spezifische.

---

## 9) Modelle & Provider

### 9.1 OpenAI (Standard)
- Modell per `-m` setzen, z. B. `gpt-4.1`, `o3` (3.5‑Familie), ggf. weitere aktuelle Varianten.
- **ChatGPT‑Login** nutzt oft automatisch ein schnelles, aktuelles Modell.
- Für API‑Key‑Betrieb: explizit `-m` setzen, um Kosten/Leistung zu steuern.

**Beispiele**
```bash
codex -m gpt-4.1
codex -m o3
```

### 9.2 Azure OpenAI
- In `config.toml` Provider `azure` definieren (siehe oben).
- **Wichtig:** Im CLI ist `--model` der **Deployment‑Name** aus Azure.

### 9.3 OpenRouter / andere kompatible Hosts
- Eigenen Provider mit `base_url`, `env_key` und ggf. `wire_api="responses"` anlegen.

### 9.4 Lokale Modelle (Ollama & GPT‑OSS)
- **Ollama** installieren und starten.
- Codex mit `--oss` oder Profil `ollama_local` nutzen.
- **Modelle:** `gpt-oss:20b` (alltagstauglich), `gpt-oss:120b` (sehr groß), sowie Mistral/Llama‑Familie.
- **Einschränkungen:** i. d. R. **kein Multimodal** (Bilder), höhere Latenz/Hardwarebedarf.

**Beispiele**
```bash
codex --oss -m gpt-oss:20b
codex --profile ollama_local
```

---

## 10) Nicht‑interaktiv & CI

Für Skripting/CI nutze `exec`:

```bash
# Direktbefehl (eine „Mini‑Session“ ohne TUI)
codex exec --auto-edit "aktualisiere die Datei CHANGELOG.md für das nächste Release"

# GitHub Actions (Beispiel)
- name: Codex Changelog Update
  run: |
    npm install -g @openai/codex
    export OPENAI_API_KEY="${{ secrets.OPENAI_API_KEY }}"
    codex exec --auto-edit "update CHANGELOG for next release"
```

---

## 11) Zero Data Retention (ZDR) & Datenschutz

- **Cloud‑Betrieb:** Bei Bedarf Antwortspeicherung deaktivieren:
  ```bash
  codex --config disable_response_storage=true
  ```
  oder in `config.toml` `disable_response_storage = true` setzen.
- **Lokal (Ollama):** Keine Daten verlassen dein System.

---

## 12) Häufige Probleme & Lösungen (Troubleshooting)

- **`codex` nicht gefunden:** `npm bin -g` prüfen; ggf. Pfad in `~/.bashrc`/`~/.zshrc` ergänzen.
- **Node zu alt:** `nvm install --lts` / `nvm use`.
- **Windows‑Zugriffsprobleme:** In **WSL2** arbeiten; Projekt unter `/home/<user>/…` oder gemountetem Laufwerk mit korrekten Rechten.
- **„Permission denied“ beim Schreiben:** Sandbox‑Modus prüfen (`workspace-write`?), Repo‑Ordner korrekt?
- **Kommandos werden nicht ausgeführt:** Modus auf **Auto‑Edit/Full‑Auto** stellen; Approval‑Policy prüfen.
- **Modell „not found“:** Modellname korrekt? Bei Azure: **Deployment‑Name** nutzen; bei lokalen Modellen: Ollama‑Service läuft?
- **Langsame Antworten lokal:** Größeres Modell → höhere Latenz. `gpt-oss:20b` statt `120b` testen; ggf. GPU‑Beschleunigung.
- **Kein Netz in Sandbox:** Absicht! Nur erlauben, wenn du es explizit möchtest (z. B. in Container‑Umgebungen).

---

## 13) Checkliste für den Projekteinsatz

1. **Repo sauber?** Lint/Tests laufen grün?
2. **`AGENTS.md` erstellt?** Projektregeln + Build/Test‑Kommandos drin?
3. **`config.toml` Profile** (z. B. `readonly`, `full_auto`, `ollama_local`) angelegt?
4. **Start in Suggest**, dann ggf. auf **Auto‑Edit** erhöhen.
5. Änderungen **kleinschrittig** übernehmen, **Diffs** prüfen, **Tests** laufen lassen.
6. Bei Bedarf **ZDR aktiv** und **ohne Netz** arbeiten.

---

## 14) Mini‑Referenz (Befehle & Flags)

```bash
codex                              # Start TUI (Suggest)
codex --auto-edit                  # Dateien automatisch schreiben
codex --full-auto                  # Schreiben + Kommandos (Sandbox)
codex -m gpt-4.1                   # Modell explizit wählen
codex --oss -m gpt-oss:20b         # Lokales Modell über Ollama
codex --profile <name>             # Profil aus config.toml
codex --login                      # ChatGPT-Login (OAuth)
codex exec "<Anweisung>"           # Headless/CI ohne TUI
codex --help                       # Hilfe / Flags
codex --version                    # Version anzeigen
```

---

## 15) Anhang: Vorlagen

### 15.1 `AGENTS.md` (Kurzfassung)
```markdown
# AGENTS.md — Projektleitfaden

## Grundregeln
- Kleine Schritte, nach jeder Änderung Lint/Tests.
- Keine Netz-/Git-Remote-Aktionen ohne Anweisung.

## Python
- Lint: ruff check .
- Format: black .
- Tests: pytest -q --maxfail=1 --disable-warnings

## Flutter
- flutter analyze
- dart format .
- flutter test

## Rollen
- Executor, Validator, Debugger, Formatter, Doc-Generator

## Abbruchkriterien
- Rot bei Lint/Tests ⇒ stoppen, Bericht liefern.
```

### 15.2 `~/.codex/config.toml` (Kurzfassung)
```toml
model = "gpt-4.1"
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[profiles.readonly]
approval_policy = "always"
sandbox_mode = "read-only"

[model_providers.oss]
name = "Open Source"
base_url = "http://localhost:11434/v1"

[profiles.ollama_local]
model_provider = "oss"
model = "gpt-oss:20b"
```
