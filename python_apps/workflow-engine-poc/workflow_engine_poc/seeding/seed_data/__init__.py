"""
Seed Data Package

Contains JSON files for seeding new tenant databases with demo data.
Files are loaded in order to respect foreign key relationships:
1. prompts.json - System prompts (no dependencies)
2. tools.json - Tool definitions (no dependencies)
3. agents.json - Agent configs (depends on prompts)
4. workflows.json - Workflow definitions (may reference agents)
"""

