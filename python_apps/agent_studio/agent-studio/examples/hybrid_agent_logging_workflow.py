"""
Hybrid Agent + Logging Workflow

Demonstrates integration between deterministic logging steps and AI agent execution.
Workflow: Log input → Execute AI Agent → Log output → Save to database

This shows how deterministic steps can enhance AI workflows with:
- Request/response logging for audit trails
- Data validation before/after agent execution
- Structured error handling and monitoring
"""

import asyncio
import tempfile
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from services.workflow_execution_context import (
    workflow_execution_context,
    DeterministicStepType
)
from steps.base_deterministic_step import (
    BaseDeterministicStep, DataInputStep, DataOutputStep,
    StepConfig, StepResult, StepStatus, StepValidationResult
)


class AgentRequestLoggerStep(DataInputStep):
    """
    Log incoming agent requests for audit trail.
    
    Input: User query and request metadata
    Output: Logged request with unique ID and timestamp
    """
    
    def validate_config(self) -> StepValidationResult:
        result = StepValidationResult()
        
        config = self.config.config
        log_file = config.get("log_file_path")
        if not log_file:
            result.errors.append("log_file_path is required")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    def get_required_inputs(self) -> List[str]:
        return ["query", "user_id"]
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        config = self.config.config
        log_file_path = config.get("log_file_path")
        
        request_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create structured log entry
        log_entry = {
            "request_id": request_id,
            "timestamp": timestamp,
            "event_type": "agent_request",
            "data": {
                "query": input_data.get("query"),
                "user_id": input_data.get("user_id"),
                "session_id": input_data.get("session_id"),
                "agent_id": input_data.get("agent_id"),
                "metadata": input_data.get("metadata", {})
            }
        }
        
        # Write to log file
        Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Pass through original data with request tracking
        output_data = input_data.copy()
        output_data.update({
            "request_id": request_id,
            "request_timestamp": timestamp,
            "logged": True
        })
        
        return StepResult(
            status=StepStatus.COMPLETED,
            data=output_data,
            metadata={"log_entry": log_entry}
        )


class MockAgentExecutionStep(BaseDeterministicStep):
    """
    Mock AI agent execution step for testing.
    In real implementation, this would integrate with existing agent execution.
    
    Input: User query and request data
    Output: Agent response with execution metadata
    """
    
    def __init__(self, config: StepConfig):
        super().__init__(config)
        # Override step type for agent execution
        self.step_type = DeterministicStepType.DATA_PROCESSING
    
    def validate_config(self) -> StepValidationResult:
        result = StepValidationResult()
        
        config = self.config.config
        agent_name = config.get("agent_name")
        if not agent_name:
            result.errors.append("agent_name is required")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    def get_required_inputs(self) -> List[str]:
        return ["query", "request_id"]
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        config = self.config.config
        agent_name = config.get("agent_name", "TestAgent")
        mock_delay = config.get("mock_delay_seconds", 0.1)
        
        # Simulate agent processing time
        await asyncio.sleep(mock_delay)
        
        query = input_data.get("query", "")
        request_id = input_data.get("request_id")
        
        # Mock agent response based on query
        if "error" in query.lower():
            # Simulate agent error
            raise Exception("Mock agent error: Database connection failed")
        
        elif "weather" in query.lower():
            response = "The weather today is sunny with a high of 75°F and low of 60°F."
        elif "time" in query.lower():
            response = f"The current time is {datetime.now().strftime('%I:%M %p')}."
        else:
            response = f"I understand you're asking about: '{query}'. This is a mock response from {agent_name}."
        
        # Create agent execution result
        execution_result = {
            "request_id": request_id,
            "agent_name": agent_name,
            "query": query,
            "response": response,
            "execution_time_ms": int(mock_delay * 1000),
            "tokens_used": len(query) + len(response),  # Mock token count
            "success": True,
            "metadata": {
                "model": "mock-gpt-4",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        
        # Pass through request data with agent response
        output_data = input_data.copy()
        output_data.update({
            "agent_response": response,
            "execution_result": execution_result,
            "agent_execution_completed": True
        })
        
        return StepResult(
            status=StepStatus.COMPLETED,
            data=output_data,
            metadata={"execution_result": execution_result}
        )


class AgentResponseLoggerStep(DataOutputStep):
    """
    Log agent responses for monitoring and analysis.
    
    Input: Agent execution result
    Output: Logged response data
    """
    
    def validate_config(self) -> StepValidationResult:
        result = StepValidationResult()
        
        config = self.config.config
        log_file = config.get("log_file_path")
        if not log_file:
            result.errors.append("log_file_path is required")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    def get_required_inputs(self) -> List[str]:
        return ["agent_response", "execution_result", "request_id"]
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        config = self.config.config
        log_file_path = config.get("log_file_path")
        
        timestamp = datetime.now().isoformat()
        execution_result = input_data.get("execution_result", {})
        
        # Create structured log entry for response
        log_entry = {
            "request_id": input_data.get("request_id"),
            "timestamp": timestamp,
            "event_type": "agent_response",
            "data": {
                "response": input_data.get("agent_response"),
                "success": execution_result.get("success", True),
                "execution_time_ms": execution_result.get("execution_time_ms"),
                "tokens_used": execution_result.get("tokens_used"),
                "agent_name": execution_result.get("agent_name"),
                "metadata": execution_result.get("metadata", {})
            }
        }
        
        # Write to log file
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        return StepResult(
            status=StepStatus.COMPLETED,
            data={
                "logged_response": True,
                "log_entry": log_entry,
                "response_data": input_data
            },
            metadata={"log_entry": log_entry}
        )


class DatabaseSaverStep(DataOutputStep):
    """
    Mock database saver step.
    In real implementation, this would save to actual database.
    
    Input: Complete interaction data
    Output: Database save confirmation
    """
    
    def validate_config(self) -> StepValidationResult:
        result = StepValidationResult()
        
        config = self.config.config
        table_name = config.get("table_name")
        if not table_name:
            result.errors.append("table_name is required")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        config = self.config.config
        table_name = config.get("table_name", "agent_interactions")
        mock_db_file = config.get("mock_db_file")
        
        # Create database record
        db_record = {
            "id": str(uuid.uuid4()),
            "request_id": input_data.get("request_id"),
            "user_id": input_data.get("user_id"),
            "query": input_data.get("query"),
            "response": input_data.get("agent_response"),
            "agent_name": input_data.get("execution_result", {}).get("agent_name"),
            "execution_time_ms": input_data.get("execution_result", {}).get("execution_time_ms"),
            "tokens_used": input_data.get("execution_result", {}).get("tokens_used"),
            "success": input_data.get("execution_result", {}).get("success", True),
            "timestamp": datetime.now().isoformat(),
            "table_name": table_name
        }
        
        # Mock database save to JSON file
        if mock_db_file:
            Path(mock_db_file).parent.mkdir(parents=True, exist_ok=True)
            with open(mock_db_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(db_record) + "\n")
        
        return StepResult(
            status=StepStatus.COMPLETED,
            data={
                "saved_to_database": True,
                "record_id": db_record["id"],
                "table_name": table_name
            },
            rollback_data={
                "record_id": db_record["id"],
                "table_name": table_name
            }
        )


def create_hybrid_workflow_config(temp_dir: str) -> Dict[str, Any]:
    """Create hybrid workflow configuration"""
    log_file = str(Path(temp_dir) / "agent_audit.log")
    db_file = str(Path(temp_dir) / "mock_database.jsonl")
    
    return {
        "workflow_id": "hybrid_agent_logging_workflow",
        "workflow_name": "AI Agent with Logging Workflow",
        "description": "Hybrid workflow combining deterministic logging with AI agent execution",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "log_request",
                "step_name": "Log Agent Request",
                "step_type": "data_input",
                "dependencies": [],
                "config": {
                    "log_file_path": log_file
                }
            },
            {
                "step_id": "execute_agent",
                "step_name": "Execute AI Agent",
                "step_type": "data_processing",
                "dependencies": ["log_request"],
                "config": {
                    "agent_name": "HybridTestAgent",
                    "mock_delay_seconds": 0.2
                }
            },
            {
                "step_id": "log_response",
                "step_name": "Log Agent Response",
                "step_type": "data_output",
                "dependencies": ["execute_agent"],
                "config": {
                    "log_file_path": log_file
                }
            },
            {
                "step_id": "save_to_database",
                "step_name": "Save to Database",
                "step_type": "data_output",
                "dependencies": ["log_response"],
                "rollback_enabled": True,
                "config": {
                    "table_name": "agent_interactions",
                    "mock_db_file": db_file
                }
            }
        ]
    }


def register_hybrid_steps():
    """Register all hybrid workflow step implementations"""
    workflow_execution_context.register_step_implementation(
        DeterministicStepType.DATA_INPUT,
        create_agent_request_logger_step
    )
    workflow_execution_context.register_step_implementation(
        DeterministicStepType.DATA_PROCESSING,
        create_mock_agent_execution_step
    )
    workflow_execution_context.register_step_implementation(
        DeterministicStepType.DATA_OUTPUT,
        create_agent_response_logger_or_db_step
    )


async def create_agent_request_logger_step(step_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Step implementation wrapper for AgentRequestLoggerStep"""
    config = StepConfig(
        step_id=step_config.get("step_id", ""),
        step_name=step_config.get("step_name", ""),
        step_type=DeterministicStepType.DATA_INPUT,
        config=step_config.get("config", {})
    )
    
    step = AgentRequestLoggerStep(config)
    result = await step.execute(input_data)
    return result.data or {}


async def create_mock_agent_execution_step(step_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Step implementation wrapper for MockAgentExecutionStep"""
    config = StepConfig(
        step_id=step_config.get("step_id", ""),
        step_name=step_config.get("step_name", ""),
        step_type=DeterministicStepType.DATA_PROCESSING,
        config=step_config.get("config", {})
    )
    
    step = MockAgentExecutionStep(config)
    result = await step.execute(input_data)
    return result.data or {}


async def create_agent_response_logger_or_db_step(step_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Step implementation wrapper for response logging or database steps"""
    step_id = step_config.get("step_id", "")
    
    config = StepConfig(
        step_id=step_id,
        step_name=step_config.get("step_name", ""),
        step_type=DeterministicStepType.DATA_OUTPUT,
        rollback_enabled=step_config.get("rollback_enabled", False),
        config=step_config.get("config", {})
    )
    
    if step_id == "log_response":
        step = AgentResponseLoggerStep(config)
    elif step_id == "save_to_database":
        step = DatabaseSaverStep(config)
    else:
        # Default to response logger
        step = AgentResponseLoggerStep(config)
    
    result = await step.execute(input_data)
    return result.data or {}


def create_test_agent_requests() -> List[Dict[str, Any]]:
    """Create test agent requests"""
    return [
        {
            "query": "What's the weather like today?",
            "user_id": "user_123",
            "session_id": "session_456",
            "agent_id": "weather_agent",
            "metadata": {"source": "web_chat", "priority": "normal"}
        },
        {
            "query": "What time is it?",
            "user_id": "user_789",
            "session_id": "session_012",
            "agent_id": "time_agent",
            "metadata": {"source": "api", "priority": "high"}
        },
        {
            "query": "This should cause an error",
            "user_id": "user_error",
            "session_id": "session_error",
            "agent_id": "test_agent",
            "metadata": {"source": "test", "priority": "low"}
        }
    ]


async def test_hybrid_workflow():
    """Test the hybrid agent + logging workflow"""
    with tempfile.TemporaryDirectory() as temp_dir:
        print("🤖 Testing Hybrid Agent + Logging Workflow")
        print(f"📁 Output directory: {temp_dir}")
        
        # Register step implementations
        register_hybrid_steps()
        
        # Create workflow configuration
        workflow_config = create_hybrid_workflow_config(temp_dir)
        
        # Test requests
        test_requests = create_test_agent_requests()
        
        for i, request in enumerate(test_requests):
            print(f"\n🔄 Processing request {i+1}/{len(test_requests)}")
            print(f"   Query: {request['query']}")
            
            try:
                # Use regular context manager (not async)
                with workflow_execution_context.deterministic_workflow_execution(
                    workflow_name="Hybrid Agent Test",
                    workflow_config=workflow_config,
                    user_id=request["user_id"]
                ) as execution_id:
                    
                    print(f"   Execution ID: {execution_id}")
                    
                    # Add input data to workflow context
                    workflow_execution_context._active_workflows[execution_id]["step_data"]["input"] = request
                    
                    # Execute all steps
                    results = await workflow_execution_context.execute_workflow(execution_id)
                    
                    print("   ✅ Request processed successfully!")
                    
                    # Show key results
                    if "save_to_database" in results:
                        db_result = results["save_to_database"]
                        print(f"   💾 Saved to database: {db_result.get('record_id')}")
                    
            except Exception as e:
                print(f"   ❌ Request failed: {e}")
        
        # Show output files
        print("\n📄 Generated Files:")
        for file_path in Path(temp_dir).glob("*"):
            print(f"   - {file_path.name} ({file_path.stat().st_size} bytes)")
            
            # Show first few lines
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()[:3]
                    for line in lines:
                        print(f"     {line.strip()}")
                    if len(lines) >= 3:
                        print("     ...")
            except:
                pass


async def main():
    """Run hybrid workflow test"""
    print("🧪 Testing Hybrid Deterministic + AI Agent Workflow")
    print("=" * 60)
    
    await test_hybrid_workflow()
    
    print("\n🎉 Hybrid workflow test completed!")


if __name__ == "__main__":
    asyncio.run(main())