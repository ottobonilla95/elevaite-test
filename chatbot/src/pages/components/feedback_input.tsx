import { TextareaAutosize } from "@mui/material";
import { fontSize } from "@mui/system";
import React, { useState } from "react";
import { BsCursor } from "react-icons/bs";
import { FiThumbsUp, FiThumbsDown } from "react-icons/fi";
import { TbFileExport } from "react-icons/tb";

export default function FeedbackInput() {
  const [isFeedbackInputReceived, setisFeedbackInputReceived] = useState(false);
  const [feedback, setFeedback] = useState<string>("");

  const change = (event: any) => {
    setFeedback(() => event.target.value);
  };
  const handleKeyDown = (e: any) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleClick();
    }
  };
  const handleClick = () => {
    console.log(feedback);
    if (feedback.trim() != "") {
      setisFeedbackInputReceived(() => true);
    }
  };

  return (
    <>
      <div className="feedback-container">
        {isFeedbackInputReceived ? (
          <p style={{ color: "white", marginLeft: "10px", fontSize: "14px" }}>
            Thank you for your feedback!
          </p>
        ) : (
          <>
            <p>Would you like to provide your feedback here?</p>
            <div className="feedback-input-container">
              <TextareaAutosize
                minRows={1}
                maxRows={1}
                className="feedback-input"
                onChange={change}
                value={feedback}
                style={{
                  background: "transparent",
                  border: "none",
                  fontSize: "14px",
                }}
                onKeyDown={handleKeyDown}
                placeholder="Please provide your feedback here"
              />
              <button
                className="button feedback-input-button"
                onClick={handleClick}
              >
                <BsCursor style={{ color: "white" }} size="26px" />
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
}
