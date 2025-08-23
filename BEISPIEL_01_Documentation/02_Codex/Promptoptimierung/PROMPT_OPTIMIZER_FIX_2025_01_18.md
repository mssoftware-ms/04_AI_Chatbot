# Task Prompt Optimizer - Behebung des Optimierungsproblems

## Problem
Der Task Prompt Optimizer zeigte beim Klick auf "Optimieren" für 5 Sekunden "Optimiere..." an, lieferte aber keine Ergebnisse zurück.

## Ursachen
1. **Fehlende API-Key-Erkennung**: Der Dialog suchte nur nach der Umgebungsvariable `OPENAI_API_KEY`, nicht aber in den Anwendungseinstellungen
2. **Unzureichende Fehlerbehandlung**: Fehler wurden in einem Thread gefangen, aber möglicherweise nicht korrekt angezeigt
3. **Keine Möglichkeit zur direkten Eingabe**: Benutzer konnten den API-Key nicht direkt im Dialog eingeben

## Implementierte Lösungen

### 1. Erweiterte API-Key-Suche
Der Dialog sucht nun nach dem API-Key in mehreren Quellen:
- Umgebungsvariable `OPENAI_API_KEY`
- Konfigurationsdatei `src/claude_flow_gui/stt_settings.json`
- Gespeicherte Konfigurationen in `.claude-flow/saved-configs/`
- Andere Anwendungseinstellungen

### 2. Direkte API-Key-Eingabe im Dialog
- Wenn kein API-Key gefunden wird, erscheint ein Eingabefeld direkt im Dialog
- Der Benutzer kann den Key eingeben und mit "API Key setzen" speichern
- Der Key wird für zukünftige Nutzung in den Einstellungen gespeichert

### 3. Verbesserte Fehlerbehandlung
- Detaillierte Debug-Ausgaben in der Konsole
- Spezifische Fehlermeldungen für verschiedene Problemtypen:
  - API-Key-Fehler
  - Modell-Verfügbarkeitsprobleme
  - Netzwerkfehler
- Statusanzeige zeigt den aktuellen API-Key-Status

### 4. Visuelle Statusanzeige
- ✅ Grüner Status wenn API-Key geladen wurde
- ⚠️ Gelbe Warnung wenn kein Key gefunden wurde
- ❌ Roter Fehler wenn OpenAI-Bibliothek fehlt

## Erforderliche Schritte für den Benutzer

### 1. OpenAI-Bibliothek installieren
```bash
pip install openai
```

### 2. API-Key konfigurieren (eine der folgenden Optionen):

#### Option A: Direkt im Dialog eingeben
1. Öffnen Sie den Task Prompt Optimizer
2. Geben Sie Ihren API-Key im Eingabefeld ein
3. Klicken Sie auf "API Key setzen"

#### Option B: Als Umgebungsvariable setzen
```bash
# Windows (PowerShell)
$Env:OPENAI_API_KEY="sk-..."

# Windows (CMD)
set OPENAI_API_KEY=sk-...

# Linux/Mac
export OPENAI_API_KEY="sk-..."
```

#### Option C: In den Anwendungseinstellungen speichern
Der API-Key kann auch in der Datei `src/claude_flow_gui/stt_settings.json` gespeichert werden:
```json
{
  "openai_api_key": "sk-...",
  ...
}
```

## Funktionstest

1. **Starten Sie die Anwendung**
2. **Geben Sie einen Task ein** in das Haupteingabefeld
3. **Klicken Sie auf "Task Prompt Optimizer"**
4. **Prüfen Sie den API-Key-Status** oben im Dialog
5. **Falls kein Key vorhanden**: Geben Sie ihn direkt ein
6. **Klicken Sie auf "Optimieren"**
7. **Beobachten Sie die Konsole** für Debug-Ausgaben

## Debug-Ausgaben

Die folgenden Debug-Meldungen helfen bei der Fehlersuche:
- `[DEBUG] Found API key in ...` - Key wurde gefunden
- `[DEBUG] OpenAI client initialized successfully` - Client ist bereit
- `[DEBUG] Starting optimization...` - Optimierung beginnt
- `[DEBUG] Response received successfully` - Antwort erhalten
- `[ERROR] ...` - Fehlermeldungen mit Details

## Bekannte Modelle

Der Dialog unterstützt folgende OpenAI-Modelle:
- gpt-5
- gpt-4.1
- gpt-4.1-mini
- o3-mini
- gpt-4-turbo-preview
- gpt-4-0125-preview
- gpt-3.5-turbo-0125

**Hinweis**: Nicht alle Modelle sind für alle Accounts verfügbar. Bei Fehlern wechseln Sie zu einem verfügbaren Modell wie `gpt-3.5-turbo` oder `gpt-4-turbo-preview`.

## Fehlerbehebung

### Problem: "OpenAI-Bibliothek nicht installiert"
**Lösung**: Führen Sie `pip install openai` aus

### Problem: "Kein API Key gefunden"
**Lösung**: Geben Sie den Key direkt im Dialog ein oder setzen Sie die Umgebungsvariable

### Problem: "Model not found" Fehler
**Lösung**: Wechseln Sie zu einem anderen Modell (z.B. gpt-3.5-turbo)

### Problem: "Invalid API key" Fehler
**Lösung**: Überprüfen Sie, dass Ihr API-Key mit "sk-" beginnt und gültig ist

## Testskript

Ein Testskript wurde erstellt unter `tests/test_prompt_optimizer_fix.py` zur Überprüfung der Installation und Konfiguration.

Ausführung:
```bash
python3 tests/test_prompt_optimizer_fix.py
```

## Zusammenfassung

Die Implementierung behebt das ursprüngliche Problem durch:
1. ✅ Mehrere Quellen für API-Key-Suche
2. ✅ Direkte Eingabemöglichkeit im Dialog
3. ✅ Verbesserte Fehlerbehandlung und Logging
4. ✅ Klare Statusanzeigen
5. ✅ Persistente Speicherung des API-Keys

Der Task Prompt Optimizer sollte nun ordnungsgemäß funktionieren, sobald die OpenAI-Bibliothek installiert und ein gültiger API-Key konfiguriert ist.