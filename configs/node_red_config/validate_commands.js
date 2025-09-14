#!/usr/bin/env node

/**
 * Command Validation Test Script
 * 
 * This script validates the command generation logic used in Node-RED flows
 * without requiring a running Node-RED instance.
 */

// Motor command validation function (extracted from Node-RED function node)
function validateMotorCommand(command) {
    const validActions = ['move_forward', 'move_backward', 'rotate_left', 'rotate_right', 'stop'];
    
    // Check if action is valid
    if (!validActions.includes(command.action)) {
        throw new Error(`Invalid action: ${command.action}`);
    }
    
    // Validate parameters if they exist
    if (command.parameters) {
        const params = command.parameters;
        
        // Validate distance (1-200 cm)
        if (params.distance !== undefined) {
            if (typeof params.distance !== 'number' || params.distance < 1 || params.distance > 200) {
                throw new Error(`Invalid distance: ${params.distance}. Must be between 1-200 cm`);
            }
        }
        
        // Validate angle (1-360 degrees)
        if (params.angle !== undefined) {
            if (typeof params.angle !== 'number' || params.angle < 1 || params.angle > 360) {
                throw new Error(`Invalid angle: ${params.angle}. Must be between 1-360 degrees`);
            }
        }
        
        // Validate speed (0.1-1.0)
        if (params.speed !== undefined) {
            if (typeof params.speed !== 'number' || params.speed < 0.1 || params.speed > 1.0) {
                throw new Error(`Invalid speed: ${params.speed}. Must be between 0.1-1.0`);
            }
        }
    }
    
    // Add metadata if missing
    if (!command.timestamp) {
        command.timestamp = new Date().toISOString();
    }
    if (!command.command_id) {
        command.command_id = 'test-' + Math.random().toString(36).substr(2, 9);
    }
    
    return command;
}

// Mission command validation function
function validateMissionCommand(command) {
    const validActions = ['start_mission', 'pause_mission', 'stop_mission', 'reset_mission'];
    
    if (!validActions.includes(command.action)) {
        throw new Error(`Invalid mission action: ${command.action}`);
    }
    
    // Add metadata
    command.timestamp = new Date().toISOString();
    command.command_id = 'test-' + Math.random().toString(36).substr(2, 9);
    
    return command;
}

// Emergency command validation function
function validateEmergencyCommand(command) {
    // Emergency commands are always valid but need proper formatting
    if (command.action !== 'emergency_stop') {
        command.action = 'emergency_stop';
    }
    
    // Ensure reason is provided
    if (!command.reason) {
        command.reason = 'test_initiated';
    }
    
    // Add metadata with high priority
    command.timestamp = new Date().toISOString();
    command.command_id = 'test-' + Math.random().toString(36).substr(2, 9);
    command.priority = 'critical';
    
    return command;
}

// Test cases
const testCases = [
    // Valid motor commands
    {
        name: "Valid move forward command",
        type: "motor",
        command: {
            action: "move_forward",
            parameters: {
                distance: 50,
                speed: 0.7
            }
        },
        shouldPass: true
    },
    {
        name: "Valid rotate command",
        type: "motor", 
        command: {
            action: "rotate_left",
            parameters: {
                angle: 90,
                speed: 0.5
            }
        },
        shouldPass: true
    },
    {
        name: "Valid stop command",
        type: "motor",
        command: {
            action: "stop"
        },
        shouldPass: true
    },
    
    // Invalid motor commands
    {
        name: "Invalid action",
        type: "motor",
        command: {
            action: "invalid_action",
            parameters: {
                distance: 50,
                speed: 0.5
            }
        },
        shouldPass: false
    },
    {
        name: "Invalid distance (too high)",
        type: "motor",
        command: {
            action: "move_forward",
            parameters: {
                distance: 500,
                speed: 0.5
            }
        },
        shouldPass: false
    },
    {
        name: "Invalid speed (too high)",
        type: "motor",
        command: {
            action: "move_forward", 
            parameters: {
                distance: 50,
                speed: 2.0
            }
        },
        shouldPass: false
    },
    
    // Valid mission commands
    {
        name: "Valid start mission",
        type: "mission",
        command: {
            action: "start_mission"
        },
        shouldPass: true
    },
    {
        name: "Valid pause mission",
        type: "mission",
        command: {
            action: "pause_mission"
        },
        shouldPass: true
    },
    
    // Invalid mission commands
    {
        name: "Invalid mission action",
        type: "mission",
        command: {
            action: "invalid_mission"
        },
        shouldPass: false
    },
    
    // Emergency commands (always valid)
    {
        name: "Valid emergency stop",
        type: "emergency",
        command: {
            action: "emergency_stop",
            reason: "user_initiated"
        },
        shouldPass: true
    },
    {
        name: "Emergency with invalid action (auto-corrected)",
        type: "emergency",
        command: {
            action: "invalid_emergency"
        },
        shouldPass: true
    }
];

// Run tests
console.log("🧪 Running Command Validation Tests\n");

let passed = 0;
let failed = 0;

testCases.forEach((testCase, index) => {
    try {
        let result;
        
        switch (testCase.type) {
            case 'motor':
                result = validateMotorCommand(JSON.parse(JSON.stringify(testCase.command)));
                break;
            case 'mission':
                result = validateMissionCommand(JSON.parse(JSON.stringify(testCase.command)));
                break;
            case 'emergency':
                result = validateEmergencyCommand(JSON.parse(JSON.stringify(testCase.command)));
                break;
            default:
                throw new Error(`Unknown test type: ${testCase.type}`);
        }
        
        if (testCase.shouldPass) {
            console.log(`✅ ${index + 1}. ${testCase.name}`);
            console.log(`   Result: ${JSON.stringify(result, null, 2)}\n`);
            passed++;
        } else {
            console.log(`❌ ${index + 1}. ${testCase.name} - Expected failure but passed`);
            console.log(`   Result: ${JSON.stringify(result, null, 2)}\n`);
            failed++;
        }
        
    } catch (error) {
        if (!testCase.shouldPass) {
            console.log(`✅ ${index + 1}. ${testCase.name} - Correctly failed`);
            console.log(`   Error: ${error.message}\n`);
            passed++;
        } else {
            console.log(`❌ ${index + 1}. ${testCase.name} - Unexpected failure`);
            console.log(`   Error: ${error.message}\n`);
            failed++;
        }
    }
});

console.log(`\n📊 Test Results: ${passed} passed, ${failed} failed`);

if (failed === 0) {
    console.log("🎉 All tests passed! Command validation is working correctly.");
    process.exit(0);
} else {
    console.log("💥 Some tests failed. Please review the validation logic.");
    process.exit(1);
}