#!/usr/bin/env node

/**
 * Telemetry Flows Validation Script
 * 
 * This script validates the Node-RED telemetry flows implementation
 * by checking flow structure, node connections, and data processing logic.
 */

const fs = require('fs');

// Read the flows configuration
const flowsPath = 'configs/node_red_config/flows.json';
const flows = JSON.parse(fs.readFileSync(flowsPath, 'utf8'));

console.log('🔍 Validating Node-RED Telemetry Flows Implementation');
console.log('=' .repeat(60));

let testsPassed = 0;
let testsTotal = 0;

function runTest(testName, testFunction) {
    testsTotal++;
    try {
        const result = testFunction();
        if (result) {
            console.log(`✅ ${testName}`);
            testsPassed++;
        } else {
            console.log(`❌ ${testName}`);
        }
    } catch (error) {
        console.log(`❌ ${testName} - Error: ${error.message}`);
    }
}

// Test 1: Check telemetry flows tab exists
runTest('Telemetry Flows Tab Exists', () => {
    return flows.some(node => node.id === 'telemetry-flows-tab' && node.type === 'tab');
});

// Test 2: Check monitoring UI tab exists
runTest('Monitoring UI Tab Exists', () => {
    return flows.some(node => node.id === 'ui-tab-monitoring' && node.type === 'ui_tab');
});

// Test 3: Check MQTT data subscriber exists
runTest('MQTT Data Subscriber Exists', () => {
    const subscriber = flows.find(node => node.id === 'mqtt-data-subscriber');
    return subscriber && 
           subscriber.type === 'mqtt in' && 
           subscriber.topic === 'orchestrator/data/+';
});

// Test 4: Check MQTT status subscriber exists
runTest('MQTT Status Subscriber Exists', () => {
    const subscriber = flows.find(node => node.id === 'mqtt-status-subscriber');
    return subscriber && 
           subscriber.type === 'mqtt in' && 
           subscriber.topic === 'orchestrator/status/+';
});

// Test 5: Check data router exists and has correct outputs
runTest('Data Router Configuration', () => {
    const router = flows.find(node => node.id === 'data-router');
    return router && 
           router.type === 'switch' && 
           router.outputs === 3 &&
           router.rules.length === 3;
});

// Test 6: Check status router exists and has correct outputs
runTest('Status Router Configuration', () => {
    const router = flows.find(node => node.id === 'status-router');
    return router && 
           router.type === 'switch' && 
           router.outputs === 4 &&
           router.rules.length === 4;
});

// Test 7: Check LiDAR processor exists
runTest('LiDAR Data Processor Exists', () => {
    const processor = flows.find(node => node.id === 'lidar-processor');
    return processor && 
           processor.type === 'function' && 
           processor.outputs === 4;
});

// Test 8: Check encoder processor exists
runTest('Encoder Data Processor Exists', () => {
    const processor = flows.find(node => node.id === 'encoder-processor');
    return processor && 
           processor.type === 'function' && 
           processor.outputs === 4;
});

// Test 9: Check robot status processor exists
runTest('Robot Status Processor Exists', () => {
    const processor = flows.find(node => node.id === 'robot-status-processor');
    return processor && 
           processor.type === 'function' && 
           processor.outputs === 5;
});

// Test 10: Check safety status processor exists
runTest('Safety Status Processor Exists', () => {
    const processor = flows.find(node => node.id === 'safety-status-processor');
    return processor && 
           processor.type === 'function' && 
           processor.outputs === 4;
});

// Test 11: Check system status processor exists
runTest('System Status Processor Exists', () => {
    const processor = flows.find(node => node.id === 'system-status-processor');
    return processor && 
           processor.type === 'function' && 
           processor.outputs === 5;
});

// Test 12: Check UI groups exist
runTest('UI Groups for Telemetry Display', () => {
    const requiredGroups = [
        'ui-group-robot-status',
        'ui-group-sensor-data', 
        'ui-group-lidar-display',
        'ui-group-system-logs'
    ];
    
    return requiredGroups.every(groupId => 
        flows.some(node => node.id === groupId && node.type === 'ui_group')
    );
});

// Test 13: Check LiDAR visualization widgets exist
runTest('LiDAR Visualization Widgets', () => {
    const lidarWidgets = [
        'ui-lidar-min-range',
        'ui-lidar-avg-range', 
        'ui-lidar-closest-obstacle',
        'ui-lidar-canvas'
    ];
    
    return lidarWidgets.every(widgetId => 
        flows.some(node => node.id === widgetId)
    );
});

// Test 14: Check robot status widgets exist
runTest('Robot Status Widgets', () => {
    const statusWidgets = [
        'ui-robot-status',
        'ui-robot-position',
        'ui-robot-heading',
        'ui-mission-status'
    ];
    
    return statusWidgets.every(widgetId => 
        flows.some(node => node.id === widgetId)
    );
});

// Test 15: Check sensor data widgets exist
runTest('Sensor Data Widgets', () => {
    const sensorWidgets = [
        'ui-distance-traveled',
        'ui-linear-velocity',
        'ui-angular-velocity',
        'ui-safety-alert'
    ];
    
    return sensorWidgets.every(widgetId => 
        flows.some(node => node.id === widgetId)
    );
});

// Test 16: Check system monitoring widgets exist
runTest('System Monitoring Widgets', () => {
    const systemWidgets = [
        'ui-system-status',
        'ui-memory-usage',
        'ui-cpu-usage',
        'ui-system-logs'
    ];
    
    return systemWidgets.every(widgetId => 
        flows.some(node => node.id === widgetId)
    );
});

// Test 17: Check debug nodes exist
runTest('Debug Nodes for Telemetry', () => {
    const debugNodes = [
        'encoder-debug',
        'robot-status-debug',
        'safety-status-debug',
        'system-status-debug'
    ];
    
    return debugNodes.every(nodeId => 
        flows.some(node => node.id === nodeId && node.type === 'debug')
    );
});

// Test 18: Check LiDAR canvas has proper template
runTest('LiDAR Canvas Template Validation', () => {
    const canvas = flows.find(node => node.id === 'ui-lidar-canvas');
    return canvas && 
           canvas.type === 'ui_template' &&
           canvas.format.includes('canvas') &&
           canvas.format.includes('lidarCanvas');
});

// Test 19: Check system logs template
runTest('System Logs Template Validation', () => {
    const logs = flows.find(node => node.id === 'ui-system-logs');
    return logs && 
           logs.type === 'ui_template' &&
           logs.format.includes('ng-repeat') &&
           logs.format.includes('log in msg.payload');
});

// Test 20: Check flow connections (data flow)
runTest('Data Flow Connections', () => {
    const dataSubscriber = flows.find(node => node.id === 'mqtt-data-subscriber');
    const dataRouter = flows.find(node => node.id === 'data-router');
    
    return dataSubscriber && 
           dataRouter &&
           dataSubscriber.wires[0].includes('data-router');
});

// Test 21: Check flow connections (status flow)
runTest('Status Flow Connections', () => {
    const statusSubscriber = flows.find(node => node.id === 'mqtt-status-subscriber');
    const statusRouter = flows.find(node => node.id === 'status-router');
    
    return statusSubscriber && 
           statusRouter &&
           statusSubscriber.wires[0].includes('status-router');
});

// Test 22: Validate LiDAR processor function code
runTest('LiDAR Processor Function Logic', () => {
    const processor = flows.find(node => node.id === 'lidar-processor');
    const func = processor.func;
    
    return func.includes('ranges') && 
           func.includes('angles') &&
           func.includes('minRange') &&
           func.includes('flow.set');
});

// Test 23: Validate robot status processor function code
runTest('Robot Status Processor Function Logic', () => {
    const processor = flows.find(node => node.id === 'robot-status-processor');
    const func = processor.func;
    
    return func.includes('position') && 
           func.includes('status') &&
           func.includes('mission') &&
           func.includes('getStatusColor');
});

// Test 24: Check log refresh timer
runTest('Log Refresh Timer Configuration', () => {
    const timer = flows.find(node => node.id === 'log-refresh-timer');
    return timer && 
           timer.type === 'inject' &&
           timer.repeat === '5';
});

console.log('\n' + '=' .repeat(60));
console.log(`📊 Test Results: ${testsPassed}/${testsTotal} tests passed`);

if (testsPassed === testsTotal) {
    console.log('🎉 All telemetry flow tests passed! Implementation is complete.');
} else {
    console.log(`⚠️  ${testsTotal - testsPassed} tests failed. Please review the implementation.`);
}

// Additional validation: Check for required MQTT topics
console.log('\n📡 MQTT Topic Coverage:');
const requiredTopics = [
    'orchestrator/data/+',
    'orchestrator/status/+'
];

requiredTopics.forEach(topic => {
    const hasSubscriber = flows.some(node => 
        node.type === 'mqtt in' && node.topic === topic
    );
    console.log(`${hasSubscriber ? '✅' : '❌'} ${topic}`);
});

// Check UI organization
console.log('\n🎨 UI Organization:');
const uiTabs = flows.filter(node => node.type === 'ui_tab');
const uiGroups = flows.filter(node => node.type === 'ui_group');
const uiWidgets = flows.filter(node => node.type && node.type.startsWith('ui_'));

console.log(`📋 UI Tabs: ${uiTabs.length}`);
console.log(`📦 UI Groups: ${uiGroups.length}`);
console.log(`🎛️  UI Widgets: ${uiWidgets.length}`);

uiTabs.forEach(tab => {
    console.log(`  📋 ${tab.name} (${tab.icon || 'no icon'})`);
});

console.log('\n✨ Telemetry flows validation complete!');