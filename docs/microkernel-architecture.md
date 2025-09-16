# Microkernel Architecture: Execution Runtime Extraction

This document outlines the revolutionary microkernel architecture that separates workflow orchestration from execution, enabling true horizontal scalability through Kubernetes pod isolation.

## Architecture Overview

The new architecture splits the workflow engine into two distinct layers:

1. **Orchestration Layer**: Manages workflows, agents, prompts, tools, and Kubernetes deployments
2. **Execution Runtime**: Lightweight, containerized runtime that executes single workflows in isolation

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Workflow API  │  │  Agent/Prompt   │  │   Kubernetes    │ │
│  │   Management    │  │   Management    │  │   Controller    │ │
│  │                 │  │                 │  │                 │ │
│  │ • CRUD Ops      │  │ • Agent Store   │  │ • Pod Creation  │ │
│  │ • Validation    │  │ • Prompt Store  │  │ • Scaling       │ │
│  │ • Routing       │  │ • Tool Registry │  │ • Monitoring    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼ HTTP Request to Pod
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION RUNTIME                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Lightweight Execution Pod                     │ │
│  │                                                             │ │
│  │  • Single Workflow JSON                                    │ │
│  │  • Minimal Dependencies (execution core only)              │ │
│  │  • Step Registry (embedded)                                │ │
│  │  • Execution Engine                                        │ │
│  │  • Streaming Response                                      │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Key Benefits

### 1. **True Horizontal Scalability**
- Each workflow execution gets its own isolated Kubernetes pod
- No shared state between executions
- Automatic scaling based on demand
- No Python GIL limitations

### 2. **Resource Isolation**
- Memory and CPU limits per workflow
- Prevents one workflow from affecting others
- Better resource utilization
- Fault isolation

### 3. **Lightweight Runtime**
- Minimal dependencies (FastAPI, OpenAI, basic steps)
- Fast startup times
- Small container images
- Efficient resource usage

### 4. **Flexible Deployment**
- On-demand pod creation
- Automatic cleanup after completion
- Support for different resource profiles
- Easy to monitor and debug

## Implementation Details

### Execution Runtime Package

**Location**: `python_packages/workflow-execution-runtime/`

**Key Components**:
- `main.py`: FastAPI application entry point
- `execution_engine.py`: Core workflow execution logic
- `step_registry.py`: Embedded step implementations
- `models.py`: Pydantic models for requests/responses
- `steps/`: Essential step implementations (AI, data, flow, trigger)

**Container Image**: Lightweight Docker image with minimal dependencies

### Orchestration Layer Enhancements

**Location**: `python_apps/workflow-engine-poc/workflow_engine_poc/orchestration/`

**Key Components**:
- `kubernetes_manager.py`: Manages pod lifecycle, deployments, services
- Enhanced workflow router with Kubernetes backend support
- Execution tracking and monitoring

### Workflow Execution Flow

1. **Request Received**: `/workflows/{workflow_id}/execute?backend=kubernetes`
2. **Pod Deployment**: Orchestration layer creates Kubernetes resources:
   - ConfigMap with workflow JSON
   - Secret with API keys
   - Deployment with runtime container
   - Service for HTTP access
3. **Execution**: Runtime pod executes workflow independently
4. **Response**: Results streamed back through orchestration layer
5. **Cleanup**: Pod automatically cleaned up after completion

### API Endpoints

#### Orchestration Layer
```
POST /workflows/{workflow_id}/execute/kubernetes
POST /workflows/{workflow_id}/stream/kubernetes
```

#### Runtime Pod (Internal)
```
GET  /health          # Health check
GET  /ready           # Readiness check
POST /execute         # Execute workflow
POST /stream          # Stream execution
GET  /status          # Current status
```

## Usage Examples

### Basic Workflow Execution

```bash
# Execute workflow with Kubernetes backend
curl -X POST "http://localhost:8000/workflows/{workflow_id}/execute/kubernetes" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": {
      "kind": "webhook",
      "data": {"message": "Hello World"}
    },
    "input_data": {
      "user_input": "Process this data"
    }
  }'
```

### Streaming Execution

```bash
# Stream workflow execution
curl -X POST "http://localhost:8000/workflows/{workflow_id}/stream/kubernetes" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": {
      "kind": "chat",
      "current_message": "What is the weather like?",
      "history": []
    }
  }'
```

## Resource Management

### Pod Resource Configuration

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Automatic Cleanup

- Pods are automatically cleaned up after workflow completion
- Configurable cleanup timeout (default: 24 hours)
- Manual cleanup via orchestration API

## Monitoring and Observability

### Health Checks
- `/health`: Basic health status
- `/ready`: Readiness for execution
- `/status`: Current execution status

### Logging
- Structured JSON logging
- Correlation IDs for request tracking
- Centralized log aggregation

### Metrics
- Execution success/failure rates
- Resource utilization
- Pod lifecycle events
- Performance metrics

## Security

### Pod Security
- Non-root container execution
- Resource limits and quotas
- Network policies
- Secret management for API keys

### API Security
- Authentication and authorization
- Input validation
- Rate limiting
- Audit logging

## Migration Path

### Phase 1: Core Implementation ✅
- Execution runtime package
- Kubernetes orchestration manager
- Basic pod lifecycle management
- API integration

### Phase 2: Production Readiness
- Comprehensive monitoring
- Error handling and recovery
- Performance optimization
- Security hardening

### Phase 3: Advanced Features
- Multi-tenant isolation
- Advanced scheduling
- Workflow composition
- Cost optimization

## Conclusion

This microkernel architecture represents a fundamental shift towards true cloud-native workflow execution. By separating orchestration from execution and leveraging Kubernetes for isolation and scaling, we achieve:

- **Unlimited Scalability**: No more Python GIL limitations
- **Better Resource Utilization**: Right-sized containers for each workflow
- **Improved Reliability**: Fault isolation and automatic recovery
- **Operational Excellence**: Better monitoring, debugging, and maintenance

The implementation provides a solid foundation for building a production-ready, enterprise-scale workflow execution platform that can handle thousands of concurrent workflows with optimal resource utilization and operational efficiency.
