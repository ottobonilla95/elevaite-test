# Email Triggers and Workflow Deployment Strategy

## Table of Contents
1. [Email Triggers Implementation](#email-triggers-implementation)
2. [Kubernetes Deployment Architecture](#kubernetes-deployment-architecture)
3. [Deployment Strategies](#deployment-strategies)
4. [Implementation Roadmap](#implementation-roadmap)
5. [Security Considerations](#security-considerations)
6. [Monitoring and Observability](#monitoring-and-observability)

---

## Email Triggers Implementation

### Current State Analysis

The workflow engine currently supports three trigger types:
- **Webhook**: HTTP endpoint triggers for external systems
- **Chat**: Interactive conversation triggers with file attachments
- **File**: Document processing triggers

### Email Trigger Architecture

#### 1. Email Trigger Schema Extension

```python
class TriggerKindEnum(str, Enum):
    webhook = "webhook"
    chat = "chat" 
    file = "file"
    email = "email"  # NEW

class EmailTriggerPayload(BaseModel):
    kind: Literal["email"] = "email"
    from_address: str
    to_address: str
    subject: str
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: List[Attachment] = Field(default_factory=list)
    message_id: str
    thread_id: Optional[str] = None
    reply_to: Optional[str] = None
    received_at: datetime
    
class EmailTriggerConfig(BaseModel):
    """Configuration for email trigger workflows"""
    imap_host: str
    imap_port: int = 993
    smtp_host: str
    smtp_port: int = 587
    username: str
    password: str  # Should be encrypted/from secrets
    polling_interval: int = 30  # seconds
    mailbox: str = "INBOX"
    filters: Optional[EmailFilters] = None
    
class EmailFilters(BaseModel):
    """Email filtering rules"""
    sender_whitelist: Optional[List[str]] = None
    sender_blacklist: Optional[List[str]] = None
    subject_patterns: Optional[List[str]] = None
    body_keywords: Optional[List[str]] = None
```

#### 2. Email Listener Service

```python
class EmailTriggerService:
    """Manages email listeners for workflows with email triggers"""
    
    def __init__(self, workflow_engine: WorkflowEngine):
        self.workflow_engine = workflow_engine
        self.active_listeners: Dict[str, EmailListener] = {}
        self.listener_tasks: Dict[str, asyncio.Task] = {}
        
    async def start_listener(self, workflow_id: str, config: EmailTriggerConfig):
        """Start email listener for a specific workflow"""
        if workflow_id in self.active_listeners:
            await self.stop_listener(workflow_id)
            
        listener = EmailListener(
            workflow_id=workflow_id,
            config=config,
            on_email_received=self._handle_email_received
        )
        
        self.active_listeners[workflow_id] = listener
        task = asyncio.create_task(listener.run())
        self.listener_tasks[workflow_id] = task
        
        logger.info(f"Started email listener for workflow {workflow_id}")
        
    async def _handle_email_received(self, workflow_id: str, email_data: dict):
        """Process received email and trigger workflow execution"""
        try:
            # Create execution context
            workflow_config = await self.get_workflow_config(workflow_id)
            execution_context = ExecutionContext(
                workflow_config=workflow_config,
                execution_id=str(uuid.uuid4())
            )
            
            # Set trigger data
            execution_context.step_io_data["trigger_raw"] = {
                "kind": "email",
                **email_data
            }
            
            # Execute workflow
            await self.workflow_engine.execute_workflow(execution_context)
            
        except Exception as e:
            logger.error(f"Failed to process email for workflow {workflow_id}: {e}")
```

#### 3. Email Processing Step

```python
async def email_trigger_step(
    step_config: Dict[str, Any], 
    input_data: Dict[str, Any], 
    execution_context: ExecutionContext
) -> Dict[str, Any]:
    """Process email trigger data into normalized format"""
    raw = execution_context.step_io_data.get("trigger_raw", {})
    
    # Extract email content
    body_text = raw.get("body_text", "")
    body_html = raw.get("body_html", "")
    
    # Parse HTML to text if needed
    if body_html and not body_text:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(body_html, 'html.parser')
        body_text = soup.get_text(strip=True)
    
    # Process attachments
    attachments = []
    for attachment in raw.get("attachments", []):
        attachments.append({
            "name": attachment.get("filename"),
            "mime": attachment.get("content_type"),
            "size_bytes": attachment.get("size"),
            "data": attachment.get("content")  # Base64 encoded
        })
    
    return {
        "kind": "email",
        "from_address": raw.get("from_address"),
        "to_address": raw.get("to_address"),
        "subject": raw.get("subject"),
        "body": body_text,
        "body_html": body_html,
        "attachments": attachments,
        "message_id": raw.get("message_id"),
        "thread_context": {
            "thread_id": raw.get("thread_id"),
            "reply_to": raw.get("reply_to"),
            "in_reply_to": raw.get("in_reply_to")
        },
        "received_at": raw.get("received_at")
    }
```

### Implementation Complexity Assessment

**Difficulty: Medium (6/10)**

**Easy Aspects:**
- Existing trigger architecture is extensible
- Email parsing logic already exists in `email_middleware`
- Step registry supports dynamic registration

**Complex Aspects:**
- Long-running IMAP connections need management
- Email state tracking (processed/unprocessed)
- Connection recovery and error handling
- Multiple email account management
- Security (credential storage, encryption)

**Estimated Implementation Time: 12-18 hours**

---

## Kubernetes Deployment Architecture

### Current Deployment State

Based on the codebase analysis:
- **Docker**: Existing Dockerfiles for various services
- **Docker Compose**: Multi-service orchestration for development
- **GitHub Actions**: CI/CD pipelines for testing/production
- **EKS**: Existing Kubernetes deployment via reusable workflows

### Workflow Deployment Models

#### Model 1: Monolithic Workflow Engine

```yaml
# Single deployment handling all workflows
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workflow-engine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: workflow-engine
  template:
    metadata:
      labels:
        app: workflow-engine
    spec:
      containers:
      - name: workflow-engine
        image: workflow-engine:latest
        ports:
        - containerPort: 8006
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: workflow-secrets
              key: database-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openai-key
```

**Pros:**
- Simple deployment model
- Shared resources and connections
- Easy to manage and monitor

**Cons:**
- Single point of failure
- Resource contention between workflows
- Difficult to scale individual workflows
- Email triggers affect all workflows

#### Model 2: Workflow-per-Deployment

```yaml
# Each workflow gets its own deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workflow-{{ workflow_id }}
  labels:
    workflow-id: "{{ workflow_id }}"
    workflow-type: "{{ workflow_type }}"
spec:
  replicas: 1
  selector:
    matchLabels:
      workflow-id: "{{ workflow_id }}"
  template:
    metadata:
      labels:
        workflow-id: "{{ workflow_id }}"
    spec:
      containers:
      - name: workflow-runner
        image: workflow-engine:latest
        command: ["python", "-m", "workflow_engine_poc.runners.single_workflow"]
        args: ["--workflow-id", "{{ workflow_id }}"]
        env:
        - name: WORKFLOW_CONFIG
          valueFrom:
            configMapKeyRef:
              name: workflow-{{ workflow_id }}-config
              key: config.json
```

**Pros:**
- Complete isolation between workflows
- Independent scaling and resource allocation
- Workflow-specific configurations
- Easy to debug and monitor individual workflows

**Cons:**
- Higher resource overhead
- More complex deployment management
- Potential resource waste for low-traffic workflows

#### Model 3: Hybrid Multi-Tenant (Recommended)

```yaml
# Workflow engine with tenant isolation
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workflow-engine-tenant-{{ tenant_id }}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: workflow-engine
      tenant: "{{ tenant_id }}"
  template:
    spec:
      containers:
      - name: workflow-engine
        image: workflow-engine:latest
        env:
        - name: TENANT_ID
          value: "{{ tenant_id }}"
        - name: WORKFLOW_FILTER
          value: "tenant={{ tenant_id }}"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

**Pros:**
- Balance between isolation and efficiency
- Tenant-based scaling
- Shared infrastructure with logical separation
- Cost-effective for multi-tenant scenarios

**Cons:**
- More complex tenant management
- Potential cross-tenant interference

### Email Trigger Deployment Considerations

#### Stateful Email Listeners

Email triggers require persistent connections and state management:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: email-trigger-service
spec:
  serviceName: email-trigger-service
  replicas: 1  # Single instance to avoid duplicate processing
  selector:
    matchLabels:
      app: email-trigger-service
  template:
    spec:
      containers:
      - name: email-listener
        image: workflow-engine:latest
        command: ["python", "-m", "workflow_engine_poc.services.email_trigger_service"]
        env:
        - name: EMAIL_CONFIGS
          valueFrom:
            secretKeyRef:
              name: email-configs
              key: configs.json
        volumeMounts:
        - name: email-state
          mountPath: /app/state
  volumeClaimTemplates:
  - metadata:
      name: email-state
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

#### Email Configuration Management

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: email-configs
type: Opaque
data:
  configs.json: |
    {
      "workflow-123": {
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "username": "workflow@company.com",
        "password": "encrypted_password",
        "polling_interval": 30
      }
    }
```

---

## Deployment Strategies

### Strategy 1: GitOps with ArgoCD

```yaml
# Application definition for ArgoCD
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: workflow-engine
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/company/workflow-engine
    targetRevision: HEAD
    path: k8s/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: workflow-engine
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Strategy 2: Helm Charts

```yaml
# values.yaml for workflow engine
replicaCount: 3

image:
  repository: workflow-engine
  tag: "latest"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8006

ingress:
  enabled: true
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: workflows.company.com
      paths:
        - path: /
          pathType: Prefix

emailTriggers:
  enabled: true
  replicas: 1
  persistence:
    enabled: true
    size: 1Gi

database:
  host: postgres-service
  port: 5432
  name: workflow_engine
  
secrets:
  database:
    url: "postgresql://user:pass@host:5432/db"
  llm:
    openai_key: "sk-..."
  email:
    configs: |
      {
        "workflow-123": {
          "username": "user@company.com",
          "password": "encrypted_password"
        }
      }
```

### Strategy 3: Operator Pattern

```yaml
# Custom Resource Definition for Workflows
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: workflows.elevaite.io
spec:
  group: elevaite.io
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              config:
                type: object
              triggers:
                type: array
                items:
                  type: object
                  properties:
                    type:
                      type: string
                      enum: ["webhook", "chat", "file", "email"]
                    config:
                      type: object
          status:
            type: object
            properties:
              phase:
                type: string
                enum: ["Pending", "Running", "Completed", "Failed"]
              deploymentStatus:
                type: string
  scope: Namespaced
  names:
    plural: workflows
    singular: workflow
    kind: Workflow
```

---

## Implementation Roadmap

### Phase 1: Email Trigger Foundation (Week 1-2)
- [ ] Extend trigger schema for email support
- [ ] Implement basic email listener service
- [ ] Add email trigger step to step registry
- [ ] Create email configuration management
- [ ] Basic testing with single email account

### Phase 2: Kubernetes Integration (Week 3-4)
- [ ] Create Kubernetes manifests for workflow engine
- [ ] Implement StatefulSet for email listeners
- [ ] Add Helm charts for deployment
- [ ] Configure secrets management
- [ ] Set up monitoring and logging

### Phase 3: Production Readiness (Week 5-6)
- [ ] Implement email state persistence
- [ ] Add connection recovery and retry logic
- [ ] Create email filtering and routing
- [ ] Add comprehensive monitoring
- [ ] Performance testing and optimization

### Phase 4: Advanced Features (Week 7-8)
- [ ] Multi-tenant email support
- [ ] Email response capabilities
- [ ] Advanced filtering and routing
- [ ] Integration with existing CI/CD
- [ ] Documentation and training

---

## Security Considerations

### Email Credentials Management
- Use Kubernetes Secrets for email credentials
- Implement credential rotation
- Encrypt sensitive data at rest
- Use service accounts with minimal permissions

### Network Security
- Implement network policies for email services
- Use TLS for all email connections
- Restrict egress traffic to required email servers
- Monitor for suspicious email activity

### Access Control
- RBAC for workflow deployment and management
- Audit logging for all email trigger activities
- Secure API endpoints with authentication
- Implement rate limiting and DDoS protection

---

## Monitoring and Observability

### Metrics to Track
- Email processing latency
- Failed email connections
- Workflow execution success rates
- Resource utilization per workflow
- Email queue depth and processing time

### Logging Strategy
- Structured logging with correlation IDs
- Email processing audit trail
- Workflow execution traces
- Error aggregation and alerting

### Alerting Rules
- Email connection failures
- High email processing latency
- Workflow execution failures
- Resource exhaustion warnings
- Security anomalies

---

## Next Steps

1. **Team Discussion**: Review email trigger architecture and deployment strategy
2. **Proof of Concept**: Implement basic email trigger with single workflow
3. **Kubernetes Setup**: Create development Kubernetes environment
4. **Security Review**: Validate security approach with security team
5. **Performance Testing**: Benchmark email processing and workflow execution
6. **Production Planning**: Plan rollout strategy and monitoring setup

## Operational Considerations

### Workflow Lifecycle Management

#### Deployment States
```python
class WorkflowDeploymentState(str, Enum):
    DRAFT = "draft"           # Workflow created but not deployed
    DEPLOYING = "deploying"   # Deployment in progress
    ACTIVE = "active"         # Running and accepting triggers
    PAUSED = "paused"         # Deployed but not processing new triggers
    UPDATING = "updating"     # Configuration update in progress
    FAILED = "failed"         # Deployment failed
    TERMINATED = "terminated" # Cleanly shut down
```

#### Deployment Operations
```bash
# Deploy a workflow
kubectl apply -f workflow-manifests/

# Scale workflow replicas
kubectl scale deployment workflow-engine --replicas=5

# Update workflow configuration
kubectl patch configmap workflow-config --patch='{"data":{"config.json":"..."}}'

# Monitor deployment status
kubectl get workflows -o wide

# View workflow logs
kubectl logs -l app=workflow-engine -f

# Emergency stop
kubectl delete deployment workflow-engine
```

### Resource Management

#### Resource Quotas per Workflow Type
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: workflow-quota
  namespace: workflows
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "10"
    services: "5"
    secrets: "10"
```

#### Horizontal Pod Autoscaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: workflow-engine-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: workflow-engine
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Email Trigger Scaling Patterns

#### Pattern 1: Single Email Service (Simple)
- One email listener service handles all email workflows
- Shared IMAP connections and processing queue
- Good for: Small deployments, single organization

#### Pattern 2: Email Service per Domain (Medium)
- Separate email listeners for different email domains
- Isolated processing and failure domains
- Good for: Multi-tenant scenarios, different email providers

#### Pattern 3: Email Service per Workflow (Complex)
- Dedicated email listener for each email-triggered workflow
- Maximum isolation but higher resource usage
- Good for: High-security environments, critical workflows

### Disaster Recovery

#### Backup Strategy
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: workflow-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:13
            command:
            - /bin/bash
            - -c
            - |
              pg_dump $DATABASE_URL > /backup/workflows-$(date +%Y%m%d).sql
              aws s3 cp /backup/ s3://workflow-backups/ --recursive
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: database-secret
                  key: url
          restartPolicy: OnFailure
```

#### Recovery Procedures
1. **Database Recovery**: Restore from latest backup
2. **Configuration Recovery**: Restore from Git repository
3. **Email State Recovery**: Rebuild from email server history
4. **Workflow State Recovery**: Resume from last checkpoint

### Cost Optimization

#### Resource Right-Sizing
```yaml
# Development environment
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"

# Production environment
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

#### Spot Instance Usage
```yaml
nodeSelector:
  node-type: spot-instance
tolerations:
- key: "spot-instance"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```

## Integration with Existing Infrastructure

### Current Infrastructure Analysis

Based on the codebase analysis, your current setup includes:

#### Existing Deployment Pipeline
- **GitHub Actions**: Automated CI/CD with testing and production deployments
- **EKS**: Kubernetes deployment via reusable workflows
- **Docker Compose**: Multi-service orchestration for development
- **ECR**: Container registry for image storage

#### Current Services Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend APIs  │    │   Databases     │
│                 │    │                 │    │                 │
│ • Next.js Apps  │◄──►│ • FastAPI       │◄──►│ • PostgreSQL    │
│ • React UIs     │    │ • Auth API      │    │ • Qdrant        │
│ • Chatbot       │    │ • RBAC          │    │ • Redis         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Workers       │
                    │                 │
                    │ • ETL Workers   │
                    │ • Flyte Workers │
                    │ • Background    │
                    └─────────────────┘
```

### Workflow Engine Integration Strategy

#### Option 1: Standalone Deployment
Deploy workflow engine as a separate service alongside existing infrastructure:

```yaml
# Add to existing docker-compose.backend.yaml
services:
  workflow-engine:
    build:
      context: .
      dockerfile: ./python_apps/workflow-engine-poc/Dockerfile
    environment:
      DATABASE_URL: ${WORKFLOW_DATABASE_URL}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      REDIS_HOST: ${REDIS_HOST}
      REDIS_PORT: ${REDIS_PORT}
    ports:
      - "8006:8006"
    depends_on:
      - postgres
      - redis
    networks:
      - backend-network

  email-trigger-service:
    build:
      context: .
      dockerfile: ./python_packages/email_middleware/Dockerfile
    environment:
      WORKFLOW_ENGINE_URL: http://workflow-engine:8006
      EMAIL_CONFIGS: ${EMAIL_CONFIGS}
    depends_on:
      - workflow-engine
    networks:
      - backend-network
```

#### Option 2: Integrated Deployment
Integrate workflow engine into existing backend services:

```yaml
# Extend existing backend service
services:
  backend:
    build:
      context: .
      dockerfile: ./elevaite_backend/Dockerfile
    environment:
      # Existing environment variables
      SQLALCHEMY_DATABASE_URL: ${ETL_DATABASE_URL}
      # Add workflow engine variables
      WORKFLOW_ENGINE_ENABLED: "true"
      EMAIL_TRIGGERS_ENABLED: "true"
    volumes:
      - ./python_apps/workflow-engine-poc:/app/workflow_engine
```

### Kubernetes Migration Strategy

#### Phase 1: Containerize Workflow Engine
```dockerfile
# Enhanced Dockerfile for production
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY python_apps/workflow-engine-poc/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY python_apps/workflow-engine-poc/ .
COPY python_packages/ ./python_packages/

# Create non-root user
RUN useradd -m -u 1000 workflow && chown -R workflow:workflow /app
USER workflow

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8006/health || exit 1

# Expose port
EXPOSE 8006

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006"]
```

#### Phase 2: Kubernetes Manifests
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: workflow-engine
  labels:
    name: workflow-engine

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: workflow-engine-config
  namespace: workflow-engine
data:
  LOG_LEVEL: "INFO"
  HOST: "0.0.0.0"
  PORT: "8006"
  ENVIRONMENT: "production"

---
# secret.yaml (template - actual values from CI/CD)
apiVersion: v1
kind: Secret
metadata:
  name: workflow-engine-secrets
  namespace: workflow-engine
type: Opaque
data:
  database-url: <base64-encoded-url>
  openai-api-key: <base64-encoded-key>
  email-configs: <base64-encoded-json>

---
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workflow-engine
  namespace: workflow-engine
  labels:
    app: workflow-engine
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: workflow-engine
  template:
    metadata:
      labels:
        app: workflow-engine
        version: v1
    spec:
      containers:
      - name: workflow-engine
        image: your-ecr-registry/workflow-engine:latest
        ports:
        - containerPort: 8006
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: workflow-engine-secrets
              key: database-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: workflow-engine-secrets
              key: openai-api-key
        envFrom:
        - configMapRef:
            name: workflow-engine-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8006
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8006
          initialDelaySeconds: 5
          periodSeconds: 5

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: workflow-engine-service
  namespace: workflow-engine
spec:
  selector:
    app: workflow-engine
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8006
  type: ClusterIP

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: workflow-engine-ingress
  namespace: workflow-engine
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - workflows.yourdomain.com
    secretName: workflow-engine-tls
  rules:
  - host: workflows.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: workflow-engine-service
            port:
              number: 80
```

#### Phase 3: CI/CD Integration
```yaml
# .github/workflows/deploy-workflow-engine.yml
name: Deploy Workflow Engine

on:
  push:
    branches: [main]
    paths: ['python_apps/workflow-engine-poc/**']

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-1

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1

    - name: Build and push Docker image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: workflow-engine
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
          -f python_apps/workflow-engine-poc/Dockerfile .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
          $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

    - name: Deploy to EKS
      run: |
        aws eks update-kubeconfig --name your-cluster-name
        kubectl set image deployment/workflow-engine \
          workflow-engine=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
          -n workflow-engine
        kubectl rollout status deployment/workflow-engine -n workflow-engine
```

This document provides a comprehensive foundation for implementing email triggers and Kubernetes deployment for the workflow engine. The modular approach allows for incremental implementation while maintaining system reliability and security.
