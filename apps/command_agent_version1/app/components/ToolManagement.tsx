"use client";

import React, { useState, useEffect } from "react";
import {
    Wrench,
    Server,
    Tag,
    Plus,
    Edit,
    Trash2,
    Play,
    Pause,
    RefreshCw,
    Filter,
    Search
} from "lucide-react";
import { useTools } from "../ui/contexts/ToolsContext";
import {
    Tool,
    ToolCategory,
    MCPServer,
    ToolCategoryCreate,
    MCPServerCreate
} from "../lib/interfaces";
import {
    createToolCategory,
    updateToolCategory,
    deleteToolCategory,
    createMCPServer,
    updateMCPServer,
    deleteMCPServer,
    fetchMCPServers
} from "../lib/tool_actions";

interface ToolManagementProps {
    className?: string;
}

export const ToolManagement: React.FC<ToolManagementProps> = ({ className = "" }) => {
    const {
        tools,
        categories,
        isLoading,
        error,
        getToolsByCategory,
        refetchTools,
        getAvailableTools
    } = useTools();

    const [activeTab, setActiveTab] = useState<"tools" | "categories" | "servers">("tools");
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedCategory, setSelectedCategory] = useState<string>("");
    const [mcpServers, setMcpServers] = useState<MCPServer[]>([]);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [editingItem, setEditingItem] = useState<any>(null);

    // Load MCP servers
    useEffect(() => {
        const loadMcpServers = async () => {
            try {
                const servers = await fetchMCPServers();
                setMcpServers(servers);
            } catch (err) {
                console.error("Failed to load MCP servers:", err);
            }
        };
        loadMcpServers();
    }, []);

    // Filter tools based on search and category
    const filteredTools = tools.filter(tool => {
        const matchesSearch = tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (tool.description?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);
        const matchesCategory = !selectedCategory || tool.category_id === selectedCategory;
        return matchesSearch && matchesCategory;
    });

    const handleCreateCategory = async (categoryData: ToolCategoryCreate) => {
        try {
            await createToolCategory(categoryData);
            await refetchTools();
            setShowCreateModal(false);
        } catch (err) {
            console.error("Failed to create category:", err);
        }
    };

    const handleCreateMCPServer = async (serverData: MCPServerCreate) => {
        try {
            await createMCPServer(serverData);
            const servers = await fetchMCPServers();
            setMcpServers(servers);
            setShowCreateModal(false);
        } catch (err) {
            console.error("Failed to create MCP server:", err);
        }
    };

    const renderToolCard = (tool: Tool) => (
        <div key={tool.tool_id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                        <Wrench className="w-4 h-4 text-blue-600" />
                        <h3 className="font-medium text-gray-900">{tool.display_name || tool.name}</h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${tool.tool_type === "local"
                            ? "bg-green-100 text-green-800"
                            : "bg-blue-100 text-blue-800"
                            }`}>
                            {tool.tool_type}
                        </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{tool.description}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>Version: {tool.version}</span>
                        <span>Timeout: {tool.timeout_seconds}s</span>
                        {tool.usage_count && <span>Used: {tool.usage_count} times</span>}
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${tool.is_active && tool.is_available
                        ? "bg-green-500"
                        : "bg-red-500"
                        }`} />
                    <span className="text-xs text-gray-500">
                        {tool.is_active && tool.is_available ? "Active" : "Inactive"}
                    </span>
                </div>
            </div>
        </div>
    );

    const renderCategoryCard = (category: ToolCategory) => {
        const toolCount = getToolsByCategory(category.category_id).length;
        return (
            <div key={category.category_id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                            <Tag className="w-4 h-4 text-purple-600" />
                            <h3 className="font-medium text-gray-900">{category.name}</h3>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{category.description}</p>
                        <div className="text-xs text-gray-500">
                            {toolCount} tool{toolCount !== 1 ? 's' : ''}
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setEditingItem(category)}
                            className="p-1 text-gray-400 hover:text-gray-600"
                        >
                            <Edit className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>
        );
    };

    const renderMCPServerCard = (server: MCPServer) => (
        <div key={server.server_id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                        <Server className="w-4 h-4 text-indigo-600" />
                        <h3 className="font-medium text-gray-900">{server.name}</h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${server.status === "active"
                            ? "bg-green-100 text-green-800"
                            : server.status === "error"
                                ? "bg-red-100 text-red-800"
                                : "bg-gray-100 text-gray-800"
                            }`}>
                            {server.status}
                        </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{server.description}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>{server.protocol}://{server.host}:{server.port}</span>
                        {server.last_health_check && (
                            <span>Last check: {new Date(server.last_health_check).toLocaleString()}</span>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setEditingItem(server)}
                        className="p-1 text-gray-400 hover:text-gray-600"
                    >
                        <Edit className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );

    if (isLoading) {
        return (
            <div className={`flex items-center justify-center p-8 ${className}`}>
                <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
                <span className="ml-2 text-gray-600">Loading tools...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className={`p-8 text-center ${className}`}>
                <div className="text-red-600 mb-2">Error loading tools</div>
                <div className="text-sm text-gray-500">{error}</div>
                <button
                    onClick={refetchTools}
                    className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className={`bg-gray-50 ${className}`}>
            {/* Header */}
            <div className="bg-white border-b border-gray-200 p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Tool Management</h1>
                        <p className="text-gray-600">Manage tools, categories, and MCP servers</p>
                    </div>
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                        <Plus className="w-4 h-4" />
                        Create New
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex gap-4 mt-6">
                    {[
                        { key: "tools", label: "Tools", count: tools.length },
                        { key: "categories", label: "Categories", count: categories.length },
                        { key: "servers", label: "MCP Servers", count: mcpServers.length }
                    ].map(tab => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key as any)}
                            className={`px-4 py-2 rounded-md text-sm font-medium ${activeTab === tab.key
                                ? "bg-blue-100 text-blue-700"
                                : "text-gray-600 hover:text-gray-900"
                                }`}
                        >
                            {tab.label} ({tab.count})
                        </button>
                    ))}
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white border-b border-gray-200 p-4">
                <div className="flex gap-4">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                    {activeTab === "tools" && (
                        <select
                            value={selectedCategory}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="">All Categories</option>
                            {categories.map(category => (
                                <option key={category.category_id} value={category.category_id}>
                                    {category.name}
                                </option>
                            ))}
                        </select>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="p-6">
                <div className="grid gap-4">
                    {activeTab === "tools" && filteredTools.map(renderToolCard)}
                    {activeTab === "categories" && categories.map(renderCategoryCard)}
                    {activeTab === "servers" && mcpServers.map(renderMCPServerCard)}
                </div>

                {/* Empty state */}
                {((activeTab === "tools" && filteredTools.length === 0) ||
                    (activeTab === "categories" && categories.length === 0) ||
                    (activeTab === "servers" && mcpServers.length === 0)) && (
                        <div className="text-center py-12">
                            <div className="text-gray-400 mb-2">
                                {activeTab === "tools" && <Wrench className="w-12 h-12 mx-auto" />}
                                {activeTab === "categories" && <Tag className="w-12 h-12 mx-auto" />}
                                {activeTab === "servers" && <Server className="w-12 h-12 mx-auto" />}
                            </div>
                            <h3 className="text-lg font-medium text-gray-900 mb-1">
                                No {activeTab} found
                            </h3>
                            <p className="text-gray-500">
                                {searchTerm ? "Try adjusting your search criteria" : `Create your first ${activeTab.slice(0, -1)}`}
                            </p>
                        </div>
                    )}
            </div>
        </div>
    );
};

export default ToolManagement;
