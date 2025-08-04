#!/usr/bin/env python3
"""
Script to find the biggest workflow in the database.

This script analyzes workflows by various metrics:
- Number of agents
- Number of connections
- Configuration complexity (JSON size)
- Number of deployments
"""

import json
import sys
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

# Add the current directory to the path to import local modules
sys.path.append('.')

from db.database import SessionLocal
from db.models import Workflow, WorkflowAgent, WorkflowConnection, WorkflowDeployment
from db import crud


def calculate_workflow_size_metrics(db: Session, workflow: Workflow) -> Dict[str, Any]:
    """Calculate various size metrics for a workflow."""
    
    # Count agents
    agent_count = db.query(WorkflowAgent).filter(
        WorkflowAgent.workflow_id == workflow.workflow_id
    ).count()
    
    # Count connections
    connection_count = db.query(WorkflowConnection).filter(
        WorkflowConnection.workflow_id == workflow.workflow_id
    ).count()
    
    # Count deployments
    deployment_count = db.query(WorkflowDeployment).filter(
        WorkflowDeployment.workflow_id == workflow.workflow_id
    ).count()
    
    # Calculate configuration size (JSON string length)
    config_size = len(json.dumps(workflow.configuration)) if workflow.configuration else 0
    
    # Calculate configuration complexity (number of keys at all levels)
    config_complexity = count_json_keys(workflow.configuration) if workflow.configuration else 0
    
    # Calculate total "size" score (weighted combination)
    size_score = (
        agent_count * 10 +           # Agents are most important
        connection_count * 5 +       # Connections show complexity
        config_complexity * 2 +      # Configuration complexity
        deployment_count * 3 +       # Deployments show usage
        config_size / 100           # Raw config size (normalized)
    )
    
    return {
        'workflow_id': str(workflow.workflow_id),
        'name': workflow.name,
        'description': workflow.description,
        'version': workflow.version,
        'agent_count': agent_count,
        'connection_count': connection_count,
        'deployment_count': deployment_count,
        'config_size_bytes': config_size,
        'config_complexity': config_complexity,
        'size_score': size_score,
        'is_deployed': workflow.is_deployed,
        'created_at': workflow.created_at.isoformat() if workflow.created_at else None,
        'tags': workflow.tags
    }


def count_json_keys(obj: Any, depth: int = 0) -> int:
    """Recursively count keys in a JSON object to measure complexity."""
    if depth > 10:  # Prevent infinite recursion
        return 0
        
    if isinstance(obj, dict):
        count = len(obj)
        for value in obj.values():
            count += count_json_keys(value, depth + 1)
        return count
    elif isinstance(obj, list):
        count = 0
        for item in obj:
            count += count_json_keys(item, depth + 1)
        return count
    else:
        return 0


def find_biggest_workflows(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Find the biggest workflows by various metrics."""
    
    print("🔍 Analyzing workflows in the database...")
    
    # Get all workflows
    workflows = crud.get_workflows(db, limit=1000)  # Get a large number
    
    if not workflows:
        print("❌ No workflows found in the database!")
        return []
    
    print(f"📊 Found {len(workflows)} workflows to analyze")
    
    # Calculate metrics for each workflow
    workflow_metrics = []
    for workflow in workflows:
        try:
            metrics = calculate_workflow_size_metrics(db, workflow)
            workflow_metrics.append(metrics)
        except Exception as e:
            print(f"⚠️  Error analyzing workflow {workflow.name}: {e}")
            continue
    
    # Sort by size score (descending)
    workflow_metrics.sort(key=lambda x: x['size_score'], reverse=True)
    
    return workflow_metrics[:limit]


def print_workflow_analysis(workflows: List[Dict[str, Any]]):
    """Print a detailed analysis of the workflows."""
    
    if not workflows:
        print("❌ No workflows to analyze!")
        return
    
    print("\n" + "="*80)
    print("🏆 BIGGEST WORKFLOWS ANALYSIS")
    print("="*80)
    
    for i, workflow in enumerate(workflows, 1):
        print(f"\n#{i} - {workflow['name']} (v{workflow['version']})")
        print("-" * 60)
        print(f"📋 Description: {workflow['description'] or 'No description'}")
        print(f"🆔 Workflow ID: {workflow['workflow_id']}")
        print(f"📅 Created: {workflow['created_at']}")
        print(f"🚀 Deployed: {'Yes' if workflow['is_deployed'] else 'No'}")
        print(f"🏷️  Tags: {workflow['tags'] or 'None'}")
        print(f"\n📊 SIZE METRICS:")
        print(f"   • Agents: {workflow['agent_count']}")
        print(f"   • Connections: {workflow['connection_count']}")
        print(f"   • Deployments: {workflow['deployment_count']}")
        print(f"   • Config Size: {workflow['config_size_bytes']:,} bytes")
        print(f"   • Config Complexity: {workflow['config_complexity']} keys")
        print(f"   • Overall Size Score: {workflow['size_score']:.2f}")
        
        if i == 1:
            print(f"\n🎯 THIS IS THE BIGGEST WORKFLOW!")
    
    print("\n" + "="*80)
    print("📈 SUMMARY STATISTICS")
    print("="*80)
    
    total_agents = sum(w['agent_count'] for w in workflows)
    total_connections = sum(w['connection_count'] for w in workflows)
    total_deployments = sum(w['deployment_count'] for w in workflows)
    avg_size_score = sum(w['size_score'] for w in workflows) / len(workflows)
    
    print(f"Total workflows analyzed: {len(workflows)}")
    print(f"Total agents across all workflows: {total_agents}")
    print(f"Total connections across all workflows: {total_connections}")
    print(f"Total deployments across all workflows: {total_deployments}")
    print(f"Average size score: {avg_size_score:.2f}")
    
    # Find workflows by specific metrics
    biggest_by_agents = max(workflows, key=lambda x: x['agent_count'])
    biggest_by_connections = max(workflows, key=lambda x: x['connection_count'])
    biggest_by_config = max(workflows, key=lambda x: x['config_size_bytes'])
    
    print(f"\n🥇 Biggest by agents: {biggest_by_agents['name']} ({biggest_by_agents['agent_count']} agents)")
    print(f"🥇 Biggest by connections: {biggest_by_connections['name']} ({biggest_by_connections['connection_count']} connections)")
    print(f"🥇 Biggest by config size: {biggest_by_config['name']} ({biggest_by_config['config_size_bytes']:,} bytes)")


def main():
    """Main function to find and analyze the biggest workflows."""
    
    print("🔍 Finding the biggest workflow in the database...")
    
    try:
        # Create database session
        db = SessionLocal()
        
        # Find biggest workflows
        biggest_workflows = find_biggest_workflows(db, limit=10)
        
        # Print analysis
        print_workflow_analysis(biggest_workflows)
        
        if biggest_workflows:
            biggest = biggest_workflows[0]
            print(f"\n🎯 THE BIGGEST WORKFLOW IS: {biggest['name']} (ID: {biggest['workflow_id']})")
            return biggest
        else:
            print("❌ No workflows found!")
            return None
            
    except Exception as e:
        print(f"❌ Error connecting to database or analyzing workflows: {e}")
        return None
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    main()
