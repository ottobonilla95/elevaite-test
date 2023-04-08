import React, { useState } from "react";
import {
  BsFillHandThumbsUpFill,
  BsFillHandThumbsDownFill,
} from "react-icons/bs";

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
      {isFeedbackButtonClicked ? (
        isFeedbackInputReceived ? (
          <p>Thank you for the response!</p>
        ) : (
          <>
            <input
              className="feedback-input"
              type="text"
              onChange={change}
              value={feedback}
              onKeyDown={handleKeyDown}
              placeholder="Please provide additional information!"
            />
            <button onClick={handleClick} className="feedback-button">
              Send
            </button>
          </>
        )
      ) : (
        <>
          <div className="feedback">
            <p>Please rate the reponse!</p>
            <div>
              <button
                id="like"
                onClick={() => handleFeedback(true)}
                className="feedback-thumbs-button"
              >
                <BsFillHandThumbsUpFill size="30px" />
              </button>
              <button
                id="dislike"
                onClick={() => handleFeedback(false)}
                className="feedback-thumbs-button"
              >
                <BsFillHandThumbsDownFill size="30px" />
              </button>
            </div>
          </div>
        </>
      )}
    </>
  );
}
