"use client";
import { ChatbotIcons, CommonButton, ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import dayjs from "dayjs";
import isBetween from "dayjs/plugin/isBetween";
import { useEffect, useState } from "react";
import { useChat } from "../../ui/contexts/ChatContext";
import "./ProjectSidebar.scss";

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

export function ProjectSidebar(): JSX.Element {
    const chatContext = useChat();
    const [isExpanded, setIsExpanded] = useState(false);
    const [displayFolders, setDisplayFolders] = useState<ProjectFolder[]>([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedProject, setSelectedProject] = useState<string|undefined>();
    const [selectedSession, setSelectedSession] = useState<string|undefined>();



    useEffect(() => {
        setDisplayFolders(testData);
    }, []); // Change the dependency array here to whatever variable you're getting from the context


    function toggleExpanded(): void {
        setIsExpanded(current => !current);
    }

    function handleCreate(): void {
        console.log("Create")
        chatContext.setActiveWindowGrid();
    }

    function handleAdvancedSearch(): void {
        console.log("Clicked advanced search");
    }

    function handleProjectClick(id: string): void {
        setSelectedProject(id);
    }

    function handleSessionClick(id: string): void {
        setSelectedSession(id);
    }




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
                        <ElevaiteIcons.SVGSideArrow/>
                    </CommonButton>
                </div>

                <div className="separator"/>

                <div className="sidebar-button-wrapper">
                    <CommonButton
                        onClick={handleCreate}
                        className="create"
                        title="Create New Chat"
                    >
                        <ChatbotIcons.SVGMenuCreate/>
                        <div className="button-label">Create New Chat</div>
                    </CommonButton>
                </div>

                <div className="separator"/>

                <div className="search-container">
                    <SimpleInput
                        value={searchTerm}
                        onChange={setSearchTerm}
                        className="search-field"
                        leftIcon={<ElevaiteIcons.SVGMagnifyingGlass/>}
                        placeholder="Search..."
                    />
                    <CommonButton
                        className="advanced-search-button"
                        onClick={handleAdvancedSearch}
                        noBackground
                    >
                        Advanced Search
                    </CommonButton>
                </div>
                
                <div className="projects-label-container">
                    <span>Projects</span>
                    <CommonButton noBackground title="Add new Project">
                        <ChatbotIcons.SVGAdd/>
                    </CommonButton>
                </div>

                <div className="projects-list">
                    <div className="projects-group-container">
                        {displayFolders.map(folder => 
                            <div key={folder.id} className="project-container">
                                <CommonButton
                                    className={["project-label", selectedProject === folder.id ? "active" : undefined].filter(Boolean).join(" ")}
                                    noBackground
                                    onClick={() => { handleProjectClick(folder.id); }}
                                >
                                    <ChatbotIcons.SVGFolder/>
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
                        <ChatbotIcons.SVGSettings/>
                        <span>Settings</span>
                    </CommonButton>
                </div>
            </div>
        </div>
    );
}












