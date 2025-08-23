# MCP‑Server mit Claude‑Flow@alpha (v2) – Addendum

*Stand: 2025-08-16*

**Kurzfassung:** `npx claude-flow@alpha init --force` richtet die MCP‑Anbindung für **Claude Code** automatisch ein. Zusätzliche Server verwaltest du mit der **Claude‑Code‑CLI** (`claude mcp …`). Für ausführende Agenten ist `--claude` erforderlich.

---

## 1) Überblick
- **MCP** verbindet Claude Code standardisiert mit Tools/Datenquellen (stdio/SSE/HTTP).  
- **Claude‑Flow v2** nutzt MCP über Claude Code; in Flow‑Befehlen sind keine MCP‑Spezialflags nötig – **wichtig ist `--claude`**.  
- **Scopes:** local (User), project (`.mcp.json` im Projekt), user (`~/.claude`).

## 2) Status prüfen
```bash
claude mcp list
claude mcp get github
```

## 3) Projektweit teilen – `.mcp.json`
```bash
# Beispiel: Linear (SSE)
claude mcp add --scope project --transport sse linear https://mcp.linear.app/sse
```
Beispiel‑Schema:
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
**Auto‑Freigabe projektweiter MCPs:** `~/.claude/settings.json` → `"enableAllProjectMcpServers": true`

## 4) Server hinzufügen (Varianten)
**stdio (lokal):**
```bash
claude mcp add airtable --env AIRTABLE_API_KEY=YOUR_KEY -- npx -y airtable-mcp-server
```
**SSE (remote):**
```bash
claude mcp add --transport sse linear https://mcp.linear.app/sse
```
**HTTP (remote):**
```bash
claude mcp add --transport http notion https://mcp.notion.com/mcp
```
**JSON direkt:**
```bash
claude mcp add-json weather-api '{
  "type": "stdio",
  "command": "/path/to/cli",
  "args": ["--api-key","abc123"],
  "env": { "CACHE_DIR": "/tmp" }
}'
```

## 5) Nutzung mit Claude‑Flow
```bash
# Einmalig initialisieren (MCP‑Setup)
npx claude-flow@alpha init --force

# Swarm/Hive nutzen (MCP wirkt automatisch über Claude Code)
npx claude-flow@alpha swarm "Fix build pipeline" --claude --verbose
npx claude-flow@alpha hive-mind spawn "Implement OAuth login" --claude --verbose
```

## 6) Tipps (CI/Automatisierung)
- `MCP_TIMEOUT` erhöhen (z. B. 15000)  
- `MAX_MCP_OUTPUT_TOKENS` begrenzt Tool‑Ausgaben  
- `--permission-prompt-tool <tool>` für Non‑Interactive‑Runs

## 7) Hinweise
- Windows nativ: stdio‑Server via `cmd /c` wrappen.  
- Repos unter `/mnt/*`: States (SQLite) auf ext4 verlagern.

## 8) Links
- Anthropic · MCP mit Claude Code — https://docs.anthropic.com/en/docs/claude-code/mcp  
- Anthropic · Claude Code CLI — https://docs.anthropic.com/en/docs/claude-code/cli-reference  
- Anthropic · Settings — https://docs.anthropic.com/en/docs/claude-code/settings  
- Github · claude‑flow — https://github.com/ruvnet/claude-flow
