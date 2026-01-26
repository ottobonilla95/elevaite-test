#!/usr/bin/env python3
"""
Test script to verify UI metadata migration logic

This script tests the migration of workflow_agents and workflow_connections
to the new schema with UI metadata (positions and connections).
"""

import json


def test_migration_logic():
    """Test the migration logic for UI metadata"""
    
    # Simulate old schema data
    workflow_id = "test-workflow-123"
    
    # Old workflow_agents data
    old_agents = [
        {
            "id": 1,
            "agent_id": "agent-aaa",
            "position_x": 100,
            "position_y": 200,
            "node_id": "node-1",
            "agent_config": {"temperature": 0.7}
        },
        {
            "id": 2,
            "agent_id": "agent-bbb",
            "position_x": 300,
            "position_y": 200,
            "node_id": "node-2",
            "agent_config": {"temperature": 0.5}
        },
        {
            "id": 3,
            "agent_id": "agent-ccc",
            "position_x": 500,
            "position_y": 200,
            "node_id": "node-3",
            "agent_config": None
        }
    ]
    
    # Old workflow_connections data
    old_connections = [
        {
            "source_agent_id": "agent-aaa",
            "target_agent_id": "agent-bbb",
            "connection_type": "default",
            "source_handle": None,
            "target_handle": None
        },
        {
            "source_agent_id": "agent-bbb",
            "target_agent_id": "agent-ccc",
            "connection_type": "conditional",
            "source_handle": "success",
            "target_handle": "input"
        }
    ]
    
    # Build agent_id to node_id mapping
    agent_to_node = {}
    for agent in old_agents:
        agent_to_node[str(agent["agent_id"])] = agent["node_id"]
    
    print("Agent to Node mapping:")
    for agent_id, node_id in agent_to_node.items():
        print(f"  {agent_id} -> {node_id}")
    
    # Convert agents to steps with UI metadata
    steps = []
    for agent in old_agents:
        agent_id = agent["agent_id"]
        position_x = agent["position_x"]
        position_y = agent["position_y"]
        node_id = agent["node_id"]
        agent_config = agent["agent_config"] if agent["agent_config"] else {}
        
        step = {
            "step_id": node_id,
            "step_type": "agent",
            "name": f"Agent {agent_id}",
            "config": {
                "agent_id": str(agent_id),
                **agent_config
            },
            "dependencies": [],
        }
        
        # Add position if available
        if position_x is not None and position_y is not None:
            step["position"] = {
                "x": float(position_x),
                "y": float(position_y)
            }
        
        steps.append(step)
    
    # Convert connections to new format
    new_connections = []
    for conn in old_connections:
        source_agent_id = str(conn["source_agent_id"])
        target_agent_id = str(conn["target_agent_id"])
        connection_type = conn["connection_type"] if conn["connection_type"] else "default"
        source_handle = conn["source_handle"]
        target_handle = conn["target_handle"]
        
        # Map agent IDs to node IDs
        if source_agent_id in agent_to_node and target_agent_id in agent_to_node:
            new_conn = {
                "source_step_id": agent_to_node[source_agent_id],
                "target_step_id": agent_to_node[target_agent_id],
                "connection_type": connection_type,
            }
            
            if source_handle:
                new_conn["source_handle"] = source_handle
            if target_handle:
                new_conn["target_handle"] = target_handle
            
            new_connections.append(new_conn)
            
            # Add to dependencies
            target_node_id = agent_to_node[target_agent_id]
            source_node_id = agent_to_node[source_agent_id]
            for step in steps:
                if step["step_id"] == target_node_id:
                    if source_node_id not in step["dependencies"]:
                        step["dependencies"].append(source_node_id)
    
    # Create final configuration
    config = {
        "name": "Test Workflow",
        "steps": steps,
        "connections": new_connections
    }
    
    # Print results
    print("\n" + "="*70)
    print("MIGRATION TEST RESULTS")
    print("="*70)
    
    print(f"\n✅ Migrated {len(steps)} steps:")
    for step in steps:
        print(f"\n  Step ID: {step['step_id']}")
        print(f"    Type: {step['step_type']}")
        print(f"    Name: {step['name']}")
        if step.get('position'):
            print(f"    Position: ({step['position']['x']}, {step['position']['y']})")
        print(f"    Config: {step['config']}")
        print(f"    Dependencies: {step['dependencies']}")
    
    print(f"\n✅ Migrated {len(new_connections)} connections:")
    for conn in new_connections:
        print(f"\n  {conn['source_step_id']} -> {conn['target_step_id']}")
        print(f"    Type: {conn['connection_type']}")
        if conn.get('source_handle'):
            print(f"    Source Handle: {conn['source_handle']}")
        if conn.get('target_handle'):
            print(f"    Target Handle: {conn['target_handle']}")
    
    print("\n" + "="*70)
    print("FINAL CONFIGURATION JSON")
    print("="*70)
    print(json.dumps(config, indent=2))
    
    # Validate
    print("\n" + "="*70)
    print("VALIDATION")
    print("="*70)
    
    # Check all steps have positions
    all_have_positions = all(step.get('position') is not None for step in steps)
    print(f"✅ All steps have positions: {all_have_positions}")
    
    # Check all connections reference valid steps
    step_ids = {step['step_id'] for step in steps}
    all_valid_connections = all(
        conn['source_step_id'] in step_ids and conn['target_step_id'] in step_ids
        for conn in new_connections
    )
    print(f"✅ All connections reference valid steps: {all_valid_connections}")
    
    # Check dependencies match connections
    expected_deps = {
        "node-2": ["node-1"],
        "node-3": ["node-2"]
    }
    deps_match = True
    for step in steps:
        if step['step_id'] in expected_deps:
            if set(step['dependencies']) != set(expected_deps[step['step_id']]):
                deps_match = False
                print(f"❌ Dependencies mismatch for {step['step_id']}")
                print(f"   Expected: {expected_deps[step['step_id']]}")
                print(f"   Got: {step['dependencies']}")
    
    if deps_match:
        print("✅ Dependencies correctly derived from connections")
    
    # Check handles preserved
    handles_preserved = any(
        conn.get('source_handle') == 'success' and conn.get('target_handle') == 'input'
        for conn in new_connections
    )
    print(f"✅ Connection handles preserved: {handles_preserved}")
    
    print("\n" + "="*70)
    if all_have_positions and all_valid_connections and deps_match and handles_preserved:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_migration_logic()

