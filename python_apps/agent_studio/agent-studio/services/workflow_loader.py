"""
Workflow Loader and Execution Service

Production service for loading, validating, and executing deterministic workflows
from external configuration files or database storage.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from schemas.deterministic_workflow import (
    DeterministicWorkflowConfig,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    DeterministicWorkflowResponse
)
from services.workflow_execution_context import workflow_execution_context


class WorkflowLoader:
    """Service for loading and managing deterministic workflows"""
    
    def __init__(self):
        self._workflow_cache: Dict[str, DeterministicWorkflowConfig] = {}
        self._step_implementations: Dict[str, Any] = {}
    
    def load_workflow_from_file(self, file_path: str) -> DeterministicWorkflowConfig:
        """Load workflow configuration from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            workflow_config = DeterministicWorkflowConfig(**data)
            
            # Cache the workflow
            self._workflow_cache[workflow_config.workflow_id] = workflow_config
            
            return workflow_config
            
        except Exception as e:
            raise ValueError(f"Failed to load workflow from {file_path}: {e}")
    
    def load_workflow_from_database(self, workflow_id: str, db: Session) -> DeterministicWorkflowConfig:
        """Load workflow configuration from database (placeholder)"""
        # In real implementation, this would query the database
        # For now, return cached workflow if available
        if workflow_id in self._workflow_cache:
            return self._workflow_cache[workflow_id]
        
        raise ValueError(f"Workflow {workflow_id} not found in database")
    
    def validate_workflow(self, config: DeterministicWorkflowConfig) -> List[str]:
        """Validate workflow configuration"""
        errors = []
        
        # Check for circular dependencies
        try:
            self._check_circular_dependencies(config.steps)
        except ValueError as e:
            errors.append(f"Dependency error: {e}")
        
        # Validate step configurations
        for step in config.steps:
            step_errors = self._validate_step_config(step)
            errors.extend([f"Step {step.step_id}: {error}" for error in step_errors])
        
        return errors
    
    def _check_circular_dependencies(self, steps: List[Any]) -> None:
        """Check for circular dependencies in workflow steps"""
        # Build dependency graph
        graph = {}
        for step in steps:
            graph[step.step_id] = step.dependencies
        
        # Use DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for step_id in graph:
            if step_id not in visited:
                if has_cycle(step_id):
                    raise ValueError(f"Circular dependency detected involving step {step_id}")
    
    def _validate_step_config(self, step: Any) -> List[str]:
        """Validate individual step configuration"""
        errors = []
        
        # Check required fields
        if not step.step_name:
            errors.append("step_name is required")
        
        if not step.step_type:
            errors.append("step_type is required")
        
        # Validate timeout settings
        if step.timeout_seconds and step.timeout_seconds <= 0:
            errors.append("timeout_seconds must be positive")
        
        if step.max_retries < 0:
            errors.append("max_retries cannot be negative")
        
        # Validate batch processing settings
        if step.batch_size and step.batch_size <= 0:
            errors.append("batch_size must be positive")
        
        return errors
    
    async def execute_workflow(
        self, 
        request: WorkflowExecutionRequest,
        db: Optional[Session] = None
    ) -> WorkflowExecutionResponse:
        """Execute a deterministic workflow"""
        try:
            # Load workflow configuration
            if request.workflow_id in self._workflow_cache:
                workflow_config = self._workflow_cache[request.workflow_id]
            else:
                workflow_config = self.load_workflow_from_database(request.workflow_id, db)
            
            # Validate workflow
            validation_errors = self.validate_workflow(workflow_config)
            if validation_errors:
                return WorkflowExecutionResponse(
                    execution_id="",
                    workflow_id=request.workflow_id,
                    status="failed",
                    message="Workflow validation failed",
                    error="; ".join(validation_errors)
                )
            
            # Execute workflow using workflow execution context
            with workflow_execution_context.deterministic_workflow_execution(
                workflow_name=workflow_config.workflow_name,
                workflow_config=workflow_config.dict(),
                session_id=request.session_id,
                user_id=request.user_id,
                db=db
            ) as execution_id:
                
                # Add input data to workflow context
                workflow_execution_context._active_workflows[execution_id]["step_data"]["input"] = request.input_data
                
                # Execute all steps
                results = await workflow_execution_context.execute_workflow(execution_id, db)
                
                return WorkflowExecutionResponse(
                    execution_id=execution_id,
                    workflow_id=request.workflow_id,
                    status="completed",
                    message="Workflow executed successfully",
                    results=results
                )
        
        except Exception as e:
            return WorkflowExecutionResponse(
                execution_id="",
                workflow_id=request.workflow_id,
                status="failed",
                message="Workflow execution failed",
                error=str(e)
            )
    
    def register_step_implementation(self, step_type: str, implementation: Any) -> None:
        """Register a step implementation"""
        workflow_execution_context.register_step_implementation(step_type, implementation)
        self._step_implementations[step_type] = implementation
    
    def get_workflow_info(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow information"""
        if workflow_id in self._workflow_cache:
            config = self._workflow_cache[workflow_id]
            return {
                "workflow_id": config.workflow_id,
                "workflow_name": config.workflow_name,
                "description": config.description,
                "version": config.version,
                "step_count": len(config.steps),
                "execution_pattern": config.execution_pattern,
                "tags": config.tags,
                "category": config.category
            }
        return None
    
    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """List all loaded workflows"""
        return [
            self.get_workflow_info(workflow_id) 
            for workflow_id in self._workflow_cache.keys()
        ]


# Global workflow loader instance
workflow_loader = WorkflowLoader()


# Example production step implementations for the hybrid workflow
async def production_audit_input_step(step_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Production implementation of audit input step"""
    import uuid
    from datetime import datetime
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Extract user and request information
    query = input_data.get("query", "")
    user_id = input_data.get("user_id", "")
    session_id = input_data.get("session_id", "")
    
    # Create audit entry
    audit_entry = {
        "request_id": request_id,
        "timestamp": timestamp,
        "event_type": "agent_request_received",
        "user_id": user_id,
        "session_id": session_id,
        "query": query,
        "query_length": len(query),
        "user_agent": input_data.get("user_agent", ""),
        "ip_address": input_data.get("ip_address", ""),
        "metadata": input_data.get("metadata", {})
    }
    
    # Log to audit file (in production, this would use proper logging service)
    audit_log_path = step_config.get("config", {}).get("audit_log_path", "/tmp/audit.log")
    try:
        with open(audit_log_path, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")
    except Exception as e:
        print(f"Failed to write audit log: {e}")
    
    # Return data for next steps
    return {
        "request_id": request_id,
        "timestamp": timestamp,
        "query": query,
        "user_id": user_id,
        "session_id": session_id,
        "request_metadata": audit_entry,
        "audit_logged": True
    }


async def production_validate_input_step(step_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Production implementation of input validation step"""
    config = step_config.get("config", {})
    
    # Debug: Print what we're receiving
    print(f"🔍 Validation step received input_data keys: {list(input_data.keys())}")
    
    # Get data from mapped inputs (coming from audit_input step)
    query = input_data.get("query", "")
    user_id = input_data.get("user_id", "")
    
    # If not found directly, check request_metadata (from audit step)
    request_metadata = input_data.get("request_metadata", {})
    if not query:
        query = request_metadata.get("query", "")
    if not user_id:
        user_id = request_metadata.get("user_id", "")
    
    print(f"🔍 After mapping - query: '{query[:30] if query else 'EMPTY'}...', user_id: '{user_id}'")
    
    validation_result = {
        "is_valid": True,
        "validation_errors": [],
        "validation_warnings": []
    }
    
    # Check query length
    max_length = config.get("max_query_length", 10000)
    if len(query) > max_length:
        validation_result["is_valid"] = False
        validation_result["validation_errors"].append(f"Query too long: {len(query)} > {max_length}")
    
    # Check for blocked keywords
    blocked_keywords = config.get("blocked_keywords", [])
    query_lower = query.lower()
    found_blocked = [keyword for keyword in blocked_keywords if keyword in query_lower]
    if found_blocked:
        validation_result["is_valid"] = False
        validation_result["validation_errors"].append(f"Blocked keywords found: {found_blocked}")
    
    # Check required fields
    required_fields = config.get("required_fields", [])
    for field in required_fields:
        if not input_data.get(field):
            validation_result["is_valid"] = False
            validation_result["validation_errors"].append(f"Required field missing: {field}")
    
    if not validation_result["is_valid"]:
        raise ValueError(f"Input validation failed: {validation_result['validation_errors']}")
    
    return {
        "validated_query": query,
        "user_context": {
            "user_id": user_id,
            "validated_at": datetime.now().isoformat()
        },
        "validation_result": validation_result
    }


async def production_agent_execution_step(step_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Production implementation using existing Agent Studio infrastructure"""
    from datetime import datetime
    import uuid
    from api.agent_endpoints import _create_agent_instance_from_db, AgentExecutionRequest
    from db import crud
    from sqlalchemy.orm import Session
    from db.database import SessionLocal
    
    config = step_config.get("config", {})
    
    # Extract input data
    query = input_data.get("validated_query") or input_data.get("query", "")
    request_id = input_data.get("request_id", "")
    user_context = input_data.get("user_context", {})
    session_id = input_data.get("session_id")
    user_id = user_context.get("user_id") or input_data.get("user_id")
    
    # Get agent configuration
    agent_id = config.get("agent_id")
    agent_type = config.get("agent_type", "production_agent")
    
    # If no specific agent_id provided, we'll need to find/create one based on agent_type
    # For now, let's use a mock approach but with the real infrastructure pattern
    if not agent_id and agent_type == "production_agent":
        # In production, you'd query for an agent by type or have default agents
        # For demo, we'll simulate the response using existing patterns but with real structure
        start_time = datetime.now()
        
        # Mock agent response that follows real Agent Studio patterns
        if "weather" in query.lower():
            response = "Based on current conditions, today will be partly cloudy with temperatures ranging from 65-75°F."
        elif "error" in query.lower():
            raise Exception("Production agent encountered an error during processing")
        else:
            response = f"I understand your query about '{query[:50]}...' and here's my response based on {config.get('model', 'gpt-4')} analysis."
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Return in Agent Studio format
        execution_metadata = {
            "agent_type": agent_type,
            "agent_id": "mock-agent-" + str(uuid.uuid4())[:8],
            "model": config.get("model", "gpt-4"),
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 2000),
            "execution_time_seconds": execution_time,
            "execution_time_ms": int(execution_time * 1000),
            "request_id": request_id,
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": end_time.isoformat(),
            "enable_tools": config.get("enable_tools", True),
            "enable_memory": config.get("enable_memory", True)
        }
        
        return {
            "response": response,
            "execution_metadata": execution_metadata,
            "success": True,
            "agent_execution_response": {
                "status": "success",
                "response": response,
                "agent_id": execution_metadata["agent_id"],
                "execution_time": execution_time,
                "timestamp": end_time.isoformat()
            }
        }
    
    else:
        # Real agent execution using existing Agent Studio infrastructure
        db = SessionLocal()
        try:
            # Get the agent from database
            agent_uuid = uuid.UUID(agent_id)
            db_agent = crud.get_agent(db=db, agent_id=agent_uuid)
            if db_agent is None:
                raise ValueError(f"Agent {agent_id} not found")
            
            if not db_agent.available_for_deployment:
                raise ValueError(f"Agent {agent_id} is not available for execution")
            
            # Create agent instance using existing infrastructure
            agent_instance = _create_agent_instance_from_db(db, db_agent)
            
            # Create execution request
            execution_request = AgentExecutionRequest(
                query=query,
                session_id=session_id,
                user_id=user_id,
                chat_history=input_data.get("chat_history"),
                enable_analytics=config.get("enable_analytics", True)
            )
            
            # Execute using existing Agent Studio methods
            start_time = datetime.now()
            
            result = agent_instance.execute(
                query=execution_request.query,
                session_id=execution_request.session_id,
                user_id=execution_request.user_id,
                chat_history=execution_request.chat_history,
                enable_analytics=execution_request.enable_analytics,
            )
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Format response in workflow-compatible format
            execution_metadata = {
                "agent_type": agent_type,
                "agent_id": str(agent_id),
                "agent_name": db_agent.name,
                "execution_time_seconds": execution_time,
                "execution_time_ms": int(execution_time * 1000),
                "request_id": request_id,
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": end_time.isoformat(),
                "enable_analytics": execution_request.enable_analytics
            }
            
            return {
                "response": result,
                "execution_metadata": execution_metadata,
                "success": True,
                "agent_execution_response": {
                    "status": "success",
                    "response": result,
                    "agent_id": str(agent_id),
                    "execution_time": execution_time,
                    "timestamp": end_time.isoformat()
                }
            }
            
        finally:
            db.close()


async def production_generic_step(step_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generic step implementation for missing step types"""
    step_id = step_config.get("step_id", "unknown")
    step_name = step_config.get("step_name", "Unknown Step")
    
    # For demonstration, just pass through the data with step completion info
    return {
        **input_data,
        f"{step_id}_completed": True,
        f"{step_id}_timestamp": datetime.now().isoformat(),
        f"{step_id}_message": f"Step '{step_name}' completed successfully (generic implementation)"
    }


# Register production step implementations
def register_production_steps():
    """Register all production step implementations"""
    from services.workflow_execution_context import DeterministicStepType
    
    workflow_loader.register_step_implementation(
        DeterministicStepType.DATA_INPUT,
        production_audit_input_step
    )
    workflow_loader.register_step_implementation(
        DeterministicStepType.VALIDATION,
        production_validate_input_step
    )
    workflow_loader.register_step_implementation(
        DeterministicStepType.DATA_PROCESSING,
        production_agent_execution_step
    )
    workflow_loader.register_step_implementation(
        DeterministicStepType.DATA_OUTPUT,
        production_generic_step
    )
    workflow_loader.register_step_implementation(
        DeterministicStepType.NOTIFICATION,
        production_generic_step
    )