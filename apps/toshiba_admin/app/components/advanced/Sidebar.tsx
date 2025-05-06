"use client";
import { ChatbotIcons, CommonButton, CommonInput, ElevaiteIcons, SimpleInput } from "@repo/ui/components";
import dayjs from "dayjs";
import isBetween from "dayjs/plugin/isBetween";
import { useEffect, useState } from "react";
import { useChat } from "../../ui/contexts/ChatContext";
import "./Sidebar.scss";
import { WindowGrid } from "../../lib/interfaces";

dayjs.extend(isBetween);

interface RecentChat {
    id: string;
    label: string;
    date: string;
    status: string;
}
interface RecentsChatsList {
    label: string;
    chats: RecentChat[];
}

const testData: RecentChat[] = [
    {
        id: "case00001",
        label: "CASE200091",
        date: dayjs().subtract(3, "hours").toISOString(),
        status: "red",
    },
    {
        id: "case00002",
        label: "CASE204535",
        date: dayjs().subtract(7, "hours").toISOString(),
        status: "orange",
    },
    {
        id: "case00003",
        label: "CASE2654491",
        date: dayjs().subtract(2, "days").toISOString(),
        status: "red",
    },
    {
        id: "case00000",
        label: "CASE00000000",
        date: dayjs().subtract(5, "days").toISOString(),
        status: "green",
    },
];

export function Sidebar(): JSX.Element {
    const chatContext = useChat();
    const [isExpanded, setIsExpanded] = useState(false);
    const [displayRecents, setDisplayRecents] = useState<RecentsChatsList[]>([]);
    const [searchTerm, setSearchTerm] = useState("");


    useEffect(() => {
        setDisplayRecents(getDisplayRecents(testData, false));
    }, []); // Change the dependency array here to whatever variable you're getting from the context


    function toggleExpanded(): void {
        setIsExpanded(current => !current);
    }

    function handleCreate(): void {
        console.log("Create")
        chatContext.setActiveWindowGrid();
    }

    function handleDiscover(): void {
        chatContext.setActiveWindowGrid(WindowGrid.discover);
    }

    function handleDashboard(): void {
        chatContext.setActiveWindowGrid(WindowGrid.dashboard);
    }

    function handleAdvancedSearch(): void {
        console.log("Clicked advanced search");
    }

    function handleChatClick(id: string): void {
        console.log("Clicked chat:", id);
    }


    // Get the array of items and make them into an object that we can iterate on the return function
    // It will include separators with labels (and possible menu actions)
    function getDisplayRecents(chats: RecentChat[], hideEmptyCategories = true): RecentsChatsList[] {
        const now = dayjs();

        // Define time boundaries
        const sevenDaysAgo = now.subtract(7, "days");

        // Group items into categories
        const categories = {
            recent: chats.filter(item => dayjs(item.date).isSame(dayjs(), "day")),
            sevenDaysAgo: chats.filter(item => dayjs(item.date).isBetween(dayjs().startOf("day"), sevenDaysAgo, null, "()")),
        };

        // Build the result, sorting each category by date descending
        const result: RecentsChatsList[] = [
            { label: "Today", chats: categories.recent },
            { label: "Previous 7 days", chats: categories.sevenDaysAgo },
        ]
            .map(category => ({
                ...category,
                chats: category.chats.sort((a, b) => dayjs(b.date).diff(dayjs(a.date)))
            }))
            .filter(category => !hideEmptyCategories || category.chats.length > 0);

        return result;
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
                        <div className="button-label">Create New Chat</div>
                    </CommonButton>
                </div>
                <div className="sidebar-button-wrapper">
                    <CommonButton
                        onClick={handleDiscover}
                        title="Discover"
                        noBackground
                    >
                        <ChatbotIcons.SVGMenuDiscover />
                        <div className="button-label">Discover</div>
                    </CommonButton>
                </div>
                <div className="sidebar-button-wrapper">
                    <CommonButton
                        onClick={handleDashboard}
                        title="Dashboard"
                        noBackground
                    >
                        <ChatbotIcons.SVGMenuScorecard />
                        <div className="button-label">Dashboard</div>
                    </CommonButton>
                </div>

                <div className="separator" />

                {/* <div className="search-container">
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
                </div> */}

                <div className="recent-chats-container">
                    {displayRecents.map(recentGroup =>
                        <div className="recent-chats-group-container" key={recentGroup.label}>
                            <div className="chat-group-label">
                                {recentGroup.label}
                            </div>
                            <div className="chat-group-contents">
                                {recentGroup.chats.length === 0 ?
                                    <div className="empty-group">No chats</div>
                                    :
                                    recentGroup.chats.map(chat =>
                                        <SidebarSession
                                            key={chat.id}
                                            chat={chat}
                                            onClick={handleChatClick}
                                        />
                                    )
                                }
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}










interface SidebarSessionProps {
    chat: RecentChat;
    onClick: (id: string) => void;
}

function SidebarSession(props: SidebarSessionProps): JSX.Element {

    function handleClick(): void {
        props.onClick(props.chat.id);
    }

    return (
        <CommonButton
            className="sidebar-session-container"
            onClick={handleClick}
            noBackground
        >
            <div className="sidebar-session-contents">
                <div className="icon"><ChatbotIcons.SVGClipboard /></div>
                <div className="details">
                    <span className="title" title={props.chat.label}>{props.chat.label}</span>
                    <span className="date" title={props.chat.date ? dayjs(props.chat.date).format("ddd DD MMMM YYYY") : ""}>
                        {props.chat.date ? dayjs(props.chat.date).format("YYYY-MM-DD") : "-"}
                    </span>
                </div>
                <div className={["status", props.chat.status].filter(Boolean).join(" ")} title={props.chat.status} />
            </div>
        </CommonButton>
    );
}





