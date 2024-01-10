"use client";
import { useState, type JSX, type SVGProps } from "react";
import { useSession } from "next-auth/react";
import { Source_Code_Pro as SourceCodePro } from "next/font/google";
import Image from "next/image";
import dayjs from "dayjs";
import { Loading } from "@repo/ui/components";
import type { ChatMessageInterface, EmbeddedMessage } from "../../lib/interfaces";
import { ask } from "../../lib/actions";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

const sourceCodePro = SourceCodePro({ subsets: ["latin"] });

interface PreviewPowerPointProps {
  summary: string;
  location: string;
}

function PreviewPowerPoint({ location, summary }: PreviewPowerPointProps): JSX.Element {
  const [chatMessages, setChatMessages] = useState<ChatMessageInterface[]>([getInitialMessage()]);
  const [userMessage, setUserMessage] = useState<string>("");
  const [isResponseLoading, setIsResponseLoading] = useState(false);

  function getInitialMessage(): ChatMessageInterface {
    const _before = `Hello. This is the summary I created from the provided data. Feel free to ask me questions about this summary or download the presentation directly.`;

    return {
      sender: "system",
      content: { before: _before, embed: summary },
      timestamp: dayjs().toISOString(),
      uuid: crypto.randomUUID(),
    };
  }

  async function handleSubmit(): Promise<void> {
    if (userMessage) {
      setUserMessage("");
      const _userMsg: ChatMessageInterface = {
        content: userMessage,
        sender: "user",
        timestamp: dayjs().toISOString(),
        uuid: crypto.randomUUID(),
      };
      chatMessages.push(_userMsg);
      setIsResponseLoading(true);
      const res = await ask(userMessage, summary);
      if (res) {
        const botMsg: ChatMessageInterface = {
          isLoading: false,
          content: res,
          sender: "system",
          uuid: crypto.randomUUID(),
          timestamp: dayjs().toISOString(),
        };
        setIsResponseLoading(false);
        setChatMessages([...chatMessages, botMsg]);
      }
    }
  }

  function handleInput(value: string): void {
    setUserMessage(value);
  }

  //This is hack to stop react from complaining.
  const handleKeyboardEvent = (event: { key: string }): void => {
    if (event.key === "Enter") {
      void handleSubmit();
    }
  };

  function handleDownload(): void {
    const url = new URL(`${BACKEND_URL}/downloadPPT/`);
    url.searchParams.append("ppt_path", location);

    fetch(url.toString(), { method: "GET" })
      .then((res) => res.blob())
      .then((blob) => {
        const fileUrl = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement("a");
        link.href = fileUrl;

        link.setAttribute("download", "presentation.pptx");
        document.body.appendChild(link);
        link.click();
      })
      .catch((error) => {
        throw new Error("Something went wrong", { cause: error as unknown });
      });
  }

  return (
    <div className="flex flex-row h-full w-full justify-center">
      {/* PPT Preview goes here */}
      <div className="flex flex-col h-full w-full justify-center items-center">
        {/* PPT Editor goes here */}
        <div className="flex flex-col flex-grow items-start w-full max-w-6xl rounded-lg border border-solid border-[#e5e5e5] bg-white">
          <div className="flex p-4 flex-row items-center justify-between gap-2 self-stretch">
            <p className="text-[#171717] font-semibold">Chatbot</p>
            <div className="flex rounded-lg bg-[#F46F22]">
              <button
                className="flex justify-center items-center px-4 py-1.5 text-white gap-2 text-sm font-medium"
                onClick={() => {
                  handleDownload();
                }}
                type="button"
              >
                <DownloadIcon />
                Download File
              </button>
            </div>
          </div>
          <div className="flex flex-grow flex-col items-start self-stretch gap-4 px-4 pb-4 h-[calc(100vh-356px)] max-h-full">
            <div className="flex overflow-y-auto px-2 h-full max-h-full flex-col-reverse">
              {isResponseLoading ? <ThinkingChatMessage /> : null}
              {chatMessages
                .sort((a, b) => (dayjs(a.timestamp).isAfter(dayjs(b.timestamp)) ? -1 : 1))
                .map((_msg) => (
                  <ChatMessage key={_msg.timestamp} message={_msg} />
                ))}
            </div>
            <div className="flex p-2 rounded-lg border border-solid border-[#e5e5e5] w-full self-end">
              <input
                className="w-full focus:outline-none p-2"
                onChange={(e) => {
                  handleInput(e.target.value);
                }}
                onKeyDown={handleKeyboardEvent}
                placeholder="Type here to send a message"
                type="text"
                value={userMessage}
              />
              <div className="flex w-[40px] h-[40px] bg-[#F46F22] items-center justify-center rounded-lg">
                <button
                  className="flex w-full h-full items-center justify-center"
                  disabled={!userMessage && !isResponseLoading}
                  onClick={handleSubmit}
                  type="button"
                >
                  <SendIcon />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PreviewPowerPoint;

function ThinkingChatMessage(): JSX.Element {
  return (
    <div className="flex flex-row p-4 gap-4 self-stretch items-start justify-center rounded-lg border border-solid border-[#E5E5E5] bg-[#17171705]">
      <div className=" w-8 h-8 rounded-full">
        <ChatbotIcon />
      </div>

      <div className="flex flex-col items-start gap-2 flex-grow">
        <div className="flex items-center gap-3">
          <p className=" text-[#171717] font-semibold text-sm">elevAIte Chat</p>
          <SmallEllipseIcon />
        </div>
        <Loading />
      </div>
    </div>
  );
}

function ChatMessage({ message }: { message: ChatMessageInterface }): JSX.Element {
  const { data: session } = useSession();

  function getAvatar(sender: "user" | "system"): JSX.Element {
    if (sender === "system") return <ChatbotIcon />;
    if (session?.user?.image) return <Image alt="User Avatar" src={session.user.image} />;
    return <DefaultAvatar />;
  }

  function getUsername(sender: "user" | "system"): string {
    if (sender === "system") return "elevAIte Chat";
    return session?.user?.name || "User";
  }

  function renderContent(_content: string | EmbeddedMessage): JSX.Element {
    if (typeof _content === "string") return <p className=" text-sm text-[#171717] opacity-80 py-2">{_content}</p>;
    return (
      <>
        {_content.before ? renderContent(_content.before) : null}
        {_content.embed ? (
          <span
            className={`${sourceCodePro.className} flex bg-gray-200 rounded-lg p-2 flex-wrap text-sm opacity-80 text-[#171717]`}
          >
            {_content.embed}
          </span>
        ) : null}
        {_content.after ? renderContent(_content.after) : null}
      </>
    );
  }

  return (
    <div
      className={`flex flex-row p-4 gap-4 self-stretch items-start justify-center ${
        message.sender === "system" ? "rounded-lg border border-solid border-[#E5E5E5] bg-[#17171705]" : ""
      }`}
    >
      <div className=" w-8 h-8 rounded-full">{getAvatar(message.sender)}</div>
      {message.isLoading ? (
        <Loading />
      ) : (
        <div className="flex flex-col items-start gap-2 flex-grow">
          <div className="flex items-center gap-3">
            <p className=" text-[#171717] font-semibold text-sm">{getUsername(message.sender)}</p>
            <SmallEllipseIcon />
            <div className="text-[#171717] font-normal text-sm opacity-[64%]">
              {dayjs(message.timestamp).format("HH:mm A")}{" "}
            </div>
          </div>
          <div>{renderContent(message.content)}</div>
        </div>
      )}
    </div>
  );
}

function DownloadIcon(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={16} width={16} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M14 10v.8c0 1.12 0 1.68-.218 2.108a2 2 0 0 1-.874.874C12.48 14 11.92 14 10.8 14H5.2c-1.12 0-1.68 0-2.108-.218a2 2 0 0 1-.874-.874C2 12.48 2 11.92 2 10.8V10m9.333-3.333L8 10m0 0L4.667 6.667M8 10V2"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
      />
    </svg>
  );
}

function ChatbotIcon(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <div className="flex bg-[#F46F22] justify-center items-center w-8 h-8 rounded-full">
      <svg fill="none" height={12} width={20} xmlns="http://www.w3.org/2000/svg" {...props}>
        <path
          d="m17.87 8.178.433-4.685C19.268 3.7 20 4.685 20 5.795c0 1.315-.965 2.383-2.13 2.383Zm-15.74 0C.965 8.178 0 7.11 0 5.795c0-1.151.732-2.096 1.697-2.302l.433 4.685ZM16.373.411A48.466 48.466 0 0 0 10.05 0a48.1 48.1 0 0 0-6.323.411c-.732.082-1.264.904-1.165 1.767l.666 7.973c.067.74.532 1.356 1.165 1.438 1.863.288 3.76.411 5.69.411 1.93 0 3.827-.123 5.69-.411.6-.082 1.099-.699 1.165-1.438l.666-7.973c0-.904-.5-1.685-1.231-1.767ZM6.356 7.644c-.532 0-.932-.658-.932-1.52 0-.864.433-1.521.932-1.521.5 0 .932.657.932 1.52s-.4 1.52-.932 1.52Zm5.558 1.685a.356.356 0 0 1-.067.205.232.232 0 0 1-.166.082H8.386a.232.232 0 0 1-.166-.082.356.356 0 0 1-.067-.205v-.74c0-.164.1-.288.233-.288h.067c.133 0 .233.124.233.288v.37h2.695v-.37c0-.164.1-.288.233-.288h.066c.134 0 .234.124.234.288v.74Zm1.763-1.685c-.532 0-.932-.658-.932-1.52 0-.864.433-1.521.932-1.521.5 0 .932.657.932 1.52s-.4 1.52-.932 1.52Z"
          fill="#fff"
        />
      </svg>
    </div>
  );
}

function DefaultAvatar(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg
      className="w-8 h-8"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path
        d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function SendIcon(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={20} width={20} xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M18.439 10.554a1.25 1.25 0 0 0 0-1.108c-.152-.307-.42-.469-.557-.546-.15-.084-.34-.17-.53-.255L3.366 2.35a7.208 7.208 0 0 0-.553-.232c-.15-.052-.452-.147-.787-.054a1.25 1.25 0 0 0-.829.748c-.126.324-.063.634-.026.789.04.168.106.37.174.573l1.353 4.078c.11.329.164.493.265.614.09.107.205.19.335.242.147.058.32.058.666.058H10a.833.833 0 0 1 0 1.666H3.98c-.346 0-.518 0-.665.058a.833.833 0 0 0-.334.24c-.102.121-.156.285-.266.612L1.351 15.82a7.235 7.235 0 0 0-.176.573c-.037.155-.102.466.025.79.143.367.45.645.828.75.336.094.639-.002.789-.054.164-.056.358-.144.553-.232l13.982-6.291c.19-.086.38-.172.53-.256.138-.077.405-.239.557-.546Z"
        fill="#fff"
      />
    </svg>
  );
}

function SmallEllipseIcon(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg fill="none" height={4} width={4} xmlns="http://www.w3.org/2000/svg" {...props}>
      <circle cx={2} cy={2} fill="#171717" opacity={0.2} r={2} />
    </svg>
  );
}
