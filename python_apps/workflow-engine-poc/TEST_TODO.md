# Testing TODO List for Workflow Engine PoC

This checklist tracks the testing work needed to bring the PoC to production-ready quality.

## Immediate (This Week)

### Fix Broken E2E Tests
- [ ] Review all 28 failing E2E tests
- [ ] Decision: Convert to integration tests OR set up E2E infrastructure
- [ ] Option A: Convert to integration tests using TestClient
  - [ ] `tests/e2e/test_approvals_e2e.py` - Convert to integration
  - [ ] `tests/e2e/test_interactive_e2e.py` - Convert to integration
  - [ ] `tests/e2e/test_megaflow.py` - Convert to integration
  - [ ] `tests/e2e/test_streaming.py` - Convert to integration
- [ ] Option B: Set up E2E infrastructure
  - [ ] Create docker-compose for E2E tests
  - [ ] Add server startup/shutdown in conftest
  - [ ] Update E2E tests to use proper base URL
- [ ] Mark tests as `@pytest.mark.skip` if not ready

### Run Coverage Baseline
- [ ] Run full test suite with coverage
- [ ] Generate HTML coverage report
- [ ] Identify files with <50% coverage
- [ ] Create issues for uncovered critical code
- [ ] Document baseline coverage percentage

### Add Critical Router Tests
- [ ] `routers/agents.py` - CRUD operations
  - [ ] Test create agent
  - [ ] Test list agents
  - [ ] Test get agent by ID
  - [ ] Test update agent
  - [ ] Test delete agent
  - [ ] Test agent tool bindings
  - [ ] Test invalid inputs
- [ ] `routers/tools.py` - Tool registry
  - [ ] Test list tools
  - [ ] Test get tool by name
  - [ ] Test create tool
  - [ ] Test update tool
  - [ ] Test delete tool
  - [ ] Test tool categories
  - [ ] Test MCP server registration
- [ ] `routers/prompts.py` - Prompt management
  - [ ] Test create prompt
  - [ ] Test list prompts
  - [ ] Test get prompt by ID
  - [ ] Test update prompt
  - [ ] Test delete prompt
- [ ] `routers/messages.py` - Agent messages
  - [ ] Test send message
  - [ ] Test get messages
  - [ ] Test message history
- [ ] `routers/approvals.py` - Approval workflow
  - [ ] Test create approval
  - [ ] Test approve/reject
  - [ ] Test approval status

## Short Term (Next 2 Weeks)

### Add Service Tests
- [ ] `services/workflows_service.py`
  - [ ] Test create_workflow
  - [ ] Test list_workflows_entities
  - [ ] Test get_workflow_entity
  - [ ] Test update_workflow
  - [ ] Test delete_workflow
  - [ ] Test workflow validation
- [ ] `services/executions_service.py`
  - [ ] Test create_execution
  - [ ] Test get_execution
  - [ ] Test list_executions
  - [ ] Test update_execution_status
  - [ ] Test execution cleanup
- [ ] `services/agents_service.py`
  - [ ] Test create_agent
  - [ ] Test list_agents
  - [ ] Test get_agent
  - [ ] Test update_agent
  - [ ] Test delete_agent
  - [ ] Test agent tool bindings
- [ ] `services/tools_service.py`
  - [ ] Test create_tool
  - [ ] Test list_tools
  - [ ] Test get_tool
  - [ ] Test update_tool
  - [ ] Test delete_tool

### Add RBAC/Security Tests
- [ ] Authentication tests
  - [ ] Test JWT validation
  - [ ] Test API key validation
  - [ ] Test token expiration
  - [ ] Test invalid tokens
  - [ ] Test missing tokens
- [ ] Authorization tests
  - [ ] Test resource ownership
  - [ ] Test role permissions
  - [ ] Test unauthorized access
  - [ ] Test cross-tenant access prevention
- [ ] Tenant isolation tests
  - [ ] Test workflows isolated by tenant
  - [ ] Test executions isolated by tenant
  - [ ] Test agents isolated by tenant
  - [ ] Test tools isolated by tenant

### Add Error Handling Tests
- [ ] Input validation tests
  - [ ] Test malformed JSON
  - [ ] Test invalid UUIDs
  - [ ] Test missing required fields
  - [ ] Test invalid field types
  - [ ] Test field length limits
- [ ] Database failure tests
  - [ ] Test connection failures
  - [ ] Test transaction rollbacks
  - [ ] Test constraint violations
  - [ ] Test deadlocks
- [ ] External service failure tests
  - [ ] Test OpenAI API failures
  - [ ] Test Anthropic API failures
  - [ ] Test Redis failures
  - [ ] Test timeout handling

## Medium Term (Next Month)

### Add Integration Tests
- [ ] Database transaction tests
  - [ ] Test rollback on error
  - [ ] Test commit on success
  - [ ] Test nested transactions
- [ ] Foreign key constraint tests
  - [ ] Test cascade deletes
  - [ ] Test constraint violations
  - [ ] Test orphan prevention
- [ ] Concurrent access tests
  - [ ] Test concurrent workflow execution
  - [ ] Test concurrent database writes
  - [ ] Test race conditions

### Add Business Logic Tests
- [ ] Scheduler tests (`scheduler.py`)
  - [ ] Test schedule creation
  - [ ] Test schedule execution
  - [ ] Test cron parsing
  - [ ] Test interval scheduling
  - [ ] Test schedule cleanup
- [ ] Streaming tests (`streaming.py`)
  - [ ] Test SSE stream creation
  - [ ] Test heartbeat
  - [ ] Test event types
  - [ ] Test connection cleanup
  - [ ] Test concurrent streams
- [ ] DBOS integration tests (`dbos_impl/`)
  - [ ] Test DBOS workflow execution
  - [ ] Test DBOS persistence
  - [ ] Test DBOS recovery
  - [ ] Test DBOS vs local execution

### Add Performance Tests
- [ ] Load tests
  - [ ] Test 100 concurrent workflow executions
  - [ ] Test 1000 workflow creations
  - [ ] Test large workflow definitions
  - [ ] Test large execution results
- [ ] Stress tests
  - [ ] Test memory usage under load
  - [ ] Test CPU usage under load
  - [ ] Test database connection pool
  - [ ] Test Redis connection pool
- [ ] Benchmark tests
  - [ ] Benchmark workflow execution time
  - [ ] Benchmark database query time
  - [ ] Benchmark API response time

## Long Term (Next 3 Months)

### Add Security Tests
- [ ] SQL injection tests
  - [ ] Test workflow name injection
  - [ ] Test step config injection
  - [ ] Test filter injection
- [ ] XSS tests
  - [ ] Test workflow description XSS
  - [ ] Test agent name XSS
  - [ ] Test prompt content XSS
- [ ] Authentication bypass tests
  - [ ] Test missing auth headers
  - [ ] Test forged tokens
  - [ ] Test expired tokens
- [ ] Authorization bypass tests
  - [ ] Test privilege escalation
  - [ ] Test horizontal access
  - [ ] Test vertical access

### Add Data Integrity Tests
- [ ] Migration tests
  - [ ] Test forward migrations
  - [ ] Test rollback migrations
  - [ ] Test data preservation
- [ ] Backup/restore tests
  - [ ] Test database backup
  - [ ] Test database restore
  - [ ] Test data consistency
- [ ] Data validation tests
  - [ ] Test data constraints
  - [ ] Test data formats
  - [ ] Test data relationships

### Add E2E Test Infrastructure
- [ ] Docker compose for E2E
  - [ ] PostgreSQL service
  - [ ] Redis service
  - [ ] Workflow engine service
  - [ ] Test data seeding
- [ ] E2E test fixtures
  - [ ] Database seeding
  - [ ] Test user creation
  - [ ] Test workflow creation
- [ ] E2E test cleanup
  - [ ] Database cleanup
  - [ ] Redis cleanup
  - [ ] File cleanup

## Continuous Improvements

### Code Coverage
- [ ] Maintain >70% overall coverage
- [ ] Maintain >80% coverage for new code
- [ ] Identify and test uncovered critical paths
- [ ] Remove dead code

### Test Quality
- [ ] Review test assertions (not just status codes)
- [ ] Add edge case tests
- [ ] Add negative tests
- [ ] Add boundary tests

### Test Performance
- [ ] Keep unit tests <1s total
- [ ] Keep integration tests <10s total
- [ ] Parallelize slow tests
- [ ] Mock external services

### Documentation
- [ ] Update TESTING.md with new patterns
- [ ] Add examples for complex tests
- [ ] Document test data factories
- [ ] Document mock strategies

## Metrics to Track

### Coverage Metrics
- [ ] Overall coverage percentage
- [ ] Coverage by module
- [ ] Coverage trend over time
- [ ] Uncovered critical paths

### Test Metrics
- [ ] Total test count
- [ ] Test pass rate
- [ ] Test execution time
- [ ] Flaky test count

### Quality Metrics
- [ ] Bug escape rate
- [ ] Test-to-code ratio
- [ ] Code review test coverage
- [ ] PR test failure rate

## Notes

- Mark completed items with `[x]`
- Add new items as needed
- Review and update weekly
- Prioritize based on risk and impact
- Don't let perfect be the enemy of good

