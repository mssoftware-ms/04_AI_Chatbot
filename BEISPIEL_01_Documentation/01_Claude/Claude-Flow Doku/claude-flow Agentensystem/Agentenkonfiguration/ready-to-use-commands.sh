#!/bin/bash
# Ready-to-use Commands für Ihr Setup
# Claude Code 1.0.83 + claude-flow@alpha v2.0.0-alpha.90

# ========================================
# 1. QUICK TEST - Sofort testen
# ========================================
npx claude-flow@alpha hive-mind spawn "Test: Hello World" \
  --claude \
  --verbose

# ========================================
# 2. MIT IHREN 10 AGENTEN
# ========================================
npx claude-flow@alpha hive-mind spawn \
  "Im fenster Launch hive, steht hinter Console output, immer noch external terminal, allerdings soll bis zum starten von claude-flow, der interne output erfolgen!" \
  --agents queen,backend-dev,frontend-dev,system-architect,tester \
  --topology hierarchical \
  --claude \
  --verbose \
  --memory persistent \
  --parallel

# ========================================
# 3. VOLLSTÄNDIGE KONFIGURATION MIT ALLEN FEATURES
# ========================================
npx claude-flow@alpha hive-mind spawn \
  "Build a REST API with authentication and testing" \
  --agents queen,backend-dev,tester,security-tester,api-documenter,devops-engineer \
  --queen-model claude-3-opus-20240229 \
  --worker-model claude-3-sonnet-20240229 \
  --topology hierarchical \
  --memory persistent \
  --neural-enabled \
  --mcp-enabled \
  --hooks enabled \
  --telemetry enabled \
  --parallel \
  --claude \
  --verbose

# ========================================
# 4. MCP TOOLS TESTEN (v90 Features!)
# ========================================

# Liste verfügbare MCP Tools
npx claude-flow@alpha mcp list-tools

# Teste DAA (Data Analysis Assistant)
npx claude-flow@alpha daa analyze --data sample.csv

# Teste Workflow Tools
npx claude-flow@alpha workflow create "API Development" \
  --steps "design,implement,test,document"

# Performance Monitoring
npx claude-flow@alpha swarm monitor --real-time

# ========================================
# 5. MIT IHRER EXISTIERENDEN CONFIG
# ========================================

# Erst Config generieren (falls noch nicht vorhanden)
cat > claude-flow.config.json << 'EOF'
{
  "name": "Python Development - Your Setup",
  "version": "2.0.0-alpha.90",
  "agents": {
    "selected": [
      "queen",
      "backend-dev",
      "frontend-dev",
      "system-architect",
      "tester",
      "performance-tester",
      "security-tester",
      "devops-engineer",
      "api-documenter",
      "pentester"
    ],
    "models": {
      "queen": "claude-3-opus-20240229",
      "workers": "claude-3-sonnet-20240229"
    }
  },
  "orchestrator": {
    "maxAgents": 10,
    "topology": "hierarchical",
    "memoryEnabled": true
  },
  "mcp": {
    "enabled": true,
    "tools": {
      "daa": true,
      "workflow": true,
      "performance": true
    }
  },
  "authentication": {
    "method": "claude-cli",
    "api_key_required": false
  }
}
EOF

# Dann mit Config starten
npx claude-flow@alpha hive-mind spawn \
  "Your task here" \
  --config claude-flow.config.json \
  --claude \
  --verbose

# ========================================
# 6. PYTHON-SPEZIFISCHE WORKFLOWS
# ========================================

# Django Projekt
npx claude-flow@alpha hive-mind spawn \
  "Create a Django REST API with user authentication" \
  --agents queen,backend-dev,tester,api-documenter \
  --preset python-django \
  --claude \
  --verbose

# FastAPI Projekt
npx claude-flow@alpha hive-mind spawn \
  "Build FastAPI microservice with async database" \
  --agents queen,backend-dev,system-architect,devops-engineer \
  --preset python-fastapi \
  --claude \
  --verbose

# Testing Suite
npx claude-flow@alpha hive-mind spawn \
  "Create comprehensive test suite with pytest" \
  --agents queen,tester,performance-tester,security-tester \
  --preset python-testing \
  --claude \
  --verbose

# ========================================
# 7. SECURITY AUDIT (Ihre Spezial-Agenten)
# ========================================
npx claude-flow@alpha hive-mind spawn \
  "Perform security audit and penetration testing" \
  --agents queen,security-tester,pentester,system-architect \
  --topology mesh \
  --priority critical \
  --sandboxed \
  --claude \
  --verbose

# ========================================
# 8. NEURAL NETWORK TRAINING (v90 Feature!)
# ========================================
npx claude-flow@alpha neural train \
  --pattern coordination \
  --epochs 50 \
  --learning-rate 0.001

# ========================================
# 9. SESSION MANAGEMENT
# ========================================

# Session speichern
npx claude-flow@alpha session save --name "python-project-v1"

# Session wiederherstellen
npx claude-flow@alpha session restore --name "python-project-v1"

# Memory Status
npx claude-flow@alpha memory usage

# ========================================
# 10. DEBUGGING & MONITORING
# ========================================

# Echtzeit-Monitoring
npx claude-flow@alpha swarm monitor --real-time

# Agent Status
npx claude-flow@alpha agent list

# Performance Metriken
npx claude-flow@alpha benchmark run --duration 60s

# Logs anzeigen
npx claude-flow@alpha logs tail --follow

# ========================================
# HILFREICHE UMGEBUNGSVARIABLEN
# ========================================
export CLAUDE_FLOW_DEBUG=verbose
export CLAUDE_FLOW_MAX_AGENTS=10
export CLAUDE_FLOW_MEMORY_PATH=.swarm/memory.db
export CLAUDE_FLOW_PARALLEL_EXECUTION=true
export CLAUDE_FLOW_TOKEN_OPTIMIZATION=true

# ========================================
# TROUBLESHOOTING
# ========================================

# Version Check
echo "Claude Code: $(claude --version)"
echo "Claude-Flow: $(npx claude-flow@alpha --version)"

# MCP Status
npx claude-flow@alpha mcp status

# Agent Verfügbarkeit
npx claude-flow@alpha agent list --available

# Config Validation
npx claude-flow@alpha config validate --file claude-flow.config.json

# ========================================
# WSL-SPEZIFISCHE PFADE
# ========================================
# Windows: D:\03_Git\02_Python\01_AI_Coding_Station
# WSL:     /mnt/d/03_Git/02_Python/01_AI_Coding_Station

# Pfad-Konvertierung für Windows-Tools
WINDOWS_PATH=$(pwd | sed 's|/mnt/\([a-z]\)|\1:|' | sed 's|/|\\|g')
echo "Windows Path: $WINDOWS_PATH"