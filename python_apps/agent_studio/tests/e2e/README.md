# E2E Workflow Tests

End-to-end tests for Agent Studio workflows using API calls.

## Setup

```bash
# Install dependencies
npm install

# Or using yarn
yarn install
```

## Running Tests

### Test the Biggest Workflow (Media Planning Command Agent)

```bash
# Run the comprehensive E2E test
npm run test

# Or directly with tsx
npx tsx test-biggest-workflow.ts
```

## What the Test Does

1. **Executes the biggest workflow** (Media Planning Command Agent) with a comprehensive Nike media planning query
2. **Polls for status** every 100ms with exponential backoff up to 2s intervals
3. **Captures full execution trace** including all steps and step_metadata
4. **Validates analytics tracking** and workflow completion
5. **Exports results** to JSON file for analysis

## Test Features

- 🎯 **Real E2E testing** via HTTP API calls
- 📊 **Rich console output** with colors and progress bars
- ⏱️ **Smart polling** with exponential backoff
- 📈 **Analytics validation** including step_metadata tracking
- 💾 **JSON export** of complete execution trace
- 🔍 **Detailed step analysis** with timing and metadata

## Configuration

Edit the `CONFIG` object in `test-biggest-workflow.ts`:

```typescript
const CONFIG = {
  baseURL: 'http://localhost:8000',        // API base URL
  workflowId: '86ee03db-910d-4d27-81a9-59c855d0a06e', // Biggest workflow ID
  pollInterval: 100,                       // Initial polling interval (ms)
  maxPollInterval: 2000,                   // Max polling interval (ms)
  timeout: 600000,                         // 10 minutes timeout
  exportResults: true                      // Export to JSON
};
```

## Prerequisites

- Agent Studio API running on `http://localhost:8000`
- The biggest workflow (Media Planning Command Agent) deployed
- Node.js 18+ installed

## Output

The test provides:
- Real-time progress updates with colored console output
- Step-by-step execution details
- Performance metrics and timing
- Analytics validation
- JSON export of complete execution trace

Example output:
```
🚀 Starting E2E Workflow Test
================================================================================
📋 Workflow: Media Planning Command Agent
🆔 Workflow ID: 86ee03db-910d-4d27-81a9-59c855d0a06e
🎯 Test Query: Create a comprehensive media plan for Nike's new Air Max campaign...
================================================================================

📤 Starting workflow execution...
✅ Execution started: abc123-def456-ghi789

📊 Polling for status updates...
[14:30:15] #001 RUNNING [████░░░░░░░░░░░░░░░░] 20.0% Executing MediaContextRetriever
[14:30:16] #002 RUNNING [████████░░░░░░░░░░░░] 40.0% Processing Salesforce integration
[14:30:17] #003 COMPLETED [████████████████████] 100.0% Workflow completed successfully

📊 Test Results Summary
================================================================================
✅ SUCCESS - Workflow completed
⏱️  Total Duration: 2.3s
🔄 Polling Attempts: 23
📋 Steps Completed: 8
🤖 Agents Involved: MediaContextRetriever, RouterAgent, SalesforceIntegrationAgent
🔧 Tools Used: media_context_retriever, create_salesforce_insertion_order

💾 Results exported to: workflow-test-abc123-def456-ghi789-1704387015123.json
```
