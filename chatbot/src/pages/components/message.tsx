import React, { useEffect, useState } from "react";
import { MessageDetails } from "..";
import DOMPurify from "isomorphic-dompurify";
import { FaUserAlt } from "react-icons/fa";
import { FaInfoCircle } from "react-icons/fa";
import Feedback from "./feedback";
type MessageProps = {
  message: MessageDetails;
};

export default function Message(props: MessageProps) {
  const [isFeedBackSent, setIsFeedBackSent] = useState(false);

  const sanitzer = DOMPurify.sanitize;
  DOMPurify.addHook('afterSanitizeAttributes', function (node) {
    // set all elements owning target to target=_blank
    if ('target' in node) {
      node.setAttribute('target', '_blank');
      node.setAttribute('rel', 'noopener');
    }
  });


  return (
    <>
      <div
        className={`answer ${
          props?.message?.from == "user" ? "user-message" : "system-message"
        }`}
      >
        <div className="icon">
          {props?.message?.from == "user" ? (
            <FaUserAlt size="30px" />
          ) : (
            <FaInfoCircle size="30px" />
          )}
        </div>
        <div
          className="response"
          dangerouslySetInnerHTML={{ __html: sanitzer(props?.message?.message) }}
        />
      </div>
      {props?.message?.from == "system" ? (
        <>
          {isFeedBackSent ? (
            <p>Thank you for your feedback!</p>
          ) : (
            <div className="feedback">
              <Feedback />
            </div>
          )}
        </>
      ) : null}
    </>
  );
}
