import React, { useEffect, useRef, useState } from "react";
import { MessageDetails } from "../pages";
import DOMPurify from "isomorphic-dompurify";
import { FaUserCircle } from "react-icons/fa";
import { FaInfoCircle } from "react-icons/fa";
import { IoIosArrowUp, IoIosArrowDown } from "react-icons/io";
import { GrDocumentText } from "react-icons/gr";
import jwt_decode from "jwt-decode";

import Feedback from "./feedback";
import FeedbackInput from "./feedback_input";
import HoverRating from "./hover_rating";
type MessageProps = {
  message: MessageDetails;
};

export default function Message(props: MessageProps) {
  const [isFeedBackSent, setIsFeedBackSent] = useState(false);
  const [hideUrl, setHideUrl] = useState(false);
  const [urls, setUrls] = useState<any>();
  const [name, setName] = useState();
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

  useEffect(() => {
    let params = new URL(window.location.href).searchParams;
    const token = params.get("token");
    if (!!token) {
      let decoded: any = jwt_decode(token);
      // let expTime = new Date(decoded.exp * 1000);
      // let currentTime = new Date().getTime();
      // if (currentTime < expTime.getTime()){
      //   console.log(expTime);
      //   setName(()=>decoded.name)
      // } else {
      //   window.location.href = process.env.NEXT_PUBLIC_LOGIN_API;
      // }
      setName(()=>decoded.name);
      // console.log(sanitzer(props?.message?.message));
    } else {
      if (!!process.env.NEXT_PUBLIC_LOGIN_API){
        window.location.href = process.env.NEXT_PUBLIC_LOGIN_API;
      }
    }
    const urlList = props?.message?.urls != undefined ? Array.from(props?.message?.urls) : []
    setUrls(()=>urlList);
  }, [props]);

  return (
    <>
      <div
        className={`answer ${
          props?.message?.from == "human" ? "user-message" : "system-message"
        }`}
      >
        {props?.message?.from == "human" ? (
          <div className="user-details">
            <div className="icon">
              <FaUserCircle style={{ color: "#5665FB" }} size="40px" />
            </div>
            <div>
              <p>{name}</p>
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
            {props?.message?.from == "ai"  && !!urls? (
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
                  ? urls.map((url:any) => (
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

          {props?.message?.from == "ai" ? (
            <>
              <HoverRating />
            </>
          ) : null}
        </div>
        {props?.message?.from == "ai" ? (
        <FeedbackInput/>) : null}

      </div>
    </>
  );
}
