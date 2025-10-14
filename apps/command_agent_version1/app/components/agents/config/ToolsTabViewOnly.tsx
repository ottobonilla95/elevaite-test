import { CommonButton, CommonModal, ElevaiteIcons } from "@repo/ui/components";
import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import { type AgentResponse, type Tool } from "../../../lib/interfaces";
import { useTools } from "../../../ui/contexts/ToolsContext";
import { getToolIcon } from "../iconUtils";
import "./ToolsTabViewOnly.scss";



interface ToolsTabViewOnlyProps {
    onDragStart: (
        event: React.DragEvent<HTMLElement>,
        agent?: AgentResponse,
        tool?: unknown,
    ) => void;
}

export function ToolsTabViewOnly(props: ToolsTabViewOnlyProps): JSX.Element {
    const { tools, isLoading } = useTools();
    const [displayTools, setDisplayTools] = useState<Tool[]>([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [titleToDisplay, setTitleToDisplay] = useState<string|undefined>();
    const [descriptionToDisplay, setDescriptionToDisplay] = useState<string|undefined>();


    useEffect(() => {
        setDisplayTools(
            tools.filter(tool => {
                const query = searchQuery.toLowerCase();
                return (
                    (tool.display_name?.toLowerCase().includes(query) ?? false) ||
                    tool.name.toLowerCase().includes(query) ||
                    tool.description.toLowerCase().includes(query)
                );
            })
        );
    }, [tools, searchQuery]);


    function handleSearch(term: string): void {
        setSearchQuery(term);
    }

    function handleClearSearch(): void {
        setSearchQuery("");
    }

    function handleToolClick(tool: Tool): void {
        setTitleToDisplay(tool.display_name ?? tool.name);
        setDescriptionToDisplay(tool.description);
    }

    function closeToolDisplay(): void {
        setTitleToDisplay(undefined);
        setDescriptionToDisplay(undefined);
    }

    function handleDragStart(event: React.DragEvent<HTMLButtonElement>, tool: Tool): void {
        props.onDragStart(event, undefined, tool);
    }

    function handleCreateTool() {
        console.log("Creating tool!");
    }



    return (
        <div className="tools-tab-container">

            <div className="tools-title">Tools</div>
            
            {/* Search Bar */}
            <div className="search-container">
                <Search size={16} className="search-icon" />
                <input
                    className="search-input"
                    type="text"
                    placeholder="Search tools..."
                    value={searchQuery}
                    onChange={(e) => { handleSearch(e.target.value); }}
                    disabled={isLoading}
                />
                <CommonButton onClick={handleClearSearch} noBackground className={["search-clear", searchQuery.length === 0 ? undefined : "needed"].filter(Boolean).join(" ")}>
                    <ElevaiteIcons.SVGXmark/>
                </CommonButton>
            </div>

            {/* <div className="tools-info">
                To attach a tool to an agent, select the agent from the canvas and click on the edit icon at its tools section.
            </div> */}

            <div className="tools-list-container">
                {isLoading ? 
                    <div className="tools-list-loading">
                        <span>Loading tools...</span>
                        <ElevaiteIcons.SVGSpinner/>
                    </div>
                    :
                    <>
                    {displayTools.map(tool => 
                        <button
                            key={tool.id}
                            onClick={() => { handleToolClick(tool); }}
                            className="tool-button"
                            type="button"
                            draggable
                            onDragStart={event => { handleDragStart(event, tool); }}
                        >
                            <div className="tool-button-content">
                                <div className="tool-button-icon">
                                    {getToolIcon(tool.name)}
                                </div>
                                <div className="tool-button-text">
                                    <span className="tool-button-title">{tool.display_name ?? tool.name}</span>
                                    <span className="tool-button-description" title={tool.description}>
                                        {tool.description}
                                    </span>
                                </div>
                            </div>
                        </button>
                    )}
                    </>
                }
            
            </div>

            <div className="create-tool-button-container">
                <CommonButton className="create-tool-button" onClick={handleCreateTool}>
                    Create new Tool
                </CommonButton>
            </div>


            {!titleToDisplay || !descriptionToDisplay ? undefined :
                <CommonModal
                    onClose={closeToolDisplay}
                >
                <div className="tools-description-wrapper">
                    <div className="tools-description-header">
                        <span className="tools-description-title">{titleToDisplay}</span>
                        <CommonButton onClick={closeToolDisplay} noBackground>
                            <ElevaiteIcons.SVGXmark />
                        </CommonButton>
                    </div>
                    <div className="tools-description-contents">
                        {descriptionToDisplay}
                    </div>
                </div>
                </CommonModal>
            }

        </div>
    );
}