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
import RowRadioButtonsGroup from "./radiobutton";
import { ChatbotV } from "./radiobutton";
import TransitionsModal from "./modal";

export default function ChatWindow(props: any) {
  const [ask, setAsk] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState<string>("");
  const [chatbotV, setChatbotV] = useState<string>(ChatbotV.InWarranty);
  const [uid, setUid] = useState("");
  const [messageIdCount, setMessageIdCount] = useState(0);
  const [isChatbotSelectionDisabled, setIsChatbotSelectionDisabled] =
    useState(false);
  const [caseId, setCaseId] = useState<number | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let params = new URL(window.location.href).searchParams;
    const token = params.get("token");
    if (!!token) {
      let decoded: any = jwt_decode(token);
      const uid = decoded.sub;
      setUid(()=> uid);
    }
  }, []);

  function setChatbotType(chatbotType: string) {
    setChatbotV(() => chatbotType);
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
        chatbotV +
        "?query=" +
        ask +
        "&uid=" +
        uid +
        "&sid=" +
        props?.chat?.id.toString() +
        "&collection=" +
        props.collection
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

  async function nonStreaming(uid:string, ask: string){
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
    axios.get(
      process.env.NEXT_PUBLIC_BACKEND_URL +
        chatbotV +
        "?query=" +
        ask +
        "&uid=" +
        uid +
        "&sid=" +
        props?.chat?.id.toString() +
        "&collection=" +
        props.collection
    ).then((data)=>{
      console.log(data.data['refs']);
      setMessageIdCount(() => messageIdCount + 2);
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
          message: data.data['text'],
          urls: data.data['refs'],
          from: "ai",
          timestamp: getCurrentTimestamp(),
        },
      ]);
      setIsLoading(() => false);
      evtSource.close();
    })

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
        if (props.collection === 'cisco_clo'){
          nonStreaming(decoded.sub.toString(), ask);
        } else {
          streaming(decoded.sub.toString(), ask);
        }
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
  const change = (event: any) => {
    setAsk(() => event.target.value);
  };

  function clearMessages(){
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
    props.clearMessages();
  }

  useEffect(() => scrollToLastMessage(), [props.chat.chat]);
  useEffect(() => {
    if (props?.chat?.title != "New Session") {
      setIsChatbotSelectionDisabled(() => true);
    }
  }, [props]);
  useEffect(
    () =>
      setCaseId(() => {
        console.log(props.collection);
        return props?.chat?.id;
      }),
    [props]
  );

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
          {/* <img src="/img/chat-header.svg" alt="search functionality" /> */}
          <RowRadioButtonsGroup
            isDisabled={isChatbotSelectionDisabled}
            setChatbotType={setChatbotType}
          />
        </div>

        <div className="final-container">
          <div className="grand-parent">
            <div className="parent-container">
              <div ref={listRef} className="parent">
                {props?.chat?.chat?.map((message: MessageDetails) => (
                    <Message key={message.id} message={message} />
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
              placeholder="Ask questions here"
            />
            {isLoading ? (
              <div className="loader">
                <CircularIndeterminate size={30}/>
              </div>
            ) : (
              <button className="button" onClick={handleClick}>
                <BsCursor style={{ color: "white" }} size="30px" />
              </button>
            )}
          </div>
          <TransitionsModal uid={uid} sid={props?.chat?.id.toString()} clearMessages={clearMessages} />
        </div>
      </div>
    </>
  );
}
