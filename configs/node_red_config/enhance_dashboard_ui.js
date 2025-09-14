#!/usr/bin/env node

/**
 * Dashboard UI Enhancement Script
 * 
 * This script enhances the existing Node-RED flows with:
 * - Glassmorphism dark theme styling
 * - Improved layout and organization
 * - Enhanced LiDAR visualization
 * - Better status displays and controls
 * - Mission parameter controls
 */

const fs = require('fs');
const path = require('path');

// Load existing flows
const flowsPath = path.join(__dirname, 'flows.json');
const flows = JSON.parse(fs.readFileSync(flowsPath, 'utf8'));

console.log('🎨 Enhancing Dashboard UI...');

// Enhanced theme configuration with glassmorphism
const enhancedTheme = {
    "name": "theme-dark",
    "lightTheme": {
        "default": "#0094CE",
        "baseColor": "#0094CE",
        "baseFont": "-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Oxygen-Sans,Ubuntu,Cantarell,Helvetica Neue,sans-serif",
        "edited": true,
        "reset": false
    },
    "darkTheme": {
        "default": "#1a1a2e",
        "baseColor": "#1a1a2e", 
        "baseFont": "-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Oxygen-Sans,Ubuntu,Cantarell,Helvetica Neue,sans-serif",
        "edited": true,
        "reset": false
    },
    "customTheme": {
        "name": "Orchestrator Glassmorphism",
        "default": "#1a1a2e",
        "baseColor": "#1a1a2e",
        "baseFont": "-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Oxygen-Sans,Ubuntu,Cantarell,Helvetica Neue,sans-serif"
    },
    "themeState": {
        "base-color": {
            "default": "#1a1a2e",
            "value": "#1a1a2e",
            "edited": true
        },
        "page-titlebar-backgroundColor": {
            "value": "rgba(26, 26, 46, 0.95)",
            "edited": true
        },
        "page-backgroundColor": {
            "value": "#0c0c1d",
            "edited": true
        },
        "page-sidebar-backgroundColor": {
            "value": "rgba(22, 33, 62, 0.8)",
            "edited": true
        },
        "group-textColor": {
            "value": "#e0e6ed",
            "edited": true
        },
        "group-borderColor": {
            "value": "rgba(255, 255, 255, 0.1)",
            "edited": true
        },
        "group-backgroundColor": {
            "value": "rgba(255, 255, 255, 0.05)",
            "edited": true
        },
        "widget-textColor": {
            "value": "#ffffff",
            "edited": true
        },
        "widget-backgroundColor": {
            "value": "rgba(255, 255, 255, 0.1)",
            "edited": true
        },
        "widget-borderColor": {
            "value": "rgba(255, 255, 255, 0.2)",
            "edited": true
        },
        "base-font": {
            "value": "-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Oxygen-Sans,Ubuntu,Cantarell,Helvetica Neue,sans-serif"
        }
    },
    "angularTheme": {
        "primary": "indigo",
        "accents": "blue", 
        "warn": "red",
        "background": "grey",
        "palette": "colours"
    }
};

// Enhanced site configuration
const enhancedSite = {
    "name": "🤖 Orchestrator Platform",
    "hideToolbar": "false",
    "allowSwipe": "false", 
    "lockMenu": "false",
    "allowTempTheme": "true",
    "dateFormat": "DD/MM/YYYY HH:mm:ss",
    "sizes": {
        "sx": 48,
        "sy": 48,
        "gx": 6,
        "gy": 6,
        "cx": 6,
        "cy": 6,
        "px": 2,
        "py": 2
    }
};

// Find and update the dashboard UI config
const dashboardConfig = flows.find(node => node.id === 'dashboard-ui-config');
if (dashboardConfig) {
    dashboardConfig.theme = enhancedTheme;
    dashboardConfig.site = enhancedSite;
    console.log('✅ Updated dashboard theme and site configuration');
}

// Add custom CSS for glassmorphism effects
const customCssNode = {
    "id": "ui-custom-css",
    "type": "ui_template",
    "z": "main-flow-tab",
    "group": "",
    "name": "Custom CSS - Glassmorphism",
    "order": 0,
    "width": 0,
    "height": 0,
    "format": `<style>
/* Glassmorphism Dashboard Styling */
body {
    background: linear-gradient(135deg, #0c0c1d 0%, #1a1a2e 50%, #16213e 100%);
    background-attachment: fixed;
}

/* Glass effect for groups */
.nr-dashboard-cardpanel {
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 15px !important;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37) !important;
}

/* Enhanced buttons with glassmorphism */
.nr-dashboard-button {
    background: rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
}

.nr-dashboard-button:hover {
    background: rgba(255, 255, 255, 0.2) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3) !important;
}

/* Emergency stop special styling */
.emergency-stop {
    background: rgba(204, 0, 0, 0.3) !important;
    border: 2px solid #cc0000 !important;
    animation: pulse 2s infinite !important;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(204, 0, 0, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(204, 0, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(204, 0, 0, 0); }
}

/* Gauge enhancements */
.nr-dashboard-gauge {
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 15px !important;
    backdrop-filter: blur(10px) !important;
}

/* Text displays with glass effect */
.nr-dashboard-text {
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 8px !important;
    backdrop-filter: blur(5px) !important;
    padding: 10px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* Slider enhancements */
.nr-dashboard-slider {
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 10px !important;
    backdrop-filter: blur(10px) !important;
}

/* Tab styling */
.md-tab {
    background: rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px) !important;
}

/* LiDAR canvas container */
.lidar-container {
    background: rgba(0, 0, 0, 0.3) !important;
    border-radius: 15px !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    padding: 15px !important;
}

/* Status indicators */
.status-active { color: #4CAF50 !important; }
.status-idle { color: #2196F3 !important; }
.status-warning { color: #FF9800 !important; }
.status-error { color: #F44336 !important; }
.status-emergency { color: #CC0000 !important; animation: blink 1s infinite; }

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0.3; }
}

/* Mission status styling */
.mission-in-progress { color: #4CAF50; font-weight: bold; }
.mission-paused { color: #FF9800; font-weight: bold; }
.mission-completed { color: #2196F3; font-weight: bold; }
.mission-failed { color: #F44336; font-weight: bold; }

/* System logs styling */
.system-logs {
    background: rgba(0, 0, 0, 0.5) !important;
    border-radius: 10px !important;
    font-family: 'Courier New', monospace !important;
    max-height: 300px !important;
    overflow-y: auto !important;
}

.log-error { color: #F44336; }
.log-warning { color: #FF9800; }
.log-info { color: #4CAF50; }
.log-debug { color: #9E9E9E; }
</style>`,
    "storeOutMessages": false,
    "fwdInMessages": false,
    "resendOnRefresh": false,
    "templateScope": "global",
    "className": "",
    "x": 150,
    "y": 400,
    "wires": [[]]
};

// Add the custom CSS node if it doesn't exist
if (!flows.find(node => node.id === 'ui-custom-css')) {
    flows.push(customCssNode);
    console.log('✅ Added custom CSS for glassmorphism effects');
}

// Add mission parameters group and controls
const missionParamsGroup = {
    "id": "ui-group-mission-params",
    "type": "ui_group",
    "name": "Mission Parameters",
    "tab": "ui-tab-control",
    "order": 4,
    "disp": true,
    "width": "12",
    "collapse": false,
    "className": ""
};

if (!flows.find(node => node.id === 'ui-group-mission-params')) {
    flows.push(missionParamsGroup);
    console.log('✅ Added Mission Parameters group');
}

// Enhanced LiDAR visualization template
const enhancedLidarTemplate = {
    "id": "ui-lidar-canvas-enhanced",
    "type": "ui_template",
    "z": "telemetry-flows-tab",
    "group": "ui-group-lidar-display",
    "name": "Enhanced LiDAR Visualization",
    "order": 1,
    "width": 12,
    "height": 8,
    "format": `<div class="lidar-container">
    <canvas id="lidarCanvas" width="600" height="400" style="border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; background: rgba(0,0,0,0.3);"></canvas>
    <div style="margin-top: 10px; display: flex; justify-content: space-between; color: #e0e6ed; font-size: 12px;">
        <span id="scanInfo">Scan Points: 0</span>
        <span id="rangeInfo">Range: 0.0m - 0.0m</span>
        <span id="obstacleInfo">Closest: N/A</span>
    </div>
</div>

<script>
(function(scope) {
    const canvas = document.getElementById('lidarCanvas');
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const maxRange = 5.0; // 5 meter max display range
    const scale = Math.min(centerX, centerY) * 0.8 / maxRange;
    
    let lastScanData = null;
    
    function drawBackground() {
        // Clear canvas with dark background
        ctx.fillStyle = 'rgba(12, 12, 29, 0.9)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw range rings
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.lineWidth = 1;
        for (let i = 1; i <= 5; i++) {
            ctx.beginPath();
            ctx.arc(centerX, centerY, i * scale, 0, 2 * Math.PI);
            ctx.stroke();
            
            // Range labels
            ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.font = '10px Arial';
            ctx.fillText(i + 'm', centerX + i * scale + 5, centerY - 5);
        }
        
        // Draw crosshairs
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, centerY);
        ctx.lineTo(canvas.width, centerY);
        ctx.moveTo(centerX, 0);
        ctx.lineTo(centerX, canvas.height);
        ctx.stroke();
        
        // Draw robot at center
        ctx.fillStyle = '#4CAF50';
        ctx.beginPath();
        ctx.arc(centerX, centerY, 8, 0, 2 * Math.PI);
        ctx.fill();
        
        // Robot direction indicator
        ctx.strokeStyle = '#4CAF50';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(centerX, centerY - 15);
        ctx.stroke();
    }
    
    function drawLidarScan(scanData) {
        if (!scanData || !scanData.ranges || !scanData.angles) return;
        
        drawBackground();
        
        const ranges = scanData.ranges;
        const angles = scanData.angles;
        let minRange = Infinity;
        let maxRange = 0;
        let closestPoint = null;
        let closestDistance = Infinity;
        
        // Draw scan points
        ctx.fillStyle = '#F44336';
        for (let i = 0; i < ranges.length && i < angles.length; i++) {
            const range = ranges[i];
            const angle = angles[i];
            
            if (range > 0 && range <= maxRange) {
                // Convert polar to cartesian (angle in degrees, 0 = forward)
                const angleRad = (angle - 90) * Math.PI / 180; // Adjust for canvas coordinates
                const x = centerX + range * scale * Math.cos(angleRad);
                const y = centerY + range * scale * Math.sin(angleRad);
                
                // Draw point
                ctx.beginPath();
                ctx.arc(x, y, 3, 0, 2 * Math.PI);
                ctx.fill();
                
                // Track statistics
                minRange = Math.min(minRange, range);
                maxRange = Math.max(maxRange, range);
                
                if (range < closestDistance) {
                    closestDistance = range;
                    closestPoint = { range: range, angle: angle };
                }
            }
        }
        
        // Highlight closest obstacle
        if (closestPoint && closestDistance < 2.0) {
            const angleRad = (closestPoint.angle - 90) * Math.PI / 180;
            const x = centerX + closestPoint.range * scale * Math.cos(angleRad);
            const y = centerY + closestPoint.range * scale * Math.sin(angleRad);
            
            ctx.strokeStyle = '#FF9800';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(x, y, 8, 0, 2 * Math.PI);
            ctx.stroke();
            
            // Draw line to closest obstacle
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.lineTo(x, y);
            ctx.stroke();
        }
        
        // Update info displays
        document.getElementById('scanInfo').textContent = \`Scan Points: \${ranges.length}\`;
        document.getElementById('rangeInfo').textContent = \`Range: \${minRange.toFixed(1)}m - \${maxRange.toFixed(1)}m\`;
        document.getElementById('obstacleInfo').textContent = closestPoint ? 
            \`Closest: \${closestPoint.range.toFixed(2)}m @ \${closestPoint.angle.toFixed(0)}°\` : 'Closest: N/A';
    }
    
    // Listen for LiDAR data updates
    scope.$watch('msg', function(msg) {
        if (msg && msg.payload) {
            try {
                const data = typeof msg.payload === 'string' ? JSON.parse(msg.payload) : msg.payload;
                if (data.ranges && data.angles) {
                    lastScanData = data;
                    drawLidarScan(data);
                }
            } catch (e) {
                console.error('Error parsing LiDAR data:', e);
            }
        }
    });
    
    // Initial draw
    drawBackground();
    
    // Redraw on canvas resize
    window.addEventListener('resize', function() {
        if (lastScanData) {
            drawLidarScan(lastScanData);
        } else {
            drawBackground();
        }
    });
    
})(scope);
</script>`,
    "storeOutMessages": false,
    "fwdInMessages": false,
    "resendOnRefresh": true,
    "templateScope": "local",
    "className": "",
    "x": 620,
    "y": 1200,
    "wires": [[]]
};

// Replace existing LiDAR canvas if it exists
const existingLidarCanvas = flows.findIndex(node => node.id === 'ui-lidar-canvas');
if (existingLidarCanvas !== -1) {
    flows[existingLidarCanvas] = enhancedLidarTemplate;
    console.log('✅ Enhanced LiDAR visualization canvas');
} else {
    flows.push(enhancedLidarTemplate);
    console.log('✅ Added enhanced LiDAR visualization canvas');
}

// Add mission parameter controls
const missionParams = [
    {
        "id": "ui-mission-name-input",
        "type": "ui_text_input",
        "z": "command-flows-tab",
        "name": "Mission Name",
        "label": "Mission Name",
        "tooltip": "Enter mission name",
        "group": "ui-group-mission-params",
        "order": 1,
        "width": 6,
        "height": 1,
        "passthru": true,
        "mode": "text",
        "delay": 300,
        "topic": "mission_name",
        "sendOnBlur": true,
        "className": "",
        "topicType": "str",
        "x": 150,
        "y": 800,
        "wires": [["mission-param-storage"]]
    },
    {
        "id": "ui-waypoint-count-slider",
        "type": "ui_slider",
        "z": "command-flows-tab",
        "name": "Waypoint Count",
        "label": "Waypoints",
        "tooltip": "Number of waypoints in mission",
        "group": "ui-group-mission-params",
        "order": 2,
        "width": 3,
        "height": 1,
        "passthru": true,
        "outs": "end",
        "topic": "waypoint_count",
        "topicType": "str",
        "min": 1,
        "max": 10,
        "step": 1,
        "className": "",
        "x": 150,
        "y": 840,
        "wires": [["mission-param-storage"]]
    },
    {
        "id": "ui-mission-timeout-slider",
        "type": "ui_slider",
        "z": "command-flows-tab",
        "name": "Mission Timeout",
        "label": "Timeout (min)",
        "tooltip": "Mission timeout in minutes",
        "group": "ui-group-mission-params",
        "order": 3,
        "width": 3,
        "height": 1,
        "passthru": true,
        "outs": "end",
        "topic": "mission_timeout",
        "topicType": "str",
        "min": 1,
        "max": 60,
        "step": 1,
        "className": "",
        "x": 150,
        "y": 880,
        "wires": [["mission-param-storage"]]
    }
];

// Add mission parameter controls if they don't exist
missionParams.forEach(param => {
    if (!flows.find(node => node.id === param.id)) {
        flows.push(param);
        console.log(`✅ Added ${param.name} control`);
    }
});

// Add mission parameter storage function
const missionParamStorage = {
    "id": "mission-param-storage",
    "type": "function",
    "z": "command-flows-tab",
    "name": "Mission Parameter Storage",
    "func": `// Store mission parameters in flow context
const param = msg.topic;
const value = msg.payload;

// Store the parameter
flow.set(param, value);

// Log the parameter update
node.log(\`Mission parameter updated: \${param} = \${value}\`);

// Get all current parameters
const params = {
    mission_name: flow.get('mission_name') || 'Default Mission',
    waypoint_count: flow.get('waypoint_count') || 3,
    mission_timeout: flow.get('mission_timeout') || 10,
    distance: flow.get('distance') || 10,
    angle: flow.get('angle') || 90,
    speed: flow.get('speed') || 0.5
};

// Send updated parameters to status display
msg.payload = params;
msg.topic = 'mission_parameters';

return msg;`,
    "outputs": 1,
    "noerr": 0,
    "initialize": "",
    "finalize": "",
    "libs": [],
    "x": 400,
    "y": 840,
    "wires": [["mission-params-display"]]
};

if (!flows.find(node => node.id === 'mission-param-storage')) {
    flows.push(missionParamStorage);
    console.log('✅ Added mission parameter storage function');
}

// Add mission parameters display
const missionParamsDisplay = {
    "id": "mission-params-display",
    "type": "ui_template",
    "z": "command-flows-tab",
    "group": "ui-group-mission-params",
    "name": "Mission Parameters Display",
    "order": 4,
    "width": 12,
    "height": 3,
    "format": `<div style="background: rgba(255,255,255,0.05); border-radius: 10px; padding: 15px; backdrop-filter: blur(10px);">
    <h4 style="color: #e0e6ed; margin-top: 0;">Current Mission Parameters</h4>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; color: #ffffff;">
        <div>
            <strong>Mission:</strong><br>
            <span id="missionName">Default Mission</span>
        </div>
        <div>
            <strong>Waypoints:</strong><br>
            <span id="waypointCount">3</span>
        </div>
        <div>
            <strong>Timeout:</strong><br>
            <span id="missionTimeout">10</span> min
        </div>
        <div>
            <strong>Distance:</strong><br>
            <span id="moveDistance">10</span> cm
        </div>
        <div>
            <strong>Angle:</strong><br>
            <span id="rotateAngle">90</span>°
        </div>
        <div>
            <strong>Speed:</strong><br>
            <span id="moveSpeed">0.5</span>
        </div>
    </div>
</div>

<script>
(function(scope) {
    scope.$watch('msg', function(msg) {
        if (msg && msg.payload && typeof msg.payload === 'object') {
            const params = msg.payload;
            
            if (params.mission_name !== undefined) {
                document.getElementById('missionName').textContent = params.mission_name;
            }
            if (params.waypoint_count !== undefined) {
                document.getElementById('waypointCount').textContent = params.waypoint_count;
            }
            if (params.mission_timeout !== undefined) {
                document.getElementById('missionTimeout').textContent = params.mission_timeout;
            }
            if (params.distance !== undefined) {
                document.getElementById('moveDistance').textContent = params.distance;
            }
            if (params.angle !== undefined) {
                document.getElementById('rotateAngle').textContent = params.angle;
            }
            if (params.speed !== undefined) {
                document.getElementById('moveSpeed').textContent = params.speed.toFixed(1);
            }
        }
    });
})(scope);
</script>`,
    "storeOutMessages": false,
    "fwdInMessages": false,
    "resendOnRefresh": true,
    "templateScope": "local",
    "className": "",
    "x": 620,
    "y": 840,
    "wires": [[]]
};

if (!flows.find(node => node.id === 'mission-params-display')) {
    flows.push(missionParamsDisplay);
    console.log('✅ Added mission parameters display');
}

// Update button styling for glassmorphism
const buttons = flows.filter(node => node.type === 'ui_button');
buttons.forEach(button => {
    if (button.id === 'ui-emergency-stop-btn') {
        button.className = 'emergency-stop';
    } else {
        button.className = 'glass-button';
    }
});

console.log(`✅ Updated ${buttons.length} buttons with glassmorphism styling`);

// Save the enhanced flows
fs.writeFileSync(flowsPath, JSON.stringify(flows, null, 2));
console.log('🎉 Dashboard UI enhancement complete!');
console.log('📁 Enhanced flows saved to flows.json');
console.log('🚀 Restart Node-RED to see the changes');

console.log('\n📋 Enhancement Summary:');
console.log('✅ Applied glassmorphism dark theme');
console.log('✅ Enhanced LiDAR visualization with real-time canvas');
console.log('✅ Added mission parameter controls');
console.log('✅ Improved button and widget styling');
console.log('✅ Added custom CSS for glass effects');
console.log('✅ Enhanced status displays with color coding');