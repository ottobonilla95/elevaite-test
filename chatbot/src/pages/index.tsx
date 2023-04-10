import { Inter } from "next/font/google";
import Header from "./components/header";
import TopHeader from "./components/topheader";
// import SideBar from "./components/sidebar";
import { AiOutlinePlus } from "react-icons/ai";
import ChatWindow from "./components/chatwindow";
import { useEffect, useState } from "react";
import SubHeader from "./components/subheader";
import { IoIosArrowBack } from "react-icons/io";

export type MessageDetails = {
  id: number;
  message: string;
  urls?: Set<string>;
  from: string;
  timestamp: string;
};

export default function Home() {
  const [chats, setChats] = useState<JSX.Element[]>([<ChatWindow key={0} />]);
  const [count, setCount] = useState(1);

  const removeElement = (index: number) => {
    const newChats = chats.filter((_, i) => i !== index);
    setChats(() => newChats);
  };

  function handleClick() {
    console.log("Clicked");
    setCount(() => count + 1);
    setChats(() => [<ChatWindow key={count} />]);
  }

  function backButtonClick() {}

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
          <button onClick={handleClick} className="sidebar-button">
            <AiOutlinePlus />
            <p>New Session</p>
          </button>

          <div className="current-sessions">
            <div className="session-header">
              <p>CURRENT SESSIONS</p>
            </div>
            <div className="session" style={{ backgroundColor: "#3E3B63" }}>
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
              <p>Case ID: #135727</p>
            </div>
            <div className="session">
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
              <p>PAN OS Version Upgrade</p>
            </div>
            <div className="session">
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
              <p>NAT Version Issue</p>
            </div>
            <div className="session"></div>
          </div>
        </div>

        {chats.map((chat, idx) => chat)}
      </div>
    </>
  );
}
