import { Inter } from "next/font/google";

import { useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import axios from "axios";
import TextareaAutosize from "@mui/base/TextareaAutosize";
import { BsFillCursorFill } from "react-icons/bs";

import Message from "./message";
import { MessageDetails } from "..";
import CircularIndeterminate from "./progress_spinner";

export default function ChatWindow() {
  const [ask, setAsk] = useState<string>("");
  const [messages, setMessages] = useState<MessageDetails[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [messageIdCount, setMessageIdCount] = useState(0);
  const fetchAnswer = useRef(() => {});
  const listRef = useRef<HTMLDivElement>(null);

  function handleClick(event: any) {
    setIsLoading(() => true);
    fetchAnswer.current();
  }
  function handleClearMessages() {
    setMessages(() => []);
  }
  function scrollToLastMessage() {
    let lastChild = listRef.current!.lastElementChild;
    lastChild?.scrollIntoView({
      block: "start",
      inline:"start",
      behavior: "smooth",
    });
  }

  const handleKeyDown = (e: any) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleClick(e);
    }
  };

  fetchAnswer.current = async () => {
    return await axios
      .get("https://api.iopex.ai/query", { params: { query: ask } })
      .then((res) => {
        console.log(ask);
        console.log(res);
        const answer =
          "" +
          res["data"]["text"] +
          ` <p>Please checkout these urls for more information:</p>
            <li><a target="_blank" href=${res["data"]["url_1"]}>${res["data"]["url_1"]}</a></li> 
            <li><a target="_blank" href=${res["data"]["url_2"]}>${res["data"]["url_2"]}</a></li> 
            <li><a target="_blank" href=${res["data"]["url_3"]}> ${res["data"]["url_3"]}</a></li>
            `;

        if (answer) {
          flushSync(() => {
            setMessages(() => [
              ...messages,
              { id: messageIdCount, message: ask, from: "user" },
              { id: messageIdCount + 1, message: answer, from: "system" },
            ]);
            setAsk(() => "");
            setMessageIdCount(() => messageIdCount + 2);
            setIsLoading(() => false);
          });
        }
      })
      .catch((error) => console.log("Error occured"));
  };

  const change = (event: any) => {
    setAsk(() => event.target.value);
  };

  useEffect(() => scrollToLastMessage(), [messages]);
  return (
    <>
      <div className="final-container">
        <div className="band"></div>
        <div className="grand-parent">
          <div className="parent-container">
            <div ref={listRef} className="parent">
                {messages.map((message, idx) => (
                  <>
                    <Message key={idx} message={message} />
                  </>
                ))}

              <div className="container-body">
                <TextareaAutosize
                  minRows={1}
                  maxRows={7}
                  className="chat-input"
                  onChange={change}
                  value={ask}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask questions regarding your products here"
                />
                {isLoading ? (
                  <div className="loader">
                    <CircularIndeterminate />
                  </div>
                ) : (
                  <button className="button" onClick={handleClick}>
                    <BsFillCursorFill size="30px" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
