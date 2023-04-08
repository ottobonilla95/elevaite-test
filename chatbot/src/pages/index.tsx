import { Inter } from "next/font/google";

import { useEffect, useRef, useState } from "react";
import axios from "axios";
import TextareaAutosize from "@mui/base/TextareaAutosize";
import { BsFillCursorFill } from "react-icons/bs";

import Message from "./components/message";
import Header from "./components/header";
import CircularIndeterminate from "./components/progress_spinner";

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const inter = Inter({ subsets: ["latin"] });

export type MessageDetails = {
  id: number;
  message: string;
  from: string;
};

export default function Home() {
  const [ask, setAsk] = useState<string>("");
  const [messages, setMessages] = useState<MessageDetails[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [messageIdCount, setMessageIdCount] = useState(0);
  const fetchAnswer = useRef(() => {});

  function handleClick(event: any) {
    setIsLoading(() => true);
    fetchAnswer.current();
  }
  function handleClearMessages() {
    setMessages(() => []);
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
          setMessages(() => [
            ...messages,
            { id: messageIdCount, message: ask, from: "user" },
            { id: messageIdCount + 1, message: answer, from: "system" },
          ]);
          setAsk(() => "");
          setMessageIdCount(() => messageIdCount + 2);
          setIsLoading(() => false);
        }
      })
      .catch((error) => console.log("Error occured"));
  };

  const change = (event: any) => {
    setAsk(() => event.target.value);
  };

  return (
    <>
      <Header />
      <div className="final-container">
        <div className="band"></div>
        <div className="parent-container">
          <div className="parent">
            {messages.map((message) => (
              <>
                <Message key={message.id} message={message} />
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
            <div>
              {messages.length > 0 ? (
                <button onClick={handleClearMessages} className="clear-button">
                  Clear Messages
                </button>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
