/* eslint-disable @next/next/no-img-element */
import { Inter } from "next/font/google";

import { useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import axios from "axios";
import TextareaAutosize from "@mui/base/TextareaAutosize";
import { BsCursor } from "react-icons/bs";

import Message from "./message";
import { MessageDetails } from "..";
import CircularIndeterminate from "./progress_spinner";

export default function ChatWindow() {
  const [ask, setAsk] = useState<string>("");
  const [messages, setMessages] = useState<MessageDetails[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [messageIdCount, setMessageIdCount] = useState(0);
  const [caseId, setCaseId] = useState<number | null>(null);
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
      inline: "start",
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
      .get("http://localhost:8000/query", { params: { query: ask } })
      .then((res) => {
        console.log(ask);
        console.log(res);

        let answer = "" + res["data"]["text"];

        if (answer) {
          flushSync(() => {
            const urls = new Set<string>([
              `<li><a target="_blank" href=${res["data"]["url_1"]}> ${res["data"]["topic_1"]}</a></li>`,
              `<li><a target="_blank" href=${res["data"]["url_2"]}> ${res["data"]["topic_2"]}</a></li>`,
              `<li><a target="_blank" href=${res["data"]["url_3"]}> ${res["data"]["topic_3"]}</a></li>`,
            ]);

            setMessages(() => [
              ...messages,
              { id: messageIdCount, message: ask, from: "user" },
              {
                id: messageIdCount + 1,
                message: answer,
                from: "system",
                urls: urls,
              },
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
  useEffect(
    () =>
      setCaseId(() => Math.floor(Math.random() * (999999 - 100000) + 100000)),
    []
  );
  return (
    <>
      <div className="band-flex">
        <div className="band-top">I am here</div>
        <div className="band-bottom">i am bottom</div>
      </div>
      <div className="band"></div>
      <div className="chat-container">
        <div className="chat-header">
          <p> Case ID: #135727 </p>
          <img src="/img/chat-header.svg" alt="search functionality"/>
        </div>

        <div className="final-container">
          <div className="grand-parent">
            <div className="parent-container">
              <div ref={listRef} className="parent">
                {messages.map((message, idx) => (
                  <>
                    <Message key={idx} message={message} />
                  </>
                ))}
              </div>
            </div>
          </div>
        </div>
        <div className="final-container-body">
          <div className="container-body">
            <TextareaAutosize
              minRows={1}
              maxRows={4}
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
                <BsCursor style={{ color: "white" }} size="30px" />
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
