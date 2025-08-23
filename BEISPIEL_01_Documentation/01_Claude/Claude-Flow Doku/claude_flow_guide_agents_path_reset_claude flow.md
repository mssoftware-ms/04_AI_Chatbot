# Claude-Flow Alpha 91 - Kompletter Leitfaden

## Inhaltsverzeichnis
1. [Speicherung von Agenten und Presets](#speicherung-von-agenten-und-presets)
2. [Wiederherstellung von Claude-Agenten](#wiederherstellung-von-claude-agenten)
3. [Erstellung benutzerdefinierter Agenten/Presets](#erstellung-benutzerdefinierter-agentenpresets)
4. [Community-Ressourcen](#community-ressourcen)
5. [Praktische Beispiele](#praktische-beispiele)

---

## Speicherung von Agenten und Presets

### Hauptspeicherort: SQLite-Datenbank

Claude-Flow verwendet ein **SQLite Memory System** mit einer robusten `.swarm/memory.db` Speicherung, die 12 spezialisierte Tabellen enthält.

**Dateistruktur:**
```
.swarm/
└── memory.db
    ├── memory_store     -- Allgemeine Schlüssel-Wert-Speicherung
    ├── sessions         -- Session-Management
    ├── agents           -- Agent-Registry und Zustand
    ├── tasks            -- Task-Tracking und Status
    ├── agent_memory     -- Agent-spezifischer Speicher
    ├── shared_state     -- Cross-Agent geteilter Zustand
    ├── events           -- Event-Log und Historie
    ├── patterns         -- Gelernte Muster und Verhaltensweisen
    ├── performance_metrics -- Performance-Tracking
    ├── workflow_state   -- Workflow-Persistierung
    ├── swarm_topology   -- Netzwerk-Topologie-Daten
    └── consensus_state  -- Distributed Consensus-Daten
```

### Agent-Definitionen

Die 64 spezialisierten Agenten sind in der `.claude/agents/` Verzeichnisstruktur organisiert, mit 16 Kategorien von Agenten.

**Agent-Struktur:**
```
.claude/
└── agents/
    ├── [16 verschiedene Kategorien]
    └── [64 spezialisierte Agenten insgesamt]
```

### Memory-Befehle

```bash
# Daten speichern
npx claude-flow@alpha memory store "project-context" "Full-stack app requirements"

# Daten abfragen
npx claude-flow@alpha memory query "authentication" --namespace sparc

# Memory-Statistiken anzeigen (zeigt 12 spezialisierte Tabellen)
npx claude-flow@alpha memory stats

# Backup erstellen
npx claude-flow@alpha memory export backup.json --namespace default

# Backup wiederherstellen
npx claude-flow@alpha memory import project-memory.json
```

### Windows-Besonderheit

Für Windows-Benutzer: SQLite wird automatisch auf In-Memory-Speicherung zurückgreifen, wenn native Module fehlschlagen. Alle Features funktionieren normal, aber Daten bleiben nicht zwischen Sessions erhalten.

---

## Wiederherstellung von Claude-Agenten

### 1. Vollständige Neuinitialisierung

```bash
# Einfachste Methode - komplette Neuinitialisierung mit --force Flag
npx claude-flow@alpha init --force
```

Dieser Befehl erstellt ALLE 91 Befehlsdokumentationsdateien und das komplette Agent-System.

### 2. Agent-System überprüfen

```bash
# Überprüfen Sie das komplette 64-Agent-System
npx claude-flow@alpha init

# Verifizieren Sie das Agent-System
ls .claude/agents/
# Zeigt alle 16 Kategorien mit 64 spezialisierten Agenten
```

### 3. Spezifische Agent-Befehle

```bash
# Alle aktiven Agenten auflisten
claude-flow agent list

# Agent-Hierarchie anzeigen
claude-flow agent hierarchy

# Agent-Ökosystem betrachten
claude-flow agent ecosystem

# Detaillierte Informationen über einen Agenten
claude-flow agent info <agent-id>
```

### 4. Memory-System wiederherstellen

```bash
# Memory-System Statistiken prüfen
npx claude-flow@alpha memory stats

# Memory-System aus Backup wiederherstellen
npx claude-flow@alpha memory import project-memory.json

# Oder komplettes Backup wiederherstellen
npx claude-flow@alpha memory restore '/backups/memory-backup.db'
```

### 5. Health Check

```bash
# Automatische Fehlerwiederherstellung und Optimierung
npx claude-flow@alpha health check --components all --auto-heal

# Fault Tolerance prüfen
npx claude-flow@alpha fault tolerance --strategy retry-with-learning
```

### 6. SQLite-Datenbank zurücksetzen

#### Vollständiger Database-Reset

```bash
# WARNUNG: Alle gespeicherten Daten gehen verloren!

# 1. Claude-Flow stoppen (falls läuft)
npx claude-flow@alpha stop

# 2. Backup erstellen (empfohlen)
npx claude-flow@alpha memory export full-backup-$(date +%Y%m%d_%H%M%S).json --namespace default

# 3. Datenbank-Datei löschen
rm .swarm/memory.db

# 4. Neuinitialisierung
npx claude-flow@alpha init --force
```

#### Selektiver Reset bestimmter Bereiche

```bash
# Nur Agent-Daten löschen
npx claude-flow@alpha memory clear --namespace agents

# Nur Session-Daten löschen
npx claude-flow@alpha memory clear --namespace sessions

# Nur Performance-Metriken löschen
npx claude-flow@alpha memory clear --namespace performance_metrics

# Alle Daten außer Konfiguration löschen
npx claude-flow@alpha memory clear --preserve-config
```

#### Database-Wartung

```bash
# Database-Größe prüfen
npx claude-flow@alpha memory stats --detailed

# Verwaiste Datensätze bereinigen
npx claude-flow@alpha memory cleanup --orphaned

# Database optimieren
npx claude-flow@alpha memory optimize --vacuum

# Database-Integrität prüfen
npx claude-flow@alpha memory check --integrity
```

#### Manuelle Datenbank-Verwaltung

```bash
# Mit SQLite direkt arbeiten (für Fortgeschrittene)
sqlite3 .swarm/memory.db

# In SQLite-Shell:
# .tables                    -- Alle Tabellen anzeigen
# .schema table_name         -- Schema einer Tabelle anzeigen
# DROP TABLE table_name;     -- Tabelle löschen
# .quit                      -- SQLite verlassen
```

#### Reset-Strategien nach Problemen

```bash
# Bei Korruption der Datenbank
npx claude-flow@alpha memory repair --auto-fix

# Bei Performance-Problemen
npx claude-flow@alpha memory rebuild --optimize

# Bei Schema-Problemen (nach Updates)
npx claude-flow@alpha memory migrate --force-update
```

### 7. Windows-spezifische Problembehebung

```bash
# SQLite testen
node -e "const Database = require('better-sqlite3'); try { const db = new Database(':memory:'); console.log('✅ SQLite funktioniert!'); db.close(); } catch (error) { console.log('❌ SQLite-Fehler:', error.message); }"

# Bei Problemen: Visual C++ Redistributables installieren
# Herunterladen von: https://aka.ms/vs/17/release/vc_redist.x64.exe

# Windows-spezifischer Database-Reset
# Wenn .swarm/memory.db gesperrt ist:
taskkill /f /im node.exe  # Alle Node-Prozesse beenden
del .swarm\memory.db      # Datei löschen (Windows-Syntax)
```

---

## Erstellung benutzerdefinierter Agenten/Presets

### Für Claude Code (Subagents)

#### Agent-Struktur verstehen

Agenten werden als Markdown-Dateien mit YAML-Frontmatter gespeichert in:
- **Projekt-spezifisch**: `.claude/agents/` (nur für aktuelles Projekt)
- **Benutzer-global**: `~/.claude/agents/` (für alle Projekte verfügbar)

#### Grundlegende Agent-Template

```markdown
---
name: ihr-agent-name
description: Beschreibung, wann dieser Agent verwendet werden soll
tools: tool1, tool2, tool3  # Optional - erbt alle Tools wenn weggelassen
model: sonnet  # Optional - sonnet, opus, oder haiku
---

Ihr Agent-System-Prompt geht hier hin.
Definieren Sie die Rolle, Fähigkeiten und Ansatz zur Problemlösung.
Fügen Sie spezifische Anweisungen, Best Practices und Einschränkungen hinzu.
```

#### Interaktive Erstellung mit /agents

```bash
/agents
```

**Schritte:**
1. **Standort wählen**: Projekt oder Persönlich
2. **Erstellungsart**: "Generate with Claude" (empfohlen) oder Manuell
3. **Tools auswählen**: Nur benötigte Tools gewähren
4. **Hintergrundfarbe**: Zur visuellen Unterscheidung
5. **Review & Speichern**

#### Bewährte Praktiken

**Best Practices:**
- **Mit Claude generieren lassen**: Erstellen Sie den initialen Agent mit Claude und passen Sie ihn dann an
- **Fokussierte Agenten**: Einzelne, klare Verantwortlichkeiten statt "Alles-Könner"
- **Detaillierte Prompts**: Spezifische Anweisungen, Beispiele und Einschränkungen
- **Tool-Minimierung**: Nur notwendige Tools gewähren
- **Beispiele einbauen**: Positive/negative Beispiele im System-Prompt

### Für Claude-Flow (Custom Agents)

#### Claude-Flow Agent-System

Claude-Flow verwendet YAML-basierte Agent-Definitionen:

```yaml
---
name: agent-name
type: agent-type
color: "#HEX_COLOR"
description: Kurze Beschreibung des Agent-Zwecks
capabilities:
  - capability_1
  - capability_2
  - capability_3
priority: high|medium|low|critical
hooks:
  pre: |
    echo "Pre-execution commands"
  post: |
    echo "Post-execution commands"
---
```

#### Agent-Erstellung in Claude-Flow

```bash
# Neuen Agent erstellen
claude-flow agent spawn --type <agent-type> --name "<agent-name>"

# Agent-Informationen anzeigen
claude-flow agent info <agent-id>

# Agent-Hierarchie verwalten
claude-flow agent hierarchy
```

#### Spezialisierte Agent-Teams

**Beispiel Development Team:**

```bash
# Vollständiges Entwicklungsteam erstellen
claude-flow agent spawn --type architect --name "Lead Architect"
claude-flow agent spawn --type coder --name "Senior Developer"
claude-flow agent spawn --type tester --name "QA Lead"
claude-flow agent spawn --type reviewer --name "Code Quality Expert"
```

---

## Community-Ressourcen

### Vorgefertigte Agent-Collections

```bash
# Umfassende Production-Ready Collection (44 Agenten)
git clone https://github.com/wshobson/agents.git ~/.claude/agents/wshobson

# Vollständige Automation Suite (35 Agenten)
git clone https://github.com/dl-ezo/claude-code-sub-agents.git ~/.claude/agents/dl-ezo

# Custom Agent Collection
git clone https://github.com/iannuttall/claude-agents.git ~/.claude/agents/iannuttall
```

---

## Praktische Beispiele

### Beispiel: Security Code-Reviewer Agent

```markdown
---
name: security-code-reviewer
description: Use for security-focused code reviews, vulnerability detection, and secure coding practices analysis
tools: Read, Grep, Write
model: sonnet
---

You are a security-focused code reviewer with expertise in:
- Common vulnerabilities (OWASP Top 10)
- Secure coding practices
- Authentication and authorization flaws
- Input validation issues
- Cryptographic implementations

When reviewing code:
1. Focus on security vulnerabilities first
2. Check for proper input validation
3. Verify authentication/authorization logic
4. Look for hardcoded secrets or credentials
5. Examine error handling for information leakage

Provide actionable feedback with specific line references and remediation suggestions.
```

### Slash Commands

Erstellen Sie Custom Slash Commands in `.claude/commands/`:

```markdown
# .claude/commands/fix-github-issue.md
Please analyze and fix the GitHub issue: $ARGUMENTS.
Follow these steps:
1. Use `gh issue view` to get the issue details
2. Understand the problem described in the issue
3. Search the codebase for relevant files
4. Implement the necessary changes to fix the issue
5. Write and run tests to verify the fix
```

**Verwendung:** `/project:fix-github-issue 1234`

---

## Praktisches Vorgehen

### Schritt-für-Schritt Anleitung:

1. **Starten Sie einfach**: Beginnen Sie mit dem `/agents` Befehl in Claude Code
2. **Lassen Sie Claude generieren**: Nutzen Sie Claude's Hilfe für den ersten Entwurf
3. **Iterieren Sie**: Testen Sie den Agent und verfeinern Sie ihn
4. **Spezialisieren Sie**: Fokussieren Sie auf einzelne, klare Aufgaben
5. **Dokumentieren Sie**: Verwenden Sie aussagekräftige Beschreibungen
6. **Teilen Sie**: Nutzen Sie Versionskontrolle für Team-Agenten

**Tipp**: Beginnen Sie mit Claude-Generierung und customisieren Sie dann - das gibt Ihnen die besten Ergebnisse.

---

## Erweiterte Features

### Hooks und Automation

Claude Code unterstützt Custom Hooks für Automation:
- **PreToolUse**: Vor Tool-Ausführung
- **PostToolUse**: Nach Tool-Fertigstellung  
- **Notification**: Bei Claude-Benachrichtigungen
- **Stop**: Wenn Claude das Antworten beendet

### Wichtige Hinweise

- In Alpha.73 wurde das Problem mit der Agent-Kopierung behoben - alle 64 Agenten werden jetzt ordnungsgemäß während der Initialisierung erstellt
- Die Initialisierung mit `--force` ist normalerweise der sicherste Weg, um das komplette Agent-System wiederherzustellen
- Claude-Flow bietet persistenten Speicher über Sessions hinweg und ermöglicht es, Kontext, Agent-Zustände und Workflow-Informationen dauerhaft zu speichern

---

*Dieser Leitfaden basiert auf Claude-Flow v2.0.0 Alpha 91 und den aktuellen Best Practices der Community.*