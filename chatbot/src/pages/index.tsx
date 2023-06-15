/* eslint-disable react-hooks/exhaustive-deps */

import TopHeader from "../components/topheader";
// import SideBar from "./components/sidebar";
import { AiOutlinePlus } from "react-icons/ai";
import ChatWindow from "../components/chatwindow";
import { useEffect, useRef, useState } from "react";
import SubHeader from "../components/subheader";
import { IoIosArrowBack } from "react-icons/io";
import { NextPageContext } from "next";

import axios from "axios";
import jwt_decode from "jwt-decode";

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
};

export default function Home() {
  const [chats, setChats] = useState<chatSessionDetails[]>([
    { id: 0, title: "New Session", chat: [] },
  ]);
  const [count, setCount] = useState(1);
  const [chatIds, setChatIds] = useState<number[]>([]);
  const [currentChatId, setCurrentChatId] = useState<number>(0);

  const removeElement = (index: number) => {
    const newChats = chats.filter((_, i) => i !== index);
    setChats(() => newChats);
  };

  function newSessionClick() {
    setCount(() => count + 1);
    setChatIds(() => [...chatIds, count]);
    setChats(() => {
      return [...chats, { id: count, title: "New Session", chat: [] }];
    });
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
          title: messages[0].message.substring(0, 25) + "...",
          chat: messages,
        },
        ...chats.slice(currentChatId + 1),
      ]);
    }
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
    }
  }
  function keButtonClick() {
    let params = new URL(window.location.href).searchParams;
    const token = params.get("token");
    window.location.href = "https://elevaite-ke.iopex.ai/?token=" + token;
  }

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
                title = messages?.data[0]?.message.substring(0, 25) + "...";
              }
              let oldSessionMessages: chatSessionDetails = {
                id: currentChatId,
                title: title,
                chat: [],
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
      <SubHeader />
      <div className="app-container">
        <div className="sidebar-container">
          <button
            onClick={backButtonClick}
            className="sidebar-button work-bench-button"
          >
            <IoIosArrowBack style={{ color: "white" }} />
            <a href="https://elevaite.iopex.ai">
              <p>Back to Workbench</p>
            </a>
          </button>
          <button
            onClick={keButtonClick}
            className="sidebar-button work-bench-button"
          >
            <IoIosArrowBack style={{ color: "white" }} />
            <p>Knowledge Engineering</p>
          </button>
          <button onClick={newSessionClick} className="sidebar-button">
            <AiOutlinePlus />
            <p>New Session</p>
          </button>

          <div className="current-sessions">
            <div className="session-header">
              <p>CURRENT SESSIONS</p>
            </div>
            {chats.map((chat) => (
              <>
                <button key={chat.id} onClick={() => changeSession(chat?.id)}>
                  <div
                    className="session"
                    style={
                      chat?.id === currentChatId
                        ? { backgroundColor: "#3E3B63" }
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
                        fill="white"
                      />
                    </svg>
                    <p> {chat?.title} </p>
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
              updateMessages={updateMessages}
            />
          ))}
      </div>
    </>
  );
}
