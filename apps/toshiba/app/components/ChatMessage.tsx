"use client";
import {
  ChatbotIcons,
  ClickOutsideDetector,
  CommonButton
} from "@repo/ui/components";
import { getInitials } from "@repo/ui/helpers";
import dayjs from "dayjs";
import { useRef, useState, useContext } from "react";
import type { ChatMessageObject } from "../lib/interfaces";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./ChatMessage.scss";
import { ChatMessageFeedback } from "./ChatMessageFeedback";
import { ChatMessageFiles } from "./ChatMessageFiles";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";




export function ChatMessage(props: ChatMessageObject): JSX.Element {
  const chatContext = useContext(ChatContext);
  const filesButtonRef = useRef<HTMLButtonElement | null>(null);
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
  const [isFilesOpen, setIsFilesOpen] = useState(false);


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


  console.log("props", props)


  return (
    <div
      className={["chat-message-container", props.isBot ? "bot" : undefined]
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
            </span>
          ) : (
            <span>{props.userName}</span>
          )}
          <div>•</div>
          <span className="date">
            {dayjs(props.date).format("MMMM DD, YYYY — hh:mm a")}
          </span>
        </div>


        <div className="message" >
          {/* <div dangerouslySetInnerHTML={{ __html: marked(props.text) }} /> */}
          <ReactMarkdown
            children={props.text}
            remarkPlugins={[remarkGfm]}
            components={{
              table: ({ node, ...props }) => (
                <table className="custom-table" {...props} />
              ),
              th: ({ node, ...props }) => <th {...props} />,
              td: ({ node, ...props }) => <td {...props} />,
            }}
          />


        </div>
        {/*{!props.isBot ? null : (*/}
        {/*<div className="media-container">*/}
        {/*  <a href="https://fastly.picsum.photos/id/13/2500/1667.jpg?hmac=SoX9UoHhN8HyklRA4A3vcCWJMVtiBXUg0W4ljWTor7s" target="_blank" rel="noopener noreferrer">*/}
        {/*    <img src="https://fastly.picsum.photos/id/13/2500/1667.jpg?hmac=SoX9UoHhN8HyklRA4A3vcCWJMVtiBXUg0W4ljWTor7s" alt="Example Image 1" />*/}
        {/*  </a>*/}
        {/*  <a href="https://picsum.photos/seed/picsum/200/300" target="_blank" rel="noopener noreferrer">*/}
        {/*    <img src="https://picsum.photos/seed/picsum/200/300" alt="Example Image 2" />*/}
        {/*  </a>*/}
        {/*  <a rel="noopener noreferrer">*/}
        {/*    <video width="150" controls>*/}
        {/*      <source src="https://www.w3schools.com/html/mov_bbb.mp4" type="video/mp4" />*/}
        {/*    </video>*/}
        {/*  </a>*/}


        {/*</div>*/}
        {/*// )}*/}




        {!props.isBot ? null : (
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


            <div className="relevant-files-container">
              <CommonButton
                passedRef={filesButtonRef}
                className={isFilesOpen ? "active" : ""}
                onClick={toggleFiles}
              >
                <ChatbotIcons.SVGDocument />
                Sources
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






