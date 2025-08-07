#!/usr/bin/env python3

import re

MARKDOWN_TEXT = """
# Enhanced Chunking Test Document

This document tests the **enhanced TextChunkingStep** with advanced chunking capabilities.

## Semantic Chunking

Semantic chunking groups sentences based on their meaning and context.

- Maintains document hierarchy
- Preserves context within sections
- Better for documentation and structured content

## Conclusion

The enhanced chunking system provides multiple strategies.
"""

def detect_markdown(content):
    """Detect if content contains markdown formatting"""
    
    markdown_patterns = [
        r'^#{1,6}\s+',  # Headers
        r'\*\*[^*]+\*\*',  # Bold
        r'\*[^*]+\*',  # Italic
        r'```[^`]*```',  # Code blocks
        r'`[^`]+`',  # Inline code
        r'\[([^\]]+)\]\([^)]+\)',  # Links
        r'^\s*[-*+]\s+',  # Lists
        r'^\s*\d+\.\s+',  # Numbered lists
        r'\|.*\|',  # Tables
    ]
    
    markdown_score = 0
    for pattern in markdown_patterns:
        try:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                print(f'Pattern "{pattern}": {len(matches)} matches - {matches[:3]}')
                markdown_score += 1
        except re.error as e:
            print(f'Regex error for pattern "{pattern}": {e}')
    
    print(f'Total markdown score: {markdown_score}')
    print(f'Has markdown: {markdown_score >= 3}')
    return markdown_score >= 3

if __name__ == "__main__":
    detect_markdown(MARKDOWN_TEXT)
