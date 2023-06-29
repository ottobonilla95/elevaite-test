/* eslint-disable @next/next/no-img-element */
import { useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import axios from "axios";
import TextareaAutosize from "@mui/base/TextareaAutosize";
import { BsCursor } from "react-icons/bs";

import Message from "./message";
import { MessageDetails } from "../pages";
import CircularIndeterminate from "./progress_spinner";
import LinearIndeterminate from "./linear_progress_indicator";
import jwt_decode from "jwt-decode";

export default function ChatWindow(props: any) {
  const [ask, setAsk] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState<string>("");
  const [messageIdCount, setMessageIdCount] = useState(0);
  const [caseId, setCaseId] = useState<number | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  function closeSession() {
    props.updateMessages(()=>[]);
    let params = new URL(window.location.href).searchParams;
    const token = params.get("token");
    if (!!token) {
      let decoded: any = jwt_decode(token);
      const uid = decoded.sub;
      axios.get(
        process.env.NEXT_PUBLIC_BACKEND_URL +
          "deleteSession?uid=" +
          uid +
          "&sid=" +
          props?.chat?.id.toString()
      );
    }
  }

  async function streaming(uid: string, ask: string) {
    const evtSource = new EventSource(
      process.env.NEXT_PUBLIC_BACKEND_URL +
        "currentStatus?uid=" +
        uid +
        "&sid=" +
        props?.chat?.id.toString()
    );
    evtSource.onmessage = (e) => {
      setAgentStatus(() => e.data);
    };
    console.log(props.collection);
    const response = await fetch(
      process.env.NEXT_PUBLIC_BACKEND_URL +
        "query?query=" +
        ask +
        "&uid=" +
        uid +
        "&sid=" +
        props?.chat?.id.toString() +
        "&collection=" + props.collection
    );
    if (!!response.body) {
      const reader = response.body
        .pipeThrough(new TextDecoderStream())
        .getReader();
      let whole_string = "";
      props.updateMessages([
        ...props.chat.chat,
        {
          id: messageIdCount,
          message: ask,
          from: "human",
          timestamp: getCurrentTimestamp(),
        },
      ]);
      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          setMessageIdCount(() => messageIdCount + 2);
          setIsLoading(() => false);
          evtSource.close();
          break;
        }
        whole_string += value;
        console.log(whole_string);
        props.updateMessages([
          ...props.chat.chat,
          {
            id: messageIdCount,
            message: ask,
            from: "human",
            timestamp: getCurrentTimestamp(),
          },
          {
            id: messageIdCount + 1,
            message: whole_string,
            from: "ai",
            timestamp: getCurrentTimestamp(),
          },
        ]);
      }
    }
  }

  function handleClick(event: any) {
    if (ask.trim() != "") {
      console.log(props.collection);
      setIsLoading(() => true);
      props.updateMessages([
        ...props.chat.chat,
        {
          id: messageIdCount,
          message: ask,
          from: "human",
          timestamp: getCurrentTimestamp(),
        },
      ]);
      let params = new URL(window.location.href).searchParams;
      const token = params.get("token");
      if (!!token) {
        let decoded: any = jwt_decode(token);
        streaming(decoded.sub.toString(), ask);
      }
      setAsk(() => "");
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

  // The code below has been replaced with streaming call
  // fetchAnswer.current = async () => {
  //   return await axios
  //     .get(process.env.NEXT_PUBLIC_BACKEND_URL +"query", { params: { query: ask } })
  //     .then((res) => {

  //       let answer = "" + res["data"]["text"];

  //       if (answer) {
  //         flushSync(() => {
  //           const current = new Date();
  //           const date = `${current.getDate()} ${current.toLocaleString(
  //             "default",
  //             {
  //               month: "short",
  //             }
  //           )}, ${current.getFullYear()} ${current.getHours()}:${
  //             current.getMinutes() < 10 ? "0" : ""
  //           }${current.getMinutes()}`;

  //           setMessages(() => [
  //             ...messages,
  //             {
  //               id: messageIdCount.toString(),
  //               message: ask,
  //               from: "human",
  //               timestamp: getCurrentTimestamp(),
  //             },
  //             {
  //               id: (messageIdCount + 1).toString(),
  //               message: answer,
  //               from: "ai",
  //               timestamp: getCurrentTimestamp(),
  //             },
  //           ]);
  //           props.updateMessages([
  //             ...messages,
  //             {
  //               id: messageIdCount,
  //               message: ask,
  //               from: "human",
  //               timestamp: getCurrentTimestamp(),
  //             },
  //             {
  //               id: messageIdCount + 1,
  //               message: answer,
  //               from: "ai",
  //               timestamp: getCurrentTimestamp(),
  //             },
  //           ]);
  //           setAsk(() => "");
  //           setMessageIdCount(() => messageIdCount + 2);
  //           setIsLoading(() => false);
  //           axios
  //             .get(process.env.NEXT_PUBLIC_BACKEND_URL+"storeSession", {
  //               params: { sessionID: props?.chat?.id.toString() },
  //             });
  //         });
  //       }
  //     })
  //     .catch((error) => console.log("Error occured"));
  // };

  const change = (event: any) => {
    setAsk(() => event.target.value);
  };

  useEffect(() => scrollToLastMessage(), [props.chat.chat]);
  useEffect(
    () =>
      setCaseId(() => {
        console.log(props.collection);
        return props?.chat?.id;
      }),
    [props]
  );

  // The code below has been replaced with server sent events
  // useEffect(() => {
  //   let intervalId: NodeJS.Timeout;
  //   if (isLoading) {
  //     intervalId = setInterval(() => {
  //       axios
  //         .get(process.env.NEXT_PUBLIC_BACKEND_URL+"currentStatus")
  //         .then((response) => {
  //           if (!response) {
  //             throw new Error("Network response was not ok");
  //           }
  //           setAgentStatus(() => response["data"]["Status"]);
  //           return response;
  //         })
  //         .catch((error) => {
  //           console.log(error);
  //         });
  //     }, 2000);
  //   }
  //   return () => clearInterval(intervalId);
  // }, [isLoading]);

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
                {props?.chat?.chat?.map((message: MessageDetails) => (
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
