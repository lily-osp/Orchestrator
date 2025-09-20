# Orchestrator Platform Deployment Guide

This directory contains deployment scripts and configurations for setting up the Orchestrator Platform on various environments.

## Deployment Options

### 1. Raspberry Pi Direct Deployment (Recommended for Production)

Use the shell script for a complete automated setup on a fresh Raspberry Pi:

```bash
# Copy the deployment script to your Raspberry Pi
scp deploy/setup_raspberry_pi.sh pi@your-pi-ip:~/

# SSH to your Raspberry Pi
ssh pi@your-pi-ip

# Run the setup script
chmod +x setup_raspberry_pi.sh
./setup_raspberry_pi.sh

# Reboot after installation
sudo reboot

# After reboot, start the services
/opt/orchestrator/start_orchestrator.sh
```

**Features:**
- Complete system setup from scratch
- Automatic dependency installation
- Service configuration and startup
- Security hardening with firewall
- Log rotation setup
- GPIO permissions configuration

### 2. Ansible Deployment (Recommended for Multiple Devices)

Use Ansible for deploying to multiple Raspberry Pi devices:

```bash
# Install Ansible on your control machine
pip install ansible

# Navigate to the ansible directory
cd deploy/ansible

# Update inventory.yml with your Raspberry Pi IP addresses
vim inventory.yml

# Run the playbook
ansible-playbook -i inventory.yml orchestrator-playbook.yml

# Check deployment status
ansible raspberry_pi -i inventory.yml -m shell -a "systemctl status orchestrator.target"
```

**Features:**
- Multi-device deployment
- Idempotent operations
- Configuration management
- Rollback capabilities
- Inventory management

### 3. Docker Deployment (Recommended for Development)

Use Docker for development and testing:

```bash
# Navigate to the docker directory
cd deploy/docker

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Access Node-RED dashboard
open http://localhost:1880

# Stop services
docker-compose down
```

**Features:**
- Isolated environment
- Easy development setup
- Mock hardware simulation
- Quick teardown and rebuild

## Prerequisites

### For Raspberry Pi Deployment
- Raspberry Pi 4 with Raspberry Pi OS (Bullseye or newer)
- SSH access enabled
- Internet connection
- At least 8GB SD card
- User with sudo privileges

### For Ansible Deployment
- Ansible 2.9+ on control machine
- SSH key-based authentication to target devices
- Python 3.6+ on target devices

### For Docker Deployment
- Docker 20.10+
- Docker Compose 1.29+
- 4GB+ RAM recommended

## Configuration

### Environment Variables

The following environment variables can be configured:

```bash
# MQTT Configuration
MQTT_HOST=localhost
MQTT_PORT=1883

# Node-RED Configuration
NODE_RED_PORT=1880

# Python Configuration
PYTHONPATH=/opt/orchestrator

# Hardware Configuration (Raspberry Pi only)
HAL_MODE=production  # or 'mock' for simulation
```

### Service Configuration

Services are configured via systemd and can be managed with:

```bash
# Check all services status
sudo systemctl status orchestrator.target

# Start/stop individual services
sudo systemctl start orchestrator-safety.service
sudo systemctl stop state-manager.service

# View service logs
sudo journalctl -u orchestrator-safety.service -f
```

## Security Considerations

### Firewall Configuration
The deployment scripts configure UFW with the following rules:
- SSH (port 22): Allowed
- Node-RED Dashboard (port 1880): Allowed
- MQTT (port 1883): Allowed only from local networks

### User Permissions
- Dedicated `orchestrator` user with minimal privileges
- GPIO/I2C/SPI access for hardware control
- No shell access for service accounts

### Network Security
- MQTT broker configured for local access only
- No external authentication by default (configure for production)
- TLS/SSL not configured by default (add for production)

## Troubleshooting

### Common Issues

1. **Services fail to start**
   ```bash
   # Check service status
   sudo systemctl status orchestrator-safety.service
   
   # Check logs
   sudo journalctl -u orchestrator-safety.service -n 50
   ```

2. **MQTT connection issues**
   ```bash
   # Test MQTT broker
   mosquitto_pub -h localhost -t test/connection -m "test"
   mosquitto_sub -h localhost -t test/connection
   ```

3. **GPIO permission issues**
   ```bash
   # Check user groups
   groups orchestrator
   
   # Reload udev rules
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

4. **Node-RED not accessible**
   ```bash
   # Check Node-RED service
   sudo systemctl status node-red.service
   
   # Check firewall
   sudo ufw status
   ```

### Log Locations

- System logs: `/var/log/syslog`
- Service logs: `journalctl -u <service-name>`
- Application logs: `/opt/orchestrator/logs/`
- MQTT logs: `/var/log/mosquitto/`

## Maintenance

### Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python dependencies
/opt/orchestrator/venv/bin/pip install -r /opt/orchestrator/requirements.txt --upgrade

# Update Node-RED
sudo npm update -g node-red
```

### Backup

```bash
# Backup configuration
tar -czf orchestrator-backup-$(date +%Y%m%d).tar.gz /opt/orchestrator/configs

# Backup logs
tar -czf orchestrator-logs-$(date +%Y%m%d).tar.gz /opt/orchestrator/logs
```

### Monitoring

```bash
# Check system resources
htop

# Check disk usage
df -h

# Check service status
sudo systemctl status orchestrator.target

# View real-time logs
sudo journalctl -f
```

## Production Deployment Checklist

- [ ] Change default passwords
- [ ] Configure TLS/SSL for MQTT
- [ ] Set up authentication for Node-RED
- [ ] Configure log rotation
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Test emergency stop procedures
- [ ] Document hardware configuration
- [ ] Set up remote access (VPN)
- [ ] Configure automatic updates

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review service logs
3. Check the project documentation
4. Open an issue on the project repository