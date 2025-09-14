#!/bin/bash

# Mosquitto MQTT Broker Installation Script for Orchestrator Platform

echo "Installing Mosquitto MQTT Broker..."

# Update package list
sudo apt-get update

# Install Mosquitto broker and clients
sudo apt-get install -y mosquitto mosquitto-clients

# Create mosquitto configuration directory if it doesn't exist
sudo mkdir -p /etc/mosquitto/conf.d

# Create basic configuration for orchestrator platform
sudo tee /etc/mosquitto/conf.d/orchestrator.conf > /dev/null << EOF
# Orchestrator Platform MQTT Configuration

# Basic settings
port 1883
listener 1883 0.0.0.0

# Allow anonymous connections (for development)
# In production, configure proper authentication
allow_anonymous true

# Persistence settings
persistence true
persistence_location /var/lib/mosquitto/

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information

# Connection settings
max_connections 100
max_inflight_messages 20
max_queued_messages 100

# Message size limits
message_size_limit 1048576

# Keepalive settings
keepalive_interval 60

# Topic patterns for orchestrator
# All orchestrator topics start with 'orchestrator/'
topic read orchestrator/#
topic write orchestrator/#
EOF

# Enable and start mosquitto service
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Check if mosquitto is running
if sudo systemctl is-active --quiet mosquitto; then
    echo "✓ Mosquitto MQTT broker installed and running successfully"
    echo "✓ Broker listening on port 1883"
    echo "✓ Configuration file: /etc/mosquitto/conf.d/orchestrator.conf"
    echo ""
    echo "Test the broker with:"
    echo "  mosquitto_pub -h localhost -t test/topic -m 'Hello MQTT'"
    echo "  mosquitto_sub -h localhost -t test/topic"
else
    echo "✗ Failed to start Mosquitto broker"
    echo "Check logs with: sudo journalctl -u mosquitto -f"
    exit 1
fi

echo ""
echo "Mosquitto installation complete!"