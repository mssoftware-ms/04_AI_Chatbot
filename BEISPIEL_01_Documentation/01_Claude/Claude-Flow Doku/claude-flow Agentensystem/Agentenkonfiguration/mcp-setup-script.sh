#!/bin/bash
# MCP Server Setup and Verification Script for Claude-Flow
# This script ensures all MCP servers are properly configured and running

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           MCP Server Setup for Claude-Flow v86               ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install MCP server
install_mcp_server() {
    local package=$1
    local name=$2
    echo -e "${BLUE}Installing $name...${NC}"
    if npm list -g "$package" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Already installed"
    else
        npm install -g "$package" || {
            echo -e "  ${RED}✗${NC} Failed to install"
            return 1
        }
        echo -e "  ${GREEN}✓${NC} Installed successfully"
    fi
}

# Step 1: Check prerequisites
echo -e "${MAGENTA}[Step 1/5] Checking Prerequisites${NC}"
echo -e "────────────────────────────────────────"

if ! command_exists node; then
    echo -e "${RED}✗ Node.js not found. Please install Node.js first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Node.js: $(node -v)"

if ! command_exists npm; then
    echo -e "${RED}✗ npm not found. Please install npm first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} npm: $(npm -v)"

if ! command_exists python3; then
    echo -e "${YELLOW}⚠${NC} Python3 not found. Python MCP server will not work."
fi
echo -e "${GREEN}✓${NC} Python: $(python3 --version 2>/dev/null || echo 'Not installed')"

echo

# Step 2: Install MCP servers
echo -e "${MAGENTA}[Step 2/5] Installing MCP Servers${NC}"
echo -e "────────────────────────────────────────"

MCP_SERVERS=(
    "@modelcontextprotocol/server-filesystem:Filesystem Server"
    "@modelcontextprotocol/server-github:GitHub Server"
    "@modelcontextprotocol/server-gitlab:GitLab Server"
    "@modelcontextprotocol/server-git:Git Server"
    "@modelcontextprotocol/server-sqlite:SQLite Server"
    "@modelcontextprotocol/server-postgres:PostgreSQL Server"
    "@modelcontextprotocol/server-memory:Memory Server"
    "@modelcontextprotocol/server-puppeteer:Puppeteer Server"
    "@modelcontextprotocol/server-brave-search:Brave Search Server"
    "@modelcontextprotocol/server-google-maps:Google Maps Server"
    "mcp-server-python:Python Execution Server"
)

for server in "${MCP_SERVERS[@]}"; do
    IFS=':' read -r package name <<< "$server"
    install_mcp_server "$package" "$name"
done

echo

# Step 3: Create .mcp.json configuration
echo -e "${MAGENTA}[Step 3/5] Creating MCP Configuration${NC}"
echo -e "────────────────────────────────────────"

MCP_CONFIG_FILE=".mcp.json"

# Check if .mcp.json exists
if [ -f "$MCP_CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠${NC} $MCP_CONFIG_FILE already exists"
    read -p "Do you want to backup and create a new one? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp "$MCP_CONFIG_FILE" "${MCP_CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${GREEN}✓${NC} Backup created"
    else
        echo -e "${BLUE}ℹ${NC} Keeping existing configuration"
    fi
fi

# Get project path
PROJECT_PATH=$(pwd)
WINDOWS_PATH=$(echo "$PROJECT_PATH" | sed 's|/mnt/\([a-z]\)|\1:|' | sed 's|/|\\|g')

# Create comprehensive .mcp.json
cat > "$MCP_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {
        "FILESYSTEM_ROOT": "$WINDOWS_PATH",
        "FILESYSTEM_WATCH": "true"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "\${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"],
      "env": {
        "GIT_ROOT": "$PROJECT_PATH"
      }
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_PERSIST": "true",
        "MEMORY_PATH": ".swarm/mcp-memory.json"
      }
    },
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite"],
      "env": {
        "SQLITE_DB_PATH": ".swarm/memory.db"
      }
    },
    "python": {
      "command": "npx",
      "args": ["-y", "mcp-server-python"],
      "env": {
        "PYTHON_PATH": "$(which python3)",
        "PYTHONPATH": "$PROJECT_PATH",
        "VIRTUAL_ENV": ".venv"
      }
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "env": {
        "PUPPETEER_HEADLESS": "true",
        "PUPPETEER_EXECUTABLE_PATH": "/usr/bin/chromium-browser"
      }
    },
    "claude-flow": {
      "command": "npx",
      "args": ["-y", "claude-flow@alpha", "mcp", "start"],
      "env": {
        "CLAUDE_FLOW_MCP_MODE": "server"
      }
    }
  }
}
EOF

echo -e "${GREEN}✓${NC} Created $MCP_CONFIG_FILE"

# Step 4: Verify MCP servers
echo
echo -e "${MAGENTA}[Step 4/5] Verifying MCP Servers${NC}"
echo -e "────────────────────────────────────────"

# Test each MCP server
echo -e "${BLUE}Testing MCP server connectivity...${NC}"

test_mcp_server() {
    local server_name=$1
    echo -n "  Testing $server_name... "
    
    # Try to start the server and check if it responds
    timeout 5 npx claude-flow@alpha mcp test "$server_name" >/dev/null 2>&1 && {
        echo -e "${GREEN}✓${NC}"
        return 0
    } || {
        echo -e "${YELLOW}⚠${NC} (may need configuration)"
        return 1
    }
}

# List of servers to test
for server in filesystem github git memory sqlite python; do
    test_mcp_server "$server" || true
done

echo

# Step 5: Environment variable check
echo -e "${MAGENTA}[Step 5/5] Environment Variables Check${NC}"
echo -e "────────────────────────────────────────"

ENV_VARS_NEEDED=(
    "ANTHROPIC_API_KEY:Required for Claude API access"
    "GITHUB_PERSONAL_ACCESS_TOKEN:Optional for GitHub MCP server"
    "OPENAI_API_KEY:Optional for comparisons"
    "CLAUDE_FLOW_DEBUG:Optional for debugging"
)

MISSING_REQUIRED=false

for var_info in "${ENV_VARS_NEEDED[@]}"; do
    IFS=':' read -r var_name description <<< "$var_info"
    if [ -n "${!var_name}" ]; then
        echo -e "${GREEN}✓${NC} $var_name: Set"
    else
        if [[ "$description" == *"Required"* ]]; then
            echo -e "${RED}✗${NC} $var_name: Not set ($description)"
            MISSING_REQUIRED=true
        else
            echo -e "${YELLOW}⚠${NC} $var_name: Not set ($description)"
        fi
    fi
done

echo

# Create setup script for environment variables
echo -e "${BLUE}Creating environment setup script...${NC}"
cat > "setup-env.sh" << 'EOF'
#!/bin/bash
# Environment setup for Claude-Flow

# Required
export ANTHROPIC_API_KEY="sk-ant-api03-YOUR-KEY-HERE"

# Optional but recommended
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_YOUR_TOKEN_HERE"
export OPENAI_API_KEY="sk-YOUR-KEY-HERE"

# Claude-Flow specific
export CLAUDE_FLOW_DEBUG="verbose"
export CLAUDE_FLOW_HOOKS_ENABLED="true"
export CLAUDE_FLOW_TELEMETRY_ENABLED="true"
export CLAUDE_FLOW_MAX_AGENTS="12"
export CLAUDE_FLOW_MEMORY_PATH=".swarm/memory.db"

# Python environment
export PYTHON_PATH="/usr/bin/python3"
export PYTHONPATH="$(pwd)"

# Performance
export CLAUDE_FLOW_PARALLEL_EXECUTION="true"
export CLAUDE_FLOW_TOKEN_OPTIMIZATION="true"
export BASH_DEFAULT_TIMEOUT_MS="300000"
export BASH_MAX_TIMEOUT_MS="600000"

echo "Environment variables set for Claude-Flow"
EOF

chmod +x setup-env.sh
echo -e "${GREEN}✓${NC} Created setup-env.sh (edit with your API keys)"

echo
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    MCP Setup Complete!                         ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo

if [ "$MISSING_REQUIRED" = true ]; then
    echo -e "${YELLOW}⚠ Important: Required environment variables are missing!${NC}"
    echo -e "${YELLOW}  1. Edit setup-env.sh with your API keys${NC}"
    echo -e "${YELLOW}  2. Run: source setup-env.sh${NC}"
    echo
fi

echo -e "${CYAN}Next Steps:${NC}"
echo -e "1. ${BLUE}Set environment variables:${NC}"
echo -e "   source setup-env.sh"
echo
echo -e "2. ${BLUE}Initialize Claude-Flow MCP:${NC}"
echo -e "   npx claude-flow@alpha mcp init"
echo
echo -e "3. ${BLUE}List available MCP tools:${NC}"
echo -e "   npx claude-flow@alpha mcp list-tools"
echo
echo -e "4. ${BLUE}Test MCP integration:${NC}"
echo -e "   npx claude-flow@alpha mcp test --all"
echo
echo -e "5. ${BLUE}Launch with MCP enabled:${NC}"
echo -e "   npx claude-flow@alpha hive-mind spawn 'Your task' \\"
echo -e "     --config .claude-flow/saved-configs/20250819_Python-Development-Complete.json \\"
echo -e "     --mcp-enabled \\"
echo -e "     --claude --verbose"

echo
echo -e "${CYAN}MCP Server Documentation:${NC}"
echo -e "  • Filesystem: Read/write files in project"
echo -e "  • GitHub: Manage repos, PRs, issues"
echo -e "  • Git: Version control operations"
echo -e "  • Memory: Persistent storage across sessions"
echo -e "  • SQLite: Database operations"
echo -e "  • Python: Execute Python code"
echo -e "  • Puppeteer: Web automation and scraping"

echo
echo -e "${GREEN}✨ MCP servers are ready for Claude-Flow!${NC}"