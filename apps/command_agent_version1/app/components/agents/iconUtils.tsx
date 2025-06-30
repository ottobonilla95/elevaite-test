import { Router, Globe, Database, Link2, Wrench, Zap, Search, Code, FileText, Calculator, Mail } from "lucide-react";
import { type AgentType } from "../../lib/interfaces";

// Get the appropriate icon based on agent type
export function getAgentIcon(_type: AgentType): JSX.Element {
    switch (_type) {
        case "router":
            return <Router size={20} className="text-blue-600" />;
        case "web_search":
            return <Globe size={20} className="text-blue-600" />;
        case "api":
            return <Link2 size={20} className="text-blue-600" />;
        case "data":
            return <Database size={20} className="text-blue-600" />;
        case "troubleshooting":
            return <Wrench size={20} className="text-blue-600" />;
        default:
            return <Router size={20} className="text-blue-600" />;
    }
};

// Get icon for tool - dynamic mapping based on tool functionality
export function getToolIcon(toolName: string): JSX.Element {
    const _name = toolName.toLowerCase();

    // Map icons based on keywords in tool names
    if (_name.includes('web') || _name.includes('search')) {
        return <Search size={16} className="text-orange-500" />;
    } else if (_name.includes('database') || _name.includes('data')) {
        return <Database size={16} className="text-orange-500" />;
    } else if (_name.includes('api') || _name.includes('http') || _name.includes('link')) {
        return <Link2 size={16} className="text-orange-500" />;
    } else if (_name.includes('code') || _name.includes('execution')) {
        return <Code size={16} className="text-orange-500" />;
    } else if (_name.includes('file') || _name.includes('document')) {
        return <FileText size={16} className="text-orange-500" />;
    } else if (_name.includes('math') || _name.includes('calculate')) {
        return <Calculator size={16} className="text-orange-500" />;
    } else if (_name.includes('mail') || _name.includes('email')) {
        return <Mail size={16} className="text-orange-500" />;
    }
    // Default icon for unknown tools
    return <Zap size={16} className="text-orange-500" />;

};

// Clean subtitle text
export function getSubtitle(_type: AgentType): string {
    if (_type === "web_search") return "web search";
    return _type.replace('_', ' ');
};



export function SidebarCollapseIcon(): JSX.Element {
    return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <g opacity="0.8">
                <path d="M18 17L13 12L18 7M11 17L6 12L11 7" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </g>
        </svg>
    );
}

export function SidebarExpandIcon(): JSX.Element {
    return (
        <svg width="14" height="12" viewBox="0 0 14 12" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M1 11L6 6L1 1M8 11L13 6L8 1" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
    );
}