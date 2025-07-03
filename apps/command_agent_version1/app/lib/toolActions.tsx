"use server";

import type {
	Tool,
	ToolCategory,
	ToolCategoryCreate,
	ToolCategoryUpdate,
	MCPServer,
	MCPServerCreate,
	MCPServerUpdate,
	ToolExecutionRequest,
	ToolExecutionResponse,
	ChatCompletionToolParam,
} from "./interfaces";
import { toolToOpenAISchema } from "./utils";
import { BACKEND_URL } from "./constants";

// Comprehensive tools API
export async function fetchAllToolsNew(
	skip = 0,
	limit = 100,
	toolType?: "local" | "remote" | "mcp",
	categoryId?: string,
	isActive?: boolean,
	isAvailable?: boolean
): Promise<Tool[]> {
	const url = new URL(`${BACKEND_URL}api/tools/`);

	// Add query parameters
	url.searchParams.set("skip", skip.toString());
	url.searchParams.set("limit", limit.toString());
	if (toolType) url.searchParams.set("tool_type", toolType);
	if (categoryId) url.searchParams.set("category_id", categoryId);
	if (isActive !== undefined) url.searchParams.set("is_active", isActive.toString());
	if (isAvailable !== undefined) url.searchParams.set("is_available", isAvailable.toString());

	const response = await fetch(url);
	if (!response.ok) throw new Error("Failed to fetch tools");

	const tools: unknown = await response.json();
	if (Array.isArray(tools)) {
		return tools as Tool[];
	}
	throw new Error("Invalid data type - expected tools array");
}

// Fetch available tools only
export async function fetchAvailableTools(): Promise<Tool[]> {
	const url = new URL(`${BACKEND_URL}api/tools/available`);

	const response = await fetch(url);
	if (!response.ok) throw new Error("Failed to fetch available tools");

	const tools: unknown = await response.json();
	if (Array.isArray(tools)) {
		return tools as Tool[];
	}
	throw new Error("Invalid data type - expected tools array");
}

// Get specific tool by ID
export async function fetchToolById(toolId: string): Promise<Tool> {
	const url = new URL(`${BACKEND_URL}api/tools/${toolId}`);

	const response = await fetch(url);
	if (!response.ok) {
		if (response.status === 404) {
			throw new Error("Tool not found");
		}
		throw new Error("Failed to fetch tool");
	}

	return await response.json() as Tool;
}

// Update tool
export async function updateTool(toolId: string, update: Partial<Tool>): Promise<Tool> {
	const url = new URL(`${BACKEND_URL}api/tools/${toolId}`);

	const response = await fetch(url, {
		method: "PUT",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify(update),
	});

	if (!response.ok) {
		if (response.status === 404) {
			throw new Error("Tool not found");
		}
		throw new Error("Failed to update tool");
	}

	return await response.json() as Tool;
}

// Delete tool
export async function deleteTool(toolId: string): Promise<void> {
	const url = new URL(`${BACKEND_URL}api/tools/${toolId}`);

	const response = await fetch(url, {
		method: "DELETE",
	});

	if (!response.ok) {
		if (response.status === 404) {
			throw new Error("Tool not found");
		}
		throw new Error("Failed to delete tool");
	}
}

// Tool Categories API
export async function fetchToolCategories(
	skip = 0,
	limit = 100
): Promise<ToolCategory[]> {
	const url = new URL(`${BACKEND_URL}api/tools/categories`);
	url.searchParams.set("skip", skip.toString());
	url.searchParams.set("limit", limit.toString());

	const response = await fetch(url);
	if (!response.ok) throw new Error("Failed to fetch tool categories");

	const categories: unknown = await response.json();
	if (Array.isArray(categories)) {
		return categories as ToolCategory[];
	}
	throw new Error("Invalid data type - expected categories array");
}

export async function fetchToolCategoryById(categoryId: string): Promise<ToolCategory> {
	const url = new URL(`${BACKEND_URL}api/tools/categories/${categoryId}`);

	const response = await fetch(url);
	if (!response.ok) {
		if (response.status === 404) {
			throw new Error("Tool category not found");
		}
		throw new Error("Failed to fetch tool category");
	}

	return await response.json() as ToolCategory;
}

export async function createToolCategory(category: ToolCategoryCreate): Promise<ToolCategory> {
	const url = new URL(`${BACKEND_URL}api/tools/categories`);

	const response = await fetch(url, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify(category),
	});

	if (!response.ok) {
		if (response.status === 400) {
			throw new Error("Tool category with this name already exists");
		}
		throw new Error("Failed to create tool category");
	}

	return await response.json() as ToolCategory;
}

export async function updateToolCategory(
	categoryId: string,
	update: ToolCategoryUpdate
): Promise<ToolCategory> {
	const url = new URL(`${BACKEND_URL}api/tools/categories/${categoryId}`);

	const response = await fetch(url, {
		method: "PUT",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify(update),
	});

	if (!response.ok) {
		if (response.status === 404) {
			throw new Error("Tool category not found");
		}
		throw new Error("Failed to update tool category");
	}

	return await response.json() as ToolCategory;
}

export async function deleteToolCategory(categoryId: string): Promise<void> {
	const url = new URL(`${BACKEND_URL}api/tools/categories/${categoryId}`);

	const response = await fetch(url, {
		method: "DELETE",
	});

	if (!response.ok) {
		if (response.status === 404) {
			throw new Error("Tool category not found");
		}
		throw new Error("Failed to delete tool category");
	}
}

// MCP Servers API
export async function fetchMCPServers(
	skip = 0,
	limit = 100,
	status?: string
): Promise<MCPServer[]> {
	const url = new URL(`${BACKEND_URL}api/tools/mcp-servers`);
	url.searchParams.set("skip", skip.toString());
	url.searchParams.set("limit", limit.toString());
	if (status) url.searchParams.set("status", status);

	const response = await fetch(url);
	if (!response.ok) throw new Error("Failed to fetch MCP servers");

	const servers: unknown = await response.json();
	if (Array.isArray(servers)) {
		return servers as MCPServer[];
	}
	throw new Error("Invalid data type - expected servers array");
}

export async function fetchActiveMCPServers(): Promise<MCPServer[]> {
	const url = new URL(`${BACKEND_URL}api/tools/mcp-servers/active`);

	const response = await fetch(url);
	if (!response.ok) throw new Error("Failed to fetch active MCP servers");

	const servers: unknown = await response.json();
	if (Array.isArray(servers)) {
		return servers as MCPServer[];
	}
	throw new Error("Invalid data type - expected servers array");
}

export async function fetchMCPServerById(serverId: string): Promise<MCPServer> {
	const url = new URL(`${BACKEND_URL}api/tools/mcp-servers/${serverId}`);

	const response = await fetch(url);
	if (!response.ok) {
		if (response.status === 404) {
			throw new Error("MCP server not found");
		}
		throw new Error("Failed to fetch MCP server");
	}

	return await response.json() as MCPServer;
}

export async function createMCPServer(server: MCPServerCreate): Promise<MCPServer> {
	const url = new URL(`${BACKEND_URL}api/tools/mcp-servers`);

	const response = await fetch(url, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify(server),
	});

	if (!response.ok) {
		if (response.status === 400) {
			throw new Error("MCP server with this name already exists");
		}
		throw new Error("Failed to create MCP server");
	}

	return await response.json() as MCPServer;
}

export async function updateMCPServer(
	serverId: string,
	update: MCPServerUpdate
): Promise<MCPServer> {
	const url = new URL(`${BACKEND_URL}api/tools/mcp-servers/${serverId}`);

	const response = await fetch(url, {
		method: "PUT",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify(update),
	});

	if (!response.ok) {
		if (response.status === 404) {
			throw new Error("MCP server not found");
		}
		throw new Error("Failed to update MCP server");
	}

	return await response.json() as MCPServer;
}

export async function deleteMCPServer(serverId: string): Promise<void> {
	const url = new URL(`${BACKEND_URL}api/tools/mcp-servers/${serverId}`);

	const response = await fetch(url, {
		method: "DELETE",
	});

	if (!response.ok) {
		if (response.status === 404) {
			throw new Error("MCP server not found");
		}
		throw new Error("Failed to delete MCP server");
	}
}

// MCP Server Health Management
export async function updateMCPServerHealth(serverId: string, isHealthy: boolean): Promise<{ message: string; status: string }> {
	const url = new URL(`${BACKEND_URL}api/tools/mcp-servers/${serverId}/health`);

	const response = await fetch(url, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({ is_healthy: isHealthy }),
	});

	if (!response.ok) {
		if (response.status === 404) {
			throw new Error("MCP server not found");
		}
		throw new Error("Failed to update MCP server health");
	}

	const res = await response.json() as unknown;
	if (typeof res === "object" && res !== null && "message" in res && "status" in res) {
		return res as { message: string; status: string };
	}
	throw new Error("Invalid data type - expected health update response");
}

// Tool Execution API
export async function executeTool(
	toolId: string,
	executionRequest: ToolExecutionRequest
): Promise<ToolExecutionResponse> {
	const url = new URL(`${BACKEND_URL}api/tools/${toolId}/execute`);

	const response = await fetch(url, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify(executionRequest),
	});

	if (!response.ok) {
		if (response.status === 404) {
			throw new Error("Tool not found");
		} else if (response.status === 400) {
			throw new Error("Tool is not available for execution");
		}
		throw new Error("Failed to execute tool");
	}

	return await response.json() as ToolExecutionResponse;
}

// Get available tools as OpenAI schemas
export async function fetchToolSchemasAsArray(): Promise<ChatCompletionToolParam[]> {
	const tools = await fetchAvailableTools();
	return tools.map(toolToOpenAISchema);
}


