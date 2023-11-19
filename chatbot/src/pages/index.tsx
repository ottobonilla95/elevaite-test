/* eslint-disable react-hooks/exhaustive-deps */

import TopHeader from "../components/topheader";
// import SideBar from "./components/sidebar";
import { AiOutlinePlus, AiOutlineMinus } from "react-icons/ai";
import ChatWindow from "../components/chatwindow";
import { useEffect, useRef, useState } from "react";
import SubHeader from "../components/subheader";
import { IoIosArrowBack } from "react-icons/io";
import { NextPageContext } from "next";

import axios from "axios";
import jwt_decode from "jwt-decode";
import { Collections } from "../components/subheader";

export type MessageDetails = {
  id: string;
  message: string;
  urls?: Set<string>;
  from: string;
  timestamp: string;
};

type chatSessionDetails = {
  id: number;
  title: string;
  chat: MessageDetails[];
  createdOn: string;
};

export default function Home() {
  const current = new Date();
  const initialTimestamp = `${current.getDate()} ${current.toLocaleString(
    "default",
    {
      month: "short",
    }
  )}, ${current.getHours()}:${
    current.getMinutes() < 10 ? "0" : ""
  }${current.getMinutes()}`;
  const [chats, setChats] = useState<chatSessionDetails[]>([
    { id: 0, title: "New Session", chat: [], createdOn: initialTimestamp }, //time of creation
  ]);
  const [count, setCount] = useState(1);
  const [chatIds, setChatIds] = useState<number[]>([]);
  const [uid, setUid] = useState("");
  const [currentChatId, setCurrentChatId] = useState<number>(0);
  const [collection, setCollection] = useState<string>(Collections.Cisco_CLO);
  const removeElement = (index: number) => {
    const newChats = chats.filter((_, i) => i !== index);
    setChats(() => newChats);
  };

  function getCurrentTimestamp() {
    const current = new Date();
    const date = `${current.getDate()} ${current.toLocaleString("default", {
      month: "short",
    })}, ${current.getHours()}:${
      current.getMinutes() < 10 ? "0" : ""
    }${current.getMinutes()}`;
    return date;
  }

  function newSessionClick() {
    //console.log("new session clicked");
    setCount(() => count + 1);
    // console.log("Count: ", count);
    setChatIds(() => [...chatIds, count]);
    //console.log("ChatIDs: ", chatIds);
    setChats(() => {
      return [
        ...chats,
        {
          id: count,
          title: "New Session",
          chat: [],
          createdOn: getCurrentTimestamp(),
        },
      ]; //time of creation
    });
    console.log("Before reverse - Chats Array: ", chats);
    //setChats(() => [...chats].reverse());
    console.log("Chats Array: ", chats);
    setCurrentChatId(() => {
      return count;
    });
  }

  function updateMessages(messages: MessageDetails[]) {
    if (messages.length > 0) {
      setChats(() => [
        ...chats.slice(0, currentChatId),
        {
          id: currentChatId,
          title: messages[0].message.substring(0, 15) + "...",
          chat: messages,
          createdOn: initialTimestamp,
        },
        ...chats.slice(currentChatId + 1),
      ]);
    }
  }

  function clearMessages(messages: MessageDetails[]) {
    setChats(() => [
      ...chats.slice(0, currentChatId),
      {
        id: currentChatId,
        title: "New Session",
        chat: messages,
        createdOn: getCurrentTimestamp(),
      },
      ...chats.slice(currentChatId + 1),
    ]);
    axios
      .get(process.env.NEXT_PUBLIC_BACKEND_URL + "loadSession", {
        params: {
          uid: uid,
          sid: currentChatId.toString(),
        },
      })
      .then((messages) => {
        let title = "New Session";
        if (messages.data.length > 0) {
          title = messages?.data[0]?.message.substring(0, 15) + "...";
        }
        let oldSessionMessages: chatSessionDetails = {
          id: currentChatId,
          title: title,
          chat: [],
          createdOn: getCurrentTimestamp(), //time of creation
        };
        if (messages !== null && messages.data !== null) {
          oldSessionMessages.chat = messages?.data;
          setChats(() => [
            ...chats.slice(0, currentChatId),
            oldSessionMessages,
            ...chats.slice(currentChatId + 1),
          ]);
        }
      });
  }
  function updateCollection(collection_name: string) {
    setCollection(() => collection_name);
    console.log(collection);
    // axios.get(process.env.NEXT_PUBLIC_BACKEND_URL+'setTenant?collection_name='+collection_name);
  }

  function changeSession(chatId: number) {
    setCurrentChatId(() => chatId);
  }

  function backButtonClick() {
    let params = new URL(window.location.href).searchParams;
    const token = params.get("token");
    if (!!token) {
      let decoded: any = jwt_decode(token);
      console.log(decoded);
      axios.get(
        process.env.NEXT_PUBLIC_BACKEND_URL +
          "deleteAllSessions?uid=" +
          decoded.sub
      );
      window.location.reload();
    }
  }
  
  function keButtonClick() {
    let params = new URL(window.location.href).searchParams;
    const token = params.get("token");
    window.location.href = "https://elevaite-ke.iopex.ai/?token=" + token;
  }

  useEffect(() => {
    let params = new URL(window.location.href).searchParams;
    const token = params.get("token");
    if (!!token) {
      let decoded: any = jwt_decode(token);
      const uid = decoded.sub;
      setUid(() => uid);
    }
  }, []);
  useEffect(() => {
    async function retrieveSession() {
      let params = new URL(window.location.href).searchParams;
      const token = params.get("token");
      if (!!token) {
        let decoded: any = jwt_decode(token);
        console.log(decoded);
        try {
          axios
            .get(process.env.NEXT_PUBLIC_BACKEND_URL + "loadSession", {
              params: {
                uid: decoded.sub,
                sid: currentChatId.toString(),
              },
            })
            .then((messages) => {
              let title = "New Session";
              if (messages.data.length > 0) {
                title = messages?.data[0]?.message.substring(0, 15) + "...";
              }
              let oldSessionMessages: chatSessionDetails = {
                id: currentChatId,
                title: title,
                chat: [],
                createdOn: getCurrentTimestamp(),
              };
              if (messages !== null && messages.data !== null) {
                oldSessionMessages.chat = messages?.data;
                setChats(() => [
                  ...chats.slice(0, currentChatId),
                  oldSessionMessages,
                  ...chats.slice(currentChatId + 1),
                ]);
              }
            });
        } catch (e) {
          console.log(e);
        }
      }
    }
    retrieveSession();
  }, [currentChatId]);

  return (
    <>
      {/* <Header /> */}
      <TopHeader />
      <SubHeader updateCollection={updateCollection} />
      <div className="app-container">
        <div className="sidebar-container">
          <button onClick={backButtonClick} className="sidebar-button">
            <AiOutlineMinus />
            <p>Clear All</p>
          </button>
          {/* <button
            onClick={keButtonClick}
            className="sidebar-button work-bench-button"
          >
            <IoIosArrowBack style={{ color: "white" }} />
            <p>Knowledge Engineering</p>
          </button> */}
          <button onClick={newSessionClick} className="sidebar-button">
            <AiOutlinePlus />
            <p>New Session</p>
          </button>

          <div className="current-sessions">
            <div className="session-header">
              <p>CURRENT SESSIONS</p>
            </div>
            {chats
              .slice()
              .reverse()
              .map((chat) => (
                <>
                  <button key={chat.id} onClick={() => changeSession(chat?.id)}>
                    <div
                      className="session"
                      style={
                        chat?.id === currentChatId
                          ? { backgroundColor: "#f1f1f1" }
                          : { backgroundColor: "transparent" }
                      }
                    >
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 20 20"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M18 0H2C0.9 0 0 0.9 0 2V20L4 16H18C19.1 16 20 15.1 20 14V2C20 0.9 19.1 0 18 0ZM18 14H4L2 16V2H18V14Z"
                          fill="#8c959f"
                        />
                      </svg>
                      <div className="text-container">
                        <p className="main-text">{chat?.title}</p>
                        {/*} <p
                        className="sub-text"
                        style={{
                          color: 'grey',
                          fontSize: '12px',
                          alignItems: 'right',
                          textAlign: 'right',
                          marginRight: '10px'
                        }}
                      >
                        {chat?.createdOn}
                      </p>*/}
                      </div>
                    </div>
                  </button>
                </>
              ))}
          </div>
        </div>

        {chats
          .filter((chat) => chat.id === currentChatId)
          .map((chat) => (
            <ChatWindow
              key={chat.id}
              chat={chat}
              collection={collection}
              updateMessages={updateMessages}
              clearMessages={clearMessages}
            />
          ))}
      </div>
    </>
  );
}
