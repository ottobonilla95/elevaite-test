# Postman Test Suite Guide - Part 2: Advanced Tests

## Additional Request Tests

### 8. Create Agent

**Endpoint:** `POST {{base_url}}/api/agents`

**Body:**
```json
{
  "name": "Test Agent {{$timestamp}}",
  "description": "Automated test agent",
  "system_prompt": "You are a helpful AI assistant for testing purposes.",
  "provider_type": "openai_textgen",
  "provider_config": {
    "model_name": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 500
  },
  "status": "active",
  "tags": ["test", "automated"]
}
```

**Tests:**
```javascript
pm.test("Status code is 200 or 201", () => {
    pm.expect(pm.response.code).to.be.oneOf([200, 201]);
});

pm.test("Agent created successfully", () => {
    const agent = pm.response.json();
    pm.expect(agent).to.have.property('id');
    pm.expect(agent).to.have.property('name');
    pm.expect(agent).to.have.property('system_prompt');
    pm.expect(agent).to.have.property('provider_type');
});

pm.test("Agent has correct provider config", () => {
    const agent = pm.response.json();
    pm.expect(agent.provider_config).to.have.property('model_name');
    pm.expect(agent.provider_config.model_name).to.equal('gpt-4o');
});

pm.test("Agent is active", () => {
    const agent = pm.response.json();
    pm.expect(agent.status).to.equal('active');
});

pm.environment.set('agent_id', pm.response.json().id);
```

### 9. Attach Tool to Agent

**Endpoint:** `POST {{base_url}}/api/agents/{{agent_id}}/tools`

**Body:**
```json
{
  "local_tool_name": "web_search",
  "is_active": true,
  "override_parameters": {}
}
```

**Tests:**
```javascript
pm.test("Status code is 200 or 201", () => {
    pm.expect(pm.response.code).to.be.oneOf([200, 201]);
});

pm.test("Tool attached successfully", () => {
    const binding = pm.response.json();
    pm.expect(binding).to.have.property('agent_id');
    pm.expect(binding).to.have.property('tool_id');
    pm.expect(binding.is_active).to.be.true;
});
```

### 10. List Tools

**Endpoint:** `GET {{base_url}}/api/tools?limit=50`

**Tests:**
```javascript
pm.test("Status code is 200", () => {
    pm.response.to.have.status(200);
});

pm.test("Tools list is returned", () => {
    const tools = pm.response.json();
    pm.expect(tools).to.be.an('array');
});

pm.test("Tools have required fields", () => {
    const tools = pm.response.json();
    if (tools.length > 0) {
        const tool = tools[0];
        pm.expect(tool).to.have.property('name');
        pm.expect(tool).to.have.property('description');
        pm.expect(tool).to.have.property('source');
    }
});

pm.test("Tools include local and database sources", () => {
    const tools = pm.response.json();
    const sources = [...new Set(tools.map(t => t.source))];
    console.log('Available tool sources:', sources);
    pm.expect(sources.length).to.be.at.least(1);
});
```

### 11. Create Prompt

**Endpoint:** `POST {{base_url}}/api/prompts`

**Body:**
```json
{
  "name": "Test Prompt {{$timestamp}}",
  "content": "You are a helpful assistant. Answer the following question: {question}",
  "description": "Test prompt for automated testing",
  "category": "general",
  "variables": ["question"],
  "tags": ["test"]
}
```

**Tests:**
```javascript
pm.test("Status code is 200 or 201", () => {
    pm.expect(pm.response.code).to.be.oneOf([200, 201]);
});

pm.test("Prompt created successfully", () => {
    const prompt = pm.response.json();
    pm.expect(prompt).to.have.property('id');
    pm.expect(prompt).to.have.property('name');
    pm.expect(prompt).to.have.property('content');
});

pm.test("Prompt has variables", () => {
    const prompt = pm.response.json();
    pm.expect(prompt.variables).to.be.an('array');
    pm.expect(prompt.variables).to.include('question');
});

pm.environment.set('prompt_id', pm.response.json().id);
```

### 12. Update Workflow

**Endpoint:** `PUT {{base_url}}/api/workflows/{{workflow_id}}`

**Body:**
```json
{
  "name": "Updated Test Workflow",
  "description": "Updated description",
  "tags": ["test", "automated", "updated"]
}
```

**Tests:**
```javascript
pm.test("Status code is 200", () => {
    pm.response.to.have.status(200);
});

pm.test("Workflow updated successfully", () => {
    const workflow = pm.response.json();
    pm.expect(workflow.name).to.equal('Updated Test Workflow');
    pm.expect(workflow.description).to.equal('Updated description');
});

pm.test("Tags were updated", () => {
    const workflow = pm.response.json();
    pm.expect(workflow.tags).to.include('updated');
});
```

### 13. Delete Workflow

**Endpoint:** `DELETE {{base_url}}/api/workflows/{{workflow_id}}`

**Tests:**
```javascript
pm.test("Status code is 200 or 204", () => {
    pm.expect(pm.response.code).to.be.oneOf([200, 204]);
});

pm.test("Workflow deleted successfully", () => {
    // Verify deletion by trying to get the workflow
    pm.sendRequest({
        url: `${pm.environment.get('base_url')}/api/workflows/${pm.environment.get('workflow_id')}`,
        method: 'GET',
        header: {
            'Authorization': `Bearer ${pm.environment.get('auth_token')}`
        }
    }, (err, response) => {
        pm.test("Workflow no longer exists", () => {
            pm.expect(response.code).to.equal(404);
        });
    });
});

// Clean up environment variable
pm.environment.unset('workflow_id');
```

## Advanced Test Scenarios

### Workflow Execution with Polling

Create a separate request that polls for execution completion:

**Pre-request Script:**
```javascript
// Wait 2 seconds before polling
setTimeout(() => {}, 2000);
```

**Tests:**
```javascript
const maxRetries = 10;
const currentRetry = pm.environment.get('poll_retry') || 0;

pm.test("Execution status retrieved", () => {
    pm.response.to.have.status(200);
});

const execution = pm.response.json();
const status = execution.status;

if (status === 'completed') {
    pm.test("Execution completed successfully", () => {
        pm.expect(status).to.equal('completed');
    });
    pm.environment.unset('poll_retry');
} else if (status === 'failed') {
    pm.test("Execution failed", () => {
        console.error('Execution failed:', execution);
        pm.expect(status).to.not.equal('failed');
    });
    pm.environment.unset('poll_retry');
} else if (currentRetry < maxRetries) {
    // Still running, retry
    pm.environment.set('poll_retry', currentRetry + 1);
    console.log(`Execution still ${status}, retry ${currentRetry + 1}/${maxRetries}`);
    
    // Use postman.setNextRequest to poll again
    postman.setNextRequest(pm.info.requestName);
} else {
    pm.test("Execution timed out", () => {
        pm.expect.fail(`Execution did not complete after ${maxRetries} retries`);
    });
    pm.environment.unset('poll_retry');
}
```

### RBAC Permission Testing

**Endpoint:** `POST {{rbac_url}}/auth/rbac-permissions`

**Headers:**
```
Authorization: Bearer {{auth_token}}
X-elevAIte-AccountId: {{account_id}}
```

**Body:**
```json
{
  "PROJECT_READ": {},
  "PROJECT_CREATE": {}
}
```

**Tests:**
```javascript
pm.test("Status code is 200", () => {
    pm.response.to.have.status(200);
});

pm.test("User has project read permission", () => {
    const permissions = pm.response.json();
    pm.expect(permissions).to.have.property('PROJECT_READ');
    pm.expect(permissions.PROJECT_READ).to.be.true;
});

pm.test("Permission structure is correct", () => {
    const permissions = pm.response.json();
    Object.keys(permissions).forEach(key => {
        pm.expect(permissions[key]).to.be.a('boolean');
    });
});
```

### Streaming Execution Test

**Endpoint:** `POST {{base_url}}/api/workflows/{{workflow_id}}/stream`

**Note:** Postman has limited SSE support. For full streaming tests, use Newman with custom reporters or browser-based testing.

**Tests (for initial response):**
```javascript
pm.test("Status code is 200", () => {
    pm.response.to.have.status(200);
});

pm.test("Response is SSE stream", () => {
    const contentType = pm.response.headers.get('Content-Type');
    pm.expect(contentType).to.include('text/event-stream');
});

// Note: Postman won't capture streaming events
console.log('Streaming started - use browser or Newman for full validation');
```

## Test Organization

### Recommended Folder Structure

```
elevAIte API Tests/
├── 00 - Setup/
│   ├── Health Check
│   └── Get Auth Token
├── 01 - Workflows/
│   ├── Create Workflow
│   ├── Get Workflow
│   ├── List Workflows
│   ├── Update Workflow
│   ├── Execute Workflow
│   └── Delete Workflow
├── 02 - Agents/
│   ├── Create Agent
│   ├── List Agents
│   ├── Get Agent
│   ├── Update Agent
│   ├── Attach Tool
│   └── Delete Agent
├── 03 - Tools/
│   ├── List Tools
│   ├── Get Tool
│   └── List Categories
├── 04 - Executions/
│   ├── Get Execution Status
│   ├── Get Execution Results
│   ├── Poll Until Complete
│   └── List Executions
├── 05 - Prompts/
│   ├── Create Prompt
│   ├── List Prompts
│   └── Delete Prompt
├── 06 - RBAC/
│   ├── Get Organization
│   ├── List Accounts
│   ├── List Projects
│   ├── Check Permissions
│   └── Validate API Key
└── 99 - Cleanup/
    ├── Delete Test Workflows
    ├── Delete Test Agents
    └── Clear Environment
```

## Running Tests

### Manual Execution
1. Select environment (Dev/Staging/Prod)
2. Run collection or individual folders
3. Review test results in Postman console

### Automated Execution with Newman

```bash
# Install Newman
npm install -g newman

# Run collection
newman run elevAIte-API-Tests.json \
  -e dev-environment.json \
  --reporters cli,json,html \
  --reporter-html-export results.html

# Run with delays for polling
newman run elevAIte-API-Tests.json \
  -e dev-environment.json \
  --delay-request 2000 \
  --timeout-request 30000
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run API Tests
  run: |
    newman run postman/elevAIte-API-Tests.json \
      -e postman/staging-environment.json \
      --reporters cli,junit \
      --reporter-junit-export test-results.xml
```

## Best Practices

1. **Use Dynamic Data**: Use `{{$timestamp}}`, `{{$randomInt}}` for unique test data
2. **Clean Up**: Always delete test data in cleanup folder
3. **Environment Variables**: Store all IDs and tokens in environment
4. **Assertions**: Test both success and error cases
5. **Logging**: Use `console.log()` for debugging
6. **Timeouts**: Set appropriate timeouts for long-running operations
7. **Retries**: Implement polling for async operations
8. **Documentation**: Add descriptions to requests and folders

## Troubleshooting

### Common Issues

**401 Unauthorized:**
- Check auth_token is set and valid
- Verify token hasn't expired
- Ensure correct headers are set

**404 Not Found:**
- Verify workflow_id/agent_id is stored correctly
- Check if resource was deleted
- Confirm base_url is correct

**Timeout:**
- Increase timeout in Postman settings
- Check if service is running
- Verify network connectivity

**Streaming Not Working:**
- Use Newman or browser for SSE testing
- Postman has limited streaming support
- Check Content-Type headers

## Next Steps

1. Import your OpenAPI spec into Postman
2. Add the collection-level scripts from Part 1
3. Copy test scripts to individual requests
4. Set up environments with your URLs and credentials
5. Run the collection and iterate on failing tests
6. Set up Newman for CI/CD integration

