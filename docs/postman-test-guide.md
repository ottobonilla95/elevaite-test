# Postman Test Suite Guide for elevAIte APIs

## Overview

This guide provides comprehensive test scripts and setup instructions for testing elevAIte APIs using Postman.

## Environment Setup

### Create Environments

Create separate environments for each deployment stage:

#### Development Environment Variables
```json
{
  "base_url": "http://localhost:8000",
  "rbac_url": "http://localhost:8001",
  "auth_token": "",
  "api_key": "",
  "workflow_id": "",
  "execution_id": "",
  "agent_id": "",
  "tool_id": "",
  "prompt_id": "",
  "organization_id": "",
  "account_id": "",
  "project_id": "",
  "test_user_email": "test@example.com"
}
```

#### Staging/Production
Same structure, different URLs.

## Collection-Level Configuration

### Pre-request Script (Collection Level)

Add this to your collection's Pre-request Scripts tab:

```javascript
// Auto-inject authentication headers
const authToken = pm.environment.get("auth_token");
const apiKey = pm.environment.get("api_key");

if (authToken) {
    pm.request.headers.add({
        key: 'Authorization',
        value: `Bearer ${authToken}`
    });
}

if (apiKey) {
    pm.request.headers.add({
        key: 'X-elevAIte-apikey',
        value: apiKey
    });
}

// Add account/project context if available
const accountId = pm.environment.get("account_id");
const projectId = pm.environment.get("project_id");

if (accountId) {
    pm.request.headers.add({
        key: 'X-elevAIte-AccountId',
        value: accountId
    });
}

if (projectId) {
    pm.request.headers.add({
        key: 'X-elevAIte-ProjectId',
        value: projectId
    });
}
```

### Tests Script (Collection Level)

Add this to your collection's Tests tab:

```javascript
// Common assertions for all requests
pm.test("Response time is acceptable", () => {
    pm.expect(pm.response.responseTime).to.be.below(10000);
});

pm.test("Response has correct content-type", () => {
    const contentType = pm.response.headers.get("Content-Type");
    if (contentType) {
        pm.expect(contentType).to.include("application/json");
    }
});

// Auto-store common IDs from responses
if (pm.response.code === 200 || pm.response.code === 201) {
    try {
        const response = pm.response.json();
        
        // Store IDs based on response structure
        if (response.id) {
            const endpoint = pm.request.url.getPath();
            
            if (endpoint.includes('/workflows')) {
                pm.environment.set('workflow_id', response.id);
                console.log('Stored workflow_id:', response.id);
            } else if (endpoint.includes('/agents')) {
                pm.environment.set('agent_id', response.id);
                console.log('Stored agent_id:', response.id);
            } else if (endpoint.includes('/tools')) {
                pm.environment.set('tool_id', response.id);
                console.log('Stored tool_id:', response.id);
            } else if (endpoint.includes('/prompts')) {
                pm.environment.set('prompt_id', response.id);
                console.log('Stored prompt_id:', response.id);
            }
        }
        
        // Store execution_id
        if (response.execution_id) {
            pm.environment.set('execution_id', response.execution_id);
            console.log('Stored execution_id:', response.execution_id);
        }
    } catch (e) {
        // Not JSON or no ID to store
    }
}
```

## Request-Specific Test Scripts

### 1. Health Check

**Endpoint:** `GET {{base_url}}/api/health`

**Tests:**
```javascript
pm.test("Status code is 200", () => {
    pm.response.to.have.status(200);
});

pm.test("Service is healthy", () => {
    const response = pm.response.json();
    pm.expect(response).to.have.property('status');
    pm.expect(response.status).to.equal('healthy');
});
```

### 2. Create Workflow

**Endpoint:** `POST {{base_url}}/api/workflows`

**Body:**
```json
{
  "name": "Test Workflow {{$timestamp}}",
  "description": "Automated test workflow",
  "configuration": {
    "steps": [
      {
        "step_id": "trigger_1",
        "step_type": "trigger",
        "name": "Webhook Trigger",
        "parameters": {
          "kind": "webhook"
        }
      },
      {
        "step_id": "agent_1",
        "step_type": "agent",
        "name": "Test Agent",
        "parameters": {
          "system_prompt": "You are a helpful assistant.",
          "model": "gpt-4o",
          "query": "{trigger.current_message}"
        },
        "depends_on": ["trigger_1"]
      }
    ]
  },
  "tags": ["test", "automated"],
  "editable": true
}
```

**Tests:**
```javascript
pm.test("Status code is 200 or 201", () => {
    pm.expect(pm.response.code).to.be.oneOf([200, 201]);
});

pm.test("Workflow created with correct structure", () => {
    const workflow = pm.response.json();
    
    pm.expect(workflow).to.have.property('id');
    pm.expect(workflow).to.have.property('name');
    pm.expect(workflow).to.have.property('configuration');
    pm.expect(workflow.configuration).to.have.property('steps');
    pm.expect(workflow.configuration.steps).to.be.an('array');
    pm.expect(workflow.configuration.steps.length).to.be.at.least(1);
});

pm.test("Workflow is editable", () => {
    const workflow = pm.response.json();
    pm.expect(workflow.editable).to.be.true;
});

pm.test("Workflow has tags", () => {
    const workflow = pm.response.json();
    pm.expect(workflow.tags).to.be.an('array');
    pm.expect(workflow.tags).to.include('test');
});

// Store workflow_id for subsequent tests
pm.environment.set('workflow_id', pm.response.json().id);
```

### 3. Get Workflow

**Endpoint:** `GET {{base_url}}/api/workflows/{{workflow_id}}`

**Tests:**
```javascript
pm.test("Status code is 200", () => {
    pm.response.to.have.status(200);
});

pm.test("Workflow matches created workflow", () => {
    const workflow = pm.response.json();
    pm.expect(workflow.id).to.equal(pm.environment.get('workflow_id'));
});

pm.test("Workflow has all required fields", () => {
    const workflow = pm.response.json();
    pm.expect(workflow).to.have.all.keys(
        'id', 'name', 'description', 'configuration', 
        'tags', 'editable', 'created_at', 'updated_at'
    );
});
```

### 4. List Workflows

**Endpoint:** `GET {{base_url}}/api/workflows?limit=10&offset=0`

**Tests:**
```javascript
pm.test("Status code is 200", () => {
    pm.response.to.have.status(200);
});

pm.test("Response is an array", () => {
    const workflows = pm.response.json();
    pm.expect(workflows).to.be.an('array');
});

pm.test("Workflows have required fields", () => {
    const workflows = pm.response.json();
    if (workflows.length > 0) {
        const workflow = workflows[0];
        pm.expect(workflow).to.have.property('id');
        pm.expect(workflow).to.have.property('name');
        pm.expect(workflow).to.have.property('configuration');
    }
});

pm.test("Created workflow is in list", () => {
    const workflows = pm.response.json();
    const workflowId = pm.environment.get('workflow_id');
    const found = workflows.some(w => w.id === workflowId);
    pm.expect(found).to.be.true;
});
```

### 5. Execute Workflow

**Endpoint:** `POST {{base_url}}/api/workflows/{{workflow_id}}/execute`

**Body (JSON):**
```json
{
  "trigger": {
    "kind": "webhook",
    "data": {
      "message": "Hello, test workflow!"
    }
  },
  "user_id": "test-user",
  "session_id": "test-session-{{$timestamp}}",
  "metadata": {
    "source": "postman-test"
  }
}
```

**Tests:**
```javascript
pm.test("Status code is 200 or 201", () => {
    pm.expect(pm.response.code).to.be.oneOf([200, 201]);
});

pm.test("Execution started successfully", () => {
    const execution = pm.response.json();
    pm.expect(execution).to.have.property('execution_id');
    pm.expect(execution).to.have.property('workflow_id');
    pm.expect(execution).to.have.property('status');
});

pm.test("Execution status is valid", () => {
    const execution = pm.response.json();
    pm.expect(execution.status).to.be.oneOf([
        'pending', 'running', 'completed', 'failed', 'waiting'
    ]);
});

pm.test("Execution has user context", () => {
    const execution = pm.response.json();
    pm.expect(execution).to.have.property('user_id');
    pm.expect(execution.user_id).to.equal('test-user');
});

// Store execution_id for polling
pm.environment.set('execution_id', pm.response.json().execution_id);
```

### 6. Get Execution Status (with Polling)

**Endpoint:** `GET {{base_url}}/api/executions/{{execution_id}}`

**Tests:**
```javascript
pm.test("Status code is 200", () => {
    pm.response.to.have.status(200);
});

pm.test("Execution has valid status", () => {
    const execution = pm.response.json();
    pm.expect(execution).to.have.property('status');
    pm.expect(execution.status).to.be.oneOf([
        'pending', 'running', 'completed', 'failed', 'waiting', 'cancelled'
    ]);
});

pm.test("Execution ID matches", () => {
    const execution = pm.response.json();
    pm.expect(execution.execution_id).to.equal(pm.environment.get('execution_id'));
});

// Poll for completion (optional - add delay between requests)
const status = pm.response.json().status;
if (status === 'pending' || status === 'running') {
    console.log('Execution still in progress:', status);
    // In a real test, you'd use Postman's "Run Collection" with delays
}

if (status === 'completed') {
    pm.test("Execution completed successfully", () => {
        pm.expect(status).to.equal('completed');
    });
}

if (status === 'failed') {
    console.error('Execution failed:', pm.response.json());
}
```

### 7. Get Execution Results

**Endpoint:** `GET {{base_url}}/api/executions/{{execution_id}}/results`

**Tests:**
```javascript
pm.test("Status code is 200", () => {
    pm.response.to.have.status(200);
});

pm.test("Results contain execution data", () => {
    const results = pm.response.json();
    pm.expect(results).to.have.property('execution_id');
    pm.expect(results).to.have.property('status');
});

pm.test("Results contain step outputs", () => {
    const results = pm.response.json();
    if (results.status === 'completed') {
        pm.expect(results).to.have.property('step_outputs');
    }
});
```


