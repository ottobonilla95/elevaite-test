"use client";
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SourceReference } from "../lib/interfaces";
import { SourcePill } from "./SourcePill";
import "./InlineSourceMessage.scss";
import Modal from "./Modal";
import { ChatMessageVideoElement } from "./advanced/ChatMessageVideoElement";

function splitByVideoDetails(
  text: string
): Array<{ type: "markdown"; text: string } | { type: "video"; xml: string }> {
  const parts: Array<{ type: "markdown"; text: string } | { type: "video"; xml: string }> = [];
  if (!text) return parts;

  const openRe = /<video-details>/i;
  const closeRe = /<\/video-details>/i;

  let cursor = 0;

  while (cursor < text.length) {
    const openMatch = text.slice(cursor).match(openRe);
    if (!openMatch || openMatch.index == null) {
      const tail = text.slice(cursor);
      if (tail) parts.push({ type: "markdown", text: tail });
      break;
    }

    const openAbs = cursor + openMatch.index;
    const afterOpen = openAbs + openMatch[0].length;

    if (openAbs > cursor) {
      parts.push({ type: "markdown", text: text.slice(cursor, openAbs) });
    }

    const closeMatch = text.slice(afterOpen).match(closeRe);
    if (!closeMatch || closeMatch.index == null) {
      // Incomplete video tag - treat as plain text
      parts.push({ type: "markdown", text: text.slice(openAbs) });
      break;
    }

    const closeAbs = afterOpen + closeMatch.index;
    const afterClose = closeAbs + closeMatch[0].length;

    parts.push({ type: "video", xml: text.slice(openAbs, afterClose) });
    cursor = afterClose;
  }

  return parts;
}

interface InlineSourceMessageProps {
  text: string;
  sources?: SourceReference[];
  isStreaming?: boolean;
}

export function InlineSourceMessage({ text, sources }: InlineSourceMessageProps): JSX.Element {
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [currentImageIndex, setCurrentImageIndex] = React.useState(0);

  if (!text) return <></>;

  // Split text into markdown and video parts
  const mixedParts = splitByVideoDetails(text);

  // If no sources and no video parts, just render markdown
  if ((!sources || sources.length === 0) && mixedParts.every(p => p.type === "markdown")) {
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
  (sources || []).forEach(source => {
    if (source.awsLink) {
      sourceMap.set(source.awsLink, source);
    }
  });

  const imageLinks: string[] = [];
  const imageNames: string[] = [];
  const imageType: "image"[] = [];
  const indexMap: { [key: number]: number } = {};
  const allSegments: React.ReactNode[] = [];

  // Helper function to generate page URLs with bounds checking
  const generatePageUrls = (source: any, centerPage: number) => {
    const urls: any[] = [];
    const names: any[] = [];

    for (let offset = -2; offset <= 2; offset++) {
      const pageNum = centerPage + offset;
      if (pageNum > 0) {
        const pageUrl = source.url.replace(`_page_${centerPage}`, `_page_${pageNum}`);
        urls.push(pageUrl);
        names.push(`${source.filename} Page ${pageNum}`);
      }
    }

    return { urls, names };
  };

  function processMarkdownText(markdownText: string): React.ReactNode[] {
    let processedText = markdownText;

    // First, replace any sources that have fullMatchText (exact matches from extraction)
    (sources || []).forEach(source => {
      if (source.fullMatchText && source.awsLink) {
        const escapedText = source.fullMatchText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(escapedText, 'g');
        processedText = processedText.replace(regex, `__SOURCE_PILL_${source.awsLink}__`);
      }
    });

    // Pattern to find the full source reference with aws_id
    const fullSourcePattern = /(.*?)\s+page\s+(\d+)\s+\[aws_id:\s+(.*?)\]/g;
    const awsIdPattern = /\[aws_id:\s+(.*?)\]/g;

    processedText = processedText.replace(fullSourcePattern, (match, filename, pageNum, awsId) => {
      const source = sourceMap.get(awsId.trim());
      if (source) {
        return `__SOURCE_PILL_${awsId.trim()}__`;
      }
      return match;
    });

    const finalProcessedText = processedText.replace(awsIdPattern, (match, awsId) => {
      const source = sourceMap.get(awsId.trim());
      if (source) {
        return `__SOURCE_PILL_${awsId.trim()}__`;
      }
      return match;
    });

    const parts = finalProcessedText.split(/(__SOURCE_PILL_.*?__)/g);
    const segments: React.ReactNode[] = [];
    const localIndexMap: { [key: number]: number } = {};

    // First pass: build image arrays and index map
    parts.forEach((part, index) => {
      const pillMatch = part.match(/__SOURCE_PILL_(.*?)__/);

      if (pillMatch) {
        const awsId = pillMatch[1];
        const source = sourceMap.get(awsId);

        if (source && source.url && awsId !== "None") {
          const centerPage = parseInt(source.pages.split(',')[0].split('-')[0].trim());
          const { urls, names } = generatePageUrls(source, centerPage);

          urls.forEach((url, idx) => {
            imageLinks.push(url);
            imageNames.push(names[idx]);
            imageType.push("image");
          });

          localIndexMap[index] = imageLinks.length - 3;
        }
      }
    });

    // Second pass: create segment nodes
    parts.forEach((part, index) => {
      const pillMatch = part.match(/__SOURCE_PILL_(.*?)__/);

      if (pillMatch) {
        const awsId = pillMatch[1];
        const source = sourceMap.get(awsId);

        if (source) {
          console.log("Index mapping: ",index, localIndexMap[index], source.filename);
          segments.push(
            <span key={`source-${index}`} className="inline-source-pill">
              {awsId.startsWith("None") ? (
                <span className="source-pill non-clickable">
                  {`${source.filename} ${source.pages.includes(",")
                    ? `Pages ${source.pages}`
                    : source.pages.includes("-")
                      ? `Pages ${source.pages}`
                      : `Page ${source.pages}`}`}
                </span>
              ) : (
                <button
                  onClick={() => {
                    setIsModalOpen(true);
                    setCurrentImageIndex(localIndexMap[index]);
                  }}
                  className="source-pill source-pill-link"
                >
                  {`${source.filename} ${source.pages.includes(",")
                    ? `Pages ${source.pages}`
                    : source.pages.includes("-")
                      ? `Pages ${source.pages}`
                      : `Page ${source.pages}`}`}
                </button>
              )}
            </span>
          );
        }
      } else if (part) {
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

    return segments;
  }

  // Process each mixed part (markdown or video)
  mixedParts.forEach((part, i) => {
    if (part.type === "markdown") {
      allSegments.push(...processMarkdownText(part.text));
    } else {
      allSegments.push(
        <ChatMessageVideoElement key={`video-${i}`} xml={part.xml} />
      );
    }
  });

  allSegments.push(
    <Modal
      key="modal"
      currentIndex={currentImageIndex}
      isOpen={isModalOpen}
      mediaNames={imageNames}
      mediaTypes={imageType}
      mediaUrls={imageLinks}
      onClose={() => setIsModalOpen(false)}
      onNext={() => { setCurrentImageIndex((prevIndex) => (prevIndex + 1) % imageLinks.length) }}
      onPrevious={() => { setCurrentImageIndex((prevIndex) => (prevIndex - 1 + imageLinks.length) % imageLinks.length) }}
    />
  );

  return <>{allSegments}</>;
}
