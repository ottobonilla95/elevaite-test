# Workflow Async Execution Testing Guide

This guide provides comprehensive testing options for the new async workflow execution system with tracing capabilities.

## 🧪 Testing Options Overview

You now have **4 different ways** to test workflow async execution:

### 1. **Original Mock Test** (`test_workflow_async.py`)
Simple unit test for tracing functionality
```bash
python test_workflow_async.py
```

### 2. **Comprehensive Test Suite** (`test_workflow_comprehensive.py`)
Advanced testing with multiple options
```bash
# Run all tests
python test_workflow_comprehensive.py

# Mock testing only  
python test_workflow_comprehensive.py --mock-only

# Test specific workflow
python test_workflow_comprehensive.py --workflow-id "60e54f16-386e-4f78-93be-462e0eb8bec2"

# Interactive workflow selection
python test_workflow_comprehensive.py --interactive

# Custom query
python test_workflow_comprehensive.py --workflow-id "YOUR_ID" --query "Your custom query"
```

### 3. **API Endpoint Testing** (`test_workflow_api.py`)
Test actual FastAPI endpoints (requires running server)
```bash
# Start FastAPI server first
python main.py  # or uvicorn main:app

# Then run API tests
python test_workflow_api.py

# Test specific workflow via API
python test_workflow_api.py --workflow-id "YOUR_ID" --query "API test"

# Monitor existing execution
python test_workflow_api.py --monitor-only "execution_id"

# Custom server URL
python test_workflow_api.py --url "http://localhost:8080"
```

### 4. **Manual API Testing**
Direct HTTP requests to test endpoints

## 📋 Available Workflows in Your Database

From the database scan, you have these workflows available for testing:

### **Simple Single-Agent Workflows:**
- **Toshiba Field Service Agent** 
  - ID: `60e54f16-386e-4f78-93be-462e0eb8bec2`
  - Agent Type: `toshiba`
  - Good for: Basic workflow testing

- **Weather web agent workflow**
  - ID: `0b711c8b-d255-4aab-a8d3-a6625d235690` 
  - Agent Type: `web_search`
  - Good for: Web search testing

- **Websearch Workflow**
  - ID: `c3a5c60f-6b27-4ff0-9a1f-754a56e6bed2`
  - Agent Type: `web_search`
  - Good for: Search functionality testing

### **Multi-Agent Workflows:**
- **Customer Service Command Agent**
  - ID: `59c93d59-18af-4752-9797-426c417dbd97`
  - Agents: 3 (router, router, toshiba)
  - Good for: Complex workflow testing

- **Media Planning Travel Agentic**
  - ID: `f2452794-62e5-483c-b203-df51a4bd18df`
  - Agents: 3 (router, router, router)
  - Good for: Multi-agent orchestration testing

## 🎯 Recommended Testing Workflow

### **Step 1: Quick Validation**
Start with mock testing to verify the tracing system works:
```bash
python test_workflow_comprehensive.py --mock-only
```

### **Step 2: Database Integration**
Test with a real workflow (no actual execution):
```bash
python test_workflow_comprehensive.py --workflow-id "60e54f16-386e-4f78-93be-462e0eb8bec2"
```

### **Step 3: Interactive Selection**
Explore available workflows interactively:
```bash
python test_workflow_comprehensive.py --interactive
```

### **Step 4: Full API Testing**
Test the complete async execution flow (requires FastAPI server):
```bash
# Terminal 1: Start server
python main.py

# Terminal 2: Run API tests  
python test_workflow_api.py --workflow-id "60e54f16-386e-4f78-93be-462e0eb8bec2"
```

## 🔍 What Each Test Validates

### **Mock Testing Validates:**
- ✅ Execution manager tracing functionality
- ✅ WorkflowStep and WorkflowTrace models
- ✅ Step status transitions
- ✅ Progress calculation
- ✅ Execution path tracking
- ✅ Branch decision recording
- ✅ Timing information capture

### **Real Workflow Testing Validates:**
- ✅ Database workflow retrieval
- ✅ Workflow configuration parsing
- ✅ Agent identification and setup
- ✅ Tracing initialization for real workflows
- ✅ Integration with existing workflow system

### **API Testing Validates:**
- ✅ FastAPI async execution endpoints
- ✅ Real-time progress monitoring
- ✅ Step-by-step execution tracking
- ✅ Background task execution
- ✅ Client polling workflows
- ✅ Error handling and timeouts
- ✅ Complete end-to-end execution

## 📊 Monitoring Capabilities

The new tracing system provides:

### **Real-time Progress Updates:**
```bash
📊 Progress: [████████████████████] 100.0% | Status: completed
📍 Current Step: Executing DataAgent
🔄 Workflow Step: 3/4
🛤️  Execution Path: CommandAgent → DataAgent
```

### **Detailed Step Information:**
```bash
📋 Step Details:
   1. ✅ data_processing (100ms)
   2. ✅ agent_execution - CommandAgent (8000ms)
   3. ✅ agent_execution - DataAgent (5200ms)
   4. ✅ data_processing (50ms)
```

### **Branch Decision Tracking:**
```bash
🌳 Branch Decisions:
  • processing_strategy: fast_path
  • data_source_choice: primary_db
```

## 🚀 API Endpoints for Client Integration

The system provides these endpoints for frontend integration:

### **Execution Control:**
- `POST /api/workflows/{id}/execute/async` - Start async execution
- `POST /api/executions/{id}/cancel` - Cancel execution

### **Monitoring (Optimized for Polling):**
- `GET /api/executions/{id}/progress` - Basic progress (poll every 1-2s)
- `GET /api/executions/{id}/steps` - Detailed steps (poll every 3-5s)
- `GET /api/executions/{id}/status` - Full status information

### **Analysis:**
- `GET /api/executions/{id}/trace` - Complete trace data
- `GET /api/executions/{id}/result` - Final execution result

## 🔧 Customization Options

### **Change Testing Workflow:**
1. **List available workflows:**
   ```bash
   python test_workflow_comprehensive.py --interactive
   ```

2. **Use specific workflow ID:**
   ```bash
   python test_workflow_comprehensive.py --workflow-id "YOUR_WORKFLOW_ID"
   ```

3. **Test with custom query:**
   ```bash
   python test_workflow_comprehensive.py --workflow-id "YOUR_ID" --query "Custom test query"
   ```

### **Modify Test Scenarios:**
Edit `test_workflow_comprehensive.py` to:
- Add custom step simulations
- Change timing parameters
- Add different error scenarios
- Modify branch decision logic

### **API Testing Configuration:**
Edit `test_workflow_api.py` to:
- Change server URL (`API_BASE_URL`)
- Adjust polling intervals (`POLL_INTERVAL`)
- Modify timeout settings (`MAX_POLL_TIME`)

## 🛠️ Troubleshooting

### **Database Connection Issues:**
```bash
# Error: connection to server at "localhost" (127.0.0.1), port 5433 failed
# Solution: Start your PostgreSQL database
docker-compose up -d postgres  # or your database startup command
```

### **Server Not Accessible:**
```bash
# Error: Server is not accessible
# Solution: Start FastAPI server
python main.py
# Or: uvicorn main:app --host 0.0.0.0 --port 8000
```

### **No Workflows Found:**
```bash
# Solution: Initialize database with default data
# Check your database fixtures or create test workflows
```

## 📈 Performance Monitoring

The tests provide performance insights:
- **Step execution timing** (in milliseconds) 
- **Total workflow duration**
- **API response times**
- **Polling efficiency**

Example output:
```bash
📋 Step Details:
   1. ✅ data_processing (50ms)
   2. ✅ agent_execution - CommandAgent (8000ms)  # Long-running agent
   3. ✅ agent_execution - DataAgent (200ms)      # Fast agent
   4. ✅ data_processing (25ms)

Duration: 8.3 seconds
```

## 🎉 Summary

You now have **comprehensive testing capabilities** for workflow async execution:

1. **Quick validation** with mock tests
2. **Database integration** testing
3. **Interactive workflow selection**
4. **Full API endpoint testing**
5. **Real-time monitoring** of executions
6. **Detailed tracing** and performance analysis

Choose the testing approach that best fits your current development needs!