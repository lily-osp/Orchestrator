#!/usr/bin/env python3
"""
Simple Web Dashboard for Orchestrator Platform

A lightweight web interface for controlling and monitoring the mock HAL
when Node-RED is not available. Provides basic controls and real-time telemetry.
"""

import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add hal_service to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from flask import Flask, render_template_string, request, jsonify
    from flask_socketio import SocketIO, emit
    import paho.mqtt.client as mqtt
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Install with: pip install flask flask-socketio paho-mqtt")


class SimpleDashboard:
    """Simple web dashboard for the Orchestrator platform"""
    
    def __init__(self, mqtt_host="localhost", mqtt_port=1883):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask dependencies not available")
        
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'orchestrator-dashboard-secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # MQTT setup
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        self.mqtt_connected = False
        
        # Data storage
        self.telemetry_data = {}
        self.robot_state = {
            'position': {'x': 0.0, 'y': 0.0},
            'heading': 0.0,
            'velocity': {'linear': 0.0, 'angular': 0.0},
            'status': 'unknown'
        }
        self.lidar_data = {'ranges': [], 'angles': []}
        
        # Setup routes and MQTT
        self._setup_routes()
        self._setup_mqtt()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template_string(DASHBOARD_HTML)
        
        @self.app.route('/api/status')
        def get_status():
            return jsonify({
                'mqtt_connected': self.mqtt_connected,
                'robot_state': self.robot_state,
                'telemetry_count': len(self.telemetry_data),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/command', methods=['POST'])
        def send_command():
            try:
                data = request.get_json()
                device = data.get('device', 'left_motor')
                action = data.get('action', 'stop')
                parameters = data.get('parameters', {})
                
                command = {
                    'timestamp': datetime.now().isoformat(),
                    'command_id': f'web_{int(time.time())}',
                    'action': action,
                    'parameters': parameters
                }
                
                topic = f"orchestrator/cmd/{device}"
                
                if self.mqtt_client and self.mqtt_connected:
                    self.mqtt_client.publish(topic, json.dumps(command))
                    return jsonify({'success': True, 'message': 'Command sent'})
                else:
                    return jsonify({'success': False, 'message': 'MQTT not connected'})
                    
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)})
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
            emit('status', {
                'mqtt_connected': self.mqtt_connected,
                'robot_state': self.robot_state
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")
    
    def _setup_mqtt(self):
        """Setup MQTT client"""
        try:
            self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "web_dashboard")
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
            self.mqtt_client.on_message = self._on_mqtt_message
            
        except Exception as e:
            print(f"Error setting up MQTT: {e}")
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.mqtt_connected = True
            print("✅ Connected to MQTT broker")
            
            # Subscribe to telemetry topics
            client.subscribe("orchestrator/data/+")
            client.subscribe("orchestrator/status/+")
            
            # Emit status update
            self.socketio.emit('mqtt_status', {'connected': True})
        else:
            print(f"❌ MQTT connection failed with code {rc}")
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.mqtt_connected = False
        print("❌ Disconnected from MQTT broker")
        self.socketio.emit('mqtt_status', {'connected': False})
    
    def _on_mqtt_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Store telemetry data
            self.telemetry_data[topic] = {
                'payload': payload,
                'timestamp': time.time()
            }
            
            # Process specific data types
            if 'orchestrator/status/robot' in topic:
                self.robot_state = payload
                self.socketio.emit('robot_state', payload)
            
            elif 'orchestrator/data/lidar' in topic:
                data = payload.get('data', {})
                if data.get('scan_available'):
                    self.lidar_data = {
                        'ranges': data.get('ranges', []),
                        'angles': data.get('angles', [])
                    }
                    self.socketio.emit('lidar_data', self.lidar_data)
            
            elif 'orchestrator/data/' in topic:
                # General telemetry data
                self.socketio.emit('telemetry', {
                    'topic': topic,
                    'data': payload
                })
            
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            return True
        except Exception as e:
            print(f"Error connecting to MQTT: {e}")
            return False
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the dashboard"""
        print(f"🌐 Starting Simple Web Dashboard on http://{host}:{port}")
        
        # Connect to MQTT
        if self.connect_mqtt():
            print("✅ MQTT connection initiated")
        else:
            print("❌ MQTT connection failed")
        
        # Run Flask app
        self.socketio.run(self.app, host=host, port=port, debug=debug)


# HTML Template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orchestrator Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: #ffffff;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #00d4ff, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 15px 25px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ff6b6b;
            animation: pulse 2s infinite;
        }
        
        .status-dot.connected {
            background: #4ecdc4;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .panel {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .panel h3 {
            margin-bottom: 20px;
            color: #00d4ff;
            font-size: 1.3em;
        }
        
        .controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .control-group label {
            font-size: 0.9em;
            color: #cccccc;
        }
        
        .btn {
            background: linear-gradient(45deg, #00d4ff, #0099cc);
            border: none;
            border-radius: 10px;
            padding: 12px 20px;
            color: white;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 212, 255, 0.4);
        }
        
        .btn.danger {
            background: linear-gradient(45deg, #ff6b6b, #cc5555);
        }
        
        .btn.danger:hover {
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
        }
        
        input[type="range"] {
            width: 100%;
            margin: 10px 0;
        }
        
        input[type="number"] {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 5px;
            padding: 8px;
            color: white;
            width: 100%;
        }
        
        .robot-state {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .state-item {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        
        .state-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #00d4ff;
        }
        
        .state-label {
            font-size: 0.9em;
            color: #cccccc;
            margin-top: 5px;
        }
        
        .lidar-canvas {
            width: 100%;
            height: 300px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .telemetry-log {
            height: 200px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.8em;
        }
        
        .log-entry {
            margin-bottom: 5px;
            padding: 5px;
            border-left: 3px solid #00d4ff;
            padding-left: 10px;
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .controls {
                grid-template-columns: 1fr;
            }
            
            .robot-state {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Orchestrator Dashboard</h1>
            <p>Mock Hardware Abstraction Layer Control Interface</p>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <div class="status-dot" id="mqtt-status"></div>
                <span>MQTT: <span id="mqtt-text">Disconnected</span></span>
            </div>
            <div class="status-item">
                <span>Robot Status: <span id="robot-status">Unknown</span></span>
            </div>
            <div class="status-item">
                <span id="timestamp">--:--:--</span>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <div class="panel">
                <h3>🎮 Robot Controls</h3>
                <div class="controls">
                    <div class="control-group">
                        <label>Distance (m)</label>
                        <input type="number" id="distance" value="1.0" step="0.1" min="0.1" max="10">
                    </div>
                    <div class="control-group">
                        <label>Speed (0-1)</label>
                        <input type="range" id="speed" min="0" max="1" step="0.1" value="0.5">
                        <span id="speed-value">0.5</span>
                    </div>
                </div>
                
                <div class="controls" style="margin-top: 20px;">
                    <button class="btn" onclick="sendCommand('move_forward')">⬆️ Forward</button>
                    <button class="btn" onclick="sendCommand('move_backward')">⬇️ Backward</button>
                    <button class="btn" onclick="sendCommand('rotate_left')">↪️ Left</button>
                    <button class="btn" onclick="sendCommand('rotate_right')">↩️ Right</button>
                </div>
                
                <div class="controls" style="margin-top: 20px;">
                    <button class="btn" onclick="sendCommand('stop')">⏹️ Stop</button>
                    <button class="btn danger" onclick="sendEmergencyStop()">🛑 E-Stop</button>
                </div>
            </div>
            
            <div class="panel">
                <h3>📊 Robot State</h3>
                <div class="robot-state">
                    <div class="state-item">
                        <div class="state-value" id="pos-x">0.00</div>
                        <div class="state-label">X Position (m)</div>
                    </div>
                    <div class="state-item">
                        <div class="state-value" id="pos-y">0.00</div>
                        <div class="state-label">Y Position (m)</div>
                    </div>
                    <div class="state-item">
                        <div class="state-value" id="heading">0.00</div>
                        <div class="state-label">Heading (rad)</div>
                    </div>
                    <div class="state-item">
                        <div class="state-value" id="velocity">0.00</div>
                        <div class="state-label">Velocity (m/s)</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <div class="panel">
                <h3>📡 LiDAR Visualization</h3>
                <canvas id="lidar-canvas" class="lidar-canvas"></canvas>
            </div>
            
            <div class="panel">
                <h3>📝 Telemetry Log</h3>
                <div id="telemetry-log" class="telemetry-log"></div>
            </div>
        </div>
    </div>

    <script>
        // Socket.IO connection
        const socket = io();
        
        // Update timestamp
        function updateTimestamp() {
            document.getElementById('timestamp').textContent = new Date().toLocaleTimeString();
        }
        setInterval(updateTimestamp, 1000);
        updateTimestamp();
        
        // Speed slider
        document.getElementById('speed').addEventListener('input', function() {
            document.getElementById('speed-value').textContent = this.value;
        });
        
        // Socket event handlers
        socket.on('connect', function() {
            console.log('Connected to server');
        });
        
        socket.on('mqtt_status', function(data) {
            const statusDot = document.getElementById('mqtt-status');
            const statusText = document.getElementById('mqtt-text');
            
            if (data.connected) {
                statusDot.classList.add('connected');
                statusText.textContent = 'Connected';
            } else {
                statusDot.classList.remove('connected');
                statusText.textContent = 'Disconnected';
            }
        });
        
        socket.on('robot_state', function(data) {
            document.getElementById('robot-status').textContent = data.status || 'Unknown';
            
            if (data.position) {
                document.getElementById('pos-x').textContent = data.position.x.toFixed(2);
                document.getElementById('pos-y').textContent = data.position.y.toFixed(2);
            }
            
            if (data.heading !== undefined) {
                document.getElementById('heading').textContent = data.heading.toFixed(2);
            }
            
            if (data.velocity && data.velocity.linear !== undefined) {
                document.getElementById('velocity').textContent = data.velocity.linear.toFixed(2);
            }
        });
        
        socket.on('lidar_data', function(data) {
            drawLidar(data);
        });
        
        socket.on('telemetry', function(data) {
            addTelemetryLog(data);
        });
        
        // Command functions
        function sendCommand(action) {
            const distance = parseFloat(document.getElementById('distance').value);
            const speed = parseFloat(document.getElementById('speed').value);
            
            let parameters = {};
            
            if (action.includes('move')) {
                parameters = { distance: distance, speed: speed };
            } else if (action.includes('rotate')) {
                parameters = { angle: 90, speed: speed }; // Default 90 degree turn
            }
            
            fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device: 'left_motor',
                    action: action,
                    parameters: parameters
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addTelemetryLog({
                        topic: 'command',
                        data: { message: `Command sent: ${action}`, success: true }
                    });
                } else {
                    addTelemetryLog({
                        topic: 'error',
                        data: { message: `Command failed: ${data.message}`, success: false }
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                addTelemetryLog({
                    topic: 'error',
                    data: { message: `Network error: ${error.message}`, success: false }
                });
            });
        }
        
        function sendEmergencyStop() {
            fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device: 'estop',
                    action: 'emergency_stop',
                    parameters: { reason: 'user_request' }
                })
            })
            .then(response => response.json())
            .then(data => {
                addTelemetryLog({
                    topic: 'emergency',
                    data: { message: 'Emergency stop activated!', success: data.success }
                });
            });
        }
        
        // LiDAR visualization
        function drawLidar(data) {
            const canvas = document.getElementById('lidar-canvas');
            const ctx = canvas.getContext('2d');
            
            // Set canvas size
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
            
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const scale = Math.min(canvas.width, canvas.height) / 20; // 10m range
            
            // Clear canvas
            ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Draw grid
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
            ctx.lineWidth = 1;
            
            for (let i = 1; i <= 10; i++) {
                const radius = i * scale;
                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                ctx.stroke();
            }
            
            // Draw robot
            ctx.fillStyle = '#00d4ff';
            ctx.beginPath();
            ctx.arc(centerX, centerY, 5, 0, 2 * Math.PI);
            ctx.fill();
            
            // Draw LiDAR points
            if (data.ranges && data.angles) {
                ctx.fillStyle = '#ff6b6b';
                
                for (let i = 0; i < data.ranges.length; i++) {
                    const range = data.ranges[i];
                    const angle = data.angles[i] * Math.PI / 180; // Convert to radians
                    
                    if (range > 0.1 && range < 12) { // Valid range
                        const x = centerX + range * scale * Math.cos(angle - Math.PI/2);
                        const y = centerY + range * scale * Math.sin(angle - Math.PI/2);
                        
                        ctx.beginPath();
                        ctx.arc(x, y, 2, 0, 2 * Math.PI);
                        ctx.fill();
                    }
                }
            }
        }
        
        // Telemetry log
        function addTelemetryLog(data) {
            const log = document.getElementById('telemetry-log');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            
            const timestamp = new Date().toLocaleTimeString();
            const topic = data.topic || 'unknown';
            const message = JSON.stringify(data.data || data, null, 2);
            
            entry.innerHTML = `<strong>${timestamp}</strong> [${topic}] ${message}`;
            
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
            
            // Keep only last 50 entries
            while (log.children.length > 50) {
                log.removeChild(log.firstChild);
            }
        }
        
        // Initialize
        drawLidar({ ranges: [], angles: [] });
    </script>
</body>
</html>
"""


def main():
    """Main entry point for the simple dashboard"""
    if not FLASK_AVAILABLE:
        print("❌ Flask dependencies not available")
        print("Install with: pip install flask flask-socketio paho-mqtt")
        return
    
    dashboard = SimpleDashboard()
    
    try:
        dashboard.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")


if __name__ == "__main__":
    main()