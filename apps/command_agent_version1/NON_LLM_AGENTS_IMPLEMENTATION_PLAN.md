# Non-LLM Based Software Agents Implementation Plan

## Overview

This document outlines the implementation plan for adding non-LLM based software agents to the Agent Studio platform. These agents will handle deterministic tasks, automated workflows, and rule-based processing without requiring LLM inference.

## Current Architecture Analysis

### Backend (python_apps/agent_studio)
- **Base Agent Class**: `Agent` with OpenAI integration, Redis communication, analytics
- **Agent Types**: CommandAgent, WebAgent, APIAgent, DataAgent, ToshibaAgent, etc.
- **Execution Patterns**: Single agent execution, multi-agent workflows, streaming responses
- **Database Layer**: Complete agent configuration persistence with versioning
- **Tool System**: Function registry with `@function_schema` decorator

### Frontend (app/command_agent_version_1)
- **Visual Designer**: React Flow-based canvas with drag-and-drop
- **Agent Components**: AgentNode, AgentConfigModal, ConfigPanel, DesignerCanvas
- **Configuration**: Multi-tabbed interface with real-time editing
- **Workflow Management**: Visual connections, deployment, testing interface

## Proposed Non-LLM Agent Types

### 1. Rule-Based Agents
- Decision tree execution
- Conditional logic workflows
- State machine implementations
- Regex pattern matching

### 2. Scripted Agents
- Shell command executors
- API orchestrators
- File system operations
- Database query agents

### 3. Reactive Agents
- Event-driven processors
- Webhook handlers
- Message queue consumers
- File watchers

## Implementation Architecture

### Backend Extensions

#### New Base Classes
```python
# agents/non_llm_base.py
class NonLLMAgent(Agent):
    """Base class for non-LLM agents"""
    execution_type: Literal["script", "rule", "reactive"] = "script"
    script_config: Optional[Dict] = None
    rule_config: Optional[Dict] = None
    
    async def execute_non_llm(self, input_data: str) -> str:
        """Execute without LLM inference"""
        pass
    
class ScriptAgent(NonLLMAgent):
    """Execute predefined scripts/commands"""
    execution_type = "script"
    
class RuleAgent(NonLLMAgent):
    """Rule-based decision making"""
    execution_type = "rule"
    
class ReactiveAgent(NonLLMAgent):
    """Event-driven processing"""
    execution_type = "reactive"
```

#### Execution Engine Enhancement
- Add non-LLM execution paths in `agent_base.py`
- Skip OpenAI integration for non-LLM agents
- Direct function execution without LLM interpretation
- Maintain analytics and Redis communication

#### Database Schema Extensions
```sql
-- Add columns to agents table
ALTER TABLE agents ADD COLUMN execution_engine VARCHAR(20) DEFAULT 'llm';
ALTER TABLE agents ADD COLUMN script_content TEXT;
ALTER TABLE agents ADD COLUMN rule_definition JSONB;
ALTER TABLE agents ADD COLUMN event_config JSONB;
ALTER TABLE agents ADD COLUMN timeout_seconds INTEGER DEFAULT 30;
ALTER TABLE agents ADD COLUMN retry_count INTEGER DEFAULT 0;

-- Add index for performance
CREATE INDEX idx_agents_execution_engine ON agents(execution_engine);
```

### Frontend Extensions

#### Agent Type Enhancements
```typescript
// Update AGENT_TYPE enum
AGENT_TYPE = {
  ...existing,
  SCRIPT: "script",
  RULE_ENGINE: "rule_engine", 
  EVENT_PROCESSOR: "event_processor",
  SCHEDULER: "scheduler",
  FILE_WATCHER: "file_watcher",
  API_POLLER: "api_poller"
}
```

#### New Configuration Components
- **ScriptConfigPanel**: Code editor for script input, environment variables
- **RuleConfigPanel**: Visual rule builder for conditional logic
- **EventConfigPanel**: Event source configuration (webhooks, queues)
- **NonLLMAgentNode**: Visual indicators for non-LLM agents

#### UI Enhancements
- Separate configuration tabs for non-LLM agents
- Script editor with syntax highlighting
- Rule builder with drag-and-drop conditions
- Test execution capabilities
- Performance metrics display

## Specific Agent Implementations

### 1. Script Execution Agent
```python
class ScriptExecutionAgent(ScriptAgent):
    """Execute shell commands or Python scripts"""
    
    async def execute(self, input_data: str) -> str:
        # Validate script safety
        # Execute with timeout and resource limits
        # Capture stdout/stderr
        # Return structured output
        pass
```

### 2. Rule Engine Agent
```python
class RuleEngineAgent(RuleAgent):
    """Process data through predefined rules"""
    
    async def execute(self, input_data: str) -> str:
        # Parse input data
        # Apply rules in order
        # Return decision/action
        pass
```

### 3. Event Processing Agent
```python
class EventProcessingAgent(ReactiveAgent):
    """Process events from queues/webhooks"""
    
    async def process_event(self, event: Dict) -> Dict:
        # Validate event structure  
        # Apply processing logic
        # Trigger downstream actions
        pass
```

### 4. API Polling Agent
```python
class APIPollingAgent(ReactiveAgent):
    """Poll external APIs for changes"""
    
    async def poll_and_process(self) -> List[Dict]:
        # Poll external API
        # Detect changes since last poll
        # Process new data
        pass
```

## Tool Integration Strategy

### Direct Tool Execution
```python
class DirectToolExecutor:
    """Execute tools directly without LLM"""
    
    def execute_tool(self, tool_name: str, params: Dict) -> Any:
        # Validate parameters against schema
        # Execute tool function directly
        # Format and return results
        pass
```

### Parameter Mapping
- Static parameter mapping from input to tools
- JSON-based configuration for parameter extraction
- Support for complex data transformations

## Workflow Integration

### Mixed Workflows
- Support LLM and non-LLM agents in same workflow
- Data transformation between agent types
- Conditional routing based on agent output type
- Unified error handling and logging

### Execution Orchestration
- CommandAgent orchestrates both agent types
- Type-aware execution routing
- Consistent response formatting
- Performance optimization for non-LLM agents

## Configuration Management

### Backend Configuration
- JSON schemas for different agent types
- Validation for script syntax and safety
- Rule engine configuration templates
- Event source connection management

### Frontend Configuration
- Tabbed interface for different agent types
- Monaco editor for script editing
- Visual rule builder components
- Real-time validation and testing

## Monitoring and Analytics

### Non-LLM Specific Metrics
- Script execution times and success rates
- Rule evaluation statistics and paths taken
- Event processing throughput
- Resource usage (CPU, memory, disk)
- Error tracking and debugging information

### Dashboard Enhancements
- Separate analytics for LLM vs non-LLM agents
- Performance comparisons
- Cost analysis (no LLM inference costs)
- Reliability metrics

## Security Considerations

### Script Execution Safety
- Sandboxed execution environments
- Resource limits (CPU, memory, time)
- Restricted file system access
- Network access controls
- Input sanitization and validation

### Rule Engine Security
- Prevent code injection in rules
- Validate rule syntax before execution
- Limit rule complexity and nesting
- Audit trail for rule changes

## Implementation Phases

### Phase 1: Foundation (2-3 weeks)
1. Create `NonLLMAgent` base classes
2. Add database schema extensions
3. Update frontend agent type selector
4. Basic script execution agent
5. Simple configuration UI

### Phase 2: Core Agents (3-4 weeks)
1. Implement `ScriptExecutionAgent` with safety measures
2. Add script configuration UI with editor
3. Implement `RuleEngineAgent` with basic rules
4. Create rule builder UI components
5. Test with simple workflows

### Phase 3: Advanced Features (4-5 weeks)
1. Event processing capabilities
2. API polling agents
3. Mixed workflow support
4. Advanced analytics and monitoring
5. Security hardening and testing

### Phase 4: Production Ready (2-3 weeks)
1. Performance optimization
2. Comprehensive error handling
3. Documentation and examples
4. User training materials
5. Production deployment

## Success Metrics

### Performance
- Non-LLM agents execute 10x faster than LLM equivalents
- Reduced latency for deterministic tasks
- Lower resource usage per execution

### Reliability
- 99.9% success rate for well-configured agents
- Predictable execution times
- Robust error handling and recovery

### Usability
- Intuitive configuration interface
- Easy migration from LLM to non-LLM agents
- Comprehensive testing capabilities

## Future Enhancements

### Advanced Agent Types
- Machine learning model inference agents
- Database synchronization agents
- File processing pipelines
- Scheduled task management

### Integration Capabilities
- External system connectors
- Message queue integrations
- Workflow templates and marketplace
- Advanced debugging tools

---

*This plan provides a comprehensive roadmap for implementing non-LLM based software agents while maintaining compatibility with the existing Agent Studio architecture.*