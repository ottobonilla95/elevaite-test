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
import { extractMediaUrls , extractMediaNames} from '../lib/testData';
import MarkdownMessage from './MarkdownMessage'; 
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
  
  
  // Function to open the media modal
  // function openMediaModal(): void {
  //   if (chatContext.latestResponse) {
  //     const urls = extractMediaUrls(chatContext.latestResponse);
  //     const names = extractMediaNames(chatContext.latestResponse);
  
  //     if (urls.length > 0) {
  //       // Create an array of unique objects containing url, name, and type
  //       const uniqueMedia = Array.from(new Set(urls.map((url, index) => {
  //         return JSON.stringify({
  //           url: url,
  //           name: names[index] || '',
  //           type: url.endsWith('.mp4') ? 'video' : 'image'
  //         });
  //       }))).map(item => JSON.parse(item));
  
  //       // Extract unique urls, names, and types from the uniqueMedia array
  //       const uniqueUrls = uniqueMedia.map(item => item.url);
  //       const uniqueNames = uniqueMedia.map(item => item.name);
  //       const uniqueTypes = uniqueMedia.map(item => item.type);
  
  //       setMediaUrls(uniqueUrls);
  //       setmediaNames(uniqueNames);
  //       setMediaTypes(uniqueTypes);
  //       setIsModalOpen(true); // Open the modal
  //     }
  //   }
  // }

  function openMediaModal(): void {
    if (chatContext.latestResponse) {
        const urls = extractMediaUrls(chatContext.latestResponse);
        const names = extractMediaNames(chatContext.latestResponse);

        if (urls.length > 0) {
            const mediaItems = urls.map((url, index) => ({
                url,
                name: names[index] || '',
                type: ['mov', 'mp4'].some(ext => url.endsWith(ext)) ? 'video' : 'image'
            }));

            setMediaUrls(mediaItems.map(item => item.url));
            setmediaNames(mediaItems.map(item => item.name));
            setMediaTypes(mediaItems.map((item): ("image" | "video") => item.type as "image" | "video"));
            setIsModalOpen(true);
        }
    }
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

    // // Function to handle clicks on media inside the message (from `dangerouslySetInnerHTML`)
    // function handleMediaClick(event: MouseEvent) {
    //   const target = event.target as HTMLElement;
      
    //   if (target.tagName === 'IMG' || (target.tagName === 'A' && target.getAttribute('href'))) {
    //     const url = target.tagName === 'IMG' ? target.getAttribute('src') : target.getAttribute('href');
    //     const isVideo = url?.endsWith('.mp4');
    //     const name = target.getAttribute('data-media-name') || "Untitled"; // You could customize this
  
    //     if (url) {
    //       setMediaUrls([url]);
    //       setmediaNames([name]);
    //       setMediaTypes([isVideo ? 'video' : 'image']);
    //       setIsModalOpen(true); // Open the modal
    //     }
    //   }
    // }
  
    // // Add event listener to detect clicks on media content (once the component is rendered)
    // useEffect(() => {
    //   const messageContent = document.getElementById(props.id);  // Ensure each message has a unique ID
    //   if (messageContent) {
    //     messageContent.addEventListener('click', handleMediaClick);
    //   }
  
    //   return () => {
    //     if (messageContent) {
    //       messageContent.removeEventListener('click', handleMediaClick);
    //     }
    //   };
    // }, [props.id]);

    
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
          <MarkdownMessage text={props.text} /> 
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
        />
      )}
    </div>
  );
}
