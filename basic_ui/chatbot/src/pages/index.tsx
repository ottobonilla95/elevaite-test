import Head from "next/head";
import Image from "next/image";
import { Anybody, Inter } from "next/font/google";
import styles from "@/styles/Home.module.css";
import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { Audio } from "react-loader-spinner";
import { FiPlay } from "react-icons/fi";
import {
  BsFillHandThumbsUpFill,
  BsFillHandThumbsDownFill,
} from "react-icons/bs";
const inter = Inter({ subsets: ["latin"] });

export default function Home() {
  const [message, setMessage] = useState<string | undefined>("");
  const [response, setResponse] = useState<string | undefined>("");
  const [buttonClicked, setButtonClicked] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isFeedbackNeeded, setIsFeedbackNeeded] = useState(false);
  const initialRender = useRef(true);
  function handleClick(event: any) {
    setButtonClicked(() => true);
  }

  const handleKeyDown = (e: any) => {
    if (e.key === "Enter") {
      handleClick(e);
    }
  };

  const handleFeedback = () =>{
    setIsFeedbackNeeded(()=> !isFeedbackNeeded);
  }
  const getAnswer = async () => {
    if (buttonClicked) {
      return await axios
        .get("http://127.0.0.1:8000/query", { params: { query: message } })
        .then((res) => {
          console.log(message);
          console.log(res);
          const answer = "" + res["data"];
          if (answer) {
            setResponse(() => answer);
            setButtonClicked(() => false);
            setIsLoading(() => false);
          }
        })
        .catch((error) => console.log("Error occured"));
    }
  };

  const change = (event: any) => {
    setMessage(() => event.target.value);
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
  }, [message, buttonClicked, initialRender, isFeedbackNeeded, isLoading]);

  return (
    <>
      <div className="parent-container">
        <div className="parent">
          <div className="container-body">
            <input
              onChange={change}
              className="chat-input"
              value={message}
              type="text"
              onKeyDown={handleKeyDown}
              placeholder="Ask questions regarding the loaded docs here"
            />
            <button className="button" onClick={handleClick}>
              <FiPlay size="30px" />
            </button>
          </div>
          {isLoading ? (
            <div className="loader">
              <Audio
                height="40"
                width="40"
                color="#fa582d"
                ariaLabel="loading"
              />
            </div>
          ) : (
            <div className="answer"> {response} </div>
          )}
          {response && !isLoading ? (
            <div className="feedback">
              <p> Did you like the response?</p>
              <div>
                <button className="feedback-button">
                  <BsFillHandThumbsUpFill size="30px" />
                </button>
                <button onClick={handleFeedback} className="feedback-button">
                  <BsFillHandThumbsDownFill size="30px" />
                </button>
              </div>
              {
                isFeedbackNeeded ? (
                  <div className="feedback-body">
                    <input className="chat-input" type="text" placeholder="Please provide addi"/> 
                    <button onClick={handleFeedback} className="button">Send feedback</button>
                  </div>
                ) : null
  
              }
            </div>
          ) : null}
        </div>
      </div>
    </>
  );
}
