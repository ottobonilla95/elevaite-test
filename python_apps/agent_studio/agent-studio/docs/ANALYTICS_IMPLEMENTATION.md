# Agent Studio Analytics Implementation

## Overview

This document describes the comprehensive workflow analytics implementation for the Agent Studio system. The analytics solution provides detailed insights into agent performance, tool usage, workflow execution, and user session patterns.

## Architecture

### Components

1. **Database Models** (`db/models.py`)
   - `AgentExecutionMetrics`: Tracks individual agent executions
   - `ToolUsageMetrics`: Tracks tool usage within executions
   - `WorkflowMetrics`: Tracks multi-agent workflows
   - `SessionMetrics`: Tracks user sessions

2. **Analytics Service** (`services/analytics_service.py`)
   - Context managers for tracking executions, tools, and workflows
   - Automatic metrics collection and logging
   - Integration with the existing logger package

3. **API Endpoints** (`api/analytics_endpoints.py`)
   - RESTful endpoints for retrieving analytics data
   - Real-time dashboard serving
   - Comprehensive summary endpoints

4. **Dashboard** (`templates/analytics_dashboard.html`)
   - Interactive web dashboard with charts
   - Real-time metrics display
   - Data export functionality

## Database Schema

### AgentExecutionMetrics
```sql
- execution_id (UUID, unique)
- agent_id (UUID, FK to agents)
- agent_name (VARCHAR)
- start_time, end_time (TIMESTAMP)
- duration_ms (INTEGER)
- status (VARCHAR: success/failure/timeout/in_progress)
- query, response (TEXT)
- error_message (TEXT)
- tools_called (JSONB)
- tool_count, retry_count (INTEGER)
- session_id, user_id, correlation_id (VARCHAR)
- tokens_used, api_calls_count (INTEGER)
```

### ToolUsageMetrics
```sql
- usage_id (UUID, unique)
- tool_name (VARCHAR)
- execution_id (UUID, FK to agent_execution_metrics)
- start_time, end_time (TIMESTAMP)
- duration_ms (INTEGER)
- status (VARCHAR)
- input_data, output_data (JSONB)
- error_message (TEXT)
- external_api_called (VARCHAR)
- api_response_time_ms, api_status_code (INTEGER)
```

### WorkflowMetrics
```sql
- workflow_id (UUID, unique)
- workflow_type (VARCHAR)
- start_time, end_time (TIMESTAMP)
- duration_ms (INTEGER)
- status (VARCHAR)
- agents_involved (JSONB)
- agent_count (INTEGER)
- total_tool_calls, total_api_calls (INTEGER)
- total_tokens_used (INTEGER)
- session_id, user_id (VARCHAR)
- user_satisfaction_score, task_completion_rate (FLOAT)
```

### SessionMetrics
```sql
- session_id (VARCHAR, unique)
- start_time, end_time (TIMESTAMP)
- duration_ms (INTEGER)
- user_id, user_agent, ip_address (VARCHAR)
- total_queries, successful_queries, failed_queries (INTEGER)
- agents_used (JSONB)
- unique_agents_count (INTEGER)
- average_response_time_ms (FLOAT)
- total_tokens_used (INTEGER)
- is_active (BOOLEAN)
```

## API Endpoints

### Analytics Endpoints
- `GET /api/analytics/dashboard` - Serve analytics dashboard
- `GET /api/analytics/agents/usage` - Agent usage statistics
- `GET /api/analytics/tools/usage` - Tool usage statistics
- `GET /api/analytics/workflows/performance` - Workflow performance metrics
- `GET /api/analytics/errors/summary` - Error analysis
- `GET /api/analytics/sessions/activity` - Session activity metrics
- `GET /api/analytics/summary` - Comprehensive analytics summary
- `GET /api/analytics/executions/{execution_id}` - Specific execution details
- `GET /api/analytics/sessions/{session_id}` - Specific session details
- `GET /api/analytics/health` - Health check

### Query Parameters
All analytics endpoints support:
- `start_date` (ISO format): Start date for analytics
- `end_date` (ISO format): End date for analytics  
- `days` (integer): Number of days to look back (default: 7)

## Usage Examples

### Tracking Agent Execution
```python
from services.analytics_service import analytics_service

with analytics_service.track_agent_execution(
    agent_id=agent.agent_id,
    agent_name="CommandAgent",
    query="search for weather",
    session_id="session_123",
    user_id="user_456"
) as execution_id:
    result = agent.execute(query)
    # Metrics are automatically collected
```

### Tracking Tool Usage
```python
with analytics_service.track_tool_usage(
    tool_name="web_search",
    execution_id=execution_id,
    input_data={"query": "weather forecast"},
    external_api_called="google_search"
) as usage_id:
    result = tool.execute(input_data)
    # Tool metrics are automatically collected
```

### Tracking Workflows
```python
with analytics_service.track_workflow(
    workflow_type="multi_agent",
    agents_involved=["WebAgent", "DataAgent"],
    session_id="session_123"
) as workflow_id:
    result = execute_multi_agent_workflow()
    # Workflow metrics are automatically collected
```

## Integration Points

### Command Agent Integration
The `CommandAgent` has been enhanced with comprehensive analytics tracking:
- Execution tracking with context managers
- Tool usage tracking for each tool call
- Workflow tracking for multi-agent orchestration
- Session management and correlation

### Logging Integration
The analytics service integrates with the existing `fastapi-logger` package:
- Structured logging for all analytics events
- Fallback to standard logging if fastapi-logger unavailable
- Debug, info, and error level logging

## Dashboard Features

### Real-time Metrics
- Active sessions count
- Queries per hour
- Average response time
- Success rate

### Visualizations
- Agent usage distribution (doughnut chart)
- Tool usage frequency (bar chart)
- Workflow performance trends
- Error analysis

### Interactive Features
- Time range selection (24h, 7d, 30d)
- Auto-refresh every 30 seconds
- CSV data export
- Responsive design

## Installation and Setup

### 1. Database Migration
```bash
cd python_apps/agent_studio/agent-studio
python db/migrations/add_analytics_tables.py
```

### 2. Install Dependencies
The analytics system uses existing dependencies:
- FastAPI for API endpoints
- SQLAlchemy for database operations
- Chart.js for dashboard visualizations

### 3. Access Dashboard
Navigate to: `http://localhost:8000/api/analytics/dashboard`

## Performance Considerations

### Database Indexes
The migration creates indexes on frequently queried columns:
- `agent_execution_metrics(agent_id, session_id, start_time)`
- `tool_usage_metrics(tool_name, execution_id)`
- `workflow_metrics(workflow_type, session_id)`
- `session_metrics(user_id, start_time)`

### Data Retention
Consider implementing data retention policies:
- Archive old metrics data
- Aggregate historical data for long-term trends
- Implement data cleanup procedures

### Monitoring
- Monitor analytics table sizes
- Track query performance
- Set up alerts for high error rates

## Future Enhancements

### Advanced Analytics
- Machine learning for performance prediction
- Anomaly detection for unusual patterns
- Cost analysis for external API usage
- User behavior analysis

### Enhanced Visualizations
- Time series charts for trends
- Heatmaps for usage patterns
- Geographic distribution of users
- Performance correlation analysis

### Integration Improvements
- Real-time streaming analytics
- Integration with external monitoring tools
- Custom alerting rules
- Advanced filtering and search

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure all paths are correctly configured
2. **Database connection**: Verify DATABASE_URL environment variable
3. **Missing tables**: Run the migration script
4. **Dashboard not loading**: Check template file path

### Debugging
- Check application logs for analytics service errors
- Verify database connectivity
- Ensure all required environment variables are set
- Test API endpoints individually

## Security Considerations

### Data Privacy
- Sensitive data is truncated in analytics storage
- User IDs are optional and can be anonymized
- Query content can be excluded from tracking

### Access Control
- Analytics endpoints should be protected with authentication
- Consider role-based access for different analytics views
- Implement rate limiting for analytics API calls

## Conclusion

The Agent Studio analytics implementation provides comprehensive insights into system performance and usage patterns. The modular design allows for easy extension and customization while maintaining high performance and reliability.
