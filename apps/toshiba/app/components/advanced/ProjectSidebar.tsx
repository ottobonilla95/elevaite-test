"use client";
import { ChatbotIcons, CommonButton, ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import dayjs from "dayjs";
import utc from 'dayjs/plugin/utc';
import timezone from "dayjs/plugin/timezone"
import isBetween from "dayjs/plugin/isBetween";
import { useEffect, useState } from "react";
import { useChat } from "../../ui/contexts/ChatContext";
import "./ProjectSidebar.scss";
import { WindowGrid } from "../../lib/interfaces";
import { MainAreaSwitcher } from "./MainAreaSwitcher";

dayjs.extend(utc);
dayjs.extend(timezone);

// eslint-disable-next-line import/no-named-as-default-member -- I'm sure I didn't mean the other extend... >.<
dayjs.extend(isBetween);

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
export function ProjectSidebar({ isExpanded, setIsExpanded }: { isExpanded: boolean; setIsExpanded: React.Dispatch<React.SetStateAction<boolean>> }): JSX.Element {
    const chatContext = useChat();
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
        console.log("Create new chat");
        // Add a new session to the context
        chatContext.addNewSession();
        // Show the welcome screen
        chatContext.setActiveWindowGrid(WindowGrid.toshiba1);
    }

    function handleAdvancedSearch(): void {
        console.log("Clicked advanced search");
    }

    function handleProjectClick(id: string): void {
        setSelectedProject(id);
    }

    function handleSessionClick(id: string): void {
        console.log("Selected session:", id);
        setSelectedSession(id);

        // If it's one of our context sessions, select it and show chat UI
        const contextSession = chatContext.sessions.find(session => session.id === id);
        if (contextSession) {
            chatContext.setSelectedSession(id);
            chatContext.setActiveWindowGrid(WindowGrid.active);
        }
    }

    // Helper to get the preview text for a message
    function getMessagePreview(text: string): string {
        return text.length > 30 ? text.substring(0, 30) + "..." : text;
    }

    console.log("chatContext", chatContext.sessions)

    return (
        <div className={[
            "advanced-sidebar-container",
            "sidebar-area",
            isExpanded ? "is-open" : undefined,
        ].filter(Boolean).join(" ")}
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
                <div className="chat-sessions-container">
                    <div className="sessions-list">
                        {chatContext.sessions.length === 0 ? (
                            <div className="empty-sessions">No chats</div>
                        ) : (
                            <>
                                <div style={{ fontWeight: 600, fontSize: '12px' }} >Recent Chats</div>
                                {[...chatContext.sessions]
                                    .filter(session => session.messages.length > 0)
                                    .sort((a, b) => new Date(b.creationDate).getTime() - new Date(a.creationDate).getTime())
                                    .map(session => {
                                        const formattedDate = dayjs(session.creationDate).format("YYYY-MM-DD");
                                        const timeWithSpace = dayjs(session.creationDate).format("HH:mm");
                                        const offset = dayjs(session.creationDate).format("Z");
                                        return (
                                            <div key={session.id} className="session-container">
                                                <CommonButton
                                                    className={[
                                                        "session-button",
                                                        chatContext.selectedSession?.id === session.id ? "active" : undefined
                                                    ].filter(Boolean).join(" ")}
                                                    noBackground
                                                    onClick={() => { handleSessionClick(session.id); }}
                                                >
                                                    <div className="session-icon">
                                                        {/* Fix for SVGComment error - use a different icon that exists */}
                                                        <ChatbotIcons.SVGClipboard />
                                                    </div>
                                                    <div className="session-details">
                                                        {/* <span className="session-title">{session.label || "Chat session"}</span> */}
                                                        <span className="session-preview">
                                                            {session.messages.length > 0
                                                                ? getMessagePreview(session.messages[session.messages.length - 1].text)
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
                                        )
                                    })
                                }
                            </>
                        )}
                    </div>
                </div>

                {/* Projects Container - Kept but hidden by default */}
                <div className="projects-label-container" style={{ display: "none" }}>
                    <span>Projects</span>
                    <CommonButton noBackground title="Add new Project">
                        <ChatbotIcons.SVGAdd />
                    </CommonButton>
                </div>

                <div className="projects-list" style={{ display: "none" }}>
                    <div className="projects-group-container">
                        {displayFolders.map(folder =>
                            <div key={folder.id} className="project-container">
                                <CommonButton
                                    className={["project-label", selectedProject === folder.id ? "active" : undefined].filter(Boolean).join(" ")}
                                    noBackground
                                    onClick={() => { handleProjectClick(folder.id); }}
                                >
                                    <ChatbotIcons.SVGFolder />
                                    <span>{folder.label}</span>
                                </CommonButton>
                                <div className={["sessions-container", selectedProject === folder.id ? "open" : undefined].filter(Boolean).join(" ")}>
                                    <div className="sessions-accordion">
                                        {folder.sessions.map(session =>
                                            <div className="session-wrapper" key={session.id}>
                                                <CommonButton
                                                    className={["session", selectedSession === session.id ? "active" : undefined].filter(Boolean).join(" ")}
                                                    noBackground
                                                    onClick={() => { handleSessionClick(session.id); }}
                                                >
                                                    <span>{session.label}</span>
                                                </CommonButton>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="bottom-container">
                    <CommonButton
                        noBackground
                        className="settings-button"
                    >
                        <ChatbotIcons.SVGSettings />
                        <span>Settings</span>
                    </CommonButton>
                </div>
            </div>
        </div>
    );
}