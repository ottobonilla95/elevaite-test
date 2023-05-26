import { Inter } from "next/font/google";
import Header from "./components/header";
import TopHeader from "./components/topheader";
// import SideBar from "./components/sidebar";
import { AiOutlinePlus } from "react-icons/ai";
import ChatWindow from "./components/chatwindow";
import { useEffect, useState } from "react";
import SubHeader from "./components/subheader";
import { IoIosArrowBack } from "react-icons/io";
import SearchResult from "./components/search_result";

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
  const [searchResult] = useState<JSX.Element>(<SearchResult />);

  const removeElement = (index: number) => {
    const newChats = chats.filter((_, i) => i !== index);
    setChats(() => newChats);
  };

  function handleClick() {
    console.log("Clicked");
    setCount(() => count + 1);
    setChats(() => [<ChatWindow key={count} />]);
  }

  function handleSearchClick() {}

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
          {/* <button onClick={handleClick} className="sidebar-button">
            <AiOutlinePlus />
            <p>New Session</p>
          </button> */}
          <button onClick={handleSearchClick} className="sidebar-button">
            <AiOutlinePlus />
            <p>New Scoop</p>
          </button>
        </div>

        {/* {chats.map((chat, idx) => chat)} */}
        {searchResult}
      </div>
    </>
  );
}
