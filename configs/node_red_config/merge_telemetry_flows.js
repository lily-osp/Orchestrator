#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Read the main flows file
const mainFlowsPath = 'configs/node_red_config/flows.json';
const mainFlows = JSON.parse(fs.readFileSync(mainFlowsPath, 'utf8'));

// Read the telemetry components
const telemetryFlowsPath = 'configs/node_red_config/telemetry_flows_addition.json';
const telemetryWidgetsPath = 'configs/node_red_config/telemetry_ui_widgets.json';
const telemetryDebugPath = 'configs/node_red_config/telemetry_debug_nodes.json';

const telemetryFlows = JSON.parse(fs.readFileSync(telemetryFlowsPath, 'utf8'));
const telemetryWidgets = JSON.parse(fs.readFileSync(telemetryWidgetsPath, 'utf8'));
const telemetryDebug = JSON.parse(fs.readFileSync(telemetryDebugPath, 'utf8'));

// Merge all components
const mergedFlows = [
    ...mainFlows,
    ...telemetryFlows,
    ...telemetryWidgets,
    ...telemetryDebug
];

// Write the merged flows back to the main file
fs.writeFileSync(mainFlowsPath, JSON.stringify(mergedFlows, null, 4));

console.log('Successfully merged telemetry flows into main flows.json');
console.log(`Total nodes: ${mergedFlows.length}`);

// Clean up temporary files
fs.unlinkSync(telemetryFlowsPath);
fs.unlinkSync(telemetryWidgetsPath);
fs.unlinkSync(telemetryDebugPath);

console.log('Cleaned up temporary files');