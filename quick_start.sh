#!/bin/bash

# Quick Start Script for Orchestrator Platform
# This script sets up and runs the complete mock system

set -e  # Exit on any error

echo "🚀 Orchestrator Platform Quick Start"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "demos/run_complete_system.py" ]; then
    print_error "Please run this script from the Orchestrator project root directory"
    exit 1
fi

print_status "Checking system dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi
print_success "Python 3 found: $(python3 --version)"

# Check if we can install Python packages
print_status "Installing Python dependencies..."
if ! pip3 install paho-mqtt flask flask-socketio &> /dev/null; then
    print_warning "Could not install Python packages globally, trying with --user"
    pip3 install --user paho-mqtt flask flask-socketio
fi
print_success "Python dependencies installed"

# Check for MQTT broker
print_status "Checking for MQTT broker..."
if command -v mosquitto &> /dev/null; then
    print_success "Mosquitto MQTT broker found"
    MQTT_AVAILABLE=true
else
    print_warning "Mosquitto MQTT broker not found"
    print_status "Attempting to install mosquitto..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y mosquitto mosquitto-clients
        MQTT_AVAILABLE=true
    elif command -v brew &> /dev/null; then
        brew install mosquitto
        MQTT_AVAILABLE=true
    else
        print_warning "Could not install mosquitto automatically"
        print_status "Please install mosquitto manually:"
        print_status "  Ubuntu/Debian: sudo apt-get install mosquitto mosquitto-clients"
        print_status "  macOS: brew install mosquitto"
        MQTT_AVAILABLE=false
    fi
fi

# Check for Node.js and Node-RED
print_status "Checking for Node.js and Node-RED..."
NODE_RED_AVAILABLE=false

if command -v node &> /dev/null && command -v npm &> /dev/null; then
    print_success "Node.js found: $(node --version)"
    
    if command -v node-red &> /dev/null; then
        print_success "Node-RED found: $(node-red --version)"
        NODE_RED_AVAILABLE=true
    else
        print_warning "Node-RED not found, attempting to install..."
        if npm install -g node-red &> /dev/null; then
            print_success "Node-RED installed successfully"
            NODE_RED_AVAILABLE=true
        else
            print_warning "Could not install Node-RED globally"
            print_status "You can install it manually with: npm install -g node-red"
        fi
    fi
else
    print_warning "Node.js not found"
    print_status "Install from: https://nodejs.org/"
fi

echo ""
print_status "System Status Summary:"
echo "  Python 3: ✅ Available"
echo "  MQTT Broker: $([ "$MQTT_AVAILABLE" = true ] && echo "✅ Available" || echo "❌ Not Available")"
echo "  Node-RED: $([ "$NODE_RED_AVAILABLE" = true ] && echo "✅ Available" || echo "❌ Not Available")"

echo ""
print_status "Choose how to run the system:"
echo "1. Complete System (Mock HAL + MQTT + Node-RED) - Recommended"
echo "2. Mock HAL + Simple Web Dashboard (if Node-RED not available)"
echo "3. Mock HAL only (for testing)"
echo "4. Just test the mock components"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        if [ "$MQTT_AVAILABLE" = true ] && [ "$NODE_RED_AVAILABLE" = true ]; then
            print_status "Starting complete system..."
            python3 demos/run_complete_system.py
        else
            print_error "Complete system requires both MQTT broker and Node-RED"
            print_status "Missing components - falling back to simple dashboard"
            python3 demos/simple_web_dashboard.py
        fi
        ;;
    2)
        print_status "Starting Mock HAL with Simple Web Dashboard..."
        
        # Start MQTT broker in background if available
        if [ "$MQTT_AVAILABLE" = true ]; then
            print_status "Starting MQTT broker..."
            mosquitto -d
            sleep 2
        fi
        
        # Start Mock HAL in background
        print_status "Starting Mock HAL..."
        python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.') / 'hal_service'))
from hal_service.mock.mock_orchestrator import MockHALOrchestrator
import threading
import time

def run_mock_hal():
    orchestrator = MockHALOrchestrator()
    if orchestrator.initialize():
        print('Mock HAL started')
        orchestrator.run()

# Start Mock HAL in background thread
hal_thread = threading.Thread(target=run_mock_hal, daemon=True)
hal_thread.start()
time.sleep(3)

# Start web dashboard
import sys
sys.path.insert(0, 'demos')
from simple_web_dashboard import SimpleDashboard
dashboard = SimpleDashboard()
dashboard.run()
" &
        
        # Wait a moment then start dashboard
        sleep 3
        python3 demos/simple_web_dashboard.py
        ;;
    3)
        print_status "Starting Mock HAL only..."
        python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.') / 'hal_service'))
from hal_service.mock.mock_orchestrator import MockHALOrchestrator

orchestrator = MockHALOrchestrator()
if orchestrator.initialize():
    print('Mock HAL started - use MQTT clients to interact')
    orchestrator.run()
"
        ;;
    4)
        print_status "Running mock component tests..."
        python3 tests/test_mock_standalone.py
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

print_success "Done!"