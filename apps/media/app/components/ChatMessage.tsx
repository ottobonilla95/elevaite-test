"use client";
import {
  ChatbotIcons,
  ClickOutsideDetector,
  CommonButton,
} from "@repo/ui/components";
import { getInitials } from "@repo/ui/helpers";
import dayjs from "dayjs";
import { useRef, useState, useContext } from "react";
import type { ChatMessageObject } from "../lib/interfaces";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./ChatMessage.scss";
import { ChatMessageFeedback } from "./ChatMessageFeedback";
import { ChatMessageFiles } from "./ChatMessageFiles";
import { extractMediaUrls , extractMediaNames} from '../lib/testData';
import Modal from "./Modal.tsx"; // Import the Modal component

export function ChatMessage(props: ChatMessageObject): JSX.Element {
  const chatContext = useContext(ChatContext);
  const filesButtonRef = useRef<HTMLButtonElement | null>(null);
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
  const [isFilesOpen, setIsFilesOpen] = useState(false);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [mediaUrls, setMediaUrls] = useState<string[]>([]);
  const [mediaNames, setmediaNames] = useState<string[]>([]);
  const [mediaTypes, setMediaTypes] = useState<('image' | 'video')[]>([]);

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

  function handleShowCreatives(): void {
    if (chatContext.latestResponse) {
        const urls = extractMediaUrls(chatContext.latestResponse);
        const names = extractMediaNames(chatContext.latestResponse);
        if (urls.length > 0) {
            const types = urls.map(url => url.endsWith('.mp4') ? 'video' : 'image');
            setMediaUrls(urls);
            setmediaNames(names);
            setMediaTypes(types);
            setIsModalOpen(true);
        }
    }
}

  return (
    <div
      className={["chat-message-container", props.isBot ? "bot" : undefined]
        .filter(Boolean)
        .join(" ")}
    > 


      <div className="main-message-container">
        
        <div className="details-container">
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
          {props.isBot ? (
            <span>
              ELEV<span className="highlight">AI</span>TE
            </span>
          ) : (
            <span>{props.userName}</span>
          )}
          <span className="date">
            {dayjs(props.date).format("MMMM DD, YYYY — hh:mm a")}
          </span>
        </div>

        <div className="message"  dangerouslySetInnerHTML={{ __html: props.text }}>
        </div>

        {!props.isBot ? null : (
          <div className="controls-container">
            
            {/* Show Creatives Button */}
            <CommonButton
              onClick={handleShowCreatives}
              className="show-creatives-button"
            >
              <ChatbotIcons.SVGDocument />
              Show Creatives
            </CommonButton>

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

            <div className="relevant-files-container">
              <CommonButton
                passedRef={filesButtonRef}
                className={isFilesOpen ? "active" : ""}
                onClick={toggleFiles}
              >
                <ChatbotIcons.SVGDocument />
                Relevant Files
              </CommonButton>
              <ClickOutsideDetector
                onOutsideClick={() => {
                  setIsFilesOpen(false);
                }}
                ignoredRefs={[filesButtonRef]}
              >
                <div
                  className={[ 
                    "files-dropdown-container",
                    isFilesOpen ? "open" : undefined,
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <div className="files-dropdown-accordion">
                    <ChatMessageFiles files={props.files} />
                  </div>
                </div>
              </ClickOutsideDetector>
            </div>
          </div>
        )}

        {!props.isBot ? null : (
          <div
            className={[ 
              "feedback-container",
              isFeedbackOpen ? "open" : undefined,
            ]
              .filter(Boolean)
              .join(" ")}
          >
            <div className="feedback-accordion">
              <ChatMessageFeedback
                id={props.id}
                feedback={props.feedback}
                onFeedbackSubmit={() => {setIsFeedbackOpen(false)}}
              />
            </div>
          </div>
        )}
      </div>

      {/* Modal to show media */}
      {isModalOpen && (
        <Modal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          mediaUrls={mediaUrls}
          mediaTypes={mediaTypes}
          mediaNames={mediaNames}
        />
      )}
    </div>
  );
}
