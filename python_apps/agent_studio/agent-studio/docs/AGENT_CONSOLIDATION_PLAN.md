# Agent Consolidation Plan

## Overview
Long-term plan to consolidate all agents to use the base class execution method, unless they require specific execution functions.

## Current State Analysis

### ✅ Agents Already Using Base Class
- **WebAgent**: ✅ Just calls `super().execute()` 
- **DataAgent**: ✅ Just calls `super().execute()`
- **APIAgent**: ✅ Just calls `super().execute()`
- **ConsolePrinterAgent**: ✅ Just calls `super().execute()`

### 🔧 Agents with Custom Execution Logic
- **ToshibaAgent**: Has custom `execute_async()` with streaming
- **CommandAgent**: Has custom `execute_stream()` method
- **HelloWorldAgent**: Has custom `_execute()` method
- **SQLAgent**: Has completely custom async execution

## Migration Strategy

### Phase 1: Standardize Interface (Post-Demo)
```python
# Enhanced base Agent class
class Agent(BaseModel):
    # ... existing fields ...
    
    # New execution configuration
    execution_mode: Literal["standard", "streaming", "async"] = "standard"
    custom_execution_config: Optional[Dict[str, Any]] = None
    
    def execute(self, query: str, **kwargs) -> str:
        """Standard synchronous execution - works for 90% of agents"""
        # Current base implementation
        
    async def execute_async(self, query: str, **kwargs) -> AsyncGenerator[str, None]:
        """Async streaming execution for specialized agents"""
        # Default implementation that yields from execute()
        
    def execute_stream(self, query: str, **kwargs) -> Generator[str, None]:
        """Sync streaming execution for CommandAgent compatibility"""
        # Default implementation that yields from execute()
```

### Phase 2: Agent-Specific Customization via Configuration
```python
# Instead of custom execute methods, use configuration
class ToshibaAgent(Agent):
    execution_mode: Literal["async"] = "async"
    custom_execution_config: Dict = {
        "streaming": True,
        "model": "gpt-4o",
        "temperature": 0.6,
        "max_tokens": 2000,
        "custom_message_format": True
    }
    
    # No custom execute method needed!
```

### Phase 3: Base Class Handles All Execution Patterns
```python
class Agent(BaseModel):
    def execute(self, query: str, **kwargs) -> str:
        """Universal execution method"""
        
        # Route based on execution_mode
        if self.execution_mode == "async":
            return self._execute_async_sync_wrapper(query, **kwargs)
        elif self.execution_mode == "streaming":
            return self._execute_streaming_sync_wrapper(query, **kwargs)
        else:
            return self._execute_standard(query, **kwargs)
    
    def _execute_standard(self, query: str, **kwargs) -> str:
        """Current base implementation"""
        # Existing logic
        
    async def _execute_async_internal(self, query: str, **kwargs):
        """Async execution with custom config support"""
        config = self.custom_execution_config or {}
        
        # Handle ToshibaAgent-style execution
        if config.get("custom_message_format"):
            messages = self._build_toshiba_messages(query, **kwargs)
        else:
            messages = self._build_standard_messages(query, **kwargs)
            
        # Use agent-specific model/temperature
        model = config.get("model", self.model)
        temperature = config.get("temperature", self.temperature)
        
        # Execute with streaming if configured
        if config.get("streaming"):
            async for chunk in self._stream_response(messages, model, temperature):
                yield chunk
        else:
            yield self._get_response(messages, model, temperature)
```

## Implementation Benefits

### ✅ Advantages
1. **Single Execution Path**: All agents use the same base logic
2. **Configuration-Driven**: Differences handled via config, not code
3. **Maintainable**: One place to fix bugs, add features
4. **Consistent**: Same analytics, error handling, tool calling for all agents
5. **Flexible**: Can still customize behavior via configuration

### 🎯 Migration Steps (Post-Demo)

**Step 1: Enhance Base Class**
- Add `execution_mode` and `custom_execution_config` fields
- Implement routing logic in base `execute()` method
- Add async and streaming wrapper methods

**Step 2: Migrate Simple Agents**
- WebAgent, DataAgent, APIAgent, ConsolePrinterAgent ✅ (already done)

**Step 3: Migrate Complex Agents**
- **ToshibaAgent**: Convert custom logic to configuration
- **CommandAgent**: Move `execute_stream` logic to base class
- **HelloWorldAgent**: Convert `_execute` to configuration
- **SQLAgent**: Convert async logic to base class pattern

**Step 4: Database Migration**
- Update agent records to include new configuration fields
- Migrate existing custom execution settings to config

## Risk Mitigation

### For Demo Safety
- ✅ Keep all existing agent classes unchanged
- ✅ No modifications to execution logic
- ✅ Only add new features, don't remove old ones

### Post-Demo
- 🔧 Implement feature flags for gradual rollout
- 🔧 A/B test new base class vs old implementations
- 🔧 Maintain backward compatibility during transition

## End State

```python
# All agents become simple configuration objects
toshiba_agent = Agent(
    name="ToshibaAgent",
    execution_mode="async",
    custom_execution_config={
        "streaming": True,
        "model": "gpt-4o", 
        "custom_message_format": "toshiba",
        "temperature": 0.6
    },
    # ... rest of config from database
)

# No custom execute methods needed!
result = toshiba_agent.execute(query)  # Routes to async streaming automatically
```

## Current Issues to Fix

### Type Casting Issue in agent_base.py
```python
# Problem: Type mismatch in message concatenation
messages = (
    [{"role": "system", "content": system_prompt}]
    + cast(List[ChatCompletionMessageParam], converted_history)
    + [{"role": "user", "content": query}]
)

# Solution: Proper type handling needed
```

## Notes
- **Priority**: Post-demo implementation
- **Goal**: Single, powerful, configurable base class
- **Benefit**: Unified execution while preserving agent uniqueness
- **Status**: Planning phase - DO NOT implement before demo
