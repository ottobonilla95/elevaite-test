"use client";

import React from "react";
import { Edit } from "lucide-react";

type AgentType = "router" | "web_search" | "api" | "data" | "troubleshooting";

interface AgentPromptEditorProps {
    type: AgentType;
    onOpenFullEditor: () => void;
}

const AgentPromptEditor: React.FC<AgentPromptEditorProps> = ({
    onOpenFullEditor
}) => {
    return (
        <div className="mt-2">
            <button
                onClick={onOpenFullEditor}
                className="w-full flex items-center justify-center bg-blue-50 hover:bg-blue-100 text-blue-600 px-4 py-2 rounded-md text-sm font-medium"
                title="Edit Prompt"
            >
                <Edit className="w-4 h-4 mr-2" />
                Edit Prompt
            </button>
        </div>
    );
};

export default AgentPromptEditor;