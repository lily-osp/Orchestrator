#!/usr/bin/env python3

import json

# Read existing flows
with open('flows.json', 'r') as f:
    flows = json.load(f)

# Mission sequencer flows to add
new_flows = [
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
        "wires": [["mission-json-validator"]]
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
        "wires": [["mission-json-validator"]]
    },
    {
        "id": "mission-json-validator",
        "type": "function",
        "z": "mission-sequencer-tab",
        "name": "Mission JSON Validator",
        "func": "// Validate and process mission JSON input\nif (msg.topic === 'mission_upload') {\n    // Get the stored JSON from context\n    const jsonText = flow.get('mission_json_text') || '[]';\n    \n    try {\n        const sequence = JSON.parse(jsonText);\n        \n        if (!Array.isArray(sequence)) {\n            throw new Error('Mission sequence must be an array');\n        }\n        \n        const validActions = ['move_forward', 'move_backward', 'rotate_left', 'rotate_right', 'stop', 'wait'];\n        \n        // Validate each step\n        for (let i = 0; i < sequence.length; i++) {\n            const step = sequence[i];\n            \n            if (!step.action || !validActions.includes(step.action)) {\n                throw new Error(`Step ${i + 1}: Invalid or missing action`);\n            }\n            \n            if (step.action !== 'stop' && step.action !== 'wait' && !step.parameters) {\n                throw new Error(`Step ${i + 1}: Missing parameters for action ${step.action}`);\n            }\n            \n            if (!step.timeout || typeof step.timeout !== 'number' || step.timeout <= 0) {\n                throw new Error(`Step ${i + 1}: Invalid or missing timeout`);\n            }\n        }\n        \n        // Mission is valid - create mission data\n        const missionData = {\n            sequence: sequence,\n            timestamp: new Date().toISOString(),\n            mission_id: 'mission_' + Date.now()\n        };\n        \n        // Store the mission sequence in flow context\n        flow.set('current_mission', missionData);\n        flow.set('mission_state', 'loaded');\n        flow.set('current_step', 0);\n        flow.set('step_start_time', null);\n        \n        // Send status update\n        const statusMsg = {\n            topic: 'orchestrator/status/mission',\n            payload: {\n                mission_id: missionData.mission_id,\n                status: 'loaded',\n                total_steps: missionData.sequence.length,\n                current_step: 0,\n                timestamp: new Date().toISOString()\n            }\n        };\n        \n        node.log(`Mission uploaded: ${missionData.mission_id} with ${missionData.sequence.length} steps`);\n        return statusMsg;\n        \n    } catch (error) {\n        node.error(`Mission validation failed: ${error.message}`);\n        \n        const errorMsg = {\n            topic: 'orchestrator/status/mission',\n            payload: {\n                status: 'error',\n                error: error.message,\n                timestamp: new Date().toISOString()\n            }\n        };\n        \n        return errorMsg;\n    }\n} else if (msg.topic === 'mission_json') {\n    // Store the JSON text for later validation\n    flow.set('mission_json_text', msg.payload);\n    return null;\n}\n\nreturn null;",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 400,
        "y": 120,
        "wires": [["mission-status-publisher"]]
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
        "wires": [["mission-state-manager"]]
    },
    {
        "id": "mission-state-manager",
        "type": "function",
        "z": "mission-sequencer-tab",
        "name": "Mission State Manager",
        "func": "// Manage mission execution state\nconst command = msg.payload;\nconst action = command.action;\n\n// Get current mission state\nlet missionState = flow.get('mission_state') || 'idle';\nlet currentMission = flow.get('current_mission');\nlet currentStep = flow.get('current_step') || 0;\n\nnode.log(`Mission command received: ${action}, current state: ${missionState}`);\n\nswitch (action) {\n    case 'start_mission':\n        if (!currentMission) {\n            node.error('No mission loaded');\n            return null;\n        }\n        \n        if (missionState === 'loaded' || missionState === 'paused' || missionState === 'completed' || missionState === 'failed') {\n            flow.set('mission_state', 'in_progress');\n            flow.set('current_step', 0);\n            flow.set('step_start_time', Date.now());\n            \n            // Start executing the first step\n            const firstStep = currentMission.sequence[0];\n            const executeMsg = {\n                topic: 'execute_step',\n                payload: {\n                    step: firstStep,\n                    step_number: 0,\n                    mission_id: currentMission.mission_id\n                }\n            };\n            \n            const statusMsg = {\n                topic: 'orchestrator/status/mission',\n                payload: {\n                    mission_id: currentMission.mission_id,\n                    status: 'in_progress',\n                    current_step: 0,\n                    total_steps: currentMission.sequence.length,\n                    timestamp: new Date().toISOString()\n                }\n            };\n            \n            return [statusMsg, executeMsg];\n        }\n        break;\n        \n    case 'pause_mission':\n        if (missionState === 'in_progress') {\n            flow.set('mission_state', 'paused');\n            \n            const statusMsg = {\n                topic: 'orchestrator/status/mission',\n                payload: {\n                    mission_id: currentMission.mission_id,\n                    status: 'paused',\n                    current_step: currentStep,\n                    total_steps: currentMission.sequence.length,\n                    timestamp: new Date().toISOString()\n                }\n            };\n            \n            return [statusMsg, null];\n        }\n        break;\n        \n    case 'stop_mission':\n        if (missionState === 'in_progress' || missionState === 'paused') {\n            flow.set('mission_state', 'stopped');\n            \n            const statusMsg = {\n                topic: 'orchestrator/status/mission',\n                payload: {\n                    mission_id: currentMission.mission_id,\n                    status: 'stopped',\n                    current_step: currentStep,\n                    total_steps: currentMission.sequence.length,\n                    reason: 'user_stop',\n                    timestamp: new Date().toISOString()\n                }\n            };\n            \n            return [statusMsg, null];\n        }\n        break;\n        \n    case 'reset_mission':\n        flow.set('mission_state', 'loaded');\n        flow.set('current_step', 0);\n        flow.set('step_start_time', null);\n        \n        const statusMsg = {\n            topic: 'orchestrator/status/mission',\n            payload: {\n                mission_id: currentMission ? currentMission.mission_id : 'none',\n                status: 'loaded',\n                current_step: 0,\n                total_steps: currentMission ? currentMission.sequence.length : 0,\n                timestamp: new Date().toISOString()\n            }\n        };\n        \n        return [statusMsg, null];\n}\n\nreturn null;",
        "outputs": 2,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 400,
        "y": 200,
        "wires": [["mission-status-publisher"], ["step-executor"]]
    },
    {
        "id": "step-executor",
        "type": "function",
        "z": "mission-sequencer-tab",
        "name": "Step Executor",
        "func": "// Execute individual mission steps\nif (msg.topic === 'execute_step') {\n    const stepData = msg.payload;\n    const step = stepData.step;\n    const stepNumber = stepData.step_number;\n    \n    node.log(`Executing step ${stepNumber + 1}: ${step.action}`);\n    \n    // Create command message based on step action\n    let commandMsg = null;\n    \n    switch (step.action) {\n        case 'move_forward':\n        case 'move_backward':\n        case 'rotate_left':\n        case 'rotate_right':\n        case 'stop':\n            commandMsg = {\n                topic: 'orchestrator/cmd/motors',\n                payload: {\n                    action: step.action,\n                    parameters: step.parameters || {},\n                    timestamp: new Date().toISOString(),\n                    command_id: msg._msgid,\n                    mission_step: stepNumber,\n                    mission_id: stepData.mission_id\n                }\n            };\n            break;\n            \n        case 'wait':\n            // For wait commands, handle with a delay\n            const waitTime = step.parameters ? step.parameters.duration || 1000 : 1000;\n            \n            setTimeout(() => {\n                // After wait, proceed to next step\n                const nextStepMsg = {\n                    topic: 'step_completed',\n                    payload: {\n                        step_number: stepNumber,\n                        mission_id: stepData.mission_id,\n                        success: true\n                    }\n                };\n                node.send(nextStepMsg);\n            }, waitTime);\n            \n            return null;\n    }\n    \n    if (commandMsg) {\n        // Set up timeout for this step\n        const timeout = step.timeout * 1000; // Convert to milliseconds\n        \n        setTimeout(() => {\n            // Check if step is still in progress\n            const currentStep = flow.get('current_step');\n            const missionState = flow.get('mission_state');\n            \n            if (currentStep === stepNumber && missionState === 'in_progress') {\n                // Step timed out\n                const timeoutMsg = {\n                    topic: 'step_timeout',\n                    payload: {\n                        step_number: stepNumber,\n                        mission_id: stepData.mission_id,\n                        timeout: step.timeout\n                    }\n                };\n                node.send(timeoutMsg);\n            }\n        }, timeout);\n        \n        return commandMsg;\n    }\n}\n\n// Handle step completion\nif (msg.topic === 'step_completed') {\n    const completionData = msg.payload;\n    const stepNumber = completionData.step_number;\n    const success = completionData.success;\n    \n    const currentMission = flow.get('current_mission');\n    const missionState = flow.get('mission_state');\n    \n    if (missionState !== 'in_progress') {\n        return null; // Mission was stopped/paused\n    }\n    \n    if (success) {\n        const nextStep = stepNumber + 1;\n        \n        if (nextStep < currentMission.sequence.length) {\n            // Execute next step\n            flow.set('current_step', nextStep);\n            flow.set('step_start_time', Date.now());\n            \n            const nextStepData = currentMission.sequence[nextStep];\n            const executeMsg = {\n                topic: 'execute_step',\n                payload: {\n                    step: nextStepData,\n                    step_number: nextStep,\n                    mission_id: currentMission.mission_id\n                }\n            };\n            \n            const statusMsg = {\n                topic: 'orchestrator/status/mission',\n                payload: {\n                    mission_id: currentMission.mission_id,\n                    status: 'in_progress',\n                    current_step: nextStep,\n                    total_steps: currentMission.sequence.length,\n                    timestamp: new Date().toISOString()\n                }\n            };\n            \n            return [statusMsg, executeMsg];\n        } else {\n            // Mission completed\n            flow.set('mission_state', 'completed');\n            \n            const statusMsg = {\n                topic: 'orchestrator/status/mission',\n                payload: {\n                    mission_id: currentMission.mission_id,\n                    status: 'completed',\n                    current_step: stepNumber,\n                    total_steps: currentMission.sequence.length,\n                    reason: 'mission_completed',\n                    timestamp: new Date().toISOString()\n                }\n            };\n            \n            return [statusMsg, null];\n        }\n    }\n}\n\nreturn null;",
        "outputs": 2,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 650,
        "y": 200,
        "wires": [["mission-status-publisher"], ["motor-mqtt-publisher", "step-executor"]]
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
        "wires": [["mission-status-formatter"]]
    },
    {
        "id": "mission-status-formatter",
        "type": "function",
        "z": "mission-sequencer-tab",
        "name": "Mission Status Formatter",
        "func": "// Format mission status for display\nconst status = msg.payload;\n\nif (status.error) {\n    msg.payload = `ERROR: ${status.error}`;\n} else {\n    const missionId = status.mission_id || 'None';\n    const state = status.status || 'Unknown';\n    const progress = `${(status.current_step || 0) + 1}/${status.total_steps || 0}`;\n    \n    msg.payload = `Mission: ${missionId} | Status: ${state} | Progress: ${progress}`;\n    \n    if (status.reason) {\n        msg.payload += ` | Reason: ${status.reason}`;\n    }\n}\n\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 400,
        "y": 440,
        "wires": [["mission-status-display"]]
    }
]

# Add new flows to existing flows
flows.extend(new_flows)

# Write updated flows
with open('flows.json', 'w') as f:
    json.dump(flows, f, indent=2)

print(f"✅ Added {len(new_flows)} mission sequencer flows")
print(f"📊 Total flows: {len(flows)}")
print("🏷️  Added Mission Sequencer tab with:")
print("   - Mission JSON input and validation")
print("   - Mission state management")
print("   - Step-by-step execution")
print("   - Real-time status display")
print("   - MQTT integration for commands and telemetry")