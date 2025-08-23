# Zentrales KI‑Memory für Claude‑Code, Claude‑Flow@alpha und Codex CLI
**Version:** 1.0 (2025‑08‑17)  
**Autor:** AI Coding Station – Architekturvorschlag  
**Lizenz:** MIT

---

## TL;DR
- **Ein Speicher, viele Clients:** Ein lokaler Memory‑Dienst (SQLite + Vektorindex) dient als *Single Source of Truth* für **Claude‑Code**, **Claude‑Flow@alpha** und **Codex CLI**.  
- **Datenschutz:** **Lokale Daten werden *nicht automatisch* an Provider gesendet.** Nur exakt die **kontextuell ausgewählten** Textausschnitte, die du dem Prompt beifügst, gehen an die API.  
- **Kostenkontrolle:** Retrieval → Top‑K Auswahl → **Kompakte Zusammenfassung** → knapper Prompt. So bleiben Tokenkosten planbar.  
- **Organisation:** Gemeinsamer Speicher, aber **strikte Tagging‑/Collection‑Strategie** (Projekt, Sprache, Artefakt‑Typ, Kategorie „UI/Fehler/Architektur“, Zeit).  
- **Skalierung:** 100 GB lokal sind OK. Wartung: Deduplizieren, Komprimieren, Backups (Dumps + Git für Textquellen).

---

## 1) Architekturübersicht
**Ziel:** Ein zentrales, lokales Memory, das alle Tools gemeinsam nutzen.

### 1.1 Komponenten
- **Persistenter Kernspeicher (SQLite):** strukturierte Einträge (id, text, metadata, timestamps, source).
- **Vektorindex (ChromaDB *oder* SQLite‑vec):** semantische Suche über `embedding`‑Spalten.
- **Embedding‑Pipeline (lokal):** z. B. `sentence-transformers` (MiniLM/MPNet). *Keine Cloud nötig.*
- **Lokaler Memory‑Service (HTTP/MCP):** dünner Dienst, der CRUD + `search(query, filters, top_k)` anbietet.  
  → Alle Clients sprechen **denselben** Service an.

### 1.2 Datenfluss (RAG)
1. **Intent erkennen** (Thema, Projekt, Sprache, Artefakt‑Typ).  
2. **Retriever** filtert nach Metadaten (z. B. `project=AI-Coding-Station`, `lang=python`, `cat=ui`).  
3. **Semantische Suche** (`top_k` 3–8) + Re‑Ranking (optional).  
4. **Aggregator** fasst Treffer zusammen (Facts/Steps/Code‑Snippets).  
5. **Composer** baut **knappen Prompt‑Kontext** (Budget z. B. 400–1200 Tokens).  
6. **LLM‑Call** (Claude/Codex/…); **nur der komponierte Kontext** wird gesendet.  
7. **Post‑Run Writer** speichert neue Erkenntnisse (Fehler→Lösung, Entscheidungen, Kommandos).

---

## 2) Werden lokale Daten an Provider gesendet?
**Kurz:** *Nein – nicht automatisch.*  
- Nur die **Kontextpassagen**, die du **explizit** in den Prompt einfügst (über deinen Retriever/Composer), werden übertragen.  
- Hältst du Embeddings & Suche **lokal**, bleiben Rohdaten lokal.  
- Deaktiviere Telemetrie der Bibliotheken; nutze *Offline‑Embeddings* für volle Datenhoheit.

---

## 3) Organisation & Taxonomie (ein Speicher, klar getrennt)
**Ein gemeinsamer Speicher** für alle KI‑Tools, aber **konsequentes Tagging** und optional **Collections**:

### 3.1 Metadaten (empfohlen)
- `scope`: `global` | `project:<name>` | `session:<id>`  
- `lang`: `python` | `ts` | `cpp` …
- `artifact`: `code`, `config`, `log`, `error`, `decision`, `doc`, `cmd`
- `category`: `ui`, `api`, `build`, `perf`, `security`, `db`, `devops`
- `framework`: `pyside6`, `qt`, `flutter`, `fastapi`, …
- `project_phase`: `design`, `impl`, `test`, `release`
- `sensitivity`: `public` | `internal` | `secret` (Filter für Export/Teilen)
- `recency`: Timestamp/ISO; erlaubt „frische“ Treffer zu priorisieren

### 3.2 Collections (optional, wenn viele Daten)
- `global_knowledge` (wiederverwendbar, sprach-/framework‑agnostisch)
- `project_<name>` (projektbezogene Artefakte)
- `incidents` (Fehler→Ursache→Fix, mit Referenzen)
- `commands_cache` (nützliche CLI/WSL/PowerShell‑Befehle + Ausgaben)

> **Praxis:** *Ein Speicher, mehrere Collections + reiche Metadaten* schlägt viele isolierte Speicher. Das verhindert Wissensinseln und erleichtert Wiederverwendung → **token‑sparend**.

---

## 4) Konkreter Workflow je Tool

### 4.1 Claude‑Code (Desktop/IDE) via MCP/HTTP
- **Pre‑Hook:** Intent→`search(top_k=5, filters={project, lang, category})`  
- **Compose:** Shrink auf ≤ 800 Tokens (Facts, kurze Snippets, Links auf Quellenpfade)  
- **Call:** Prompt + komprimierter Kontext  
- **Post‑Hook:** neue Erkenntnisse/Fehlerlösungen persistieren (`artifact=decision/error/…`).

### 4.2 Claude‑Flow@alpha
- **Node „Retrieve“:** Filter + Vektor‑Suche  
- **Node „Summarize“ (lokal oder günstiges Modell):** Destillation (Ziele, Constraints, API‑Keys *nie* inline)  
- **Node „LLM“:** nur destillierten Kontext anhängen  
- **Node „Persist“:** Ergebnisse/Kommandos/Logs speichern (mit Rückverweisen auf Dateien/Commits).

### 4.3 Codex CLI (OpenAI)
- **Wrapper‑Script:**  
  1) `retrieve.py --q "$TASK" --filters "project=...,lang=python,category=ui" --top_k 5`  
  2) `summarize.py --in retrieved.json --max_tokens 600`  
  3) `codex exec --context summarized.md -- "$TASK"`  
  4) `store.py --task "$TASK" --stdout out.log --stderr err.log --tags "artifact=decision"`

> **Wichtig:** Beim OpenAI‑Aufruf **niemals** Rohdaten beilegen – immer nur die **Zusammenfassung** und gezielte **Snippets**.

---

## 5) Token‑Optimierungsregeln (pragmatisch und wirksam)
- **Budget pro Call festlegen:** z. B. *Kontext ≤ 800, User‑Prompt ≤ 300, Antwort ≤ 1200 Tokens.*  
- **Top‑K klein halten:** 3–5; Re‑Ranking statt „mehr Treffer“.  
- **Chunking:** 300–800 Tokens, 10–15 % Overlap.  
- **Komprimieren:** Fehler/Fixe als **Regelglieder** speichern („Wenn A→Fehler B, dann Lösung C“).  
- **Deduplizieren:** Hash über normalisierten Text; nur neue Erkenntnisse persistieren.  
- **Recency‑Boost:** Treffer < 14 Tage bevorzugen.  
- **Nicht senden:** Secrets, Keys, PII, große Logs; stattdessen **Pointer** (Datei+Zeile, Commit‑SHA).  
- **Günstige Modelle für Vor‑Summaries** nutzen (lokal oder kleiner API‑Tarif), teure Modelle nur für finale Synthese.

---

## 6) Qualitäts- und Wartungsprozess
- **Nightly:** Dedupe, Re‑index, `VACUUM` (SQLite), vektor‑`optimize`.  
- **Weekly:** „Consolidation“ (ähnliche Einträge mergen, Langtexte → Bullet‑Regeln).  
- **Monthly:** Qualitätsreview: tote Projekte archivieren (`scope=archive`), Tagging‑Standards nachziehen.  
- **Backups:**  
  - **DB‑Dump** (`.sql/.json`) + **Index‑Snapshot** (Chroma/SQLite‑vec Dateien).  
  - 7‑Tage Rotation lokal; optional zusätzlicher verschlüsselter Off‑Site‑Speicher.  
  - Git nur für **Quelltexte/Docs**; DB‑Dumps als Artefakt anhängen (kein Binär‑Spam).

**Cron‑Beispiel (WSL):**
```bash
0 2 * * * /opt/ai-mem/maintenance.sh  # dedupe, vacuum, snapshot
```

---

## 7) Datenmodell (Minimal, praxistauglich)
```yaml
id: uuid
text: str                      # gespeicherter Inhalt (kompakt)
embedding: float[]             # im Vektorspeicher
metadata:
  scope: global|project:<n>|session:<id>
  lang: python|ts|…
  artifact: code|config|log|error|decision|doc|cmd
  category: ui|api|build|perf|security|db|devops
  framework: pyside6|qt|flutter|…
  file: path:line             # optionaler Pointer statt Volltext
  hash: sha256                # für De‑Dup
  sensitivity: public|internal|secret
created_at: iso8601
updated_at: iso8601
```

---

## 8) Beispiel‑Richtlinien (Do/Don’t)
**Do**
- Kurze Snippets statt ganzer Dateien.
- Entscheidungen & Begründungen festhalten (warum X, nicht Y).
- Fehlermuster + Fix als kondensierte Regel speichern.

**Don’t**
- Secrets/PII in Speicher oder Prompts.  
- Ungefilterte Logs/Stacktraces einblenden.  
- „Alles mitschicken“ – *Retrieval first, Compress second*.

---

## 9) Umsetzungsschritte (Start‑Guide)
1. **Service aufsetzen:** FastAPI/Go‑Binary oder MCP‑Server, Pfad `~/.ai-mem/`.  
2. **DB anlegen:** SQLite + Chroma/SQLite‑vec, Indizes für `scope, lang, category`.  
3. **Embedding lokal:** `sentence-transformers` installieren, Modell cachen.  
4. **Wrapper integrieren:** Pre‑/Post‑Hooks in Claude‑Flow und Codex CLI.  
5. **Tagging‑Standard dokumentieren** (README.md im Repo).  
6. **Backups + Maintenance** (Script + Cron).  
7. **KPIs:** Retrieval‑Trefferqualität, Token/Call, Kosten/Feature, Zeit/Antwort.

---

## 10) FAQ
- **Sollen Daten thematisch oder projektbezogen getrennt werden?**  
  **Beides über Metadaten**: *ein* gemeinsamer Speicher, aber `scope=project:<name>` und Kategorien/Tags. Suche immer mit Filtern + Semantik.
- **Senden wir große Datenberge an die API?**  
  Nein. Nur **kuratierten, knappen Kontext** (Top‑Treffer, destilliert). Rohdaten bleiben lokal.
- **100 GB – problematisch?**  
  Nicht grundsätzlich. Achte auf Indizes, regelmäßige Optimierung, Archivierung alter Projekte. Chunking + Tags halten Suchen schnell.
- **Trennung sensibler Daten?**  
  Ja: `sensitivity`‑Tag erzwingen und diese Einträge **nie** in Prompts exportieren; nur Pointer.

---

## 11) Beispiel‑Konfiguration (Ausschnitt)
```ini
# ai-mem.toml
[storage]
root = "/home/<user>/.ai-mem"
backend = "sqlite"
vector = "sqlite-vec"  # oder "chroma"

[retrieval]
top_k = 5
min_score = 0.35
max_context_tokens = 900

[embedding]
provider = "local"
model = "sentence-transformers/all-MiniLM-L6-v2"
batch_size = 32

[privacy]
strip_secrets = true
telemetry = "off"
export_secrets = false

[maintenance]
dedupe = "nightly"
consolidate = "weekly"
snapshot = "daily"
```

---

## 12) Checkliste (Go‑Live)
- [ ] Embeddings lokal & Telemetrie aus.  
- [ ] Wrapper in **Claude‑Flow**/**Codex CLI** aktiv.  
- [ ] Tagging‑Standard im Repo dokumentiert.  
- [ ] Backups + Rotation getestet (Restore‑Probe!).  
- [ ] KPI‑Dashboard: Token/Call, Trefferqualität, Kosten.

---

**Schlussfolgerung:**  
Ein **gemeinsamer** lokaler Speicher mit **striktem Tagging** + **gezieltem Retrieval** liefert maximale Wiederverwendbarkeit bei minimalen Tokenkosten. Rohdaten bleiben lokal; an die Provider gehen nur **kompakt kuratierte** Auszüge. Das System ist damit skalierbar, kosteneffizient und tool‑agnostisch – ideal für Claude‑Code, Claude‑Flow@alpha und Codex CLI.
