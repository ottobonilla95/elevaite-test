"use client";
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SourceReference } from "../lib/interfaces";
import { SourcePill } from "./SourcePill";
import "./InlineSourceMessage.scss";
import Modal from "./Modal";

interface InlineSourceMessageProps {
  text: string;
  sources: SourceReference[];
}

export function InlineSourceMessage({ text, sources }: InlineSourceMessageProps): JSX.Element {
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [currentImageIndex, setCurrentImageIndex] = React.useState(0);

  if (!text) return <></>;
  if (!sources || sources.length === 0) {
    // If no sources, just render the markdown
    return (
      <ReactMarkdown
        children={text}
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ node, ...props }) => (
            <table className="custom-table" {...props} />
          ),
          th: ({ node, ...props }) => <th {...props} />,
          td: ({ node, ...props }) => <td {...props} />,
        }}
      />
    );
  }

  // Create a map of aws_id to source for quick lookup
  const sourceMap = new Map<string, SourceReference>();
  sources.forEach(source => {
    if (source.awsLink) {
      sourceMap.set(source.awsLink, source);
    }
  });

  // Create a working copy of the text
  let processedText = text;

  // First, replace any sources that have fullMatchText (exact matches from extraction)
  sources.forEach(source => {
    if (source.fullMatchText && source.awsLink) {
      // Escape special regex characters in the fullMatchText
      const escapedText = source.fullMatchText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(escapedText, 'g');

      // Replace with a placeholder
      processedText = processedText.replace(regex, `__SOURCE_PILL_${source.awsLink}__`);
    }
  });

  // Pattern to find the full source reference with aws_id (for any that weren't caught by fullMatchText)
  // This matches patterns like: "6800 Parts Manual (3) page 91 [aws_id: 6800 Parts Manual (3)_page_91]"
  const fullSourcePattern = /(.*?)\s+page\s+(\d+)\s+\[aws_id:\s+(.*?)\]/g;

  // Also look for just the aws_id tag in case it appears alone
  const awsIdPattern = /\[aws_id:\s+(.*?)\]/g;

  // Split the text into segments: regular text and source matches
  const segments: React.ReactNode[] = [];

  // Then try to find and replace any remaining full source patterns
  processedText = processedText.replace(fullSourcePattern, (match, filename, pageNum, awsId) => {
    const source = sourceMap.get(awsId.trim());
    if (source) {
      // Return a placeholder that we'll replace with the actual component
      return `__SOURCE_PILL_${awsId.trim()}__`;
    }
    return match; // Keep the original text if no matching source
  });

  // Finally, find and replace any standalone aws_id tags
  const finalProcessedText = processedText.replace(awsIdPattern, (match, awsId) => {
    const source = sourceMap.get(awsId.trim());
    if (source) {
      return `__SOURCE_PILL_${awsId.trim()}__`;
    }
    return match; // Keep the original text if no matching source
  });

  // Split by our placeholder and create the segments
  const parts = finalProcessedText.split(/(__SOURCE_PILL_.*?__)/g);
  const imageLinks: string[] = [];
  const imageNames: string[] = [];
  const imageType: "image"[] = [];
  const indexMap = {}

  parts.forEach((part, index) => {
    const pillMatch = part.match(/__SOURCE_PILL_(.*?)__/);
    console.log("pillMatch:", index);

    if (pillMatch) {
      // This is a placeholder for a source pill
      const awsId = pillMatch[1];
      const source = sourceMap.get(awsId);
      console.log("source:", source);
      if (source && source.url) {
        imageLinks.push(source.url);
        imageNames.push(`${source.filename} ${source.pages.includes(",")
          ? `Pages ${source.pages}`
          : source.pages.includes("-")
            ? `Pages ${source.pages}`
            : `Page ${source.pages}`}`);
        imageType.push("image");
        indexMap[index] = imageLinks.length - 1;
      }
    }
  });

  // Process each part
  parts.forEach((part, index) => {
    const pillMatch = part.match(/__SOURCE_PILL_(.*?)__/);

    if (pillMatch) {
      // This is a placeholder for a source pill
      const awsId = pillMatch[1];
      const source = sourceMap.get(awsId);

      if (source) {
        console.log("Where Modal?")
        segments.push(
          <span key={`source-${index}`} className="inline-source-pill">
            {/* <SourcePill sources={[source]} /> */}
            <button onClick={() => { setIsModalOpen(true); setCurrentImageIndex(indexMap[index]) }} className="source-pill source-pill-link">
              {`${source.filename} ${source.pages.includes(",")
                ? `Pages ${source.pages}`
                : source.pages.includes("-")
                  ? `Pages ${source.pages}`
                  : `Page ${source.pages}`}`}
            </button>
          </span>
        );
      }
    } else if (part) {
      // This is regular text
      segments.push(
        <ReactMarkdown
          key={`text-${index}`}
          children={part}
          remarkPlugins={[remarkGfm]}
          components={{
            table: ({ node, ...props }) => (
              <table className="custom-table" {...props} />
            ),
            th: ({ node, ...props }) => <th {...props} />,
            td: ({ node, ...props }) => <td {...props} />,
          }}
        />
      );
    }
  });

  segments.push(
    <Modal
      currentIndex={currentImageIndex}
      isOpen={isModalOpen}
      mediaNames={imageNames}
      mediaTypes={imageType}
      mediaUrls={imageLinks}
      onClose={() => setIsModalOpen(false)}
      onNext={() => { setCurrentImageIndex((prevIndex) => (prevIndex + 1) % imageLinks.length) }}
      onPrevious={() => { setCurrentImageIndex((prevIndex) => (prevIndex - 1 + imageLinks.length) % imageLinks.length) }}
    />)

  // No need to add remaining text as we've processed the entire string
  console.log("segments:", segments);
  return <>{segments}</>;
}
