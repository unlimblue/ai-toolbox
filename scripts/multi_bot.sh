#!/bin/bash
# Cyber Dynasty Multi-Bot System Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="${SCRIPT_DIR}/.."
VENV_DIR="${PROJECT_DIR}/.venv"

# Configuration
TOKEN_FILE="${HOME}/.openclaw/secrets/cyber_dynasty_tokens.env"
LOG_DIR="${PROJECT_DIR}/logs"
PID_FILE="/tmp/cyber_dynasty.pid"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        error "Do not run as root"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 not found"
        exit 1
    fi
    
    # Check virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        error "Virtual environment not found at $VENV_DIR"
        error "Please run: pip install -e ."
        exit 1
    fi
    
    # Check token file
    if [ ! -f "$TOKEN_FILE" ]; then
        error "Token file not found: $TOKEN_FILE"
        error "Please create it with required environment variables"
        exit 1
    fi
    
    # Check token file permissions
    PERMS=$(stat -c %a "$TOKEN_FILE")
    if [ "$PERMS" != "600" ]; then
        warn "Token file permissions are $PERMS, should be 600"
        warn "Fixing permissions..."
        chmod 600 "$TOKEN_FILE"
    fi
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    
    log "Prerequisites check passed"
}

# Load environment variables
load_env() {
    log "Loading environment variables..."
    
    if [ -f "$TOKEN_FILE" ]; then
        export $(grep -v '^#' "$TOKEN_FILE" | xargs)
        log "Environment loaded from $TOKEN_FILE"
    else
        error "Token file not found: $TOKEN_FILE"
        exit 1
    fi
    
    # Verify required variables
    REQUIRED_VARS=("HUB_BOT_TOKEN" "CHENGXIANG_BOT_TOKEN" "TAIWEI_BOT_TOKEN" "KIMI_API_KEY")
    MISSING=()
    
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            MISSING+=("$var")
        fi
    done
    
    if [ ${#MISSING[@]} -ne 0 ]; then
        error "Missing required environment variables: ${MISSING[*]}"
        exit 1
    fi
    
    log "All required environment variables found"
}

# Start the service
start() {
    log "Starting Cyber Dynasty Multi-Bot System..."
    
    check_prerequisites
    load_env
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            warn "Service is already running (PID: $PID)"
            return 1
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    # Activate virtual environment and start
    source "$VENV_DIR/bin/activate"
    
    LOG_FILE="${LOG_DIR}/multi_bot_$(date +%Y%m%d_%H%M%S).log"
    
    log "Starting multi-bot service..."
    log "Log file: $LOG_FILE"
    
    nohup python -m ai_toolbox.multi_bot.main > "$LOG_FILE" 2>&1 &
    PID=$!
    
    # Save PID
    echo $PID > "$PID_FILE"
    
    # Wait a moment to check if process started successfully
    sleep 2
    
    if ps -p "$PID" > /dev/null 2>&1; then
        log "Service started successfully (PID: $PID)"
        log "View logs with: tail -f $LOG_FILE"
        return 0
    else
        error "Failed to start service"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Stop the service
stop() {
    log "Stopping Cyber Dynasty Multi-Bot System..."
    
    if [ ! -f "$PID_FILE" ]; then
        warn "PID file not found, service may not be running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        kill "$PID"
        
        # Wait for process to terminate
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        
        if ps -p "$PID" > /dev/null 2>&1; then
            warn "Process didn't terminate, forcing..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        log "Service stopped"
    else
        warn "Process not found (PID: $PID)"
        rm -f "$PID_FILE"
    fi
}

# Check service status
status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log "Service is running (PID: $PID)"
            
            # Show recent logs
            LATEST_LOG=$(ls -t ${LOG_DIR}/multi_bot_*.log 2>/dev/null | head -1)
            if [ -n "$LATEST_LOG" ]; then
                echo ""
                log "Recent logs:"
                tail -n 5 "$LATEST_LOG"
            fi
            
            return 0
        else
            warn "PID file exists but process not running"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        log "Service is not running"
        return 1
    fi
}

# View logs
logs() {
    LATEST_LOG=$(ls -t ${LOG_DIR}/multi_bot_*.log 2>/dev/null | head -1)
    
    if [ -n "$LATEST_LOG" ]; then
        log "Viewing logs: $LATEST_LOG"
        tail -f "$LATEST_LOG"
    else
        error "No log files found in $LOG_DIR"
        exit 1
    fi
}

# Run tests
test() {
    log "Running tests..."
    
    source "$VENV_DIR/bin/activate"
    
    # Run multi-bot tests
    log "Running multi-bot tests..."
    python -m pytest tests/unit/multi_bot/ tests/integration/ -v --tb=short
    
    if [ $? -eq 0 ]; then
        log "All tests passed!"
    else
        error "Some tests failed"
        exit 1
    fi
}

# Main command handler
case "${1:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 2
        start
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    test)
        test
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|test}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the multi-bot service"
        echo "  stop     - Stop the multi-bot service"
        echo "  restart  - Restart the multi-bot service"
        echo "  status   - Check service status"
        echo "  logs     - View service logs"
        echo "  test     - Run tests"
        exit 1
        ;;
esac