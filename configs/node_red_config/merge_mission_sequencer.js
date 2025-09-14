#!/usr/bin/env node

/**
 * Script to merge mission sequencer flows into the main flows.json file
 */

const fs = require('fs');
const path = require('path');

const FLOWS_FILE = path.join(__dirname, 'flows.json');
const MISSION_SEQUENCER_FILE = path.join(__dirname, 'mission_sequencer_flows.json');
const BACKUP_FILE = path.join(__dirname, 'flows_backup_before_mission_sequencer.json');

function mergeFlows() {
    try {
        // Read existing flows
        console.log('Reading existing flows...');
        const existingFlows = JSON.parse(fs.readFileSync(FLOWS_FILE, 'utf8'));
        
        // Read mission sequencer flows
        console.log('Reading mission sequencer flows...');
        const missionSequencerFlows = JSON.parse(fs.readFileSync(MISSION_SEQUENCER_FILE, 'utf8'));
        
        // Create backup
        console.log('Creating backup...');
        fs.writeFileSync(BACKUP_FILE, JSON.stringify(existingFlows, null, 2));
        
        // Check for ID conflicts
        const existingIds = new Set(existingFlows.map(node => node.id));
        const conflictingIds = missionSequencerFlows.filter(node => existingIds.has(node.id));
        
        if (conflictingIds.length > 0) {
            console.error('ID conflicts detected:');
            conflictingIds.forEach(node => console.error(`  - ${node.id} (${node.type})`));
            
            // Generate new IDs for conflicting nodes
            console.log('Generating new IDs for conflicting nodes...');
            const idMapping = {};
            
            conflictingIds.forEach(node => {
                const newId = node.id + '-mission-seq';
                idMapping[node.id] = newId;
                node.id = newId;
            });
            
            // Update references to changed IDs
            missionSequencerFlows.forEach(node => {
                // Update wires references
                if (node.wires) {
                    node.wires = node.wires.map(wireArray => 
                        wireArray.map(wireId => idMapping[wireId] || wireId)
                    );
                }
                
                // Update group references
                if (node.group && idMapping[node.group]) {
                    node.group = idMapping[node.group];
                }
                
                // Update tab references
                if (node.z && idMapping[node.z]) {
                    node.z = idMapping[node.z];
                }
                
                // Update broker references
                if (node.broker && idMapping[node.broker]) {
                    node.broker = idMapping[node.broker];
                }
            });
        }
        
        // Merge flows
        console.log('Merging flows...');
        const mergedFlows = [...existingFlows, ...missionSequencerFlows];
        
        // Write merged flows
        console.log('Writing merged flows...');
        fs.writeFileSync(FLOWS_FILE, JSON.stringify(mergedFlows, null, 2));
        
        console.log('✅ Mission sequencer flows merged successfully!');
        console.log(`📁 Backup created: ${BACKUP_FILE}`);
        console.log(`📊 Added ${missionSequencerFlows.length} new nodes`);
        console.log(`📊 Total nodes: ${mergedFlows.length}`);
        
        // Summary of added components
        const addedTabs = missionSequencerFlows.filter(node => node.type === 'tab');
        const addedGroups = missionSequencerFlows.filter(node => node.type === 'ui_group');
        const addedNodes = missionSequencerFlows.filter(node => !['tab', 'ui_group'].includes(node.type));
        
        console.log('\n📋 Summary of added components:');
        console.log(`  Tabs: ${addedTabs.length}`);
        console.log(`  UI Groups: ${addedGroups.length}`);
        console.log(`  Flow Nodes: ${addedNodes.length}`);
        
        if (addedTabs.length > 0) {
            console.log('\n🏷️  Added tabs:');
            addedTabs.forEach(tab => console.log(`    - ${tab.label}`));
        }
        
    } catch (error) {
        console.error('❌ Error merging flows:', error.message);
        process.exit(1);
    }
}

// Run the merge
mergeFlows();