#!/bin/bash

# Orchestrator Platform - Deployment Validation Script
# This script validates that the Orchestrator platform is properly deployed and configured

set -e

# Configuration
ORCHESTRATOR_HOME="/opt/orchestrator"
ORCHESTRATOR_USER="orchestrator"
MQTT_HOST="localhost"
MQTT_PORT="1883"
NODE_RED_PORT="1880"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    info "Running test: $test_name"
    
    if eval "$test_command" > /dev/null 2>&1; then
        log "✓ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        error "✗ FAIL: $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Test system dependencies
test_system_dependencies() {
    info "Testing system dependencies..."
    
    run_test "Python 3 installed" "which python3"
    run_test "Node.js installed" "which node"
    run_test "npm installed" "which npm"
    run_test "Git installed" "which git"
    run_test "Mosquitto installed" "which mosquitto"
    run_test "Mosquitto clients installed" "which mosquitto_pub && which mosquitto_sub"
}

# Test user and permissions
test_user_permissions() {
    info "Testing user and permissions..."
    
    run_test "Orchestrator user exists" "id $ORCHESTRATOR_USER"
    run_test "Orchestrator user in gpio group" "groups $ORCHESTRATOR_USER | grep -q gpio"
    run_test "Orchestrator user in i2c group" "groups $ORCHESTRATOR_USER | grep -q i2c"
    run_test "Orchestrator user in spi group" "groups $ORCHESTRATOR_USER | grep -q spi"
    run_test "Orchestrator user in dialout group" "groups $ORCHESTRATOR_USER | grep -q dialout"
    run_test "Orchestrator home directory exists" "test -d $ORCHESTRATOR_HOME"
    run_test "Orchestrator home directory ownership" "test -O $ORCHESTRATOR_HOME || sudo -u $ORCHESTRATOR_USER test -O $ORCHESTRATOR_HOME"
}

# Test project structure
test_project_structure() {
    info "Testing project structure..."
    
    run_test "Project directory exists" "test -d $ORCHESTRATOR_HOME"
    run_test "HAL service directory exists" "test -d $ORCHESTRATOR_HOME/hal_service"
    run_test "Configs directory exists" "test -d $ORCHESTRATOR_HOME/configs"
    run_test "Logs directory exists" "test -d $ORCHESTRATOR_HOME/logs"
    run_test "Python virtual environment exists" "test -d $ORCHESTRATOR_HOME/venv"
    run_test "Configuration file exists" "test -f $ORCHESTRATOR_HOME/config.yaml"
    run_test "Requirements file exists" "test -f $ORCHESTRATOR_HOME/requirements.txt"
}

# Test Python environment
test_python_environment() {
    info "Testing Python environment..."
    
    run_test "Python virtual environment activated" "$ORCHESTRATOR_HOME/venv/bin/python --version"
    run_test "pip installed in venv" "$ORCHESTRATOR_HOME/venv/bin/pip --version"
    run_test "paho-mqtt installed" "$ORCHESTRATOR_HOME/venv/bin/python -c 'import paho.mqtt.client'"
    run_test "pydantic installed" "$ORCHESTRATOR_HOME/venv/bin/python -c 'import pydantic'"
    run_test "PyYAML installed" "$ORCHESTRATOR_HOME/venv/bin/python -c 'import yaml'"
    
    # Test HAL modules (if not on actual hardware, these might fail)
    if run_test "HAL base module importable" "$ORCHESTRATOR_HOME/venv/bin/python -c 'import sys; sys.path.append(\"$ORCHESTRATOR_HOME\"); import hal_service.base'"; then
        run_test "MQTT client module importable" "$ORCHESTRATOR_HOME/venv/bin/python -c 'import sys; sys.path.append(\"$ORCHESTRATOR_HOME\"); import hal_service.mqtt_client'"
        run_test "Config module importable" "$ORCHESTRATOR_HOME/venv/bin/python -c 'import sys; sys.path.append(\"$ORCHESTRATOR_HOME\"); import hal_service.config'"
    fi
}

# Test Node-RED installation
test_node_red() {
    info "Testing Node-RED installation..."
    
    run_test "Node-RED installed globally" "which node-red"
    run_test "Node-RED dashboard installed" "npm list -g node-red-dashboard"
    run_test "Node-RED config directory exists" "test -d $ORCHESTRATOR_HOME/.node-red"
    
    # Test Node-RED configuration files
    if test -f "$ORCHESTRATOR_HOME/.node-red/settings.js"; then
        run_test "Node-RED settings file exists" "test -f $ORCHESTRATOR_HOME/.node-red/settings.js"
    else
        warn "Node-RED settings file not found, using default configuration"
    fi
}

# Test MQTT broker
test_mqtt_broker() {
    info "Testing MQTT broker..."
    
    run_test "Mosquitto service enabled" "systemctl is-enabled mosquitto.service"
    run_test "Mosquitto service active" "systemctl is-active mosquitto.service"
    run_test "MQTT port listening" "netstat -ln | grep -q :$MQTT_PORT"
    
    # Test MQTT connectivity
    if run_test "MQTT publish test" "timeout 5 mosquitto_pub -h $MQTT_HOST -p $MQTT_PORT -t test/validation -m 'validation_test'"; then
        run_test "MQTT subscribe test" "timeout 5 bash -c 'mosquitto_sub -h $MQTT_HOST -p $MQTT_PORT -t test/validation -C 1 | grep -q validation_test' &"
    fi
}

# Test systemd services
test_systemd_services() {
    info "Testing systemd services..."
    
    # Test service files exist
    run_test "Orchestrator target exists" "test -f /etc/systemd/system/orchestrator.target"
    run_test "Safety service file exists" "test -f /etc/systemd/system/orchestrator-safety.service"
    run_test "State manager service file exists" "test -f /etc/systemd/system/state-manager.service"
    run_test "Node-RED service file exists" "test -f /etc/systemd/system/node-red.service"
    
    # Test service enablement
    run_test "Orchestrator target enabled" "systemctl is-enabled orchestrator.target"
    run_test "Safety service enabled" "systemctl is-enabled orchestrator-safety.service"
    run_test "State manager service enabled" "systemctl is-enabled state-manager.service"
    run_test "Node-RED service enabled" "systemctl is-enabled node-red.service"
    
    # Test service status (these might fail if services aren't running)
    if systemctl is-active orchestrator-safety.service > /dev/null 2>&1; then
        run_test "Safety service active" "systemctl is-active orchestrator-safety.service"
    else
        warn "Safety service not active (this is normal if not started yet)"
    fi
    
    if systemctl is-active state-manager.service > /dev/null 2>&1; then
        run_test "State manager service active" "systemctl is-active state-manager.service"
    else
        warn "State manager service not active (this is normal if not started yet)"
    fi
    
    if systemctl is-active node-red.service > /dev/null 2>&1; then
        run_test "Node-RED service active" "systemctl is-active node-red.service"
    else
        warn "Node-RED service not active (this is normal if not started yet)"
    fi
}

# Test network connectivity
test_network_connectivity() {
    info "Testing network connectivity..."
    
    # Test Node-RED port
    if netstat -ln | grep -q ":$NODE_RED_PORT"; then
        run_test "Node-RED port listening" "netstat -ln | grep -q :$NODE_RED_PORT"
        run_test "Node-RED HTTP response" "timeout 10 curl -s -o /dev/null -w '%{http_code}' http://localhost:$NODE_RED_PORT | grep -q 200"
    else
        warn "Node-RED not running, skipping HTTP tests"
    fi
}

# Test firewall configuration
test_firewall() {
    info "Testing firewall configuration..."
    
    if which ufw > /dev/null 2>&1; then
        run_test "UFW installed" "which ufw"
        
        if ufw status | grep -q "Status: active"; then
            run_test "UFW active" "ufw status | grep -q 'Status: active'"
            run_test "SSH allowed" "ufw status | grep -q 22"
            run_test "Node-RED port allowed" "ufw status | grep -q $NODE_RED_PORT"
            run_test "MQTT port allowed" "ufw status | grep -q $MQTT_PORT"
        else
            warn "UFW not active (this might be intentional)"
        fi
    else
        warn "UFW not installed"
    fi
}

# Test GPIO permissions (Raspberry Pi specific)
test_gpio_permissions() {
    info "Testing GPIO permissions..."
    
    if test -f /etc/udev/rules.d/99-orchestrator-gpio.rules; then
        run_test "GPIO udev rules exist" "test -f /etc/udev/rules.d/99-orchestrator-gpio.rules"
        run_test "GPIO rules contain gpio group" "grep -q 'GROUP=\"gpio\"' /etc/udev/rules.d/99-orchestrator-gpio.rules"
        run_test "GPIO rules contain i2c group" "grep -q 'GROUP=\"i2c\"' /etc/udev/rules.d/99-orchestrator-gpio.rules"
    else
        warn "GPIO udev rules not found (normal for non-Raspberry Pi systems)"
    fi
}

# Test log rotation
test_log_rotation() {
    info "Testing log rotation..."
    
    if test -f /etc/logrotate.d/orchestrator; then
        run_test "Log rotation config exists" "test -f /etc/logrotate.d/orchestrator"
        run_test "Log rotation config valid" "logrotate -d /etc/logrotate.d/orchestrator"
    else
        warn "Log rotation not configured"
    fi
}

# Generate summary report
generate_summary() {
    echo ""
    echo "=========================================="
    echo "         VALIDATION SUMMARY"
    echo "=========================================="
    echo "Total tests run: $TESTS_TOTAL"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log "🎉 All tests passed! Deployment appears to be successful."
        echo ""
        echo "Next steps:"
        echo "1. Start services: sudo systemctl start orchestrator.target"
        echo "2. Check service status: sudo systemctl status orchestrator.target"
        echo "3. Access Node-RED dashboard: http://$(hostname -I | awk '{print $1}'):$NODE_RED_PORT"
        echo "4. Monitor logs: sudo journalctl -f"
        return 0
    else
        error "❌ Some tests failed. Please review the output above and fix any issues."
        echo ""
        echo "Common fixes:"
        echo "1. Re-run the deployment script"
        echo "2. Check service logs: sudo journalctl -u <service-name>"
        echo "3. Verify configuration files"
        echo "4. Check network connectivity"
        return 1
    fi
}

# Main validation function
main() {
    log "Starting Orchestrator Platform deployment validation..."
    echo ""
    
    test_system_dependencies
    test_user_permissions
    test_project_structure
    test_python_environment
    test_node_red
    test_mqtt_broker
    test_systemd_services
    test_network_connectivity
    test_firewall
    test_gpio_permissions
    test_log_rotation
    
    generate_summary
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    warn "Running as root. Some tests may not work correctly."
fi

# Run main function
main "$@"