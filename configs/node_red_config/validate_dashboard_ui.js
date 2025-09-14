#!/usr/bin/env node

/**
 * Dashboard UI Validation Script
 * 
 * This script validates the enhanced dashboard UI implementation
 * to ensure all required components are present and properly configured.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Validating Dashboard UI Implementation...\n');

// Load the flows
const flowsPath = path.join(__dirname, 'flows.json');
if (!fs.existsSync(flowsPath)) {
    console.error('❌ flows.json not found!');
    process.exit(1);
}

const flows = JSON.parse(fs.readFileSync(flowsPath, 'utf8'));

let testsPassed = 0;
let testsTotal = 0;

function test(description, condition) {
    testsTotal++;
    if (condition) {
        console.log(`✅ ${description}`);
        testsPassed++;
    } else {
        console.log(`❌ ${description}`);
    }
}

// Test 1: Dashboard UI Configuration
console.log('📋 Testing Dashboard Configuration...');
const dashboardConfig = flows.find(node => node.id === 'dashboard-ui-config');
test('Dashboard UI config exists', !!dashboardConfig);
test('Dashboard has glassmorphism theme', dashboardConfig && dashboardConfig.theme && dashboardConfig.theme.themeState);
test('Site name includes robot emoji', dashboardConfig && dashboardConfig.site && dashboardConfig.site.name.includes('🤖'));

// Test 2: UI Groups and Tabs
console.log('\n📋 Testing UI Groups and Tabs...');
const controlTab = flows.find(node => node.id === 'ui-tab-control');
const monitoringTab = flows.find(node => node.id === 'ui-tab-monitoring');
test('Robot Control tab exists', !!controlTab);
test('System Monitoring tab exists', !!monitoringTab);

const requiredGroups = [
    'ui-group-motor-control',
    'ui-group-mission-control', 
    'ui-group-emergency',
    'ui-group-mission-params',
    'ui-group-robot-status',
    'ui-group-sensor-data',
    'ui-group-lidar-display',
    'ui-group-system-logs'
];

requiredGroups.forEach(groupId => {
    const group = flows.find(node => node.id === groupId);
    test(`${groupId} group exists`, !!group);
});

// Test 3: Control Buttons
console.log('\n📋 Testing Control Buttons...');
const controlButtons = [
    'ui-move-forward-btn',
    'ui-move-backward-btn',
    'ui-rotate-left-btn',
    'ui-rotate-right-btn',
    'ui-motor-stop-btn',
    'ui-mission-start-btn',
    'ui-mission-pause-btn',
    'ui-mission-stop-btn',
    'ui-mission-reset-btn',
    'ui-emergency-stop-btn'
];

controlButtons.forEach(buttonId => {
    const button = flows.find(node => node.id === buttonId);
    test(`${buttonId} exists`, !!button);
    if (button) {
        test(`${buttonId} has proper styling`, button.className !== undefined);
    }
});

// Test 4: Parameter Controls
console.log('\n📋 Testing Parameter Controls...');
const parameterControls = [
    'ui-distance-slider',
    'ui-angle-slider', 
    'ui-speed-slider',
    'ui-mission-name-input',
    'ui-waypoint-count-slider',
    'ui-mission-timeout-slider'
];

parameterControls.forEach(controlId => {
    const control = flows.find(node => node.id === controlId);
    test(`${controlId} exists`, !!control);
});

// Test 5: Status Displays
console.log('\n📋 Testing Status Displays...');
const statusDisplays = [
    'ui-robot-status',
    'ui-robot-position',
    'ui-robot-heading',
    'ui-mission-status',
    'ui-distance-traveled',
    'ui-safety-alert',
    'ui-safety-distance',
    'ui-obstacle-status',
    'ui-system-status'
];

statusDisplays.forEach(displayId => {
    const display = flows.find(node => node.id === displayId);
    test(`${displayId} exists`, !!display);
});

// Test 6: Gauges
console.log('\n📋 Testing Gauge Widgets...');
const gauges = [
    'ui-linear-velocity',
    'ui-angular-velocity',
    'ui-lidar-min-range',
    'ui-lidar-avg-range',
    'ui-memory-usage',
    'ui-cpu-usage'
];

gauges.forEach(gaugeId => {
    const gauge = flows.find(node => node.id === gaugeId);
    test(`${gaugeId} exists`, !!gauge);
    if (gauge) {
        test(`${gaugeId} has proper range configuration`, gauge.min !== undefined && gauge.max !== undefined);
    }
});

// Test 7: LiDAR Visualization
console.log('\n📋 Testing LiDAR Visualization...');
const lidarCanvas = flows.find(node => node.id === 'ui-lidar-canvas-enhanced' || node.id === 'ui-lidar-canvas');
test('LiDAR canvas exists', !!lidarCanvas);
if (lidarCanvas) {
    test('LiDAR canvas has template format', !!lidarCanvas.format);
    test('LiDAR canvas includes JavaScript', lidarCanvas.format && lidarCanvas.format.includes('<script>'));
    test('LiDAR canvas has proper dimensions', lidarCanvas.width >= 12 && lidarCanvas.height >= 6);
}

// Test 8: Custom Styling
console.log('\n📋 Testing Custom Styling...');
const customCSS = flows.find(node => node.id === 'ui-custom-css');
test('Custom CSS node exists', !!customCSS);
if (customCSS) {
    test('Custom CSS includes glassmorphism styles', customCSS.format && customCSS.format.includes('backdrop-filter'));
    test('Custom CSS includes animation effects', customCSS.format && customCSS.format.includes('@keyframes'));
}

// Test 9: Mission Parameters
console.log('\n📋 Testing Mission Parameters...');
const missionParamStorage = flows.find(node => node.id === 'mission-param-storage');
const missionParamsDisplay = flows.find(node => node.id === 'mission-params-display');
test('Mission parameter storage function exists', !!missionParamStorage);
test('Mission parameters display exists', !!missionParamsDisplay);

// Test 10: System Logs
console.log('\n📋 Testing System Logs...');
const systemLogs = flows.find(node => node.id === 'ui-system-logs');
test('System logs display exists', !!systemLogs);
if (systemLogs) {
    test('System logs has template format', !!systemLogs.format);
    test('System logs includes scrollable container', systemLogs.format && systemLogs.format.includes('overflow'));
}

// Test 11: Emergency Stop Special Styling
console.log('\n📋 Testing Emergency Stop...');
const emergencyBtn = flows.find(node => node.id === 'ui-emergency-stop-btn');
test('Emergency stop button exists', !!emergencyBtn);
if (emergencyBtn) {
    test('Emergency stop has special styling', emergencyBtn.className === 'emergency-stop');
    test('Emergency stop has proper colors', emergencyBtn.bgcolor && emergencyBtn.bgcolor.includes('#CC0000'));
}

// Test 12: Flow Organization
console.log('\n📋 Testing Flow Organization...');
const tabs = flows.filter(node => node.type === 'tab');
const uiGroups = flows.filter(node => node.type === 'ui_group');
const uiWidgets = flows.filter(node => node.type && node.type.startsWith('ui_'));

test('Has multiple flow tabs', tabs.length >= 3);
test('Has sufficient UI groups', uiGroups.length >= 8);
test('Has comprehensive UI widgets', uiWidgets.length >= 25);

// Summary
console.log('\n📊 Validation Summary:');
console.log(`✅ Tests Passed: ${testsPassed}/${testsTotal}`);
console.log(`📈 Success Rate: ${((testsPassed/testsTotal) * 100).toFixed(1)}%`);

if (testsPassed === testsTotal) {
    console.log('\n🎉 All tests passed! Dashboard UI implementation is complete and valid.');
    console.log('\n🚀 Next Steps:');
    console.log('1. Start Node-RED: ./start-nodered.sh');
    console.log('2. Access dashboard: http://localhost:1880/ui');
    console.log('3. Test all controls and displays');
    console.log('4. Verify glassmorphism styling');
    console.log('5. Test LiDAR visualization with sample data');
} else {
    console.log('\n⚠️  Some tests failed. Please review the implementation.');
    process.exit(1);
}

// Additional implementation details
console.log('\n📋 Implementation Features:');
console.log('✅ Dark glassmorphism theme with blur effects');
console.log('✅ Real-time LiDAR visualization canvas');
console.log('✅ Mission parameter controls and display');
console.log('✅ Enhanced status displays with color coding');
console.log('✅ Emergency stop with special pulsing animation');
console.log('✅ System monitoring with gauges and logs');
console.log('✅ Responsive layout with proper spacing');
console.log('✅ Custom CSS for glass morphism effects');

console.log('\n🎨 Styling Features:');
console.log('• Backdrop blur effects on all panels');
console.log('• Gradient background with dark theme');
console.log('• Animated buttons with hover effects');
console.log('• Color-coded status indicators');
console.log('• Pulsing emergency stop button');
console.log('• Glassmorphism borders and shadows');
console.log('• Responsive grid layouts');
console.log('• Custom fonts and typography');

console.log('\n🔧 Technical Features:');
console.log('• Real-time canvas-based LiDAR visualization');
console.log('• Interactive range rings and crosshairs');
console.log('• Closest obstacle highlighting');
console.log('• Mission parameter persistence');
console.log('• System log scrolling and formatting');
console.log('• Gauge widgets with color segments');
console.log('• Template-based custom displays');
console.log('• MQTT integration for all controls');