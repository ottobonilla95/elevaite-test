"""
Test script for Enhanced FileReaderStep

This script tests the enhanced FileReaderStep with both simple and advanced modes
to ensure backward compatibility and new functionality work correctly.
"""

import asyncio
import tempfile
import os
from pathlib import Path

from file_reader_step import FileReaderStep, FileReaderStepConfig
from enhanced_config import ExecutionMode, ConfigDefaults


async def test_simple_mode():
    """Test FileReaderStep in simple mode (backward compatibility)"""
    print("Testing Simple Mode...")
    
    # Create a test text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document for simple mode.\nIt has multiple lines.\nAnd some content to parse.")
        test_file = f.name
    
    try:
        # Simple mode configuration
        config = FileReaderStepConfig(
            step_name="test_simple_reader",
            config={
                "file_path": test_file,
                "supported_formats": [".txt"],
                "max_file_size": 1024 * 1024,
                "encoding": "utf-8"
            }
        )
        
        # Create and execute step
        step = FileReaderStep(config)
        result = await step.execute({})
        
        # Verify results
        assert result.status.value == "completed", f"Expected completed, got {result.status}"
        assert result.data["success"] == True, "Expected success=True"
        assert "This is a test document" in result.data["content"], "Content not found"
        assert result.data["metadata"]["extraction_method"] in ["text", "utf-8"], "Wrong extraction method"
        
        print("✅ Simple mode test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Simple mode test failed: {e}")
        return False
    finally:
        os.unlink(test_file)


async def test_advanced_mode():
    """Test FileReaderStep in advanced mode"""
    print("Testing Advanced Mode...")
    
    # Create a test text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document for advanced mode.\nIt has multiple lines.\nAnd some content to parse.")
        test_file = f.name
    
    try:
        # Advanced mode configuration
        config = FileReaderStepConfig(
            step_name="test_advanced_reader",
            config={
                "execution_mode": "advanced",
                "file_path": test_file,
                "advanced_parsing": {
                    "default_mode": "auto_parser",
                    "parsers": {
                        "txt": {
                            "default_tool": "markitdown",
                            "available_tools": ["markitdown"]
                        }
                    }
                },
                "max_file_size": 1024 * 1024
            }
        )
        
        # Create and execute step
        step = FileReaderStep(config)
        result = await step.execute({})
        
        # Verify results
        assert result.status.value == "completed", f"Expected completed, got {result.status}"
        assert result.data["success"] == True, "Expected success=True"
        assert "This is a test document" in result.data["content"], "Content not found"
        assert result.data["metadata"]["execution_mode"] == "advanced", "Wrong execution mode"
        assert "parser_used" in result.data["metadata"], "Parser info missing"
        
        print("✅ Advanced mode test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Advanced mode test failed: {e}")
        return False
    finally:
        os.unlink(test_file)


async def test_config_migration():
    """Test configuration migration from different formats"""
    print("Testing Configuration Migration...")
    
    try:
        # Test elevaite_ingestion style config
        elevaite_config = {
            "parsing": {
                "default_mode": "auto_parser",
                "parsers": {
                    "pdf": {
                        "default_tool": "docling",
                        "available_tools": ["docling", "pdfplumber"]
                    }
                }
            },
            "chunking": {
                "default_strategy": "semantic_chunking"
            }
        }
        
        config = FileReaderStepConfig(
            step_name="test_migration",
            config=elevaite_config
        )
        
        step = FileReaderStep(config)
        
        # Verify config was migrated
        assert step._get_execution_mode() == ExecutionMode.ELEVAITE_DIRECT, "Wrong execution mode detected"
        
        print("✅ Configuration migration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration migration test failed: {e}")
        return False


async def test_parser_availability():
    """Test parser availability detection"""
    print("Testing Parser Availability...")
    
    try:
        config = FileReaderStepConfig(
            step_name="test_parsers",
            config={"execution_mode": "advanced"}
        )
        
        step = FileReaderStep(config)
        
        # Get available parsers
        available_parsers = step.parser_factory.get_available_parsers()
        
        print(f"Available parsers: {available_parsers}")
        
        # Should have at least some basic parsers
        assert len(available_parsers) > 0, "No parsers available"
        
        print("✅ Parser availability test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Parser availability test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting Enhanced FileReaderStep Tests\n")
    
    tests = [
        test_simple_mode,
        test_advanced_mode,
        test_config_migration,
        test_parser_availability
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced FileReaderStep is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
