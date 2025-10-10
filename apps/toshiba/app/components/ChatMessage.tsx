"use client";
import {
  ChatbotIcons,
  ClickOutsideDetector,
  CommonButton
} from "@repo/ui/components";
import { getInitials } from "@repo/ui/helpers";
import dayjs from "dayjs";
import { useRef, useState, useContext, useEffect } from "react";
import type { ChatMessageObject } from "../lib/interfaces";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./ChatMessage.scss";
import { ChatMessageFeedback } from "./ChatMessageFeedback";
import { ChatMessageFiles } from "./ChatMessageFiles";
import { SourcePill } from "./SourcePill";
import { InlineSourceMessage } from "./InlineSourceMessage";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// Add new interface for streaming status props
interface ChatMessageProps extends ChatMessageObject {
  isStreaming?: boolean;
  agentStatus?: string;
}

export function ChatMessage(props: ChatMessageProps): JSX.Element {
  const chatContext = useContext(ChatContext);
  const filesButtonRef = useRef<HTMLButtonElement | null>(null);
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
  const [isFilesOpen, setIsFilesOpen] = useState(false);
  const messageRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom of message when new content is streamed in
  useEffect(() => {
    if (props.isStreaming && messageRef.current) {
      messageRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [props.text, props.isStreaming]);

  useEffect(() => {
    if (containsVideoDetailsTag(props.text)) {
      console.log("[ChatMessage] <video-details> detected", { id: props.id });
    }
  }, [props.text]);

  function handleVote(vote: 1 | -1): void {
    const newVote = props.vote === vote ? 0 : vote;
    if (newVote === -1) setIsFeedbackOpen(true);
    chatContext.updateMessageVote(props.id, newVote);
  }

  function toggleFeedback(): void {
    setIsFeedbackOpen((current) => !current);
  }

  function toggleFiles(): void {
    setIsFilesOpen((current) => !current);
  }

  function containsVideoDetailsTag(text?: string | null): boolean {
    if (!text) return false;
    // matches: <video-details> or <video-details ...>
    return /<\s*video-details(?:\s|>)/i.test(text);
  }

  return (
    <div
      className={[
        "chat-message-container",
        props.isBot ? "bot" : undefined,
        props.isStreaming ? "streaming" : undefined
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="profile-image-container">
        <div
          className={["profile-image-backdrop", props.isBot ? "bot" : undefined]
            .filter(Boolean)
            .join(" ")}
        >
          {props.isBot ? (
            <ChatbotIcons.ChatbotProfileLogo />
          ) : (
            getInitials(props.userName)
          )}
        </div>
      </div>

      <div className="main-message-container">
        <div className="details-container">
          {props.isBot ? (
              <span>
              ELEV<span className="highlight">AI</span>TE
                {/* {props.isStreaming && (
                    <span className="agent-status"> • {chatContext.agentStatus ? chatContext.agentStatus : "Thinking..."} </span>
                )} */}
            </span>
          ) : (
              <span>{props.userName}</span>
          )}
          <div>•</div>
          <span className="date">
            {dayjs(props.date).format("MMMM DD, YYYY — hh:mm a")}
          </span>
        </div>

        <div className="message" ref={messageRef}>
          {props.text ?
            <InlineSourceMessage text={props.text} sources={props.sources} isStreaming={props.isStreaming} />
          : props.isStreaming ? (
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          ) : null}
        </div>

        {!props.isBot || props.isStreaming ? null : (
          <div className="controls-container">
            <div className="voting-buttons">
              <CommonButton
                className={props.vote === 1 ? "active" : ""}
                onClick={() => {
                  handleVote(1);
                }}
              >
                <ChatbotIcons.SVGThumbs type="up" />
                {props.vote === 1 ? "Upvoted" : ""}
              </CommonButton>
              <CommonButton
                className={props.vote === -1 ? "active" : ""}
                onClick={() => {
                  handleVote(-1);
                }}
              >
                <ChatbotIcons.SVGThumbs type="down" />
                {props.vote === -1 ? "Downvoted" : ""}
              </CommonButton>
            </div>

            <CommonButton
              className={isFeedbackOpen ? "active" : ""}
              onClick={toggleFeedback}
            >
              <ChatbotIcons.SVGFeedback />
              Provide Feedback
            </CommonButton>

            {/*<div className="relevant-files-container">*/}
            {/*  <CommonButton*/}
            {/*    passedRef={filesButtonRef}*/}
            {/*    className={isFilesOpen ? "active" : ""}*/}
            {/*    onClick={toggleFiles}*/}
            {/*  >*/}
            {/*    <ChatbotIcons.SVGDocument />*/}
            {/*    Sources*/}
            {/*  </CommonButton>*/}
            {/*  <ClickOutsideDetector*/}
            {/*    onOutsideClick={() => {*/}
            {/*      setIsFilesOpen(false);*/}
            {/*    }}*/}
            {/*    ignoredRefs={[filesButtonRef]}*/}
            {/*  >*/}
            {/*    <div*/}
            {/*      className={[*/}
            {/*        "files-dropdown-container",*/}
            {/*        isFilesOpen ? "open" : undefined,*/}
            {/*      ]*/}
            {/*        .filter(Boolean)*/}
            {/*        .join(" ")}*/}
            {/*    >*/}
            {/*      <div className="files-dropdown-accordion">*/}
            {/*        <ChatMessageFiles files={props.files} />*/}
            {/*      </div>*/}
            {/*    </div>*/}
            {/*  </ClickOutsideDetector>*/}
            {/*</div>*/}
          </div>
        )}

        {!props.isBot || props.isStreaming ? null : (
          <div className={["feedback-container", isFeedbackOpen ? "open" : undefined].filter(Boolean).join(" ")} >
            <div className="feedback-accordion">
              <ChatMessageFeedback
                id={props.id}
                feedback={props.feedback}
                onFeedbackSubmit={() => {
                  setIsFeedbackOpen(false)
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}