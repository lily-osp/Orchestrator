#!/usr/bin/env node

/**
 * Dashboard UI Test Script
 * 
 * This script demonstrates the dashboard functionality by publishing
 * sample MQTT messages to test the UI components and visualizations.
 */

const mqtt = require('mqtt');

console.log('🧪 Testing Dashboard UI with Sample Data...\n');

// Connect to MQTT broker
const client = mqtt.connect('mqtt://localhost:1883', {
    clientId: 'dashboard-ui-tester',
    clean: true
});

client.on('connect', function () {
    console.log('✅ Connected to MQTT broker');
    
    // Test LiDAR data
    console.log('📡 Publishing sample LiDAR data...');
    const lidarData = {
        timestamp: new Date().toISOString(),
        ranges: [1.2, 1.5, 0.8, 2.1, 3.0, 1.8, 2.5, 1.1, 4.2, 2.8, 1.9, 3.5],
        angles: [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330],
        min_range: 0.1,
        max_range: 10.0
    };
    client.publish('orchestrator/data/lidar', JSON.stringify(lidarData));
    
    // Test encoder data
    console.log('🔄 Publishing sample encoder data...');
    const encoderData = {
        timestamp: new Date().toISOString(),
        left_count: 1250,
        right_count: 1248,
        distance_traveled: 5.2,
        velocity: {
            linear: 0.5,
            angular: 0.1
        }
    };
    client.publish('orchestrator/data/encoders', JSON.stringify(encoderData));
    
    // Test robot status
    console.log('🤖 Publishing sample robot status...');
    const robotStatus = {
        timestamp: new Date().toISOString(),
        status: 'active',
        position: {
            x: 10.5,
            y: 5.2,
            heading: 90.0
        },
        mission: 'in_progress',
        reason: 'executing_waypoint'
    };
    client.publish('orchestrator/status/robot', JSON.stringify(robotStatus));
    
    // Test safety status
    console.log('🛡️ Publishing sample safety status...');
    const safetyStatus = {
        timestamp: new Date().toISOString(),
        status: 'active',
        obstacle_detected: false,
        min_distance: 1.5,
        safety_threshold: 0.5,
        last_trigger: null
    };
    client.publish('orchestrator/status/safety', JSON.stringify(safetyStatus));
    
    // Test system status
    console.log('💻 Publishing sample system status...');
    const systemStatus = {
        timestamp: new Date().toISOString(),
        status: 'active',
        component: 'hal_service',
        uptime: 3600,
        memory_usage: 45.2,
        cpu_usage: 12.8
    };
    client.publish('orchestrator/status/system', JSON.stringify(systemStatus));
    
    console.log('\n✅ Sample data published successfully!');
    console.log('🌐 Open dashboard at: http://localhost:1880/ui');
    console.log('📊 Check "System Monitoring" tab to see the data');
    console.log('🎮 Test controls on "Robot Control" tab');
    
    // Publish periodic updates
    let counter = 0;
    const interval = setInterval(() => {
        counter++;
        
        // Update LiDAR with moving obstacle
        const movingLidarData = {
            ...lidarData,
            timestamp: new Date().toISOString(),
            ranges: lidarData.ranges.map((range, i) => 
                range + Math.sin(counter * 0.1 + i) * 0.3
            )
        };
        client.publish('orchestrator/data/lidar', JSON.stringify(movingLidarData));
        
        // Update robot position
        const movingRobotStatus = {
            ...robotStatus,
            timestamp: new Date().toISOString(),
            position: {
                x: 10.5 + Math.cos(counter * 0.05) * 2,
                y: 5.2 + Math.sin(counter * 0.05) * 2,
                heading: (counter * 2) % 360
            }
        };
        client.publish('orchestrator/status/robot', JSON.stringify(movingRobotStatus));
        
        // Update system resources
        const dynamicSystemStatus = {
            ...systemStatus,
            timestamp: new Date().toISOString(),
            memory_usage: 45 + Math.random() * 20,
            cpu_usage: 10 + Math.random() * 30
        };
        client.publish('orchestrator/status/system', JSON.stringify(dynamicSystemStatus));
        
        if (counter >= 100) {
            clearInterval(interval);
            console.log('\n🏁 Test completed. Dashboard should show dynamic data updates.');
            client.end();
        }
    }, 500);
    
});

client.on('error', function (error) {
    console.error('❌ MQTT connection error:', error);
    console.log('💡 Make sure MQTT broker is running: mosquitto -v');
    process.exit(1);
});

// Handle graceful shutdown
process.on('SIGINT', function() {
    console.log('\n🛑 Stopping dashboard test...');
    client.end();
    process.exit(0);
});