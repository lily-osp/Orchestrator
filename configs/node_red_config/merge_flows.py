#!/usr/bin/env python3

import json
import os
from datetime import datetime

def merge_mission_sequencer():
    """Merge mission sequencer flows into main flows.json"""
    
    # Read existing flows
    with open('flows.json', 'r') as f:
        existing_flows = json.load(f)
    
    # Create backup
    backup_name = f'flows_backup_before_mission_sequencer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(backup_name, 'w') as f:
        json.dump(existing_flows, f, indent=2)
    
    print(f"Created backup: {backup_name}")
    
    # Define mission sequencer flows
    mission_sequencer_flows = [
        {
            "id": "mission-sequencer-tab",
            "type": "tab",
            "label": "Mission Sequencer",
            "disabled": False,
            "info": "Mission sequencer flow that executes sequences of commands from JSON array input and manages mission state",
            "env": []
        },
        {
            "id": "ui-group-mission-sequencer",
            "type": "ui_group",
            "name": "Mission Sequencer",
            "tab": "ui-tab-control",
            "order": 5,
            "disp": True,
            "width": "12",
            "collapse": False,
            "className": ""
        },
        {
            "id": "ui-group-mission-status",
            "type": "ui_group",
            "name": "Mission Status",
            "tab": "ui-tab-control",
            "order": 6,
            "disp": True,
            "width": "12",
            "collapse": False,
            "className": ""
        },
        {
            "id": "mission-sequence-input",
            "type": "ui_text_input",
            "z": "mission-sequencer-tab",
            "name": "Mission JSON Input",
            "label": "Mission Sequence (JSON)",
            "tooltip": "Enter mission sequence as JSON array",
            "group": "ui-group-mission-sequencer",
            "order": 1,
            "width": 8,
            "height": 1,
            "passthru": True,
            "mode": "text",
            "delay": 300,
            "topic": "mission_json",
            "sendOnBlur": True,
            "className": "",
            "topicType": "str",
            "x": 150,
            "y": 100,
            "wires": [
                [
                    "mission-json-validator"
                ]
            ]
        },
        {
            "id": "mission-upload-btn",
            "type": "ui_button",
            "z": "mission-sequencer-tab",
            "name": "Upload Mission",
            "group": "ui-group-mission-sequencer",
            "order": 2,
            "width": 4,
            "height": 1,
            "passthru": False,
            "label": "Upload Mission",
            "tooltip": "Upload and validate mission sequence",
            "color": "white",
            "bgcolor": "green",
            "className": "",
            "icon": "upload",
            "payload": "upload",
            "payloadType": "str",
            "topic": "mission_upload",
            "topicType": "str",
            "x": 150,
            "y": 140,
            "wires": [
                [
                    "mission-json-validator"
                ]
            ]
        },
        {
            "id": "mission-json-validator",
            "type": "function",
            "z": "mission-sequencer-tab",
            "name": "Mission JSON Validator",
            "func": """// Validate and process mission JSON input
if (msg.topic === 'mission_upload') {
    // Get the stored JSON from context
    const jsonText = flow.get('mission_json_text') || '[]';
    
    try {
        const sequence = JSON.parse(jsonText);
        
        if (!Array.isArray(sequence)) {
            throw new Error('Mission sequence must be an array');
        }
        
        const validActions = ['move_forward', 'move_backward', 'rotate_left', 'rotate_right', 'stop', 'wait'];
        
        // Validate each step
        for (let i = 0; i < sequence.length; i++) {
            const step = sequence[i];
            
            if (!step.action || !validActions.includes(step.action)) {
                throw new Error(`Step ${i + 1}: Invalid or missing action`);
            }
            
            if (step.action !== 'stop' && step.action !== 'wait' && !step.parameters) {
                throw new Error(`Step ${i + 1}: Missing parameters for action ${step.action}`);
            }
            
            if (!step.timeout || typeof step.timeout !== 'number' || step.timeout <= 0) {
                throw new Error(`Step ${i + 1}: Invalid or missing timeout`);
            }
        }
        
        // Mission is valid - create mission data
        const missionData = {
            sequence: sequence,
            timestamp: new Date().toISOString(),
            mission_id: 'mission_' + Date.now()
        };
        
        // Store the mission sequence in flow context
        flow.set('current_mission', missionData);
        flow.set('mission_state', 'loaded');
        flow.set('current_step', 0);
        flow.set('step_start_time', null);
        
        // Send status update
        const statusMsg = {
            topic: 'orchestrator/status/mission',
            payload: {
                mission_id: missionData.mission_id,
                status: 'loaded',
                total_steps: missionData.sequence.length,
                current_step: 0,
                timestamp: new Date().toISOString()
            }
        };
        
        node.log(`Mission uploaded: ${missionData.mission_id} with ${missionData.sequence.length} steps`);
        return statusMsg;
        
    } catch (error) {
        node.error(`Mission validation failed: ${error.message}`);
        
        const errorMsg = {
            topic: 'orchestrator/status/mission',
            payload: {
                status: 'error',
                error: error.message,
                timestamp: new Date().toISOString()
            }
        };
        
        return errorMsg;
    }
} else if (msg.topic === 'mission_json') {
    // Store the JSON text for later validation
    flow.set('mission_json_text', msg.payload);
    return null;
}

return null;""",
            "outputs": 1,
            "noerr": 0,
            "initialize": "",
            "finalize": "",
            "libs": [],
            "x": 400,
            "y": 120,
            "wires": [
                [
                    "mission-status-publisher"
                ]
            ]
        },
        {
            "id": "mission-cmd-listener",
            "type": "mqtt in",
            "z": "mission-sequencer-tab",
            "name": "Mission Command Listener",
            "topic": "orchestrator/cmd/mission",
            "qos": "1",
            "datatype": "json",
            "broker": "mqtt-broker-config",
            "nl": False,
            "rap": True,
            "rh": 0,
            "inputs": 0,
            "x": 150,
            "y": 200,
            "wires": [
                [
                    "mission-state-manager"
                ]
            ]
        },
        {
            "id": "mission-state-manager",
            "type": "function",
            "z": "mission-sequencer-tab",
            "name": "Mission State Manager",
            "func": """// Manage mission execution state
const command = msg.payload;
const action = command.action;

// Get current mission state
let missionState = flow.get('mission_state') || 'idle';
let currentMission = flow.get('current_mission');
let currentStep = flow.get('current_step') || 0;

node.log(`Mission command received: ${action}, current state: ${missionState}`);

switch (action) {
    case 'start_mission':
        if (!currentMission) {
            node.error('No mission loaded');
            return null;
        }
        
        if (missionState === 'loaded' || missionState === 'paused' || missionState === 'completed' || missionState === 'failed') {
            flow.set('mission_state', 'in_progress');
            flow.set('current_step', 0);
            flow.set('step_start_time', Date.now());
            
            // Start executing the first step
            const firstStep = currentMission.sequence[0];
            const executeMsg = {
                topic: 'execute_step',
                payload: {
                    step: firstStep,
                    step_number: 0,
                    mission_id: currentMission.mission_id
                }
            };
            
            const statusMsg = {
                topic: 'orchestrator/status/mission',
                payload: {
                    mission_id: currentMission.mission_id,
                    status: 'in_progress',
                    current_step: 0,
                    total_steps: currentMission.sequence.length,
                    timestamp: new Date().toISOString()
                }
            };
            
            return [statusMsg, executeMsg];
        }
        break;
        
    case 'pause_mission':
        if (missionState === 'in_progress') {
            flow.set('mission_state', 'paused');
            
            const statusMsg = {
                topic: 'orchestrator/status/mission',
                payload: {
                    mission_id: currentMission.mission_id,
                    status: 'paused',
                    current_step: currentStep,
                    total_steps: currentMission.sequence.length,
                    timestamp: new Date().toISOString()
                }
            };
            
            return [statusMsg, null];
        }
        break;
        
    case 'stop_mission':
        if (missionState === 'in_progress' || missionState === 'paused') {
            flow.set('mission_state', 'stopped');
            
            const statusMsg = {
                topic: 'orchestrator/status/mission',
                payload: {
                    mission_id: currentMission.mission_id,
                    status: 'stopped',
                    current_step: currentStep,
                    total_steps: currentMission.sequence.length,
                    reason: 'user_stop',
                    timestamp: new Date().toISOString()
                }
            };
            
            return [statusMsg, null];
        }
        break;
        
    case 'reset_mission':
        flow.set('mission_state', 'loaded');
        flow.set('current_step', 0);
        flow.set('step_start_time', null);
        
        const statusMsg = {
            topic: 'orchestrator/status/mission',
            payload: {
                mission_id: currentMission ? currentMission.mission_id : 'none',
                status: 'loaded',
                current_step: 0,
                total_steps: currentMission ? currentMission.sequence.length : 0,
                timestamp: new Date().toISOString()
            }
        };
        
        return [statusMsg, null];
}

return null;""",
            "outputs": 2,
            "noerr": 0,
            "initialize": "",
            "finalize": "",
            "libs": [],
            "x": 400,
            "y": 200,
            "wires": [
                [
                    "mission-status-publisher"
                ],
                [
                    "step-executor"
                ]
            ]
        },
        {
            "id": "step-executor",
            "type": "function",
            "z": "mission-sequencer-tab",
            "name": "Step Executor",
            "func": """// Execute individual mission steps
if (msg.topic === 'execute_step') {
    const stepData = msg.payload;
    const step = stepData.step;
    const stepNumber = stepData.step_number;
    
    node.log(`Executing step ${stepNumber + 1}: ${step.action}`);
    
    // Create command message based on step action
    let commandMsg = null;
    
    switch (step.action) {
        case 'move_forward':
        case 'move_backward':
        case 'rotate_left':
        case 'rotate_right':
        case 'stop':
            commandMsg = {
                topic: 'orchestrator/cmd/motors',
                payload: {
                    action: step.action,
                    parameters: step.parameters || {},
                    timestamp: new Date().toISOString(),
                    command_id: msg._msgid,
                    mission_step: stepNumber,
                    mission_id: stepData.mission_id
                }
            };
            break;
            
        case 'wait':
            // For wait commands, handle with a delay
            const waitTime = step.parameters ? step.parameters.duration || 1000 : 1000;
            
            setTimeout(() => {
                // After wait, proceed to next step
                const nextStepMsg = {
                    topic: 'step_completed',
                    payload: {
                        step_number: stepNumber,
                        mission_id: stepData.mission_id,
                        success: true
                    }
                };
                node.send(nextStepMsg);
            }, waitTime);
            
            return null;
    }
    
    if (commandMsg) {
        // Set up timeout for this step
        const timeout = step.timeout * 1000; // Convert to milliseconds
        
        setTimeout(() => {
            // Check if step is still in progress
            const currentStep = flow.get('current_step');
            const missionState = flow.get('mission_state');
            
            if (currentStep === stepNumber && missionState === 'in_progress') {
                // Step timed out
                const timeoutMsg = {
                    topic: 'step_timeout',
                    payload: {
                        step_number: stepNumber,
                        mission_id: stepData.mission_id,
                        timeout: step.timeout
                    }
                };
                node.send(timeoutMsg);
            }
        }, timeout);
        
        return commandMsg;
    }
}

// Handle step completion
if (msg.topic === 'step_completed') {
    const completionData = msg.payload;
    const stepNumber = completionData.step_number;
    const success = completionData.success;
    
    const currentMission = flow.get('current_mission');
    const missionState = flow.get('mission_state');
    
    if (missionState !== 'in_progress') {
        return null; // Mission was stopped/paused
    }
    
    if (success) {
        const nextStep = stepNumber + 1;
        
        if (nextStep < currentMission.sequence.length) {
            // Execute next step
            flow.set('current_step', nextStep);
            flow.set('step_start_time', Date.now());
            
            const nextStepData = currentMission.sequence[nextStep];
            const executeMsg = {
                topic: 'execute_step',
                payload: {
                    step: nextStepData,
                    step_number: nextStep,
                    mission_id: currentMission.mission_id
                }
            };
            
            const statusMsg = {
                topic: 'orchestrator/status/mission',
                payload: {
                    mission_id: currentMission.mission_id,
                    status: 'in_progress',
                    current_step: nextStep,
                    total_steps: currentMission.sequence.length,
                    timestamp: new Date().toISOString()
                }
            };
            
            return [statusMsg, executeMsg];
        } else {
            // Mission completed
            flow.set('mission_state', 'completed');
            
            const statusMsg = {
                topic: 'orchestrator/status/mission',
                payload: {
                    mission_id: currentMission.mission_id,
                    status: 'completed',
                    current_step: stepNumber,
                    total_steps: currentMission.sequence.length,
                    reason: 'mission_completed',
                    timestamp: new Date().toISOString()
                }
            };
            
            return [statusMsg, null];
        }
    }
}

return null;""",
            "outputs": 2,
            "noerr": 0,
            "initialize": "",
            "finalize": "",
            "libs": [],
            "x": 650,
            "y": 200,
            "wires": [
                [
                    "mission-status-publisher"
                ],
                [
                    "motor-mqtt-publisher",
                    "step-executor"
                ]
            ]
        },
        {
            "id": "mission-status-publisher",
            "type": "mqtt out",
            "z": "mission-sequencer-tab",
            "name": "Mission Status Publisher",
            "topic": "orchestrator/status/mission",
            "qos": "1",
            "retain": "true",
            "respTopic": "",
            "contentType": "",
            "userProps": "",
            "correl": "",
            "expiry": "",
            "broker": "mqtt-broker-config",
            "x": 680,
            "y": 100,
            "wires": []
        },
        {
            "id": "mission-status-display",
            "type": "ui_text",
            "z": "mission-sequencer-tab",
            "group": "ui-group-mission-status",
            "order": 1,
            "width": 12,
            "height": 1,
            "name": "Mission Status",
            "label": "Mission Status:",
            "format": "{{msg.payload}}",
            "layout": "row-spread",
            "className": "",
            "x": 400,
            "y": 400,
            "wires": []
        },
        {
            "id": "mission-status-listener",
            "type": "mqtt in",
            "z": "mission-sequencer-tab",
            "name": "Mission Status Listener",
            "topic": "orchestrator/status/mission",
            "qos": "1",
            "datatype": "json",
            "broker": "mqtt-broker-config",
            "nl": False,
            "rap": True,
            "rh": 0,
            "inputs": 0,
            "x": 150,
            "y": 400,
            "wires": [
                [
                    "mission-status-formatter"
                ]
            ]
        },
        {
            "id": "mission-status-formatter",
            "type": "function",
            "z": "mission-sequencer-tab",
            "name": "Mission Status Formatter",
            "func": """// Format mission status for display
const status = msg.payload;

if (status.error) {
    msg.payload = `ERROR: ${status.error}`;
} else {
    const missionId = status.mission_id || 'None';
    const state = status.status || 'Unknown';
    const progress = `${(status.current_step || 0) + 1}/${status.total_steps || 0}`;
    
    msg.payload = `Mission: ${missionId} | Status: ${state} | Progress: ${progress}`;
    
    if (status.reason) {
        msg.payload += ` | Reason: ${status.reason}`;
    }
}

return msg;""",
            "outputs": 1,
            "noerr": 0,
            "initialize": "",
            "finalize": "",
            "libs": [],
            "x": 400,
            "y": 440,
            "wires": [
                [
                    "mission-status-display"
                ]
            ]
        }
    ]
    
    # Check for ID conflicts
    existing_ids = {node['id'] for node in existing_flows}
    conflicting_ids = [node for node in mission_sequencer_flows if node['id'] in existing_ids]
    
    if conflicting_ids:
        print(f"Warning: Found {len(conflicting_ids)} ID conflicts:")
        for node in conflicting_ids:
            print(f"  - {node['id']} ({node['type']})")
        
        # Generate new IDs for conflicting nodes
        id_mapping = {}
        for node in conflicting_ids:
            new_id = node['id'] + '-mission-seq'
            id_mapping[node['id']] = new_id
            node['id'] = new_id
        
        # Update references to changed IDs
        for node in mission_sequencer_flows:
            # Update wires references
            if 'wires' in node:
                node['wires'] = [
                    [id_mapping.get(wire_id, wire_id) for wire_id in wire_array]
                    for wire_array in node['wires']
                ]
            
            # Update group references
            if 'group' in node and node['group'] in id_mapping:
                node['group'] = id_mapping[node['group']]
            
            # Update tab references
            if 'z' in node and node['z'] in id_mapping:
                node['z'] = id_mapping[node['z']]
            
            # Update broker references
            if 'broker' in node and node['broker'] in id_mapping:
                node['broker'] = id_mapping[node['broker']]
    
    # Merge flows
    merged_flows = existing_flows + mission_sequencer_flows
    
    # Write merged flows
    with open('flows.json', 'w') as f:
        json.dump(merged_flows, f, indent=2)
    
    print(f"✅ Mission sequencer flows merged successfully!")
    print(f"📊 Added {len(mission_sequencer_flows)} new nodes")
    print(f"📊 Total nodes: {len(merged_flows)}")
    
    # Summary of added components
    added_tabs = [node for node in mission_sequencer_flows if node['type'] == 'tab']
    added_groups = [node for node in mission_sequencer_flows if node['type'] == 'ui_group']
    added_nodes = [node for node in mission_sequencer_flows if node['type'] not in ['tab', 'ui_group']]
    
    print(f"\n📋 Summary of added components:")
    print(f"  Tabs: {len(added_tabs)}")
    print(f"  UI Groups: {len(added_groups)}")
    print(f"  Flow Nodes: {len(added_nodes)}")
    
    if added_tabs:
        print(f"\n🏷️  Added tabs:")
        for tab in added_tabs:
            print(f"    - {tab['label']}")

if __name__ == "__main__":
    os.chdir('configs/node_red_config')
    merge_mission_sequencer()