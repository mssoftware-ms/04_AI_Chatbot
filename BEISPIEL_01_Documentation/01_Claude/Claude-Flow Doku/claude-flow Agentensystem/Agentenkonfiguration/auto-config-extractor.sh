#!/bin/bash
# Claude-Flow Configuration Auto-Extractor and Merger
# This script automatically extracts values from existing configs and creates a complete configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Output file
OUTPUT_CONFIG=".claude-flow/saved-configs/20250819_Python-Development-Complete.json"
TEMP_CONFIG="/tmp/claude-flow-config-temp.json"

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}     Claude-Flow Configuration Auto-Extractor v1.0${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo

# Function to extract JSON value
extract_json_value() {
    local file=$1
    local key=$2
    if [ -f "$file" ]; then
        python3 -c "
import json
import sys
try:
    with open('$file', 'r') as f:
        data = json.load(f)
    keys = '$key'.split('.')
    value = data
    for k in keys:
        if k in value:
            value = value[k]
        else:
            print('NOT_FOUND')
            sys.exit(0)
    print(json.dumps(value) if isinstance(value, (dict, list)) else value)
except:
    print('ERROR')
" 2>/dev/null || echo "NOT_FOUND"
    else
        echo "FILE_NOT_FOUND"
    fi
}

# Initialize configuration object
echo -e "${BLUE}[1/8] Initializing configuration structure...${NC}"
cat > "$TEMP_CONFIG" << 'EOF'
{
  "extracted_from": {},
  "warnings": [],
  "config": {}
}
EOF

# 1. Extract from .claude/settings.json
echo -e "${BLUE}[2/8] Extracting from .claude/settings.json...${NC}"
if [ -f ".claude/settings.json" ]; then
    MODEL=$(extract_json_value ".claude/settings.json" "model")
    PERMISSIONS=$(extract_json_value ".claude/settings.json" "permissions")
    HOOKS=$(extract_json_value ".claude/settings.json" "hooks")
    ENV_VARS=$(extract_json_value ".claude/settings.json" "env")
    
    echo -e "  ${GREEN}✓${NC} Model: $MODEL"
    echo -e "  ${GREEN}✓${NC} Permissions found"
    echo -e "  ${GREEN}✓${NC} Hooks found"
    
    # Store extracted values
    python3 << EOF
import json
with open('$TEMP_CONFIG', 'r') as f:
    config = json.load(f)
config['extracted_from']['claude_settings'] = {
    'model': '$MODEL',
    'permissions': $PERMISSIONS if '$PERMISSIONS' != 'NOT_FOUND' else {},
    'hooks': $HOOKS if '$HOOKS' != 'NOT_FOUND' else {},
    'env': $ENV_VARS if '$ENV_VARS' != 'NOT_FOUND' else {}
}
with open('$TEMP_CONFIG', 'w') as f:
    json.dump(config, f, indent=2)
EOF
else
    echo -e "  ${YELLOW}⚠${NC} File not found - using defaults"
fi

# 2. Extract from .mcp.json
echo -e "${BLUE}[3/8] Extracting MCP server configurations...${NC}"
if [ -f ".mcp.json" ]; then
    MCP_SERVERS=$(extract_json_value ".mcp.json" "mcpServers")
    
    if [ "$MCP_SERVERS" != "NOT_FOUND" ] && [ "$MCP_SERVERS" != "ERROR" ]; then
        echo -e "  ${GREEN}✓${NC} MCP servers configuration found"
        
        # Count MCP servers
        SERVER_COUNT=$(echo "$MCP_SERVERS" | python3 -c "import json, sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        echo -e "  ${GREEN}✓${NC} Found $SERVER_COUNT MCP server(s)"
        
        # Store MCP configuration
        python3 << EOF
import json
with open('$TEMP_CONFIG', 'r') as f:
    config = json.load(f)
config['extracted_from']['mcp'] = {
    'servers': $MCP_SERVERS,
    'count': $SERVER_COUNT
}
with open('$TEMP_CONFIG', 'w') as f:
    json.dump(config, f, indent=2)
EOF
    else
        echo -e "  ${YELLOW}⚠${NC} No MCP servers found"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} .mcp.json not found - MCP will need manual configuration"
    echo -e "  ${YELLOW}  Run: npx claude-flow@alpha mcp init${NC}"
fi

# 3. Extract environment variables
echo -e "${BLUE}[4/8] Checking environment variables...${NC}"
ENV_CHECK=""

check_env() {
    local var_name=$1
    local var_value="${!var_name}"
    if [ -n "$var_value" ]; then
        echo -e "  ${GREEN}✓${NC} $var_name: [SET]"
        ENV_CHECK="$ENV_CHECK\"$var_name\":\"FOUND\","
        return 0
    else
        echo -e "  ${RED}✗${NC} $var_name: [NOT SET]"
        ENV_CHECK="$ENV_CHECK\"$var_name\":\"MISSING\","
        return 1
    fi
}

check_env "ANTHROPIC_API_KEY" || true
check_env "GITHUB_PERSONAL_ACCESS_TOKEN" || true
check_env "OPENAI_API_KEY" || true
check_env "CLAUDE_FLOW_DEBUG" || true
check_env "PYTHON_PATH" || true
check_env "PYTHONPATH" || true

# 4. Check for existing agents
echo -e "${BLUE}[5/8] Scanning for custom agents...${NC}"
AGENT_COUNT=0
if [ -d ".claude/agents" ]; then
    AGENT_COUNT=$(ls -1 .claude/agents/*.md 2>/dev/null | wc -l)
    if [ $AGENT_COUNT -gt 0 ]; then
        echo -e "  ${GREEN}✓${NC} Found $AGENT_COUNT custom agent(s)"
        ls -1 .claude/agents/*.md 2>/dev/null | while read agent; do
            echo -e "    • $(basename $agent)"
        done
    else
        echo -e "  ${YELLOW}⚠${NC} No custom agents found"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} .claude/agents directory not found"
fi

# 5. Check Python environment
echo -e "${BLUE}[6/8] Checking Python environment...${NC}"
PYTHON_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2 || echo "NOT_FOUND")
PIP_VERSION=$(pip3 --version 2>/dev/null | cut -d' ' -f2 || echo "NOT_FOUND")
VENV_EXISTS="false"
[ -d ".venv" ] && VENV_EXISTS="true"
[ -d "venv" ] && VENV_EXISTS="true"

echo -e "  ${GREEN}✓${NC} Python: $PYTHON_VERSION"
echo -e "  ${GREEN}✓${NC} Pip: $PIP_VERSION"
echo -e "  ${GREEN}✓${NC} Virtual Environment: $VENV_EXISTS"

# 6. Generate complete configuration
echo -e "${BLUE}[7/8] Generating complete configuration...${NC}"

# Create the final configuration
python3 << 'PYTHON_SCRIPT'
import json
import os
from datetime import datetime

# Load temporary config with extracted data
with open('/tmp/claude-flow-config-temp.json', 'r') as f:
    extracted = json.load(f)

# Build complete configuration
config = {
    "name": "01_AI_Coding_Station - 🐍 Python Development",
    "version": "2.0.0-alpha.86",
    "generated": datetime.now().isoformat(),
    "generated_by": "auto-config-extractor",
    
    "project": {
        "name": "01_AI_Coding_Station - 🐍 Python Development",
        "namespace": "alpha",
        "path": os.getcwd().replace('/mnt/d/', 'D:\\').replace('/', '\\'),
        "working_directory": os.getcwd().replace('/mnt/d/', 'D:\\').replace('/', '\\'),
        "wsl_path": os.getcwd()
    },
    
    "orchestrator": {
        "maxAgents": 10,
        "maxConcurrentAgents": 8,
        "defaultTopology": "hierarchical",
        "strategy": "development",
        "memoryEnabled": True,
        "faultTolerance": {
            "strategy": "retry-with-learning",
            "maxRetries": 3,
            "byzantineFaultTolerance": True,
            "healthCheckInterval": 30000
        }
    }
}

# Add model configuration
if 'claude_settings' in extracted['extracted_from']:
    model = extracted['extracted_from']['claude_settings'].get('model', 'sonnet')
    config['agents'] = {
        "models": {
            "queen": f"claude-3-opus-20240229",
            "workers": f"claude-3-{model}-20240229" if model in ['sonnet', 'haiku'] else "claude-3-sonnet-20240229",
            "fallback": "claude-3-haiku-20240307"
        }
    }

# Add permissions
if 'claude_settings' in extracted['extracted_from']:
    permissions = extracted['extracted_from']['claude_settings'].get('permissions', {})
    config['permissions'] = permissions

# Add hooks
if 'claude_settings' in extracted['extracted_from']:
    hooks = extracted['extracted_from']['claude_settings'].get('hooks', {})
    config['hooks'] = hooks

# Add MCP configuration
if 'mcp' in extracted['extracted_from']:
    mcp_servers = extracted['extracted_from']['mcp'].get('servers', {})
    config['mcp'] = {
        "enabled": True,
        "servers": mcp_servers
    }
else:
    # Default MCP configuration
    config['mcp'] = {
        "enabled": True,
        "servers": {
            "claude-flow": {
                "command": "npx",
                "args": ["-y", "claude-flow@alpha", "mcp", "start"]
            }
        }
    }

# Add complete agent list
config['agents']['selected'] = [
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
]

# Add memory configuration
config['memory'] = {
    "backend": "sqlite",
    "persistentSessions": True,
    "database": ".swarm/memory.db",
    "cacheSizeMB": 1024,
    "compression": True,
    "namespaces": ["default", "sparc", "neural", "coordination", "python-dev"]
}

# Add Python-specific configuration
config['python'] = {
    "version": os.popen('python3 --version 2>/dev/null').read().strip().split()[1] if os.system('python3 --version >/dev/null 2>&1') == 0 else "3.11",
    "virtualEnv": ".venv" if os.path.exists('.venv') else "venv" if os.path.exists('venv') else None,
    "packageManager": "pip",
    "linter": "ruff",
    "formatter": "black",
    "typeChecker": "mypy",
    "testRunner": "pytest"
}

# Add environment variables
config['environment'] = {
    "variables": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
        "ANTHROPIC_MODEL": "claude-3-sonnet-20240229",
        "CLAUDE_FLOW_MAX_AGENTS": "10",
        "CLAUDE_FLOW_MEMORY_PATH": ".swarm/memory.db",
        "CLAUDE_FLOW_DEBUG": os.environ.get('CLAUDE_FLOW_DEBUG', 'verbose'),
        "CLAUDE_FLOW_HOOKS_ENABLED": "true",
        "BASH_DEFAULT_TIMEOUT_MS": "300000",
        "BASH_MAX_TIMEOUT_MS": "600000"
    }
}

# Add other necessary configurations
config['swarm'] = {
    "topology": "hierarchical",
    "queen_type": "strategic"
}

config['settings'] = {
    "memorySize": "1GB",
    "parallelExecution": True,
    "verboseLogging": True
}

config['preset'] = "🐍 Python Development"
config['codex_mode'] = False

# Save the configuration
output_path = ".claude-flow/saved-configs/20250819_Python-Development-Complete.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"Configuration saved to: {output_path}")

# Print summary
print("\nConfiguration Summary:")
print(f"  • Models: {config['agents']['models']['queen']} (Queen), {config['agents']['models']['workers']} (Workers)")
print(f"  • MCP Servers: {len(config['mcp']['servers'])} configured")
print(f"  • Agents: {len(config['agents']['selected'])} selected")
print(f"  • Memory: SQLite with {config['memory']['cacheSizeMB']}MB cache")
print(f"  • Python: Version {config['python']['version']}")
PYTHON_SCRIPT

echo
echo -e "${BLUE}[8/8] Validating configuration...${NC}"

# Check for critical missing items
CRITICAL_MISSING=""
[ -z "$ANTHROPIC_API_KEY" ] && CRITICAL_MISSING="$CRITICAL_MISSING\n  ${RED}✗${NC} ANTHROPIC_API_KEY not set"
[ ! -f ".mcp.json" ] && CRITICAL_MISSING="$CRITICAL_MISSING\n  ${YELLOW}⚠${NC} .mcp.json missing (MCP features limited)"

if [ -n "$CRITICAL_MISSING" ]; then
    echo -e "${YELLOW}⚠ Configuration Warnings:${NC}"
    echo -e "$CRITICAL_MISSING"
    echo
fi

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Configuration extraction complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo
echo -e "Next steps:"
echo -e "1. ${CYAN}Set missing environment variables:${NC}"
echo -e "   export ANTHROPIC_API_KEY='your-key-here'"
echo
echo -e "2. ${CYAN}Initialize MCP servers (if needed):${NC}"
echo -e "   npx claude-flow@alpha mcp init"
echo
echo -e "3. ${CYAN}Launch Claude-Flow:${NC}"
echo -e "   npx claude-flow@alpha hive-mind spawn 'Your task' \\"
echo -e "     --config '$OUTPUT_CONFIG' \\"
echo -e "     --claude --verbose"
echo
echo -e "${CYAN}Config file: $OUTPUT_CONFIG${NC}"

# Clean up
rm -f "$TEMP_CONFIG"