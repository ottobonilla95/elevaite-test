#!/usr/bin/env python3
"""
Test script for Enhanced TextChunkingStep

This script tests the enhanced TextChunkingStep with both simple and advanced modes
to ensure backward compatibility and new functionality work correctly.
"""

import asyncio
import os
import sys

# Add the agent_studio path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from steps.tokenizer.text_chunking_step import TextChunkingStep, TextChunkingStepConfig
from steps.tokenizer.enhanced_config import ExecutionMode


# Test content samples
SIMPLE_TEXT = """
This is a simple test document for chunking. It contains multiple sentences that should be processed correctly.
The enhanced TextChunkingStep should handle this content in both simple and advanced modes.
This text will be used to verify backward compatibility with existing chunking strategies.
"""

MARKDOWN_TEXT = """
# Enhanced Chunking Test Document

This document tests the **enhanced TextChunkingStep** with advanced chunking capabilities.

## Semantic Chunking

Semantic chunking groups sentences based on their meaning and context. This approach creates more coherent chunks that maintain topical consistency.

The algorithm uses sentence embeddings to calculate similarity between consecutive sentences. When similarity drops below a threshold, a new chunk is created.

## MDStructure Chunking

Markdown structure chunking respects the document's hierarchical structure. It preserves headers, sections, and other markdown elements.

### Benefits of Structure-Aware Chunking

- Maintains document hierarchy
- Preserves context within sections
- Better for documentation and structured content

### Implementation Details

The chunker analyzes markdown headers (both ATX and Setext styles) and creates chunks that respect these boundaries.

## Sentence Chunking

Sentence-based chunking focuses on natural sentence boundaries. It can use spaCy for better sentence detection or fall back to regex patterns.

This approach works well for narrative content and ensures that sentences are not split across chunks.

## Conclusion

The enhanced chunking system provides multiple strategies for different content types, ensuring optimal chunk quality for various use cases.
"""

TECHNICAL_TEXT = """
Algorithm Performance Analysis

The proposed algorithm demonstrates significant improvements in processing efficiency. 
Initial benchmarks show a 40% reduction in computation time compared to baseline methods.

Methodology

We conducted experiments using three different datasets: synthetic data, real-world samples, and edge cases.
Each dataset was processed using both the original and enhanced algorithms.
Performance metrics included execution time, memory usage, and accuracy scores.

Results

The enhanced algorithm consistently outperformed the baseline across all test scenarios.
Memory usage was reduced by an average of 25%, while maintaining 99.2% accuracy.
Edge case handling improved significantly, with error rates dropping from 3.1% to 0.8%.

Discussion

These results indicate that the optimization strategies successfully address the identified bottlenecks.
The improved performance makes the algorithm suitable for real-time applications.
Future work will focus on further optimization and scalability improvements.
"""


async def test_simple_mode_chunking():
    """Test simple mode chunking (backward compatibility)"""
    print("🔬 Testing Simple Mode Chunking...")
    
    try:
        # Simple mode configuration
        config = TextChunkingStepConfig(
            step_name="test_simple_chunking",
            config={
                "chunk_strategy": "sliding_window",
                "chunk_size": 200,
                "overlap": 0.2,
                "min_chunk_size": 50,
                "max_chunk_size": 400
            }
        )
        
        # Create and execute step
        step = TextChunkingStep(config)
        result = await step.execute({"content": SIMPLE_TEXT})
        
        # Verify results
        assert result.status.value == "completed", f"Expected completed, got {result.status}"
        assert result.data.get("success", False), "Expected success=True"
        assert len(result.data.get("chunks", [])) > 0, "No chunks produced"
        
        chunks = result.data["chunks"]
        metadata = result.data["metadata"]
        
        print(f"   ✅ Simple mode execution successful")
        print(f"   ✅ Chunks produced: {len(chunks)}")
        print(f"   ✅ Strategy used: {metadata.get('chunk_strategy')}")
        print(f"   ✅ Average chunk size: {metadata.get('average_chunk_size')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Simple mode test failed: {e}")
        return False


async def test_advanced_semantic_chunking():
    """Test advanced semantic chunking"""
    print("🔬 Testing Advanced Semantic Chunking...")
    
    try:
        # Advanced semantic chunking configuration
        config = TextChunkingStepConfig(
            step_name="test_semantic_chunking",
            config={
                "execution_mode": "advanced",
                "advanced_chunking": {
                    "default_strategy": "semantic",
                    "strategies": {
                        "semantic_chunking": {
                            "breakpoint_threshold_type": "percentile",
                            "breakpoint_threshold_amount": 85,
                            "max_chunk_size": 1000,
                            "min_chunk_size": 100
                        }
                    }
                }
            }
        )
        
        # Create and execute step
        step = TextChunkingStep(config)
        result = await step.execute({"content": TECHNICAL_TEXT})
        
        # Verify results
        assert result.status.value == "completed", f"Expected completed, got {result.status}"
        assert result.data.get("success", False), "Expected success=True"
        
        chunks = result.data["chunks"]
        metadata = result.data["metadata"]
        
        assert metadata.get("execution_mode") == "advanced", "Wrong execution mode"
        assert "semantic" in metadata.get("chunker_used", ""), "Wrong chunker used"
        
        print(f"   ✅ Advanced semantic chunking successful")
        print(f"   ✅ Chunks produced: {len(chunks)}")
        print(f"   ✅ Chunker used: {metadata.get('chunker_used')}")
        print(f"   ✅ Execution mode: {metadata.get('execution_mode')}")
        
        # Check for semantic-specific metrics
        if "avg_semantic_score" in metadata:
            print(f"   ✅ Semantic score: {metadata.get('avg_semantic_score'):.3f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Advanced semantic chunking test failed: {e}")
        return False


async def test_mdstructure_chunking():
    """Test markdown structure chunking"""
    print("🔬 Testing MDStructure Chunking...")
    
    try:
        # MDStructure chunking configuration
        config = TextChunkingStepConfig(
            step_name="test_mdstructure_chunking",
            config={
                "execution_mode": "advanced",
                "advanced_chunking": {
                    "default_strategy": "mdstructure",
                    "strategies": {
                        "mdstructure": {
                            "chunk_size": 800,
                            "min_chunk_size": 100,
                            "max_chunk_size": 1500,
                            "respect_headers": True,
                            "include_headers": True
                        }
                    }
                }
            }
        )
        
        # Create and execute step
        step = TextChunkingStep(config)
        result = await step.execute({"content": MARKDOWN_TEXT})
        
        # Verify results
        assert result.status.value == "completed", f"Expected completed, got {result.status}"
        assert result.data.get("success", False), "Expected success=True"
        
        chunks = result.data["chunks"]
        metadata = result.data["metadata"]
        
        assert metadata.get("execution_mode") == "advanced", "Wrong execution mode"
        assert "mdstructure" in metadata.get("chunker_used", ""), "Wrong chunker used"
        
        print(f"   ✅ MDStructure chunking successful")
        print(f"   ✅ Chunks produced: {len(chunks)}")
        print(f"   ✅ Chunker used: {metadata.get('chunker_used')}")
        
        # Check for structure-specific metrics
        if "max_structure_level" in metadata:
            print(f"   ✅ Max structure level: {metadata.get('max_structure_level')}")
        
        # Verify chunks have structure information
        structured_chunks = [c for c in chunks if c.get("headers")]
        print(f"   ✅ Chunks with headers: {len(structured_chunks)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ MDStructure chunking test failed: {e}")
        return False


async def test_auto_strategy_selection():
    """Test automatic strategy selection"""
    print("🔬 Testing Auto Strategy Selection...")
    
    try:
        # Auto strategy selection configuration
        config = TextChunkingStepConfig(
            step_name="test_auto_selection",
            config={
                "execution_mode": "advanced",
                "advanced_chunking": {
                    "default_strategy": "auto",
                    "auto_select_strategy": True
                }
            }
        )
        
        # Test with different content types
        test_cases = [
            ("Markdown content", MARKDOWN_TEXT),
            ("Technical content", TECHNICAL_TEXT),
            ("Simple content", SIMPLE_TEXT)
        ]
        
        step = TextChunkingStep(config)
        
        for content_type, content in test_cases:
            result = await step.execute({"content": content})
            
            assert result.status.value == "completed", f"Failed for {content_type}"
            assert result.data.get("success", False), f"No success for {content_type}"
            
            metadata = result.data["metadata"]
            chunker_used = metadata.get("chunker_used", "unknown")
            
            print(f"   ✅ {content_type}: {chunker_used} strategy selected")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Auto strategy selection test failed: {e}")
        return False


async def test_config_migration():
    """Test configuration migration from elevaite_ingestion format"""
    print("🔬 Testing Configuration Migration...")
    
    try:
        # Elevaite_ingestion style configuration
        elevaite_config = {
            "chunking": {
                "default_strategy": "semantic_chunking",
                "strategies": {
                    "semantic_chunking": {
                        "breakpoint_threshold_type": "percentile",
                        "breakpoint_threshold_amount": 90
                    }
                }
            }
        }
        
        config = TextChunkingStepConfig(
            step_name="test_migration",
            config=elevaite_config
        )
        
        step = TextChunkingStep(config)
        
        # Verify config was migrated
        execution_mode = step._get_execution_mode()
        assert execution_mode == ExecutionMode.ELEVAITE_DIRECT, "Wrong execution mode detected"
        
        # Test execution
        result = await step.execute({"content": TECHNICAL_TEXT})
        assert result.status.value == "completed", "Execution failed"
        
        print("   ✅ Configuration migration successful")
        print(f"   ✅ Detected mode: {execution_mode}")
        print("   ✅ Execution completed successfully")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Config migration test failed: {e}")
        return False


async def test_chunker_availability():
    """Test chunker availability detection"""
    print("🔬 Testing Chunker Availability...")
    
    try:
        config = TextChunkingStepConfig(
            step_name="test_chunker_availability",
            config={"execution_mode": "advanced"}
        )
        
        step = TextChunkingStep(config)
        available_chunkers = step.chunker_factory.get_available_chunkers()
        
        print(f"   ✅ Available chunkers: {available_chunkers}")
        
        # Check for basic chunkers
        assert len(available_chunkers) > 0, "No chunkers available"
        
        # Test chunker info
        for chunker_name, is_available in available_chunkers.items():
            if is_available:
                info = step.chunker_factory.get_chunker_info(chunker_name)
                print(f"   ✅ {chunker_name}: {info['description']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Chunker availability test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Enhanced TextChunkingStep Tests")
    print("=" * 60)
    
    tests = [
        test_simple_mode_chunking,
        test_advanced_semantic_chunking,
        test_mdstructure_chunking,
        test_auto_strategy_selection,
        test_config_migration,
        test_chunker_availability
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
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        print("✅ Enhanced TextChunkingStep is ready for production use")
    else:
        print("⚠️  Some tests failed")
        print("🔧 Check the implementation and dependencies")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
