import { Inter } from "next/font/google";
import Header from "./components/header";
// import SideBar from "./components/sidebar";
import { AiOutlinePlus } from "react-icons/ai";
import ChatWindow from "./components/chatwindow";
import { useEffect, useState } from "react";

export type MessageDetails = {
  id: number;
  message: string;
  from: string;
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
    setCount(()=>count+1);
    setChats(() => [<ChatWindow key={count} />]);
  }

  return (
    <>
      <Header />
      <div className="app-container">
        <div className="sidebar-container">
          <button onClick={handleClick} className="sidebar-button">
            <AiOutlinePlus />
            New Case
          </button>
        </div>
        {chats.map((chat, idx) => chat)}
      </div>
    </>
  );
}
