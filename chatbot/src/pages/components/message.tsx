import React, { useState } from "react";
import { MessageDetails } from "..";
import DOMPurify from "isomorphic-dompurify";
import { grey } from "@mui/material/colors";
import { FaUserAlt } from "react-icons/fa";
import { FaInfoCircle } from "react-icons/fa";
type MessageProps = {
  message: MessageDetails;
};

export default function Message(props: MessageProps) {
  const sanitzer = DOMPurify.sanitize;
  return (
    <div
      className={`answer ${
        props.message.from == "user" ? "user-message" : "system-message"
      }`}
    >
      <div className="icon">
        {props.message.from == "user" ? (
          <FaUserAlt size="30px" />
        ) : (
          <FaInfoCircle size="30px" />
        )}
      </div>

      <div
        className="response"
        dangerouslySetInnerHTML={{ __html: sanitzer(props.message.message) }}
      />
    </div>
  );
}
