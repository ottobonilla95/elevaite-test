import { Inter } from "next/font/google";

import { useEffect, useRef, useState } from "react";

import axios from "axios";
import TextareaAutosize from "@mui/base/TextareaAutosize";
import { BsFillCursorFill } from "react-icons/bs";

import Message from "./components/message";
import Header from "./components/header";
import CircularIndeterminate from "./components/progress_spinner";

const inter = Inter({ subsets: ["latin"] });

export type MessageDetails = {
  id: number;
  message: string;
  from: string;
};

export default function Home() {
  const [ask, setAsk] = useState<string>("");
  const [messages, setMessages] = useState<MessageDetails[]>([]);
  const [buttonClicked, setButtonClicked] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [messageIdCount, setMessageIdCount] = useState(0);
  const initialRender = useRef(true);
  const fetchAnswer = useRef(() => {});
  function handleClick(event: any) {
    setButtonClicked(() => true);
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
    if (buttonClicked) {
      const target = "_blank";
      return await axios
        .get("http://127.0.0.1:8000/query", { params: { query: ask } })
        .then((res) => {
          console.log(ask);
          console.log(res);
          const answer =
            "" +
            res["data"]["text"] +
            ` Please checkout these urls for more information <div>
            1. <a target=${target} href=${res["data"]["url_1"]}> ${res["data"]["topic_1"]}</a> 
            2. <a target=${target} href=${res["data"]["url_2"]}> ${res["data"]["topic_1"]}</a> 
            3. <a target=${target} href=${res["data"]["url_3"]}> ${res["data"]["topic_1"]}</a>
            </div>
            `;

          if (answer) {
            setMessages(() => [
              ...messages,
              { id: messageIdCount, message: ask, from: "user" },
              { id: messageIdCount + 1, message: answer, from: "system" },
            ]);
            setAsk(() => "");
            setMessageIdCount(() => messageIdCount + 2);
            setButtonClicked(() => false);
            setIsLoading(() => false);
          }
        })
        .catch((error) => console.log("Error occured"));
    }
  };

  const change = (event: any) => {
    setAsk(() => event.target.value);
  };

  useEffect(() => {
    if (initialRender.current) {
      initialRender.current = false;
    } else {
      if (buttonClicked) {
        setIsLoading(() => true);
        fetchAnswer.current();
      }
    }
  }, [ask, buttonClicked, initialRender, isLoading]);

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
                placeholder="Ask questions regarding the loaded docs here"
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
