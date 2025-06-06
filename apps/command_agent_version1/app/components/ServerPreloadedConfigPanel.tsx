import { fetchAllTools } from "../lib/actions";
import ConfigPanelWithPreloadedTools from "./ConfigPanelWithPreloadedTools";
import { AgentType } from "./type";

interface ServerPreloadedConfigPanelProps {
    agentName: string;
    agentType: AgentType;
    description: string;
    onEditPrompt: () => void;
    onSave?: (configData: any) => void;
    onClose?: () => void;
    onNameChange?: (newName: string) => void;
}

export default async function ServerPreloadedConfigPanel(props: ServerPreloadedConfigPanelProps) {
    // Pre-load tools on the server
    let preloadedTools = [];
    try {
        const toolsResponse = await fetchAllTools();
        preloadedTools = toolsResponse.tools;
    } catch (error) {
        console.error("Failed to pre-load tools on server:", error);
        // Fallback to empty array if server-side fetch fails
        preloadedTools = [];
    }

    return (
        <ConfigPanelWithPreloadedTools
            {...props}
            preloadedTools={preloadedTools}
        />
    );
}
