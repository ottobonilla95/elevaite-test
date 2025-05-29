"use client";
import { ChatbotIcons } from "@repo/ui/components";
import { SourceReference } from "../lib/interfaces";
import "./SourcePill.scss";

interface SourcePillProps {
  sources: SourceReference[];
}

export function SourcePill({ sources }: SourcePillProps): JSX.Element {
  if (!sources || sources.length === 0) {
    return <></>;
  }

  return (
    <div className="source-pill-container">
      {sources.map((source, index) => {
        const pillContent = (
          <>
            <ChatbotIcons.SVGDocument />
            <span className="source-filename" title={source.filename}>
              {source.filename}
            </span>
            <span className="source-pages">
              {source.pages.includes(",")
                ? `Pages ${source.pages}`
                : source.pages.includes("-")
                  ? `Pages ${source.pages}`
                  : `Page ${source.pages}`}
            </span>
          </>
        );

        return source.url ? (
          <a
            key={index}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="source-pill source-pill-link"
          >
            {pillContent}
          </a>
        ) : (
          <div key={index} className="source-pill">
            {pillContent}
          </div>
        );
      })}
    </div>
  );
}
