---
title: Maschinenlesbare Technik‑Doku – Best Practices (Markdown + JSONL)
version: 1.0
tags: [documentation, markdown, jsonl, rag, chunking, fine-tuning]
last_updated: 2025-08-16
---

# Ziel
So strukturierst du technische Doku, damit **LLMs** sie **sauber parsen**, **indexieren** (RAG) und **trainieren** (Fine‑Tuning) können – ohne Informationsverlust.

---

## 1) Primärformat: **Markdown (.md)**
Warum Markdown?
- **Klare Struktur** (Überschriften, Listen, Codefences) → hervorragend für header‑basiertes Chunking.  citeturn1search1
- **Weit verbreitet** – viele Ingest‑Pipelines können Markdown direkt splitten (z. B. LangChain).  citeturn1search10turn1search19
- **Konvertierbar** – PDFs/Word vor dem Ingest nach Markdown/TXT konvertieren.

**Konventionen**
- Max. 80–120 Zeichen pro Zeile (diff‑freundlich).
- Sinnvolle **H1–H3**‑Gliederung; **ein Thema pro Abschnitt**.
- **Kürzere Absätze**; Tabellen nur wenn nötig (oder in Listen umformen).
- Code immer in **sprachgetrennten Fences**: ```bash```, ```cmd```, ```powershell``` etc.

**Beispiel‑Skeleton**
```markdown
---
title: WSL vs. Windows – Quoting & Pfade
version: 1.0
tags: [wsl, cmd, bash]
---

# Überblick
…

## Quoting
### Bash
```bash
echo "hi"
```
```

---

## 2) Chunking für RAG
Empfehlung: **Header‑basiertes** Chunking + **inhaltliche** Grenzen respektieren.  citeturn1search1turn1search12

- **Chunkgröße** als Startwert: **~200–500 Tokens**, je nach Domäne; bei faktenlastigen Queries eher 128–256, bei kontextreichen Abschnitten größer.  citeturn1search7turn1search3
- **Overlap** 10–20 % zur Kontextbrücke.
- **Codeblöcke nicht splitten**; Tabellen ggf. in Listen normalisieren.
- Tooling: `MarkdownHeaderTextSplitter` (LangChain).  citeturn1search2turn1search10

---

## 3) JSONL für Training / Auswertung
Für **Supervised Fine‑Tuning** erwartet OpenAI **JSONL** mit Chat‑Nachrichten.  citeturn1search8

**Beispiel (`dataset.jsonl`)**
```jsonl
{"messages":[
  {"role":"system","content":"Du bist ein technischer Assistent."},
  {"role":"user","content":"Wie escape ich ; in Windows Terminal?"},
  {"role":"assistant","content":"In wt.exe trennt ; Subkommandos. Verwende \\; oder vermeide ; durch Script-Wrapper."}
]}
```

**Hinweise**
- **Kurze, präzise** Beispiele; vermeiden, mehrere Konzepte in einem Sample zu mischen.
- **Einheitlicher Stil** (Terminologie, Groß/Kleinschreibung).
- **Evaluation** separat anlegen – gleiche Struktur wie Training.

---

## 4) Metadaten & Dateischnitt
- Pro **Thema/Datei** ≤ ~2–3 k Tokens; große Werke in Kapitel‑Dateien splitten.
- **YAML‑Frontmatter** (Titel, Version, Tags) für Retrieval‑Filter.
- **Eindeutige Dateinamen** (`wsl-windows-quoting.md`).

---

## 5) Ingest‑Pipeline (Empfehlung)
1. **Quellen** (PDF/DOCX/HTML) → **Markdown** normalisieren.  
2. **Reinigung**: Unicode‑Norm, Whitespace, feste Codefences, Tabellen prüfen.  
3. **Chunking** – header‑aware; semantische Grenzen berücksichtigen.  citeturn1search12  
4. **Indizieren** (Vektor + BM25 hybrid).  
5. **Antwortformat** standardisieren (JSON/Structured Outputs), wo sinnvoll.  citeturn1search14

---

## 6) Anti‑Pattern (vermeiden)
- Reine **PDFs** mit Mehrspalten‑Layout ohne Konvertierung.  
- **Überlange Tabellen** als Screenshot.  
- Prompt‑Marker (`$`, `>`) **im** Codeblock belassen – erschwert exakte Ausführung.
- Unsaubere Zeichensätze (Mischung UTF‑8/UTF‑16) ohne Deklaration.

---

## 7) Quick‑Checkliste
- [ ] Markdown mit H1–H3, kurze Absätze, sprachgetrennte Codefences.  
- [ ] Header‑basiertes Chunking (200–500 Tokens, 10–20 % Overlap).  citeturn1search1turn1search7  
- [ ] JSONL für Training vorhanden, konsistenten Stil prüfen.  citeturn1search8  
- [ ] Metadaten/Dateinamen eindeutig, Kapitel‑Schnitt < 3 k Tokens.  
- [ ] PDFs/Word nur als Quelle – konvertiert und bereinigt.
