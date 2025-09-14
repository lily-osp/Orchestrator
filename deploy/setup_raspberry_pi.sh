#!/bin/bash

# Orchestrator Platform - Raspberry Pi Setup Script
# This script automates the complete setup of the Orchestrator platform on a fresh Raspberry Pi

set -e  # Exit on any error

# Configuration
ORCHESTRATOR_USER="orchestrator"
ORCHESTRATOR_HOME="/opt/orchestrator"
PROJECT_REPO="https://github.com/your-org/orchestrator-platform.git"
NODE_RED_VERSION="3.1.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Please run as pi user."
    fi
}

# Update system packages
update_system() {
    log "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y git curl wget vim htop tree
}

# Install Python dependencies
install_python() {
    log "Installing Python and pip..."
    sudo apt install -y python3 python3-pip python3-venv python3-dev
    
    # Install system-level Python packages needed for GPIO
    sudo apt install -y python3-rpi.gpio python3-smbus python3-serial
}

# Install Node.js and npm
install_nodejs() {
    log "Installing Node.js and npm..."
    
    # Install Node.js 18.x LTS
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
    
    # Verify installation
    node_version=$(node --version)
    npm_version=$(npm --version)
    log "Node.js version: $node_version"
    log "npm version: $npm_version"
}

# Install and configure Mosquitto MQTT broker
install_mosquitto() {
    log "Installing Mosquitto MQTT broker..."
    sudo apt install -y mosquitto mosquitto-clients
    
    # Create mosquitto configuration
    sudo tee /etc/mosquitto/conf.d/orchestrator.conf > /dev/null <<EOF
# Orchestrator Platform MQTT Configuration
listener 1883 localhost
allow_anonymous true
max_keepalive 300
max_connections 100

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information
log_timestamp true
EOF

    # Enable and start mosquitto
    sudo systemctl enable mosquitto
    sudo systemctl start mosquitto
    
    log "Testing MQTT broker..."
    timeout 5 mosquitto_pub -h localhost -t test/connection -m "setup_test" || warn "MQTT test failed"
}

# Create orchestrator user and directories
setup_orchestrator_user() {
    log "Setting up orchestrator user and directories..."
    
    # Create orchestrator user if it doesn't exist
    if ! id "$ORCHESTRATOR_USER" &>/dev/null; then
        sudo useradd -r -m -d "$ORCHESTRATOR_HOME" -s /bin/bash "$ORCHESTRATOR_USER"
        sudo usermod -a -G gpio,i2c,spi,dialout "$ORCHESTRATOR_USER"
    fi
    
    # Create necessary directories
    sudo mkdir -p "$ORCHESTRATOR_HOME"/{logs,configs,data}
    sudo chown -R "$ORCHESTRATOR_USER:$ORCHESTRATOR_USER" "$ORCHESTRATOR_HOME"
}

# Clone and setup the orchestrator project
setup_project() {
    log "Setting up Orchestrator project..."
    
    # Clone the project (or copy from current directory if running locally)
    if [[ -d "/home/pi/orchestrator-platform" ]]; then
        log "Copying project from local directory..."
        sudo cp -r /home/pi/orchestrator-platform/* "$ORCHESTRATOR_HOME/"
    else
        log "Cloning project from repository..."
        sudo -u "$ORCHESTRATOR_USER" git clone "$PROJECT_REPO" "$ORCHESTRATOR_HOME"
    fi
    
    # Set proper ownership
    sudo chown -R "$ORCHESTRATOR_USER:$ORCHESTRATOR_USER" "$ORCHESTRATOR_HOME"
    
    # Create Python virtual environment
    log "Creating Python virtual environment..."
    sudo -u "$ORCHESTRATOR_USER" python3 -m venv "$ORCHESTRATOR_HOME/venv"
    
    # Install Python dependencies
    log "Installing Python dependencies..."
    sudo -u "$ORCHESTRATOR_USER" "$ORCHESTRATOR_HOME/venv/bin/pip" install --upgrade pip
    sudo -u "$ORCHESTRATOR_USER" "$ORCHESTRATOR_HOME/venv/bin/pip" install -r "$ORCHESTRATOR_HOME/requirements.txt"
}

# Install and configure Node-RED
setup_node_red() {
    log "Installing Node-RED..."
    
    # Install Node-RED globally
    sudo npm install -g --unsafe-perm node-red@$NODE_RED_VERSION
    
    # Install Node-RED dashboard
    sudo npm install -g --unsafe-perm node-red-dashboard
    
    # Setup Node-RED for orchestrator user
    sudo mkdir -p "$ORCHESTRATOR_HOME/.node-red"
    sudo chown -R "$ORCHESTRATOR_USER:$ORCHESTRATOR_USER" "$ORCHESTRATOR_HOME/.node-red"
    
    # Copy Node-RED configuration
    if [[ -d "$ORCHESTRATOR_HOME/configs/node_red_config" ]]; then
        sudo cp -r "$ORCHESTRATOR_HOME/configs/node_red_config"/* "$ORCHESTRATOR_HOME/.node-red/"
        sudo chown -R "$ORCHESTRATOR_USER:$ORCHESTRATOR_USER" "$ORCHESTRATOR_HOME/.node-red"
    fi
}

# Configure systemd services
setup_systemd_services() {
    log "Setting up systemd services..."
    
    # Copy service files
    sudo cp "$ORCHESTRATOR_HOME/configs/systemd"/*.service /etc/systemd/system/
    
    # Update service files with correct paths
    sudo sed -i "s|/home/pi/orchestrator-platform|$ORCHESTRATOR_HOME|g" /etc/systemd/system/*.service
    sudo sed -i "s|User=pi|User=$ORCHESTRATOR_USER|g" /etc/systemd/system/orchestrator-*.service
    sudo sed -i "s|Group=pi|Group=$ORCHESTRATOR_USER|g" /etc/systemd/system/orchestrator-*.service
    
    # Create orchestrator target
    sudo tee /etc/systemd/system/orchestrator.target > /dev/null <<EOF
[Unit]
Description=Orchestrator Platform Services
Documentation=https://github.com/your-org/orchestrator-platform
Wants=mosquitto.service
After=mosquitto.service

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable services
    sudo systemctl daemon-reload
    sudo systemctl enable mosquitto.service
    sudo systemctl enable orchestrator.target
    sudo systemctl enable orchestrator-safety.service
    sudo systemctl enable state-manager.service
    sudo systemctl enable node-red.service
}

# Configure GPIO permissions
setup_gpio_permissions() {
    log "Configuring GPIO permissions..."
    
    # Add orchestrator user to gpio group
    sudo usermod -a -G gpio "$ORCHESTRATOR_USER"
    
    # Create udev rules for GPIO access
    sudo tee /etc/udev/rules.d/99-orchestrator-gpio.rules > /dev/null <<EOF
# GPIO access for orchestrator user
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0664"
SUBSYSTEM=="i2c-dev", GROUP="i2c", MODE="0664"
SUBSYSTEM=="spidev", GROUP="spi", MODE="0664"
KERNEL=="ttyUSB*", GROUP="dialout", MODE="0664"
KERNEL=="ttyACM*", GROUP="dialout", MODE="0664"
EOF

    # Reload udev rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
}

# Configure firewall (if needed)
setup_firewall() {
    log "Configuring firewall..."
    
    # Install ufw if not present
    sudo apt install -y ufw
    
    # Configure basic firewall rules
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow Node-RED dashboard (port 1880)
    sudo ufw allow 1880/tcp
    
    # Allow MQTT (port 1883) only from local network
    sudo ufw allow from 192.168.0.0/16 to any port 1883
    sudo ufw allow from 10.0.0.0/8 to any port 1883
    sudo ufw allow from 172.16.0.0/12 to any port 1883
    
    # Enable firewall
    sudo ufw --force enable
}

# Create startup script
create_startup_script() {
    log "Creating startup script..."
    
    sudo tee "$ORCHESTRATOR_HOME/start_orchestrator.sh" > /dev/null <<'EOF'
#!/bin/bash

# Orchestrator Platform Startup Script

echo "Starting Orchestrator Platform..."

# Start all services
sudo systemctl start mosquitto.service
sudo systemctl start orchestrator.target

# Wait for services to start
sleep 5

# Check service status
echo "Service Status:"
sudo systemctl status mosquitto.service --no-pager -l
sudo systemctl status orchestrator-safety.service --no-pager -l
sudo systemctl status state-manager.service --no-pager -l
sudo systemctl status node-red.service --no-pager -l

echo "Orchestrator Platform started successfully!"
echo "Node-RED Dashboard: http://$(hostname -I | awk '{print $1}'):1880"
EOF

    sudo chmod +x "$ORCHESTRATOR_HOME/start_orchestrator.sh"
    sudo chown "$ORCHESTRATOR_USER:$ORCHESTRATOR_USER" "$ORCHESTRATOR_HOME/start_orchestrator.sh"
}

# Create log rotation configuration
setup_log_rotation() {
    log "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/orchestrator > /dev/null <<EOF
$ORCHESTRATOR_HOME/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $ORCHESTRATOR_USER $ORCHESTRATOR_USER
    postrotate
        systemctl reload orchestrator-safety.service > /dev/null 2>&1 || true
        systemctl reload state-manager.service > /dev/null 2>&1 || true
    endscript
}
EOF
}

# Verify installation
verify_installation() {
    log "Verifying installation..."
    
    # Check Python installation
    python_version=$("$ORCHESTRATOR_HOME/venv/bin/python" --version)
    log "Python version: $python_version"
    
    # Check Node.js installation
    node_version=$(node --version)
    log "Node.js version: $node_version"
    
    # Check services
    log "Checking service configurations..."
    sudo systemctl is-enabled mosquitto.service || warn "Mosquitto service not enabled"
    sudo systemctl is-enabled orchestrator-safety.service || warn "Safety service not enabled"
    sudo systemctl is-enabled state-manager.service || warn "State manager service not enabled"
    sudo systemctl is-enabled node-red.service || warn "Node-RED service not enabled"
    
    # Test MQTT connection
    log "Testing MQTT connection..."
    timeout 5 mosquitto_pub -h localhost -t test/setup -m "installation_complete" || warn "MQTT test failed"
    
    log "Installation verification complete!"
}

# Main installation function
main() {
    log "Starting Orchestrator Platform installation on Raspberry Pi..."
    
    check_root
    update_system
    install_python
    install_nodejs
    install_mosquitto
    setup_orchestrator_user
    setup_project
    setup_node_red
    setup_systemd_services
    setup_gpio_permissions
    setup_firewall
    create_startup_script
    setup_log_rotation
    verify_installation
    
    log "Installation completed successfully!"
    log ""
    log "Next steps:"
    log "1. Reboot the system: sudo reboot"
    log "2. After reboot, start services: $ORCHESTRATOR_HOME/start_orchestrator.sh"
    log "3. Access Node-RED dashboard at: http://$(hostname -I | awk '{print $1}'):1880"
    log "4. Check logs at: $ORCHESTRATOR_HOME/logs/"
    log ""
    log "For troubleshooting, check service status with:"
    log "  sudo systemctl status orchestrator.target"
}

# Run main function
main "$@"