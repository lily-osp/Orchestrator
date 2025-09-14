#!/bin/bash

# Orchestrator Platform - Quick Development Setup
# This script sets up a minimal development environment for testing

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    command -v python3 >/dev/null 2>&1 || error "Python 3 is required but not installed"
    command -v node >/dev/null 2>&1 || error "Node.js is required but not installed"
    command -v npm >/dev/null 2>&1 || error "npm is required but not installed"
    
    log "Prerequisites check passed"
}

# Setup Python environment
setup_python() {
    log "Setting up Python environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log "Python environment ready"
}

# Install Node-RED locally
setup_node_red() {
    log "Setting up Node-RED..."
    
    cd "$PROJECT_ROOT"
    
    # Install Node-RED locally if not already installed
    if [ ! -d "node_modules/node-red" ]; then
        npm install node-red@3.1.0 node-red-dashboard
    fi
    
    # Create Node-RED directory
    mkdir -p .node-red
    
    # Copy configuration if it exists
    if [ -d "configs/node_red_config" ]; then
        cp -r configs/node_red_config/* .node-red/ 2>/dev/null || true
    fi
    
    log "Node-RED setup complete"
}

# Install and start Mosquitto (if available)
setup_mosquitto() {
    log "Setting up MQTT broker..."
    
    if command -v mosquitto >/dev/null 2>&1; then
        log "Mosquitto already installed"
        
        # Start mosquitto in background if not running
        if ! pgrep mosquitto > /dev/null; then
            mosquitto -d -p 1883
            log "Started Mosquitto broker on port 1883"
        else
            log "Mosquitto already running"
        fi
    else
        warn "Mosquitto not installed. Please install it manually:"
        warn "  Ubuntu/Debian: sudo apt install mosquitto mosquitto-clients"
        warn "  macOS: brew install mosquitto"
        warn "  Or use Docker: docker run -it -p 1883:1883 eclipse-mosquitto:2.0"
    fi
}

# Create development configuration
create_dev_config() {
    log "Creating development configuration..."
    
    cd "$PROJECT_ROOT"
    
    # Create a development config if it doesn't exist
    if [ ! -f "config.dev.yaml" ]; then
        cat > config.dev.yaml << 'EOF'
# Development Configuration for Orchestrator Platform

mqtt:
  broker_host: localhost
  broker_port: 1883
  keepalive: 60
  qos_commands: 1
  qos_telemetry: 0

system:
  heartbeat_interval: 30.0
  logging:
    level: DEBUG
    console_output: true
    file_output: true
    format: json
    log_dir: logs
    max_log_size: 10485760
    backup_count: 3

# Mock hardware configuration for development
motors:
  - name: left_motor
    type: dc
    gpio_pins:
      enable: 18
      direction: 19
    encoder_pins:
      a: 20
      b: 21
    max_speed: 1.0
    acceleration: 0.5

  - name: right_motor
    type: dc
    gpio_pins:
      enable: 22
      direction: 23
    encoder_pins:
      a: 24
      b: 25
    max_speed: 1.0
    acceleration: 0.5

sensors:
  - name: lidar_01
    type: lidar
    interface:
      port: /dev/ttyUSB0
      baudrate: 115200
      timeout: 1.0
    publish_rate: 10.0

  - name: left_encoder
    type: encoder
    interface:
      pin: 20
      mode: IN
      pull_up_down: PUD_UP
    publish_rate: 20.0

safety:
  enabled: true
  obstacle_threshold: 0.5
  emergency_stop_timeout: 0.1
EOF
        log "Created development configuration: config.dev.yaml"
    fi
}

# Create startup scripts
create_startup_scripts() {
    log "Creating startup scripts..."
    
    cd "$PROJECT_ROOT"
    
    # Create start script for development
    cat > start_dev.sh << 'EOF'
#!/bin/bash

# Start Orchestrator Platform in development mode

echo "Starting Orchestrator Platform (Development Mode)..."

# Set environment variables
export PYTHONPATH="$(pwd)"
export MQTT_HOST="localhost"
export HAL_MODE="mock"

# Create logs directory
mkdir -p logs

# Start services in background
echo "Starting mock HAL service..."
source venv/bin/activate
python demos/demo_mock_hal.py --config config.dev.yaml &
HAL_PID=$!

echo "Starting Node-RED..."
./node_modules/.bin/node-red --userDir .node-red --port 1880 &
NODERED_PID=$!

echo "Services started!"
echo "  - Mock HAL PID: $HAL_PID"
echo "  - Node-RED PID: $NODERED_PID"
echo "  - Node-RED Dashboard: http://localhost:1880"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "Stopping services..."; kill $HAL_PID $NODERED_PID 2>/dev/null; exit 0' INT
wait
EOF

    chmod +x start_dev.sh
    
    # Create stop script
    cat > stop_dev.sh << 'EOF'
#!/bin/bash

echo "Stopping Orchestrator Platform development services..."

# Kill Node-RED
pkill -f "node-red" || true

# Kill Python services
pkill -f "demo_mock_hal.py" || true
pkill -f "orchestrator_hal.py" || true

# Kill mosquitto if started by this script
pkill -f "mosquitto.*1883" || true

echo "Services stopped"
EOF

    chmod +x stop_dev.sh
    
    log "Created startup scripts: start_dev.sh, stop_dev.sh"
}

# Create test script
create_test_script() {
    log "Creating test script..."
    
    cd "$PROJECT_ROOT"
    
    cat > test_dev.sh << 'EOF'
#!/bin/bash

# Test Orchestrator Platform development setup

echo "Testing Orchestrator Platform..."

# Activate Python environment
source venv/bin/activate

# Run basic tests
echo "Running Python tests..."
python -m pytest tests/ -v --tb=short

# Test MQTT connectivity
echo "Testing MQTT connectivity..."
timeout 5 python -c "
import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc):
    print(f'Connected to MQTT broker with result code {rc}')
    client.publish('test/dev', 'Hello from development setup!')
    client.disconnect()

client = mqtt.Client()
client.on_connect = on_connect
client.connect('localhost', 1883, 60)
client.loop_forever()
" || echo "MQTT test failed (broker might not be running)"

echo "Development setup test complete!"
EOF

    chmod +x test_dev.sh
    
    log "Created test script: test_dev.sh"
}

# Main setup function
main() {
    log "Starting Orchestrator Platform quick development setup..."
    
    check_prerequisites
    setup_python
    setup_node_red
    setup_mosquitto
    create_dev_config
    create_startup_scripts
    create_test_script
    
    log "Development setup complete!"
    echo ""
    echo "Quick start commands:"
    echo "  Start development environment: ./start_dev.sh"
    echo "  Run tests: ./test_dev.sh"
    echo "  Stop services: ./stop_dev.sh"
    echo ""
    echo "Access points:"
    echo "  Node-RED Dashboard: http://localhost:1880"
    echo "  MQTT Broker: localhost:1883"
    echo ""
    echo "Configuration:"
    echo "  Development config: config.dev.yaml"
    echo "  Logs directory: logs/"
}

# Run main function
main "$@"