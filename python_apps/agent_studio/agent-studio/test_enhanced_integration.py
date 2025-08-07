#!/usr/bin/env python3
"""
Quick Integration Test for Enhanced FileReaderStep

This script tests the enhanced FileReaderStep integration to ensure
it works correctly with the existing agent_studio infrastructure.
"""

import asyncio
import tempfile
import os
import json
from pathlib import Path

# Add the agent_studio path to import modules
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from steps.tokenizer.file_reader_step import FileReaderStep, FileReaderStepConfig
from steps.tokenizer.enhanced_config import ExecutionMode


async def test_simple_mode_integration():
    """Test simple mode integration (backward compatibility)"""
    print("🔬 Testing Simple Mode Integration...")
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document for simple mode integration.\n")
        f.write("It contains multiple lines of text.\n")
        f.write("The enhanced FileReaderStep should process this in simple mode.")
        test_file = f.name
    
    try:
        # Simple mode configuration (existing format)
        config = FileReaderStepConfig(
            step_name="test_simple_integration",
            config={
                "file_path": test_file,
                "supported_formats": [".txt"],
                "max_file_size": 1024 * 1024,
                "encoding": "utf-8",
                "extract_metadata": True
            }
        )
        
        # Create and execute step
        step = FileReaderStep(config)
        result = await step.execute({})
        
        # Verify results
        assert result.status.value == "completed", f"Expected completed, got {result.status}"
        assert result.data.get("success", False), "Expected success=True"
        assert "test document" in result.data.get("content", ""), "Content not found"
        
        print("   ✅ Simple mode execution successful")
        print(f"   ✅ Content length: {len(result.data.get('content', ''))}")
        print(f"   ✅ Metadata keys: {list(result.data.get('metadata', {}).keys())}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Simple mode test failed: {e}")
        return False
    finally:
        os.unlink(test_file)


async def test_advanced_mode_integration():
    """Test advanced mode integration"""
    print("🔬 Testing Advanced Mode Integration...")
    
    # Create a markdown test file
    markdown_content = """# Test Document

This is a **test document** for advanced mode integration.

## Features
- Enhanced parsing
- Structured content
- Metadata extraction

### Table Example
| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

The enhanced FileReaderStep should process this in advanced mode.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(markdown_content)
        test_file = f.name
    
    try:
        # Advanced mode configuration
        config = FileReaderStepConfig(
            step_name="test_advanced_integration",
            config={
                "execution_mode": "advanced",
                "file_path": test_file,
                "supported_formats": [".md", ".txt"],
                "max_file_size": 1024 * 1024,
                "extract_metadata": True,
                "advanced_parsing": {
                    "default_mode": "auto_parser",
                    "use_markitdown": True,
                    "parsers": {
                        "md": {
                            "default_tool": "markitdown",
                            "available_tools": ["markitdown"]
                        }
                    }
                }
            }
        )
        
        # Create and execute step
        step = FileReaderStep(config)
        result = await step.execute({})
        
        # Verify results
        assert result.status.value == "completed", f"Expected completed, got {result.status}"
        assert result.data.get("success", False), "Expected success=True"
        assert "test document" in result.data.get("content", "").lower(), "Content not found"
        
        metadata = result.data.get("metadata", {})
        assert metadata.get("execution_mode") == "advanced", "Wrong execution mode"
        
        print("   ✅ Advanced mode execution successful")
        print(f"   ✅ Content length: {len(result.data.get('content', ''))}")
        print(f"   ✅ Parser used: {metadata.get('parser_used', 'unknown')}")
        print(f"   ✅ Execution mode: {metadata.get('execution_mode', 'unknown')}")
        print(f"   ✅ Structured content: {metadata.get('structured_content', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Advanced mode test failed: {e}")
        return False
    finally:
        os.unlink(test_file)


async def test_config_migration_integration():
    """Test configuration migration"""
    print("🔬 Testing Configuration Migration...")
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content for config migration.")
        test_file = f.name
    
    try:
        # Elevaite_ingestion style configuration
        elevaite_config = {
            "file_path": test_file,
            "parsing": {
                "default_mode": "auto_parser",
                "parsers": {
                    "txt": {
                        "default_tool": "markitdown",
                        "available_tools": ["markitdown"]
                    }
                }
            }
        }
        
        config = FileReaderStepConfig(
            step_name="test_migration_integration",
            config=elevaite_config
        )
        
        # Create step and verify migration
        step = FileReaderStep(config)
        execution_mode = step._get_execution_mode()
        
        assert execution_mode == ExecutionMode.ELEVAITE_DIRECT, f"Expected ELEVAITE_DIRECT, got {execution_mode}"
        
        # Execute to verify it works
        result = await step.execute({})
        assert result.status.value == "completed", "Execution failed"
        
        print("   ✅ Configuration migration successful")
        print(f"   ✅ Detected mode: {execution_mode}")
        print("   ✅ Execution completed successfully")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Config migration test failed: {e}")
        return False
    finally:
        os.unlink(test_file)


async def test_parser_availability():
    """Test parser availability detection"""
    print("🔬 Testing Parser Availability...")
    
    try:
        config = FileReaderStepConfig(
            step_name="test_parser_availability",
            config={"execution_mode": "advanced"}
        )
        
        step = FileReaderStep(config)
        available_parsers = step.parser_factory.get_available_parsers()
        
        print(f"   ✅ Available parsers: {available_parsers}")
        
        # Check for basic parsers
        assert len(available_parsers) > 0, "No parsers available"
        
        # Test parser info
        for file_type, parsers in available_parsers.items():
            for parser_name in parsers:
                info = step.parser_factory.get_parser_info(parser_name)
                print(f"   ✅ {parser_name}: available={info['available']}, formats={info['supported_formats']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Parser availability test failed: {e}")
        return False


async def main():
    """Run all integration tests"""
    print("🚀 Enhanced FileReaderStep Integration Tests")
    print("=" * 60)
    
    tests = [
        test_simple_mode_integration,
        test_advanced_mode_integration,
        test_config_migration_integration,
        test_parser_availability
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
            print()  # Add spacing
        except Exception as e:
            print(f"   ❌ Test {test.__name__} crashed: {e}\n")
    
    print("=" * 60)
    print(f"📊 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✅ Enhanced FileReaderStep is ready for production use")
    else:
        print("⚠️  Some integration tests failed")
        print("🔧 Check the implementation and dependencies")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
