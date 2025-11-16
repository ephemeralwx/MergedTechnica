#!/bin/bash

# start-all.sh - Run both the Electron app and Python agent server
# This script starts both servers in the background

set -e  # Exit on error

echo "================================"
echo "🚀 Starting MergedCodeTechnica"
echo "================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Define project directories
GUI_ACTOR_DIR="$SCRIPT_DIR/GUI-Actor"
ELECTRON_DIR="$SCRIPT_DIR/manus-x-cluely"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file paths
AGENT_LOG="$SCRIPT_DIR/agent-server.log"
ELECTRON_LOG="$SCRIPT_DIR/electron.log"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down servers...${NC}"
    
    # Kill background processes
    if [ ! -z "$AGENT_PID" ]; then
        kill $AGENT_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Agent server stopped${NC}"
    fi
    
    if [ ! -z "$ELECTRON_PID" ]; then
        kill $ELECTRON_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Electron app stopped${NC}"
    fi
    
    echo -e "${GREEN}👋 Shutdown complete${NC}"
    exit 0
}

# Set up trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Check if directories exist
if [ ! -d "$GUI_ACTOR_DIR" ]; then
    echo -e "${RED}❌ Error: GUI-Actor directory not found at: $GUI_ACTOR_DIR${NC}"
    exit 1
fi

if [ ! -d "$ELECTRON_DIR" ]; then
    echo -e "${RED}❌ Error: manus-x-cluely directory not found at: $ELECTRON_DIR${NC}"
    exit 1
fi

echo -e "${BLUE}📂 GUI-Actor directory: $GUI_ACTOR_DIR${NC}"
echo -e "${BLUE}📂 Electron directory: $ELECTRON_DIR${NC}"
echo ""

# Start Python Agent Server
echo -e "${YELLOW}🐍 Starting Python Agent Server...${NC}"
cd "$GUI_ACTOR_DIR"

# Check Python version compatibility - try to find a compatible Python version
PYTHON_CMD=""
PYTHON_VERSION=""

# Try python3.12 first
if command -v python3.12 &> /dev/null; then
    PYTHON_VERSION=$(python3.12 --version 2>&1 | awk '{print $2}')
    PYTHON_CMD="python3.12"
    echo -e "${GREEN}✓ Found Python 3.12: $PYTHON_VERSION${NC}"
elif command -v python3.11 &> /dev/null; then
    PYTHON_VERSION=$(python3.11 --version 2>&1 | awk '{print $2}')
    PYTHON_CMD="python3.11"
    echo -e "${GREEN}✓ Found Python 3.11: $PYTHON_VERSION${NC}"
elif command -v python3.10 &> /dev/null; then
    PYTHON_VERSION=$(python3.10 --version 2>&1 | awk '{print $2}')
    PYTHON_CMD="python3.10"
    echo -e "${GREEN}✓ Found Python 3.10: $PYTHON_VERSION${NC}"
else
    # Fallback to default python3 and check version
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ] && [ "$PYTHON_MINOR" -le 12 ]; then
        PYTHON_CMD="python3"
        echo -e "${GREEN}✓ Found compatible Python: $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}❌ Error: No compatible Python version found${NC}"
        echo -e "${RED}   Current default Python: $PYTHON_VERSION${NC}"
        echo -e "${YELLOW}GUI-Actor requires Python 3.10, 3.11, or 3.12${NC}"
        echo ""
        echo -e "${YELLOW}Please install Python 3.12:${NC}"
        echo -e "   ${BLUE}brew install python@3.12${NC}"
        echo ""
        echo -e "${YELLOW}Then create a virtual environment:${NC}"
        echo -e "   ${BLUE}cd GUI-Actor${NC}"
        echo -e "   ${BLUE}python3.12 -m venv env${NC}"
        echo -e "   ${BLUE}cd ..${NC}"
        echo -e "   ${BLUE}./start-all.sh${NC}"
        echo ""
        exit 1
    fi
fi

# Check for virtual environments (prefer 'env' over 'venv')
VENV_PATH=""
if [ -d "env" ]; then
    VENV_PATH="env"
elif [ -d "venv" ]; then
    VENV_PATH="venv"
fi

# Create virtual environment if none exists
if [ -z "$VENV_PATH" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    echo -e "${YELLOW}Using $PYTHON_CMD (version $PYTHON_VERSION)...${NC}"
    $PYTHON_CMD -m venv env
    VENV_PATH="env"
fi

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Verify the Python version in the venv
VENV_PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
VENV_PYTHON_MAJOR=$(echo $VENV_PYTHON_VERSION | cut -d. -f1)
VENV_PYTHON_MINOR=$(echo $VENV_PYTHON_VERSION | cut -d. -f2)

echo -e "${BLUE}📍 Virtual environment Python: $VENV_PYTHON_VERSION${NC}"

if [ "$VENV_PYTHON_MAJOR" -eq 3 ] && [ "$VENV_PYTHON_MINOR" -ge 13 ]; then
    echo -e "${RED}❌ Error: Virtual environment has Python 3.13+ ($VENV_PYTHON_VERSION)${NC}"
    echo -e "${YELLOW}The existing virtual environment was created with an incompatible Python version.${NC}"
    echo ""
    echo -e "${YELLOW}Please remove it and create a new one:${NC}"
    echo -e "   ${BLUE}rm -rf env${NC}"
    echo -e "   ${BLUE}python3.12 -m venv env${NC}"
    echo ""
    exit 1
fi

if [ "$VENV_PYTHON_MAJOR" -eq 3 ] && [ "$VENV_PYTHON_MINOR" -lt 10 ]; then
    echo -e "${RED}❌ Error: Virtual environment has Python < 3.10 ($VENV_PYTHON_VERSION)${NC}"
    echo -e "${YELLOW}GUI-Actor requires Python 3.10-3.12${NC}"
    echo ""
    echo -e "${YELLOW}Please remove it and create a new one:${NC}"
    echo -e "   ${BLUE}rm -rf env${NC}"
    echo -e "   ${BLUE}python3.12 -m venv env${NC}"
    echo ""
    exit 1
fi

# Check if dependencies are installed by checking for multiple required packages
DEPS_MISSING=false
echo -e "${YELLOW}🔍 Checking dependencies...${NC}"
for pkg in flask PIL torch pyautogui pynput transformers accelerate; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        DEPS_MISSING=true
        echo -e "${YELLOW}   Missing package: $pkg${NC}"
    fi
done

if [ "$DEPS_MISSING" = true ]; then
    echo -e "${YELLOW}⚠️  Dependencies not installed. Installing now...${NC}"
    echo -e "${YELLOW}   This may take several minutes for large packages like PyTorch...${NC}"
    pip install --upgrade pip 2>&1 | grep -v "Requirement already satisfied" || true
    
    # Install PyObjC first on macOS (needed for pyautogui and pynput)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${YELLOW}📦 Installing macOS-specific dependencies (PyObjC)...${NC}"
        pip install pyobjc-core pyobjc-framework-Quartz || {
            echo -e "${RED}❌ Failed to install PyObjC${NC}"
            exit 1
        }
    fi
    
    # Install requirements.txt (includes PyTorch and all other deps)
    if pip install -r requirements.txt; then
        echo -e "${GREEN}✅ Requirements installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install requirements${NC}"
        echo -e "${YELLOW}Trying to install packages individually...${NC}"
        
        # Try installing problem packages individually
        for pkg in pyautogui pynput; do
            echo -e "${YELLOW}Installing $pkg...${NC}"
            pip install $pkg || echo -e "${YELLOW}⚠️  Warning: $pkg installation had issues${NC}"
        done
    fi
fi

# Always ensure PyTorch is installed before gui_actor (needed for flash-attn)
echo -e "${YELLOW}🔍 Verifying PyTorch installation...${NC}"
if ! python3 -c "import torch" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing PyTorch and torchvision...${NC}"
    if pip install torch torchvision; then
        echo -e "${GREEN}✅ PyTorch and torchvision installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install PyTorch${NC}"
        exit 1
    fi
else
    # Check if torchvision is also installed
    if ! python3 -c "import torchvision" 2>/dev/null; then
        echo -e "${YELLOW}📦 Installing torchvision...${NC}"
        pip install torchvision
    fi
    echo -e "${GREEN}✅ PyTorch and torchvision are already installed${NC}"
fi

# Check if gui_actor module is installed
if ! python3 -c "import gui_actor" 2>/dev/null; then
    # Install gui_actor package in editable mode WITHOUT flash-attn
    echo -e "${YELLOW}📦 Installing GUI-Actor package (skipping flash-attn)...${NC}"
    echo -e "${YELLOW}   Note: flash-attn is not needed for inference${NC}"
    
    # First, install all dependencies with EXACT versions (except flash-attn and macOS-incompatible packages)
    echo -e "${YELLOW}   Installing package dependencies with exact versions...${NC}"
    
    # Base packages for all platforms
    pip install pre-commit>=3.7.1 \
                opencv-python-headless>=4.10.0.84 \
                accelerate==1.1.1 \
                qwen-vl-utils==0.0.8 \
                transformers==4.51.3 \
                datasets>=2.18.0 \
                wandb==0.18.3 2>&1 | tee /tmp/gui-actor-deps.log
    
    # Skip deepspeed and liger-kernel on macOS (require triton which is Linux-only)
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo -e "${YELLOW}   Installing Linux-specific packages (deepspeed, liger-kernel)...${NC}"
        pip install deepspeed==0.16.0 liger-kernel==0.5.2
    else
        echo -e "${YELLOW}   ⚠️  Skipping deepspeed and liger-kernel on macOS (require Linux/triton)${NC}"
    fi
    
    # Now install the package in editable mode, but flash-attn will be skipped
    # because we're using --no-deps to avoid reinstalling dependencies
    echo -e "${YELLOW}   Installing GUI-Actor package in editable mode...${NC}"
    if pip install --no-deps -e . 2>&1 | tee /tmp/gui-actor-install.log; then
        echo -e "${GREEN}✅ GUI-Actor package installed successfully (without flash-attn)${NC}"
    else
        echo -e "${RED}❌ Failed to install GUI-Actor package${NC}"
        echo -e "${YELLOW}Check /tmp/gui-actor-install.log for details${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ GUI-Actor package is already installed${NC}"
    
    # Verify versions even if package is installed
    echo -e "${YELLOW}🔍 Checking package versions...${NC}"
    NEEDS_REINSTALL=false
    
    # Check accelerate version
    ACCELERATE_VERSION=$(python3 -c "import accelerate; print(accelerate.__version__)" 2>/dev/null || echo "none")
    if [ "$ACCELERATE_VERSION" != "1.1.1" ]; then
        echo -e "${YELLOW}   ⚠️  accelerate version mismatch: $ACCELERATE_VERSION (need 1.1.1)${NC}"
        NEEDS_REINSTALL=true
    fi
    
    # Check transformers version
    TRANSFORMERS_VERSION=$(python3 -c "import transformers; print(transformers.__version__)" 2>/dev/null || echo "none")
    if [ "$TRANSFORMERS_VERSION" != "4.51.3" ]; then
        echo -e "${YELLOW}   ⚠️  transformers version mismatch: $TRANSFORMERS_VERSION (need 4.51.3)${NC}"
        NEEDS_REINSTALL=true
    fi
    
    if [ "$NEEDS_REINSTALL" = true ]; then
        echo -e "${YELLOW}📦 Reinstalling dependencies with correct versions...${NC}"
        pip install --force-reinstall \
                    accelerate==1.1.1 \
                    transformers==4.51.3 \
                    qwen-vl-utils==0.0.8 \
                    datasets>=2.18.0 \
                    wandb==0.18.3
        
        # Skip Linux-only packages on macOS
        if [[ "$OSTYPE" != "darwin"* ]]; then
            pip install --force-reinstall deepspeed==0.16.0 liger-kernel==0.5.2
        fi
    else
        echo -e "${GREEN}✅ Package versions are correct${NC}"
    fi
fi

# Verify critical packages are now installed
echo -e "${YELLOW}🔍 Verifying installations...${NC}"
VERIFY_FAILED=false
for pkg in flask PIL torch torchvision pyautogui pynput gui_actor; do
    if python3 -c "import $pkg" 2>/dev/null; then
        echo -e "${GREEN}   ✓ $pkg${NC}"
    else
        echo -e "${RED}   ✗ $pkg (FAILED)${NC}"
        VERIFY_FAILED=true
    fi
done

if [ "$VERIFY_FAILED" = true ]; then
    echo -e "${RED}❌ Some packages failed verification${NC}"
    echo -e "${YELLOW}Attempting manual installation of failed packages...${NC}"
    
    # Try one more time with individual installations
    if ! python3 -c "import pyautogui" 2>/dev/null; then
        pip install --force-reinstall pyautogui
    fi
    if ! python3 -c "import pynput" 2>/dev/null; then
        pip install --force-reinstall pynput
    fi
    
    # Final verification
    echo -e "${YELLOW}Final verification...${NC}"
    FINAL_VERIFY_FAILED=false
    for pkg in pyautogui pynput; do
        if ! python3 -c "import $pkg" 2>/dev/null; then
            echo -e "${RED}   ✗ $pkg still failed${NC}"
            FINAL_VERIFY_FAILED=true
        fi
    done
    
    if [ "$FINAL_VERIFY_FAILED" = true ]; then
        echo -e "${RED}❌ Critical packages failed to install${NC}"
        echo -e "${YELLOW}Installed packages:${NC}"
        pip list
        exit 1
    fi
fi

# Start agent server in background
echo -e "${GREEN}▶️  Agent server starting on http://127.0.0.1:5001${NC}"
python3 agent_server.py > "$AGENT_LOG" 2>&1 &
AGENT_PID=$!
echo -e "${GREEN}✅ Agent server started (PID: $AGENT_PID)${NC}"
echo -e "${BLUE}   Logs: $AGENT_LOG${NC}"

# Wait a moment for agent server to start
echo -e "${YELLOW}⏳ Waiting for agent server to initialize...${NC}"
sleep 5

# Check if agent server is running
if ! kill -0 $AGENT_PID 2>/dev/null; then
    echo -e "${RED}❌ Agent server failed to start. Check logs at: $AGENT_LOG${NC}"
    tail -n 20 "$AGENT_LOG"
    exit 1
fi

# Check if agent server is responding
echo -e "${YELLOW}🔍 Checking agent server health...${NC}"
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://127.0.0.1:5001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Agent server is healthy${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}❌ Agent server health check failed after $MAX_RETRIES attempts${NC}"
        echo -e "${YELLOW}Last 20 lines from agent log:${NC}"
        tail -n 20 "$AGENT_LOG"
        exit 1
    fi
    echo -e "${YELLOW}   Retry $RETRY_COUNT/$MAX_RETRIES...${NC}"
    sleep 2
done

echo ""

# Start Electron App
echo -e "${YELLOW}⚡ Starting Electron App...${NC}"
cd "$ELECTRON_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found. Installing dependencies...${NC}"
    npm install
fi

# Start Electron in development mode
echo -e "${GREEN}▶️  Electron app starting...${NC}"
npm run dev > "$ELECTRON_LOG" 2>&1 &
ELECTRON_PID=$!
echo -e "${GREEN}✅ Electron app started (PID: $ELECTRON_PID)${NC}"
echo -e "${BLUE}   Logs: $ELECTRON_LOG${NC}"

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✨ All servers started successfully!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}📊 Status:${NC}"
echo -e "${GREEN}   🐍 Agent Server: http://127.0.0.1:5001${NC}"
echo -e "${GREEN}   ⚡ Electron App: Running${NC}"
echo ""
echo -e "${YELLOW}💡 Usage:${NC}"
echo -e "   1. Press ${BLUE}Cmd+Space${NC} (or ${BLUE}Ctrl+Space${NC}) to show the app"
echo -e "   2. Toggle the ${GREEN}Agent${NC} button on to enable agent mode"
echo -e "   3. Enter your goal and press Enter"
echo ""
echo -e "${YELLOW}📋 Logs:${NC}"
echo -e "   Agent: ${BLUE}$AGENT_LOG${NC}"
echo -e "   Electron: ${BLUE}$ELECTRON_LOG${NC}"
echo ""
echo -e "${RED}Press Ctrl+C to stop all servers${NC}"
echo ""

# Wait for both processes
wait $AGENT_PID $ELECTRON_PID