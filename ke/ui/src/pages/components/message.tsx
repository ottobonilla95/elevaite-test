import React, { useEffect, useRef, useState } from "react";
import { MessageDetails } from "..";
import DOMPurify from "isomorphic-dompurify";
import { FaUserCircle } from "react-icons/fa";
import { FaInfoCircle } from "react-icons/fa";
import { IoIosArrowUp, IoIosArrowDown } from "react-icons/io";
import { GrDocumentText } from "react-icons/gr";

import Feedback from "./feedback";
import FeedbackInput from "./feedback_input";
type MessageProps = {
  message: MessageDetails;
};

export default function Message(props: MessageProps) {
  const [isFeedBackSent, setIsFeedBackSent] = useState(false);
  const [hideUrl, setHideUrl] = useState(false);
  const sanitzer = DOMPurify.sanitize;

  DOMPurify.addHook("afterSanitizeAttributes", function (node) {
    // set all elements owning target to target=_blank
    if ("target" in node) {
      node.setAttribute("target", "_blank");
      node.setAttribute("rel", "noopener");
    }
  });

  function hideOrShow() {
    setHideUrl(() => !hideUrl);
  }

  const urls =
    props?.message?.urls != undefined ? Array.from(props?.message?.urls) : [];
  return (
    <>
      <div
        className={`answer ${
          props?.message?.from == "user" ? "user-message" : "system-message"
        }`}
      >
        {props?.message?.from == "user" ? (
          <div className="user-details">
            <div className="icon">
              <FaUserCircle style={{ color: "#5665FB" }} size="40px" />
            </div>
            <div>
              <p>Aadhithya Dinesh</p>
              <p className="message-date">{props?.message?.timestamp}</p>
            </div>
          </div>
        ) : (
          <div className="user-details">
            <div className="icon">
              <FaInfoCircle style={{ color: "#F46F22" }} size="40px" />
            </div>
            <div>
              <p>elevAIte</p>
              <p className="message-date">{props?.message?.timestamp}</p>
            </div>
          </div>
        )}
        <div className="response-container">
          <div className="response">
            <div
              dangerouslySetInnerHTML={{
                __html: sanitzer(props?.message?.message),
              }}
            />
            {props?.message?.from == "system"  && urls.length>0? (
              <div className="url-responses">
                <>
                  <div onClick={hideOrShow} className="url-flex">
                    <p>Show relevant links and files</p>
                    {hideUrl ? (
                      <IoIosArrowUp style={{ marginLeft: "5px" }} />
                    ) : (
                      <IoIosArrowDown style={{ marginLeft: "5px" }} />
                    )}
                  </div>
                </>
                {hideUrl
                  ? urls.map((url) => (
                      <>
                        <div className="url-image">
                          <GrDocumentText
                            style={{ color: "#37B2FF", marginRight: "10px" }}
                          />
                          <div
                            dangerouslySetInnerHTML={{
                              __html: sanitzer(url),
                            }}
                          />
                        </div>
                      </>
                    ))
                  : null}
              </div>
            ) : null}
          </div>

          {props?.message?.from == "system" ? (
            <>
              <Feedback />
            </>
          ) : null}
        </div>
        {props?.message?.from == "system" ? (
        <FeedbackInput/>) : null}

      </div>
    </>
  );
}
