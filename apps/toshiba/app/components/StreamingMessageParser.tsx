"use client";
import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './StreamingMessageParser.scss';

interface StreamingMessageParserProps {
  text: string;
  isStreaming: boolean;
}

interface ParsedContent {
  type: 'TEXT' | 'TABLE' | 'SOURCE';
  content: string;
}

export function StreamingMessageParser({ text, isStreaming }: StreamingMessageParserProps): JSX.Element {
  const [parsedContent, setParsedContent] = useState<ParsedContent[]>([]);

  useEffect(() => {
    if (!text) {
      setParsedContent([]);
      return;
    }

    // Parse the text to identify different sections
    const sections: ParsedContent[] = [];
    let currentText = '';
    
    // Regular expressions to match the different sections
    const textRegex = /<TEXT>(.*?)<\/TEXT>/gs;
    const tableRegex = /<TABLE>(.*?)<\/TABLE>/gs;
    const sourceRegex = /<SOURCE>(.*?)<\/SOURCE>/gs;
    
    // Find all TEXT sections
    let textMatch;
    let lastIndex = 0;
    
    // Process TEXT sections
    while ((textMatch = textRegex.exec(text)) !== null) {
      const matchStart = textMatch.index;
      const matchEnd = textRegex.lastIndex;
      
      // Add any text before the match as regular text
      if (matchStart > lastIndex) {
        const beforeText = text.substring(lastIndex, matchStart);
        if (beforeText.trim()) {
          sections.push({ type: 'TEXT', content: beforeText });
        }
      }
      
      // Add the matched TEXT content
      sections.push({ type: 'TEXT', content: textMatch[1] });
      lastIndex = matchEnd;
    }
    
    // Add any remaining text after the last TEXT match
    if (lastIndex < text.length) {
      const remainingText = text.substring(lastIndex);
      
      // Process TABLE sections in the remaining text
      let tableMatch;
      let tableLastIndex = 0;
      const tableText = remainingText;
      
      while ((tableMatch = tableRegex.exec(remainingText)) !== null) {
        const tableMatchStart = tableMatch.index;
        const tableMatchEnd = tableRegex.lastIndex;
        
        // Add any text before the table
        if (tableMatchStart > tableLastIndex) {
          const beforeTable = remainingText.substring(tableLastIndex, tableMatchStart);
          if (beforeTable.trim()) {
            sections.push({ type: 'TEXT', content: beforeTable });
          }
        }
        
        // Add the table content
        sections.push({ type: 'TABLE', content: tableMatch[1] });
        tableLastIndex = tableMatchEnd;
      }
      
      // Process SOURCE sections in the remaining text
      if (tableLastIndex < remainingText.length) {
        const afterTableText = remainingText.substring(tableLastIndex);
        let sourceMatch;
        let sourceLastIndex = 0;
        
        while ((sourceMatch = sourceRegex.exec(afterTableText)) !== null) {
          const sourceMatchStart = sourceMatch.index;
          const sourceMatchEnd = sourceRegex.lastIndex;
          
          // Add any text before the source
          if (sourceMatchStart > sourceLastIndex) {
            const beforeSource = afterTableText.substring(sourceLastIndex, sourceMatchStart);
            if (beforeSource.trim()) {
              sections.push({ type: 'TEXT', content: beforeSource });
            }
          }
          
          // Add the source content
          sections.push({ type: 'SOURCE', content: sourceMatch[1] });
          sourceLastIndex = sourceMatchEnd;
        }
        
        // Add any remaining text after the last source
        if (sourceLastIndex < afterTableText.length) {
          const finalText = afterTableText.substring(sourceLastIndex);
          if (finalText.trim()) {
            sections.push({ type: 'TEXT', content: finalText });
          }
        }
      }
    }
    
    // If no sections were found, treat the entire text as a TEXT section
    if (sections.length === 0 && text.trim()) {
      sections.push({ type: 'TEXT', content: text });
    }
    
    setParsedContent(sections);
  }, [text]);

  // Function to convert table string to markdown table
  const convertToMarkdownTable = (tableStr: string): string => {
    const lines = tableStr.trim().split('\n');
    let markdownTable = '';
    
    // Process each line of the table
    lines.forEach((line, index) => {
      // Clean up the line and split by pipe
      const cells = line.trim().split('|').filter(cell => cell.trim() !== '');
      
      if (cells.length > 0) {
        // Add the cells with proper markdown formatting
        markdownTable += '| ' + cells.join(' | ') + ' |\n';
        
        // Add the separator row after the header
        if (index === 0) {
          markdownTable += '| ' + cells.map(() => '---').join(' | ') + ' |\n';
        }
      }
    });
    
    return markdownTable;
  };

  return (
    <div className="streaming-message-parser">
      {parsedContent.map((section, index) => {
        switch (section.type) {
          case 'TEXT':
            return (
              <div key={`text-${index}`} className="text-section">
                <ReactMarkdown
                  children={section.content}
                  remarkPlugins={[remarkGfm]}
                />
              </div>
            );
          case 'TABLE':
            return (
              <div key={`table-${index}`} className="table-section">
                <ReactMarkdown
                  children={convertToMarkdownTable(section.content)}
                  remarkPlugins={[remarkGfm]}
                  components={{
                    table: ({ node, ...props }) => (
                      <table className="streaming-table" {...props} />
                    ),
                    th: ({ node, ...props }) => <th {...props} />,
                    td: ({ node, ...props }) => <td {...props} />,
                  }}
                />
              </div>
            );
          case 'SOURCE':
            return (
              <div key={`source-${index}`} className="source-section">
                <span className="source-label">Source:</span> {section.content}
              </div>
            );
          default:
            return null;
        }
      })}
      {isStreaming && parsedContent.length === 0 && (
        <div className="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      )}
    </div>
  );
}
