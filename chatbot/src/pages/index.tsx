import Head from "next/head";
import Image from "next/image";
import { Anybody, Inter } from "next/font/google";
import styles from "@/styles/Home.module.css";
import { useEffect, useRef, useState } from "react";

import axios from "axios";

import { Audio } from "react-loader-spinner";
import DOMPurify from "isomorphic-dompurify";
import TextareaAutosize from "@mui/base/TextareaAutosize";
import {
  BsFillHandThumbsUpFill,
  BsFillHandThumbsDownFill,
  BsFillCursorFill,
} from "react-icons/bs";

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
  const [isFeedbackNeeded, setIsFeedbackNeeded] = useState(false);
  const [messageIdCount, setMessageIdCount] = useState(0);
  const initialRender = useRef(true);
  const messageEl = useRef(null);
  function handleClick(event: any) {
    setButtonClicked(() => true);
  }

  const handleKeyDown = (e: any) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleClick(e);
    }
  };

  const handleFeedback = () => {
    setIsFeedbackNeeded(() => !isFeedbackNeeded);
  };
  const getAnswer = async () => {
    if (buttonClicked) {
      return await axios
        .get("http://127.0.0.1:8000/query", { params: { query: ask } })
        .then((res) => {
          console.log(ask);
          console.log(res);
          const answer = "" + res["data"];

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
        getAnswer();
      }
    }
  }, [ask, buttonClicked, initialRender, isFeedbackNeeded, isLoading]);

  return (
    <>
      <Header />
      <div className="final-container">
      <div className="band"></div>
        <div className="parent-container">
          <div className="parent" >
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
          </div>
        </div>
      </div>
    </>
  );
}
