#!/usr/bin/env python3
"""
Test script for HAL Orchestrator Service

This script tests the basic functionality of the HAL orchestrator
without requiring actual hardware or MQTT broker.
"""

import sys
import time
from pathlib import Path

# Add hal_service to Python path
sys.path.insert(0, str(Path(__file__).parent / "hal_service"))

import orchestrator_hal


def test_configuration_loading():
    """Test configuration loading functionality."""
    print("Testing configuration loading...")
    
    orchestrator = orchestrator_hal.HALOrchestrator(config_path='config.yaml', test_mode=True)
    
    # Test configuration loading
    if orchestrator._load_configuration():
        print(f"✓ Configuration loaded successfully")
        print(f"  - Motors: {len(orchestrator.config.motors)}")
        print(f"  - Sensors: {len(orchestrator.config.sensors)}")
        return True
    else:
        print("✗ Configuration loading failed")
        return False


def test_initialization():
    """Test full initialization in test mode."""
    print("\nTesting initialization...")
    
    orchestrator = orchestrator_hal.HALOrchestrator(config_path='config.yaml', test_mode=True)
    
    if orchestrator.initialize():
        print("✓ Initialization successful")
        
        # Test system status
        status = orchestrator.get_system_status()
        print(f"✓ System status retrieved: running={status['running']}")
        
        return orchestrator
    else:
        print("✗ Initialization failed")
        return None


def test_graceful_shutdown(orchestrator):
    """Test graceful shutdown."""
    print("\nTesting graceful shutdown...")
    
    try:
        orchestrator.shutdown()
        print("✓ Shutdown completed successfully")
        return True
    except Exception as e:
        print(f"✗ Shutdown failed: {e}")
        return False


def main():
    """Run all tests."""
    print("HAL Orchestrator Service Test Suite")
    print("=" * 40)
    
    # Test configuration loading
    if not test_configuration_loading():
        return False
    
    # Test initialization
    orchestrator = test_initialization()
    if not orchestrator:
        return False
    
    # Test shutdown
    if not test_graceful_shutdown(orchestrator):
        return False
    
    print("\n" + "=" * 40)
    print("✓ All tests passed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)