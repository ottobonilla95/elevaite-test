#!/usr/bin/env python3
"""
Agent Studio Test Overview

This script provides an overview of all organized tests in the agent studio.
It shows the test structure and can be used to understand what tests are available.
"""

import os
import sys
from pathlib import Path


def count_test_files(directory):
    """Count test files in a directory."""
    if not os.path.exists(directory):
        return 0
    return len([f for f in os.listdir(directory) if f.startswith('test_') and f.endswith('.py')])


def list_test_files(directory):
    """List test files in a directory."""
    if not os.path.exists(directory):
        return []
    return [f for f in os.listdir(directory) if f.startswith('test_') and f.endswith('.py')]


def main():
    """Display test overview."""
    print("🧪 Agent Studio Test Organization Overview")
    print("=" * 60)
    
    base_dir = Path(__file__).parent / "tests"
    
    # Test categories
    categories = {
        "📊 Analytics Tests": "analytics",
        "🔄 Workflow Tests": "workflows", 
        "🧪 Functional Tests": "functional",
        "🔗 Integration Tests": "integration",
        "⚙️  Unit Tests": "unit"
    }
    
    total_tests = 0
    
    for category_name, directory in categories.items():
        test_dir = base_dir / directory
        test_count = count_test_files(test_dir)
        total_tests += test_count
        
        print(f"\n{category_name}")
        print("-" * 40)
        print(f"Location: tests/{directory}/")
        print(f"Test files: {test_count}")
        
        if test_count > 0:
            files = list_test_files(test_dir)
            for file in sorted(files):
                print(f"  • {file}")
    
    print(f"\n{'=' * 60}")
    print(f"📈 Total test files: {total_tests}")
    print(f"\n🚀 To run tests, use:")
    print(f"  python run_tests.py --help")
    print(f"  python run_tests.py --all")
    print(f"  python run_tests.py --unit")
    print(f"  python run_tests.py --workflows")
    print(f"  python run_tests.py --analytics-unit")


if __name__ == "__main__":
    main()
