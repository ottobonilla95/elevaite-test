/* eslint-disable @next/next/no-img-element */
import { useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import axios from "axios";
import TextareaAutosize from "@mui/base/TextareaAutosize";
import { BsCursor } from "react-icons/bs";

import Message from "./message";
import { MessageDetails } from "..";
import CircularIndeterminate from "./progress_spinner";
import LinearIndeterminate from "./linear_progress_indicator";

export default function ChatWindow(props: any) {
  const [ask, setAsk] = useState<string>("");
  const [messages, setMessages] = useState<MessageDetails[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState<string>("");
  const [messageIdCount, setMessageIdCount] = useState(0);
  const [caseId, setCaseId] = useState<number | null>(null);
  const fetchAnswer = useRef(() => {});
  const listRef = useRef<HTMLDivElement>(null);

  function closeSession() {
    console.log("Close Session Clicked");
    // Uncomment the line below to call the api once ready
    // clearMessages().then((data) => console.log(data));
  }

  function handleClick(event: any) {
    if (ask.trim() != "") {
      setIsLoading(() => true);
      setMessages(() => [
        ...messages,
        {
          id: messageIdCount.toString(),
          message: ask,
          from: "human",
          timestamp: getCurrentTimestamp(),
        },
      ]);
      fetchAnswer.current();
    }
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

  function getCurrentTimestamp() {
    const current = new Date();
    const date = `${current.getDate()} ${current.toLocaleString("default", {
      month: "short",
    })}, ${current.getFullYear()} ${current.getHours()}:${
      current.getMinutes() < 10 ? "0" : ""
    }${current.getMinutes()}`;
    return date;
  }

  fetchAnswer.current = async () => {
    return await axios
      .get("http://localhost:8000/query", { params: { query: ask } })
      .then((res) => {
        console.log(ask);
        console.log(res);

        let answer = "" + res["data"]["text"];

        if (answer) {
          flushSync(() => {
            let urls = new Set<string>();
            if (res["data"]["url_1"] != undefined) {
              urls.add(
                `<li><a target="_blank" href=${res["data"]["url_1"]}> ${res["data"]["topic_1"]}</a></li>`
              );
            }
            if (res["data"]["url_2"] != undefined) {
              urls.add(
                `<li><a target="_blank" href=${res["data"]["url_2"]}> ${res["data"]["topic_2"]}</a></li>`
              );
            }
            if (res["data"]["url_3"] != undefined) {
              urls.add(
                `<li><a target="_blank" href=${res["data"]["url_3"]}> ${res["data"]["topic_3"]}</a></li>`
              );
            }
            const current = new Date();
            const date = `${current.getDate()} ${current.toLocaleString(
              "default",
              {
                month: "short",
              }
            )}, ${current.getFullYear()} ${current.getHours()}:${
              current.getMinutes() < 10 ? "0" : ""
            }${current.getMinutes()}`;

            setMessages(() => [
              ...messages,
              {
                id: messageIdCount.toString(),
                message: ask,
                from: "human",
                timestamp: getCurrentTimestamp(),
              },
              {
                id: (messageIdCount + 1).toString(),
                message: answer,
                from: "ai",
                urls: urls,
                timestamp: getCurrentTimestamp(),
              },
            ]);
            props.updateMessages([
              ...messages,
              {
                id: messageIdCount,
                message: ask,
                from: "human",
                timestamp: getCurrentTimestamp(),
              },
              {
                id: messageIdCount + 1,
                message: answer,
                from: "ai",
                urls: urls,
                timestamp: getCurrentTimestamp(),
              },
            ]);
            setAsk(() => "");
            setMessageIdCount(() => messageIdCount + 2);
            setIsLoading(() => false);
            axios
              .get("http://localhost:8000/storeSession", {
                params: { sessionID: props.chat.id.toString() },
              })
              .then((res) => console.log(res));
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
      setCaseId(() => {
        console.log(props);
        return props.chat.id;
      }),
    [props]
  );

  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    if (isLoading) {
      intervalId = setInterval(() => {
        axios
          .get("http://127.0.0.1:8000/currentStatus")
          .then((response) => {
            if (!response) {
              throw new Error("Network response was not ok");
            }
            setAgentStatus(() => response["data"]["Status"]);
            console.log(response["data"]);
            return response;
          })
          .catch((error) => {
            console.log(error);
          });
      }, 2000);
    }
    return () => clearInterval(intervalId);
  }, [isLoading]);
  return (
    <>
      <div className="band-flex">
        <div className="band-top"></div>
        <div className="band-bottom"></div>
      </div>
      <div className="band"></div>
      <div className="chat-container">
        <div className="chat-header">
          <p> {props?.chat?.title}</p>
          <img src="/img/chat-header.svg" alt="search functionality" />
        </div>

        <div className="final-container">
          <div className="grand-parent">
            <div className="parent-container">
              <div ref={listRef} className="parent">
                {props.chat.chat.map((message: MessageDetails) => (
                  <>
                    <Message key={message.id} message={message} />
                  </>
                ))}
              </div>
            </div>
          </div>
        </div>
        {isLoading ? <LinearIndeterminate agentStatus={agentStatus} /> : null}
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
          <button className="button session-button" onClick={closeSession}>
            <img src="/img/session-button.svg" alt="session button" />
          </button>
        </div>
      </div>
    </>
  );
}
