import React, { useState } from "react";
import {
  FiThumbsUp,
  FiThumbsDown,
} from "react-icons/fi";
import { TbFileExport } from "react-icons/tb";

export default function Feedback() {
  const [isFeedbackButtonClicked, setIsFeedbackButtonClicked] = useState(false);
  const [isFeedbackInputReceived, setisFeedbackInputReceived] = useState(false);
  const [feedback, setFeedback] = useState<string>("");
  const handleFeedback = (liked: boolean) => {
    //send the respone to
    if (liked) {
      console.log("liked");
    } else {
      console.log("disliked");
    }
    setIsFeedbackButtonClicked(() => true);
  };

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
    setisFeedbackInputReceived(() => true);
  };

  return (
    <>
      <div className="feedback">
        <div>
          <button
            id="like"
            onClick={() => handleFeedback(true)}
            className="feedback-thumbs-button"
          >
            <FiThumbsUp style={{color:"#A7A4C4"}} size="20px" />
          </button>
          <button
            id="dislike"
            onClick={() => handleFeedback(false)}
            className="feedback-thumbs-button"
          >
            <FiThumbsDown style={{color:"#A7A4C4"}} size="20px" />
          </button>
          <button
            id="send"
            onClick={() => handleFeedback(false)}
            className="feedback-thumbs-button"
          >
          <TbFileExport style={{color:"#A7A4C4"}} size="20px" />
          </button>
        </div>
      </div>
    </>
  );
}
