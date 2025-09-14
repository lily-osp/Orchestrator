# Node-RED Configuration for Orchestrator Platform

This directory contains the Node-RED configuration for the Orchestrator robotics platform.

## Overview

Node-RED serves as the visual programming interface and web dashboard for the Orchestrator platform. It provides:

- Visual flow editor for creating robotic sequences
- Web-based dashboard for monitoring and control
- MQTT integration for communication with the HAL layer
- Real-time telemetry visualization

## Files

- `settings.js` - Main Node-RED configuration file
- `flows.json` - Initial flow configuration with MQTT setup
- `package.json` - Node.js dependencies
- `start-nodered.sh` - Startup script
- `README.md` - This documentation

## Installation

### Prerequisites

1. Node.js (v18 or higher)
2. npm
3. Mosquitto MQTT broker

### Setup

1. Install Node-RED globally:
   ```bash
   npm install -g node-red
   ```

2. Install the dashboard plugin:
   ```bash
   npm install -g @flowfuse/node-red-dashboard
   ```

3. Install local dependencies:
   ```bash
   cd configs/node_red_config
   npm install
   ```

## Running Node-RED

### Manual Start

```bash
# From the project root directory
./configs/node_red_config/start-nodered.sh
```

### As System Service

1. Copy the systemd service file:
   ```bash
   sudo cp configs/systemd/node-red.service /etc/systemd/system/
   ```

2. Update the service file paths if needed:
   ```bash
   sudo nano /etc/systemd/system/node-red.service
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable node-red.service
   sudo systemctl start node-red.service
   ```

4. Check service status:
   ```bash
   sudo systemctl status node-red.service
   ```

## Access

- **Flow Editor**: http://localhost:1880/admin
- **Dashboard**: http://localhost:1880/ui
- **API Endpoints**: http://localhost:1880/api

### Default Credentials

- **Username**: admin
- **Password**: password

> **Note**: Change the default password in production by updating the `adminAuth` section in `settings.js`

## MQTT Configuration

The Node-RED instance is pre-configured to connect to the local Mosquitto MQTT broker with the following settings:

- **Broker**: localhost:1883
- **Client ID**: node-red-orchestrator
- **Topics**:
  - Commands: `orchestrator/cmd/+`
  - Telemetry: `orchestrator/data/+`
  - Status: `orchestrator/status/+`

## Initial Flows

The initial flow configuration includes:

1. **MQTT Broker Configuration**: Connection to local Mosquitto broker
2. **System Heartbeat**: Publishes system status every 30 seconds
3. **Command Listener**: Subscribes to command topics
4. **Telemetry Listener**: Subscribes to sensor data topics
5. **Debug Nodes**: For monitoring message flow during development

## Security

The configuration includes basic security features:

- Password-protected admin interface
- HTTP node authentication
- Static content authentication
- Credential encryption

For production deployment, consider:

- Using HTTPS with SSL certificates
- Implementing stronger authentication
- Restricting network access
- Regular security updates

## Troubleshooting

### Common Issues

1. **Node-RED won't start**:
   - Check if port 1880 is available
   - Verify Node.js version (>=18)
   - Check file permissions

2. **MQTT connection fails**:
   - Ensure Mosquitto broker is running
   - Check broker configuration
   - Verify network connectivity

3. **Dashboard not accessible**:
   - Confirm dashboard plugin is installed
   - Check UI path configuration
   - Verify port forwarding if accessing remotely

### Logs

- **Service logs**: `sudo journalctl -u node-red.service -f`
- **Node-RED logs**: Available in the flow editor debug panel

## Development

### Adding New Flows

1. Access the flow editor at http://localhost:1880/admin
2. Create new flows using the visual editor
3. Deploy changes using the Deploy button
4. Test functionality using the debug panel

### Installing Additional Nodes

Use the Palette Manager in the flow editor or install via npm:

```bash
cd configs/node_red_config
npm install node-red-contrib-[package-name]
```

## Integration with HAL

The Node-RED configuration is designed to integrate seamlessly with the Hardware Abstraction Layer (HAL):

- **Commands**: Node-RED flows publish commands to `orchestrator/cmd/*` topics
- **Telemetry**: HAL publishes sensor data to `orchestrator/data/*` topics
- **Status**: Both layers publish status to `orchestrator/status/*` topics

This enables bidirectional communication between the visual programming interface and the hardware control layer.