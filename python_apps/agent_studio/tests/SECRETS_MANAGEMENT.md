# Test Secrets Management Guide

This guide explains how to manage API keys and secrets for testing without committing them to the repository.

## Overview

The test suite uses a **three-tier approach** for environment variables:

1. **`.env.test`** (committed) - Safe defaults, no real secrets
2. **`.env.test.local`** (gitignored) - Your personal secrets for local testing
3. **Environment variables** - CI/CD secrets, highest priority

## File Structure

```
python_apps/agent_studio/
├── agent-studio/
│   ├── .env                    # Development environment (gitignored)
│   ├── .env.test              # Test defaults (COMMITTED - no secrets!)
│   └── .env.test.local        # Your test secrets (GITIGNORED)
└── tests/
    └── conftest.py            # Loads .env.test then .env.test.local
```

## How It Works

### 1. Committed File: `.env.test`

This file is **committed to the repository** and contains **safe default values**:

```bash
# .env.test (committed)
TEST_DATABASE_URL=postgresql://elevaite:elevaite@localhost:5433/agent_studio
TEST_OPENAI_API_KEY=sk-test-mock-key  # Fake key, won't work
TEST_ANTHROPIC_API_KEY=                # Empty
```

**Purpose**: 
- Provides defaults for CI/CD
- Documents what variables are needed
- Safe to commit (no real secrets)

### 2. Local File: `.env.test.local` (Your Secrets)

This file is **gitignored** and contains **your real API keys**:

```bash
# .env.test.local (gitignored - YOUR SECRETS)
TEST_OPENAI_API_KEY=sk-proj-your-real-key-here
TEST_ANTHROPIC_API_KEY=sk-ant-your-real-key-here
```

**Purpose**:
- Store your personal API keys
- Override defaults from `.env.test`
- Never committed to git

### 3. Environment Variables (CI/CD)

In CI/CD, set environment variables directly:

```bash
# GitHub Actions, GitLab CI, etc.
export TEST_OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}
export TEST_DATABASE_URL=${{ secrets.TEST_DB_URL }}
```

**Purpose**:
- Highest priority (overrides both .env files)
- Used in CI/CD pipelines
- Managed by your CI/CD platform

## Setup Instructions

### For Local Development (No Real API Calls)

Just run tests - they'll use mock keys:

```bash
pytest tests/integration/ -v
```

### For Local Development (With Real API Keys)

1. **Create your local secrets file**:
```bash
cd python_apps/agent_studio/agent-studio
cp .env.test .env.test.local
```

2. **Edit `.env.test.local` with your real keys**:
```bash
# .env.test.local
TEST_OPENAI_API_KEY=sk-proj-your-real-openai-key
TEST_ANTHROPIC_API_KEY=sk-ant-your-real-anthropic-key
```

3. **Run tests** (will use your real keys):
```bash
pytest tests/integration/ -v
```

⚠️ **Warning**: This will make real API calls and incur costs!

### For CI/CD

1. **Add secrets to your CI/CD platform**:
   - GitHub: Settings → Secrets → Actions
   - GitLab: Settings → CI/CD → Variables
   - Jenkins: Credentials

2. **Set environment variables in your CI config**:

**GitHub Actions**:
```yaml
# .github/workflows/test.yml
env:
  TEST_OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  TEST_DATABASE_URL: ${{ secrets.TEST_DB_URL }}
```

**GitLab CI**:
```yaml
# .gitlab-ci.yml
test:
  variables:
    TEST_OPENAI_API_KEY: $OPENAI_API_KEY
    TEST_DATABASE_URL: $TEST_DB_URL
```

## Priority Order

When tests run, environment variables are loaded in this order (later overrides earlier):

1. `.env.test` (committed defaults)
2. `.env.test.local` (your local secrets)
3. Environment variables (CI/CD or shell)

Example:
```bash
# .env.test has:
TEST_OPENAI_API_KEY=sk-test-mock-key

# .env.test.local has:
TEST_OPENAI_API_KEY=sk-proj-my-real-key

# Result: Uses sk-proj-my-real-key

# But if you set environment variable:
export TEST_OPENAI_API_KEY=sk-proj-override-key

# Result: Uses sk-proj-override-key (highest priority)
```

## Mocking OpenAI Calls

For tests that execute workflows/agents, use the `mock_openai_client` fixture:

```python
def test_agent_execution(test_client, mock_openai_client):
    """OpenAI calls will be mocked - no real API calls."""
    response = test_client.post("/api/agents/execute", json={...})
    # No real OpenAI API call made
```

Without the fixture, tests will use whatever API key is configured (mock or real).

## Best Practices

### ✅ DO

- Commit `.env.test` with safe defaults
- Use `.env.test.local` for your personal keys
- Add `.env.test.local` to `.gitignore` (already done)
- Use `mock_openai_client` fixture for tests that don't need real LLM calls
- Document required variables in `.env.test`

### ❌ DON'T

- Commit real API keys to `.env.test`
- Commit `.env.test.local` to git
- Hard-code API keys in test files
- Use production keys in tests
- Share your `.env.test.local` file

## Checking What's Committed

To verify no secrets are committed:

```bash
# Check what's in .env.test (should be safe)
cat python_apps/agent_studio/agent-studio/.env.test

# Verify .env.test.local is gitignored
git check-ignore python_apps/agent_studio/agent-studio/.env.test.local
# Should output: python_apps/agent_studio/agent-studio/.env.test.local

# Check git status (should not show .env.test.local)
git status
```

## Troubleshooting

### "Tests are making real API calls!"

**Problem**: You have a real API key set  
**Solution**: 
```bash
# Check what key is being used
echo $TEST_OPENAI_API_KEY

# Unset it
unset TEST_OPENAI_API_KEY

# Or use mock fixture
def test_something(test_client, mock_openai_client):
    ...
```

### "I accidentally committed my API key!"

**Problem**: Real key in `.env.test`  
**Solution**:
1. Immediately revoke the key in your provider's dashboard
2. Remove it from `.env.test`
3. Use `git filter-branch` or BFG Repo-Cleaner to remove from history
4. Generate a new key

### "CI tests are failing with 'Invalid API key'"

**Problem**: CI doesn't have secrets configured  
**Solution**:
- Add secrets to your CI/CD platform
- Or: Tests should use mock keys by default (check `.env.test`)

## Summary

```
┌─────────────────────────────────────────────────────────┐
│                   Priority Order                         │
├─────────────────────────────────────────────────────────┤
│ 1. .env.test          → Safe defaults (COMMITTED)       │
│ 2. .env.test.local    → Your secrets (GITIGNORED)       │
│ 3. Environment vars   → CI/CD secrets (HIGHEST)         │
└─────────────────────────────────────────────────────────┘

✅ Safe to commit:     .env.test
❌ Never commit:       .env.test.local
🔒 Use for CI/CD:      Environment variables
🎭 Use for tests:      mock_openai_client fixture
```

