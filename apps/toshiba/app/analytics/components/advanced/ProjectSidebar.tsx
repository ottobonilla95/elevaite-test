"use client";
import {
  ChatbotIcons,
  CommonButton,
  ElevaiteIcons,
  SimpleInput,
} from "@repo/ui/components";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
import isBetween from "dayjs/plugin/isBetween";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useChat } from "../../ui/contexts/ChatContext";
import "./ProjectSidebar.scss";
import { WindowGrid } from "../../../lib/interfaces";

dayjs.extend(utc);
dayjs.extend(timezone);

// eslint-disable-next-line import/no-named-as-default-member -- I'm sure I didn't mean the other extend... >.<
dayjs.extend(isBetween);

function SettingsIcon(): JSX.Element {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 44 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M18.7438 29.2139L19.4744 30.8569C19.6915 31.346 20.046 31.7616 20.4946 32.0533C20.9433 32.3449 21.467 32.5001 22.0021 32.5C22.5373 32.5001 23.0609 32.3449 23.5096 32.0533C23.9583 31.7616 24.3127 31.346 24.5299 30.8569L25.2605 29.2139C25.5205 28.6309 25.958 28.1448 26.5105 27.825C27.0665 27.5043 27.7096 27.3677 28.348 27.4347L30.1355 27.625C30.6676 27.6813 31.2045 27.582 31.6813 27.3392C32.1581 27.0963 32.5542 26.7204 32.8216 26.2569C33.0893 25.7938 33.2169 25.2628 33.1887 24.7286C33.1606 24.1944 32.9781 23.6798 32.6632 23.2472L31.6049 21.7931C31.2281 21.2714 31.0267 20.6435 31.0299 20C31.0298 19.3582 31.233 18.7329 31.6105 18.2139L32.6688 16.7597C32.9836 16.3272 33.1662 15.8126 33.1943 15.2783C33.2224 14.7441 33.0949 14.2132 32.8271 13.75C32.5598 13.2865 32.1637 12.9106 31.6869 12.6678C31.2101 12.425 30.6731 12.3257 30.141 12.3819L28.3535 12.5722C27.7152 12.6393 27.072 12.5027 26.516 12.1819C25.9624 11.8603 25.5249 11.3717 25.266 10.7861L24.5299 9.14306C24.3127 8.65396 23.9583 8.23839 23.5096 7.94675C23.0609 7.6551 22.5373 7.49991 22.0021 7.5C21.467 7.49991 20.9433 7.6551 20.4946 7.94675C20.046 8.23839 19.6915 8.65396 19.4744 9.14306L18.7438 10.7861C18.485 11.3717 18.0474 11.8603 17.4938 12.1819C16.9378 12.5027 16.2946 12.6393 15.6563 12.5722L13.8632 12.3819C13.3312 12.3257 12.7942 12.425 12.3174 12.6678C11.8406 12.9106 11.4445 13.2865 11.1771 13.75C10.9094 14.2132 10.7819 14.7441 10.81 15.2783C10.8381 15.8126 11.0206 16.3272 11.3355 16.7597L12.3938 18.2139C12.7712 18.7329 12.9745 19.3582 12.9744 20C12.9745 20.6418 12.7712 21.2671 12.3938 21.7861L11.3355 23.2403C11.0206 23.6728 10.8381 24.1874 10.81 24.7217C10.7819 25.2559 10.9094 25.7868 11.1771 26.25C11.4448 26.7132 11.8409 27.0889 12.3176 27.3317C12.7943 27.5745 13.3312 27.674 13.8632 27.6181L15.6507 27.4278C16.2891 27.3607 16.9323 27.4973 17.4882 27.8181C18.0439 28.1388 18.4835 28.6275 18.7438 29.2139Z"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <path
        d="M21.9999 23.75C24.071 23.75 25.7499 22.0711 25.7499 20C25.7499 17.9289 24.071 16.25 21.9999 16.25C19.9288 16.25 18.2499 17.9289 18.2499 20C18.2499 22.0711 19.9288 23.75 21.9999 23.75Z"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
  );
}

interface ProjectFolder {
  id: string;
  label: string;
  date: string;
  sessions: Session[];
  isOpen?: boolean;
}
interface Session {
  id: string;
  label: string;
}

const testData: ProjectFolder[] = [
  {
    id: "project_01",
    label: "Project A",
    date: dayjs().subtract(3, "hours").toISOString(),
    sessions: [
      { id: "session_01", label: "Session 1" },
      { id: "session_02", label: "Session 2" },
      { id: "session_03", label: "Session 3" },
    ],
  },
  {
    id: "project_02",
    label: "Project B",
    date: dayjs().subtract(7, "hours").toISOString(),
    sessions: [
      { id: "session_04", label: "Session 1" },
      { id: "session_05", label: "Session 2" },
      { id: "session_06", label: "Session 3" },
      { id: "session_07", label: "Session 4" },
      { id: "session_08", label: "Session 5" },
    ],
  },
  {
    id: "project_03",
    label: "Project C",
    date: dayjs().subtract(2, "days").toISOString(),
    sessions: [
      { id: "session_09", label: "Session 1" },
      { id: "session_10", label: "Session 2" },
    ],
  },
  {
    id: "project_04",
    label: "Project D",
    date: dayjs().subtract(5, "days").toISOString(),
    sessions: [
      { id: "session_11", label: "Session 1" },
      { id: "session_12", label: "Session 2" },
      { id: "session_13", label: "Session 3" },
    ],
  },
];

// export function ProjectSidebar({ isExpanded, setIsExpanded }:ProjectSidebarProps): JSX.Element {
export function ProjectSidebar({
  isExpanded,
  setIsExpanded,
}: {
  isExpanded: boolean;
  setIsExpanded: React.Dispatch<React.SetStateAction<boolean>>;
}): JSX.Element {
  const chatContext = useChat();
  const router = useRouter();
  const pathname = usePathname();
  // const [isExpanded, setIsExpanded] = useState(false);
  const [displayFolders, setDisplayFolders] = useState<ProjectFolder[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedProject, setSelectedProject] = useState<string | undefined>();
  const [selectedSession, setSelectedSession] = useState<string | undefined>();

  useEffect(() => {
    // Initialize with test data for folders
    setDisplayFolders(testData);

    // If we have sessions in the context, we can use those too
    if (chatContext.sessions.length > 0) {
      setSelectedSession(chatContext.selectedSession?.id);
    }
  }, [chatContext.selectedSession?.id]);

  function toggleExpanded(): void {
    setIsExpanded((current: boolean) => !current);
  }

  function handleCreate(): void {
    if (pathname !== "/chatbot") {
      router.push("/chatbot");
      return;
    }

    // console.log("Create new chat");
    // Add a new session to the context
    chatContext.addNewSession();
    // Show the welcome screen
    chatContext.setActiveWindowGrid(WindowGrid.toshiba1);
  }

  function handleAdvancedSearch(): void {
    // console.log("Clicked advanced search");
  }

  function handleSettings(): void {
    console.log("Settings button clicked!");
    router.push("/settings");
  }

  function handleProjectClick(id: string): void {
    setSelectedProject(id);
  }

  function handleSessionClick(id: string): void {
    // console.log("Selected session:", id);
    setSelectedSession(id);

    // If it's one of our context sessions, select it and show chat UI
    const contextSession = chatContext.sessions.find(
      (session) => session.id === id
    );
    if (contextSession) {
      chatContext.setSelectedSession(id);
      chatContext.setActiveWindowGrid(WindowGrid.active);
    }
  }

  // Helper to get the preview text for a message
  function getMessagePreview(text: string): string {
    return text.length > 30 ? text.substring(0, 30) + "..." : text;
  }

  // console.log("chatContext", chatContext.sessions)

  return (
    <div
      className={[
        "advanced-sidebar-container",
        "sidebar-area",
        isExpanded ? "is-open" : undefined,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="advanced-sidebar-contents">
        <div className="sidebar-button-wrapper">
          <CommonButton
            onClick={toggleExpanded}
            className="expand-toggle"
            noBackground
            title={isExpanded ? "Minimize the sidebar" : "Expand the sidebar"}
          >
            <ElevaiteIcons.SVGSideArrow />
          </CommonButton>
        </div>

        <div className="separator" />

        <div className="sidebar-button-wrapper">
          <CommonButton
            onClick={handleCreate}
            className="create"
            title="Create New Chat"
          >
            <ChatbotIcons.SVGMenuCreate />
            <div className="button-label">New chat</div>
          </CommonButton>
        </div>

        <div className="separator" />

        {/* <div className="search-container">
                    <SimpleInput
                        value={searchTerm}
                        onChange={setSearchTerm}
                        className="search-field"
                        leftIcon={<ElevaiteIcons.SVGMagnifyingGlass />}
                        placeholder="Search..."
                    />
                    <CommonButton
                        className="advanced-search-button"
                        onClick={handleAdvancedSearch}
                        noBackground
                    >
                        Advanced Search
                    </CommonButton>
                </div> */}

        {/* Chat Sessions Container */}
        {pathname !== "/settings" && (
          <div className="chat-sessions-container">
            <div className="sessions-list">
              {chatContext.sessions.length === 0 ? (
                <div className="empty-sessions">
                  {chatContext.recentChatsMessage}
                </div>
              ) : (
                <>
                  <div style={{ fontWeight: 600, fontSize: "12px" }}>
                    Recent Chats
                  </div>
                  {[...chatContext.sessions]
                    .filter((session) => session.messages.length > 0)
                    .sort(
                      (a, b) =>
                        new Date(b.creationDate).getTime() -
                        new Date(a.creationDate).getTime()
                    )
                    .map((session) => {
                      const formattedDate = dayjs(session.creationDate).format(
                        "YYYY-MM-DD"
                      );
                      const timeWithSpace = dayjs(session.creationDate).format(
                        "HH:mm"
                      );
                      const offset = dayjs(session.creationDate).format("Z");
                      return (
                        <div key={session.id} className="session-container">
                          <CommonButton
                            className={[
                              "session-button",
                              chatContext.selectedSession?.id === session.id
                                ? "active"
                                : undefined,
                            ]
                              .filter(Boolean)
                              .join(" ")}
                            noBackground
                            onClick={() => {
                              handleSessionClick(session.id);
                            }}
                          >
                            <div className="session-icon">
                              {/* Fix for SVGComment error - use a different icon that exists */}
                              <ChatbotIcons.SVGClipboard />
                            </div>
                            <div className="session-details">
                              {/* <span className="session-title">{session.label || "Chat session"}</span> */}
                              <span className="session-preview">
                                {session.label
                                  ? session.label
                                  : session.messages.length > 0
                                    ? getMessagePreview(
                                      session.messages[
                                        session.messages.length - 1
                                      ].text
                                    )
                                    : "New conversation"}
                              </span>
                              <span className="session-date">
                                {/* {session.creationDate
                                                                ? ({ formattedDate } {timeWithSpace} GMT{offset})
                                                            : ""} */}
                                {formattedDate} | {timeWithSpace} | GMT{offset}
                              </span>
                            </div>
                          </CommonButton>
                        </div>
                      );
                    })}
                </>
              )}
            </div>
          </div>
        )}

        {/* Projects Container - Kept but hidden by default */}
        <div className="projects-label-container" style={{ display: "none" }}>
          <span>Projects</span>
          <CommonButton noBackground title="Add new Project">
            <ChatbotIcons.SVGAdd />
          </CommonButton>
        </div>

        <div className="projects-list" style={{ display: "none" }}>
          <div className="projects-group-container">
            {displayFolders.map((folder) => (
              <div key={folder.id} className="project-container">
                <CommonButton
                  className={[
                    "project-label",
                    selectedProject === folder.id ? "active" : undefined,
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  noBackground
                  onClick={() => {
                    handleProjectClick(folder.id);
                  }}
                >
                  <ChatbotIcons.SVGFolder />
                  <span>{folder.label}</span>
                </CommonButton>
                <div
                  className={[
                    "sessions-container",
                    selectedProject === folder.id ? "open" : undefined,
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <div className="sessions-accordion">
                    {folder.sessions.map((session) => (
                      <div className="session-wrapper" key={session.id}>
                        <CommonButton
                          className={[
                            "session",
                            selectedSession === session.id
                              ? "active"
                              : undefined,
                          ]
                            .filter(Boolean)
                            .join(" ")}
                          noBackground
                          onClick={() => {
                            handleSessionClick(session.id);
                          }}
                        >
                          <span>{session.label}</span>
                        </CommonButton>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Settings button at the bottom */}
        <div className="sidebar-button-wrapper" style={{ marginTop: "auto" }}>
          <CommonButton
            onClick={handleSettings}
            className="settings-toggle"
            noBackground
            title="Settings"
          >
            <SettingsIcon />
          </CommonButton>
        </div>
      </div>
    </div>
  );
}
