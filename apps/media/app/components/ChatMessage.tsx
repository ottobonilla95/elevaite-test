"use client";
import {
  ChatbotIcons,
  ClickOutsideDetector,
  CommonButton,
} from "@repo/ui/components";
import { getInitials } from "@repo/ui/helpers";
import dayjs from "dayjs";
import { useRef, useState, useContext, useEffect } from "react";
import type { ChatMessageObject } from "../lib/interfaces";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./ChatMessage.scss";
import { ChatMessageFeedback } from "./ChatMessageFeedback";
import { ChatMessageFiles } from "./ChatMessageFiles";
import { extractUniqueMediaData} from '../lib/testData';
import MarkdownMessage from './MarkdownMessage'; 
import Modal from "./Modal.tsx"; // Import the Modal component

export function ChatMessage(props: ChatMessageObject): JSX.Element {
  const chatContext = useContext(ChatContext);
  const filesButtonRef = useRef<HTMLButtonElement | null>(null);
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
  const [isFilesOpen, setIsFilesOpen] = useState(false);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [mediaUrls, setMediaUrls] = useState<string[]>([]);
  const [mediaNames, setMediaNames] = useState<string[]>([]);
  const [mediaTypes, setMediaTypes] = useState<('image' | 'video')[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);


  function openMediaModal(): void {
    const { urls, names } = extractUniqueMediaData(props.text);
  
    if (urls.length > 0) {
      const mediaItems = urls.map((url, index) => ({
        url,
        name: names[index] || '',
        type: ['mov', 'mp4'].some(ext => url.endsWith(ext)) ? 'video' : 'image',
      }));
  
      // Set the media types with correct type assertions
      setMediaUrls(mediaItems.map(item => item.url));
      setMediaNames(mediaItems.map(item => item.name));
      setMediaTypes(mediaItems.map(item => item.type as 'image' | 'video')); // Ensure types are correct
      setIsModalOpen(true);
    }
  }
  
  function openImageModal(url: string, alt: string, title: string): void {
    const baseUrl = url.replace(/\.thumbnail\.jpg$/, '');
    const extension = alt.includes('.') ? alt.split('.').pop() : 'jpg';
    const fullUrl = `${baseUrl}.${extension}`;
  
    const { urls, names } = extractUniqueMediaData(props.text);
    const mediaItems = urls.map((url, index) => ({
      url,
      name: names[index] || '',
      type: ['mov', 'mp4'].some(ext => url.endsWith(ext)) ? 'video' : 'image',
    }));
  
    setMediaUrls(mediaItems.map(item => item.url));
    setMediaNames(mediaItems.map(item => item.name));
    setMediaTypes(mediaItems.map(item => item.type as 'image' | 'video')); // Ensure types are correct
  
    const currentIndex = mediaItems.findIndex(item => item.url === fullUrl);
    setCurrentIndex(currentIndex !== -1 ? currentIndex : 0);
  
    setIsModalOpen(true);
  }
  
function goToNext(): void {
  setCurrentIndex((prevIndex) => (prevIndex + 1) % mediaUrls.length);
}

function goToPrevious(): void {
  setCurrentIndex((prevIndex) => (prevIndex - 1 + mediaUrls.length) % mediaUrls.length);
}

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

        <div className="message">
          <MarkdownMessage text={props.text} onImageClick={openImageModal} />
        </div>
        {/* <div className="message"  dangerouslySetInnerHTML={{ __html: props.text }}>
        </div> */}

        {!props.isBot ? null : (
          <div className="controls-container">
            
            {/* Show Creatives Button */}
            <CommonButton
              onClick={openMediaModal}
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
          currentIndex={currentIndex}
          onNext={goToNext}
          onPrevious={goToPrevious}
        />
      )}
    </div>
  );
}
