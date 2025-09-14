#!/bin/bash

# Node-RED Startup Script for Orchestrator Platform
# This script starts Node-RED with the orchestrator configuration

# Set the working directory to the Node-RED config directory
cd "$(dirname "$0")"

# Set environment variables
export NODE_RED_HOME=$(pwd)
export PORT=1880

# Check if MQTT broker is running
echo "Checking MQTT broker availability..."
if ! command -v mosquitto &> /dev/null; then
    echo "Warning: Mosquitto MQTT broker not found. Please install it first:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install mosquitto mosquitto-clients"
    echo ""
fi

# Check if mosquitto is running
if ! pgrep -x "mosquitto" > /dev/null; then
    echo "Warning: Mosquitto broker is not running. Starting it..."
    sudo systemctl start mosquitto || echo "Failed to start mosquitto. Please start it manually."
fi

# Install Node-RED dependencies if not already installed
if [ ! -d "node_modules" ]; then
    echo "Installing Node-RED dependencies..."
    npm install
fi

# Start Node-RED with our configuration
echo "Starting Node-RED for Orchestrator Platform..."
echo "Web interface will be available at: http://localhost:$PORT"
echo "Dashboard will be available at: http://localhost:$PORT/ui"
echo "Admin interface: http://localhost:$PORT/admin"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: password"
echo ""

# Start Node-RED
node-red --settings ./settings.js --verbose