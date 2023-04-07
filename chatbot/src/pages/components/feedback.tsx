import React, { useState } from "react";
import {
  BsFillHandThumbsUpFill,
  BsFillHandThumbsDownFill,
} from "react-icons/bs";

export default function Feedback() {
  const [isFeedbackButtonClicked, setIsFeedbackButtonClicked] = useState(false);
  const handleFeedback = (liked: boolean) => {
    //send the respone to 
    if (liked){
        console.log("liked");
    } else {
        console.log("disliked");
    }
    setIsFeedbackButtonClicked(() => true);
  };

  return (
    <>
      {isFeedbackButtonClicked ? null : (
        <>
          <div className="feedback">
          <p>Please rate the reponse!</p>
            <div>
              <button id="like" onClick={() => handleFeedback(true)} className="feedback-thumbs-button">
                <BsFillHandThumbsUpFill size="30px" />
              </button>
              <button id="dislike" onClick={() => handleFeedback(false)} className="feedback-thumbs-button">
                <BsFillHandThumbsDownFill size="30px" />
              </button>
            </div>
          </div>
        </>
      )
      }
    </>
  );
}
