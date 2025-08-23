<!-- rebuilt 2025-08-16 with MCP section -->
# Claude‑Flow@alpha – Befehlszeilen‑Wizard (v2.2.1) · Handbuch
*Stand: 2025-08-16*

## Ziel
Einzeiler für `claude-flow@alpha` (WSL/CMD/WT) generieren, ohne sie auszuführen. **`--claude`** ist Pflicht für ausführende Agenten.

## Bedienung
1) Projektpfad (Windows) → WSL‑Pfad prüfen  
2) Preset & Objective, Saved‑Config optional  
3) Flags (`--claude`, `--verbose`, weitere)  
4) Ausgabeformat (WSL/CMD/WT/Nur Linux)  
5) Befehl erzeugen → kopieren/speichern

## Ausgabeformate (Beispiele)
```bat
wsl.exe -d "Ubuntu" -- bash -lc "export LANG=C.UTF-8; export LC_ALL=C.UTF-8; cd '/mnt/d/.../AI Coding Station' && npx claude-flow@alpha hive-mind spawn '<objective>' --claude --verbose --config ./\.claude-flow/saved-configs/AI\ Coding\ Station.json"
```
```bat
cmd /c start "" wsl.exe -d "Ubuntu" -- bash -lc "export LANG=C.UTF-8; export LC_ALL=C.UTF-8; cd '/mnt/d/…' && npx claude-flow@alpha swarm '<objective>' --claude --verbose"
```
```bat
wt new-tab --title "CF@alpha" wsl.exe -d "Ubuntu" -- bash -lc "export LANG=C.UTF-8; export LC_ALL=C.UTF-8; cd '/mnt/d/…' && npx claude-flow@alpha hive-mind status --verbose"
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


## Links
- Anthropic · MCP, CLI, Settings  
- GitHub · ruvnet/claude‑flow  
- Microsoft · WSL Filesystems
