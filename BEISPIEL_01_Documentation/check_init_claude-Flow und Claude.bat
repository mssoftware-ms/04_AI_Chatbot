#!/bin/bash
echo "=== Checking Claude Tools Initialization ==="

CLAUDE_CODE_INIT=false
CLAUDE_FLOW_INIT=false

# Check für .claude Verzeichnis
if [ -d ".claude" ]; then
    echo "✓ .claude Verzeichnis gefunden"
    
    # Check für Claude Code spezifische Dateien
    if [ -f ".claude/config.json" ] || [ -f ".claude/claude_config.json" ] || [ -f ".claude/project.json" ]; then
        CLAUDE_CODE_INIT=true
        echo "  ├─ Claude Code Konfigurationsdateien gefunden"
    fi
    
    # Check für Claude Flow spezifische Dateien/Verzeichnisse
    if [ -d ".claude/monitoring" ] || [ -d ".claude/flows" ] || [ -d ".claude/workflows" ]; then
        CLAUDE_FLOW_INIT=true
        echo "  ├─ Claude Flow Verzeichnisse gefunden"
    fi
fi

# Check für Claude Flow Konfiguration im Root
if [ -f "claude-flow.config.json" ] || [ -f "claude-flow.config.js" ]; then
    CLAUDE_FLOW_INIT=true
    echo "✓ Claude Flow Konfigurationsdatei im Root gefunden"
fi

# Check in package.json
if [ -f "package.json" ] && grep -q "claude-flow" package.json 2>/dev/null; then
    echo "✓ Claude Flow in package.json gefunden"
fi

echo ""
echo "=== ERGEBNIS ==="

if [ "$CLAUDE_CODE_INIT" = true ] && [ "$CLAUDE_FLOW_INIT" = true ]; then
    echo "✓ BEIDE Tools wurden initialisiert:"
    echo "  ├─ claude init wurde ausgeführt"
    echo "  └─ npx claude-flow@alpha init wurde ausgeführt"
elif [ "$CLAUDE_FLOW_INIT" = true ]; then
    echo "✓ NUR Claude Flow wurde initialisiert"
    echo "  └─ claude init wurde NICHT separat ausgeführt"
elif [ "$CLAUDE_CODE_INIT" = true ]; then
    echo "✓ NUR Claude Code wurde initialisiert"
    echo "  └─ claude-flow wurde NICHT ausgeführt"
else
    echo "✗ KEINE Claude Tools wurden initialisiert"
fi

# Optional: Zeige Verzeichnisinhalt für manuelle Inspektion
if [ -d ".claude" ]; then
    echo ""
    echo "=== .claude Verzeichnisinhalt (zur manuellen Prüfung) ==="
    ls -la .claude/ 2>/dev/null | head -10
fi