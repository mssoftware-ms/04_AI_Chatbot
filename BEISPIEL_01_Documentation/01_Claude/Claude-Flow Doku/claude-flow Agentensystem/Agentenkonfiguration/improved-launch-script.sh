#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# Claude-Flow Hive Mind Launch Script v2.0
# Enhanced with proper configuration and error handling

set -e
set -o pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Environment setup
export PATH="$PATH:/usr/local/bin:/usr/bin"
export npm_config_yes=true
export FORCE_COLOR=1
export CI=false

# Claude-Flow specific environment variables
export ANTHROPIC_MODEL="claude-3-sonnet-20240229"
export CLAUDE_FLOW_MAX_AGENTS="10"
export CLAUDE_FLOW_MEMORY_PATH=".swarm/memory.db"
export CLAUDE_FLOW_DEBUG="verbose"
export CLAUDE_FLOW_HOOKS_ENABLED="true"
export CLAUDE_FLOW_PARALLEL_EXECUTION="true"
export CLAUDE_FLOW_TOKEN_OPTIMIZATION="true"
export BASH_DEFAULT_TIMEOUT_MS="300000"
export BASH_MAX_TIMEOUT_MS="600000"

# Project configuration
PROJECT_NAME="01_AI_Coding_Station - 🐍 Python Development"
PROJECT_PATH="/mnt/d/03_Git/02_Python/01_AI_Coding_Station"
CONFIG_FILE=".claude-flow/saved-configs/20250819_Python-Development-Complete.json"
LOG_DIR=".claude-flow/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/hive-mind_${TIMESTAMP}.log"

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$*${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_color $BLUE "🔍 Checking prerequisites..."
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        print_color $RED "❌ Node.js is not installed. Please install Node.js first."
        exit 1
    fi
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        print_color $RED "❌ npm is not installed. Please install npm first."
        exit 1
    fi
    
    # Check Node.js version (minimum 18.0.0)
    NODE_VERSION=$(node -v | cut -d'v' -f2)
    MIN_VERSION="18.0.0"
    if [ "$(printf '%s\n' "$MIN_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]; then
        print_color $YELLOW "⚠️  Node.js version $NODE_VERSION is below recommended version $MIN_VERSION"
    fi
    
    print_color $GREEN "✅ Prerequisites check passed"
}

# Function to setup directories
setup_directories() {
    print_color $BLUE "📁 Setting up directories..."
    
    # Create necessary directories if they don't exist
    mkdir -p "${PROJECT_PATH}/.claude-flow/saved-configs"
    mkdir -p "${PROJECT_PATH}/.claude-flow/logs"
    mkdir -p "${PROJECT_PATH}/.swarm"
    mkdir -p "${PROJECT_PATH}/.claude/agents"
    mkdir -p "${PROJECT_PATH}/.hive-mind/sessions"
    
    print_color $GREEN "✅ Directories created/verified"
}

# Function to initialize memory database
init_memory() {
    print_color $BLUE "💾 Initializing memory system..."
    
    if [ ! -f "${PROJECT_PATH}/.swarm/memory.db" ]; then
        print_color $YELLOW "Creating new memory database..."
        # Initialize empty SQLite database structure
        touch "${PROJECT_PATH}/.swarm/memory.db"
    else
        print_color $GREEN "Memory database exists"
    fi
}

# Main execution
main() {
    clear
    
    # Print header
    echo '╔══════════════════════════════════════════════════════════════════╗'
    echo '║         🐝 CLAUDE FLOW HIVE MIND - ENHANCED LAUNCHER 🐝          ║'
    echo '╚══════════════════════════════════════════════════════════════════╝'
    echo
    print_color $CYAN "📋 Project: ${PROJECT_NAME}"
    print_color $CYAN "📁 Path: ${PROJECT_PATH}"
    print_color $CYAN "⚙️  Config: ${CONFIG_FILE}"
    print_color $CYAN "📝 Log: ${LOG_FILE}"
    echo '════════════════════════════════════════════════════════════════════'
    echo
    
    # Run prerequisite checks
    check_prerequisites
    
    # Change to project directory
    print_color $BLUE "📍 Changing to project directory..."
    cd "${PROJECT_PATH}" || {
        print_color $RED "❌ ERROR: Failed to change to project directory"
        exit 1
    }
    
    # Verify we're in the right place
    if [ "$(pwd)" != "${PROJECT_PATH}" ]; then
        print_color $RED "❌ ERROR: Not in correct directory"
        print_color $RED "Expected: ${PROJECT_PATH}"
        print_color $RED "Current: $(pwd)"
        exit 1
    fi
    
    print_color $GREEN "✅ Directory confirmed: $(pwd)"
    
    # Setup environment
    setup_directories
    init_memory
    
    # Check if configuration file exists
    if [ ! -f "${CONFIG_FILE}" ]; then
        print_color $YELLOW "⚠️  Configuration file not found: ${CONFIG_FILE}"
        print_color $YELLOW "Creating default configuration..."
        # Here you would copy the complete JSON configuration
        # For now, we'll use the existing one
        CONFIG_FILE=".claude-flow/saved-configs/20250819_-Python-Development.json"
    fi
    
    # Prepare the task
    TASK='Im fenster Launch hive, steht hinter Console output, immer noch external terminal, allerdings soll bis zum starten von claude-flow, der interne output erfolgen! Also bis dahin Console output verwenden. unabhängig davon welchen status die checkbox external terminal hat, damit ist einfach nur gemeint, in wechen wsl fenster claude startet.'
    
    # Build the command
    print_color $BLUE "🛠️  Building command..."
    CMD="npx claude-flow@alpha hive-mind spawn"
    CMD="${CMD} '${TASK}'"
    CMD="${CMD} --config '${CONFIG_FILE}'"
    CMD="${CMD} --claude"
    CMD="${CMD} --verbose"
    CMD="${CMD} --memory-enabled"
    CMD="${CMD} --parallel-execution"
    CMD="${CMD} --hooks-enabled"
    CMD="${CMD} --telemetry"
    CMD="${CMD} --topology hierarchical"
    CMD="${CMD} --queen-model claude-3-opus-20240229"
    CMD="${CMD} --worker-model claude-3-sonnet-20240229"
    CMD="${CMD} --max-agents 10"
    
    echo '════════════════════════════════════════════════════════════════════'
    print_color $MAGENTA "🚀 Launching Hive Mind with enhanced configuration..."
    echo
    print_color $CYAN "Command:"
    echo "${CMD}" | fold -w 70 -s | sed 's/^/  /'
    echo '════════════════════════════════════════════════════════════════════'
    echo
    
    # Create log file
    {
        echo "═══════════════════════════════════════════════════════════════"
        echo "Hive Mind Launch Log - ${TIMESTAMP}"
        echo "Project: ${PROJECT_NAME}"
        echo "Path: ${PROJECT_PATH}"
        echo "═══════════════════════════════════════════════════════════════"
        echo
    } >> "${LOG_FILE}"
    
    # Execute the command with logging
    print_color $YELLOW "⏳ Spawning Hive Mind swarm..."
    echo
    
    # Execute with error handling and logging
    if eval "${CMD}" 2>&1 | tee -a "${LOG_FILE}"; then
        EXIT_CODE=0
        print_color $GREEN "✅ Task completed successfully"
    else
        EXIT_CODE=$?
        print_color $RED "❌ Task failed with exit code: ${EXIT_CODE}"
        
        # Show last error lines from log
        print_color $YELLOW "📋 Last error lines:"
        tail -n 10 "${LOG_FILE}" | grep -E "(ERROR|Error|error|FAIL|Fail|fail)" || true
    fi
    
    echo '════════════════════════════════════════════════════════════════════'
    
    # Post-execution summary
    print_color $BLUE "📊 Execution Summary:"
    print_color $CYAN "  • Exit Code: ${EXIT_CODE}"
    print_color $CYAN "  • Log File: ${LOG_FILE}"
    print_color $CYAN "  • Memory DB: .swarm/memory.db"
    
    # Check agent status
    if [ ${EXIT_CODE} -eq 0 ]; then
        print_color $BLUE "🐝 Checking active agents..."
        npx claude-flow@alpha agent list 2>/dev/null || true
    fi
    
    echo '════════════════════════════════════════════════════════════════════'
    
    # Keep terminal open
    print_color $YELLOW "Press any key to close..."
    read -n 1 -s -r || true
    echo
    
    # Optional: Keep bash session open for debugging
    if [ "${DEBUG_MODE:-false}" = "true" ]; then
        print_color $MAGENTA "Debug mode: Keeping shell session open..."
        exec bash -i
    fi
}

# Error handler
trap 'print_color $RED "❌ Script interrupted or failed at line $LINENO"' ERR

# Run main function
main "$@"