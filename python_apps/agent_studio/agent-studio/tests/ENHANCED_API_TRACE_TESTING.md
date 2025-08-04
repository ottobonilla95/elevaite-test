# Enhanced API Trace Testing

The API test suite has been significantly enhanced to include **real-time trace monitoring** capabilities. This provides comprehensive visibility into workflow execution with live updates.

## 🆕 New Trace Monitoring Features

### **1. Real-time Trace Updates During Execution**

The `monitor_execution` method now includes live trace monitoring:

```bash
🔍 Monitoring execution: abc123-def456
============================================================
📊 Progress: [████████████████████] 100.0% | Status: running
📍 Current Step: Executing DataAgent
🔄 Workflow Step: 3/4
🛤️  Execution Path: CommandAgent → DataAgent

# Live trace updates:
🌳 Branch Decision: processing_strategy → fast_path
🔗 Live Execution Path: CommandAgent → DataAgent → ToshibaAgent
⏱️  CommandAgent: 8000ms
⏱️  DataAgent: 1200ms
  ✅ agent_execution - ToshibaAgent [completed]
```

### **2. Dedicated Trace-Only Monitoring**

New `--trace-only` option for focused trace monitoring:

```bash
python test_workflow_api.py --trace-only "execution_id"
```

This provides:
- **Step-by-step progress** with timing
- **Branch decision tracking** as they happen
- **Execution path visualization**
- **Real-time status updates**

### **3. Comprehensive Final Trace Analysis**

Enhanced summary with detailed breakdowns:

```bash
🔍 Complete Trace Analysis:
  Total Steps: 4
  Steps Completed: 4
  Full Execution Path: CommandAgent → DataAgent → ToshibaAgent

📋 Detailed Step Breakdown:
     1. ✅ data_processing (50ms)
     2. ✅ CommandAgent (8000ms)
     3. ✅ DataAgent (1200ms)
     4. ✅ data_processing (25ms)

⏱️  Total Step Duration: 9275ms (9.28s)

🌳 Branch Decision Details:
    • processing_strategy: fast_path
      └─ Decided at: 2024-01-15T10:30:15Z

📋 Workflow Metadata:
    Workflow ID: 60e54f16-386e-4f78-93be-462e0eb8bec2
    Execution ID: abc123-def456
```

## 🚀 Usage Options

### **Full Execution with Trace Monitoring**
```bash
# Test workflow with comprehensive trace monitoring
python test_workflow_api.py --workflow-id "60e54f16-386e-4f78-93be-462e0eb8bec2"
```

**Shows:**
- ✅ Basic progress updates
- ✅ Step-by-step execution  
- ✅ **Real-time trace data**
- ✅ Branch decisions as they happen
- ✅ Execution path updates
- ✅ Step timing information
- ✅ Comprehensive final analysis

### **Trace-Only Monitoring**
```bash
# Monitor only trace information for an existing execution
python test_workflow_api.py --trace-only "execution_id_here"
```

**Shows:**
- 🔄 Trace-specific progress bar
- 📋 Step updates with timing
- 🌳 Branch decisions 
- 🛤️  Execution path visualization
- ⚠️  Handles cases where trace data isn't available

### **General Execution Monitoring**
```bash
# Monitor existing execution (all data including trace)
python test_workflow_api.py --monitor-only "execution_id_here"
```

**Shows:**
- 📊 Full progress monitoring
- 🔍 **Enhanced trace updates**
- 📋 Step details
- 🎯 Final comprehensive analysis

## 🔍 Real-time Trace Information

### **Live Updates Include:**

1. **Branch Decisions** (as they happen)
   ```bash
   🌳 Branch Decision: data_source_choice → primary_db
   🌳 Branch Decision: processing_mode → parallel
   ```

2. **Execution Path Tracking**
   ```bash
   🔗 Live Execution Path: CommandAgent → DataAgent
   🔗 Live Execution Path: CommandAgent → DataAgent → ToshibaAgent
   ```

3. **Step Timing** (for completed steps)
   ```bash
   ⏱️  CommandAgent: 8000ms
   ⏱️  DataAgent: 1200ms
   ⏱️  ToshibaAgent: 3500ms
   ```

4. **Step Status Updates**
   ```bash
   ✅ agent_execution - CommandAgent [completed]
   🔄 agent_execution - DataAgent [running]
   ⏳ data_processing [pending]
   ```

### **Enhanced Final Analysis:**

- **Complete step breakdown** with input/output data
- **Total execution timing** analysis
- **Branch decision history** with timestamps
- **Workflow metadata** for debugging
- **Error details** if any steps failed

## 📋 API Endpoints Used

The enhanced tester uses all trace-related endpoints:

1. **`GET /api/executions/{id}/trace`** - Full trace data
2. **`GET /api/executions/{id}/steps`** - Step-by-step details  
3. **`GET /api/executions/{id}/progress`** - Basic progress
4. **`GET /api/executions/{id}/status`** - Overall status

## 🎯 Benefits for Development

### **Real-time Debugging**
- See exactly where workflows get stuck
- Monitor branch decision logic
- Track agent execution timing
- Identify performance bottlenecks

### **Client Integration Testing**
- Verify polling strategies work correctly
- Test real-time UI update scenarios
- Validate trace data structure
- Ensure proper error handling

### **Performance Analysis**
- Step-by-step timing analysis
- Total execution duration tracking
- Agent performance comparison
- Resource usage insights

## 📈 Example Full Trace Output

```bash
🚀 Testing Workflow Execution
Workflow ID: 60e54f16-386e-4f78-93be-462e0eb8bec2
Query: Test the Toshiba Field Service Agent

🔍 Monitoring execution: abc123-def456
============================================================
📊 Progress: [████░░░░░░░░░░░░░░░░] 20.0% | Status: running
📍 Current Step: Initializing workflow
🔄 Workflow Step: 1/4

  ✅ data_processing - System [completed]
  🔄 agent_execution - ToshibaAgent [running]

🌳 Branch Decision: service_type → field_service
🔗 Live Execution Path: ToshibaAgent
⏱️  data_processing: 50ms

📊 Progress: [████████████████████] 100.0% | Status: completed
✅ Execution COMPLETED

============================================================
📋 EXECUTION SUMMARY
============================================================
Status: completed
Progress: 100.0%
Duration: 12.3 seconds

🔍 Complete Trace Analysis:
  Total Steps: 4
  Steps Completed: 4
  Full Execution Path: ToshibaAgent

📋 Detailed Step Breakdown:
     1. ✅ data_processing (50ms)
     2. ✅ ToshibaAgent (12000ms)
        Input: {'query': 'Test the Toshiba Field Service Agent'}
        Output: {'result': 'Service request processed successfully'}
     3. ✅ data_processing (25ms)

⏱️  Total Step Duration: 12075ms (12.08s)

🌳 Branch Decision Details:
    • service_type: field_service
      └─ Decided at: 2024-01-15T10:30:15Z

📋 Workflow Metadata:
    Workflow ID: 60e54f16-386e-4f78-93be-462e0eb8bec2
    Execution ID: abc123-def456
```

## 🎉 Summary

The enhanced API testing now provides **complete workflow execution visibility** with:

- ✅ **Real-time trace monitoring** during execution
- ✅ **Live branch decision tracking**
- ✅ **Step-by-step timing analysis**
- ✅ **Execution path visualization**
- ✅ **Comprehensive final analysis**
- ✅ **Dedicated trace-only monitoring mode**

This gives you **full observability** into workflow execution for debugging, performance analysis, and client integration testing! 🔍✨