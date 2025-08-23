<!-- rebuilt 2025-08-16 with MCP section -->
# Claude‑Flow@alpha – WSL Prompt & Command Wizard · Handbuch
*Stand: 2025-08-16*

## Inhalt
Überblick · Voraussetzungen · Quickstart · Konzepte · Konfiguration · CLI · Wizard · MCP · SQLite · Troubleshooting · Links

## Überblick
Wizard erzeugt Einzeiler für `wsl.exe … bash -lc "…"`, setzt UTF‑8, wechselt ins Projekt. **`--claude`** ist erforderlich für ausführende Agenten.

## Voraussetzungen
- Windows + WSL (Ubuntu), Node.js 18+, npm 9+
- Claude Code global (`npm i -g @anthropic-ai/claude-code`), Claude‑Flow via `npx`

## Quickstart
1) Projektpfad setzen → WSL‑Pfad prüfen  
2) Optional Saved‑Config `.claude-flow/saved-configs/*.json`  
3) Preset & Flags (`--claude`, `--verbose`) → **Befehl erzeugen**

## Konzepte
- **Swarm** → `npx claude-flow@alpha swarm "…" --claude`  
- **Hive‑Mind** → `npx claude-flow@alpha hive-mind spawn "…" --claude`

## Konfiguration & Speicherorte
- Saved‑Configs `.claude-flow/saved-configs/<NAME>.json` → `--config ./…`  
- Daten: `.hive-mind/` (Konfig/Sessions), `.swarm/` (SQLite: `memory.db`)  
- Namespaces: `--namespace`

## Wichtige CLI‑Kommandos
```bash
npx claude-flow@alpha init --force
npx claude-flow@alpha --help
npx claude-flow@alpha hive-mind spawn "Ziel" --claude --verbose
npx claude-flow@alpha swarm "Ziel" --claude --verbose
npx claude-flow@alpha hive-mind status
npx claude-flow@alpha memory stats|list|search
```


## MCP‑Server: Einrichtung & Nutzung (mit Claude Code)

**Kurzfassung:** `npx claude-flow@alpha init --force` richtet in v2 die MCP‑Anbindung für **Claude Code** automatisch ein. Zusätzliche Server verwaltest du mit der **Claude‑Code‑CLI** (`claude mcp …`).

**Status prüfen**
```bash
claude mcp list
claude mcp get github
```

**Projektweit teilen (`.mcp.json`)**
```bash
claude mcp add --scope project --transport sse linear https://mcp.linear.app/sse
```
Beispielschema:
```json
{
  "mcpServers": {
    "linear": {
      "type": "sse",
      "url": "https://mcp.linear.app/sse",
      "headers": {}
    }
  }
}
```

**Weitere Varianten**
```bash
# stdio (lokal)
claude mcp add airtable --env AIRTABLE_API_KEY=YOUR_KEY -- npx -y airtable-mcp-server

# HTTP
claude mcp add --transport http notion https://mcp.notion.com/mcp

# JSON direkt
claude mcp add-json weather-api '{"type":"stdio","command":"/path/to/cli","args":["--api-key","abc"],"env":{"CACHE_DIR":"/tmp"}}'
```

**Settings & Automatisierung**
- `~/.claude/settings.json` → `"enableAllProjectMcpServers": true`
- Zeitlimits/Output: `MCP_TIMEOUT=15000`, `MAX_MCP_OUTPUT_TOKENS=...`



## SQLite für Claude‑Flow: Neuinstallation, Reparatur & Reset

Claude‑Flow nutzt eine **SQLite‑Datenbank** (Standard: `.swarm/memory.db`) für Persistenz/Memory. Fehler wie **„disk I/O error“** sind häufig Dateisystem‑/Locking‑Probleme (z. B. `/mnt/*`). Empfohlen: State/Projekt im **WSL‑ext4**‑Dateisystem.

**1) Installation/Neuinstallation (Ubuntu/WSL)**
```bash
sudo apt update
sudo apt install --reinstall sqlite3 libsqlite3-0 libsqlite3-dev -y
sqlite3 --version
```

**2) Node‑Bindings reparieren (falls genutzt)**
```bash
# optional, wenn das Projekt native Bindings wie 'better-sqlite3' verwendet
npm rebuild better-sqlite3
# alternativ
npm install --build-from-source better-sqlite3
```

**3) State auf ext4 verlagern (empfohlen)**
```bash
# Ziel auf ext4
mkdir -p ~/cf_state/myproj/{hive,swarm}

# im Projekt (unter /mnt/...):
cd /pfad/zum/projekt
# vorhandene Ordner sichern/entfernen (falls vorhanden & entbehrlich)
mv .hive-mind .hive-mind.bak.$(date +%s) 2>/dev/null || true
mv .swarm     .swarm.bak.$(date +%s)     2>/dev/null || true

ln -s ~/cf_state/myproj/hive  .hive-mind
ln -s ~/cf_state/myproj/swarm .swarm
```

**4) Datenbank zurücksetzen**
```bash
# Achtung: löscht persistente Erinnerungen/Status
rm -f .swarm/memory.db .swarm/memory.db-journal .swarm/*.sqlite-shm .swarm/*.sqlite-wal 2>/dev/null || true
npx claude-flow@alpha init --force
```

**5) Health‑Checks**
```bash
npx claude-flow@alpha memory stats
npx claude-flow@alpha memory list --limit 10
npx claude-flow@alpha hive-mind status --verbose
```


## Troubleshooting
- **SQLite „disk I/O error“** → State auf ext4, DB reset, ggf. `better-sqlite3` rebuild  
- **Keine Agenten** → `--claude` gesetzt? `@anthropic-ai/claude-code` installiert?  
- **WSL‑Performance** → Projekt im Linux‑Dateisystem (nicht `/mnt`)

## Links
- Anthropic · MCP, CLI, Settings  
- GitHub · ruvnet/claude‑flow  
- Microsoft · WSL Filesystems
