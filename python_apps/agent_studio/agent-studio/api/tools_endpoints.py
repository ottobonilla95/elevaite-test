"""
Tools API endpoints for Agent Studio
Provides access to all available tools that agents can use
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from pydantic import BaseModel

# Import tools from agents module
from agents.tools import tool_store, tool_schemas

router = APIRouter(prefix="/api/tools", tags=["tools"])


class ToolInfo(BaseModel):
    """Tool information model"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function_type: str = "function"


class ToolsResponse(BaseModel):
    """Response model for tools endpoints"""
    tools: List[ToolInfo]
    total_count: int


@router.get("/", response_model=ToolsResponse)
def get_all_tools():
    """
    Get all available tools that agents can use.
    
    Returns:
        ToolsResponse: List of all available tools with their schemas
    """
    try:
        tools_list = []
        
        for tool_name, tool_schema in tool_schemas.items():
            # Extract tool information from OpenAI schema
            function_info = tool_schema.get("function", {})
            
            tool_info = ToolInfo(
                name=tool_name,
                description=function_info.get("description", "No description available"),
                parameters=function_info.get("parameters", {}),
                function_type=tool_schema.get("type", "function")
            )
            tools_list.append(tool_info)
        
        return ToolsResponse(
            tools=tools_list,
            total_count=len(tools_list)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tools: {str(e)}")


@router.get("/{tool_name}")
def get_tool_by_name(tool_name: str):
    """
    Get detailed information about a specific tool.
    
    Args:
        tool_name: Name of the tool to retrieve
        
    Returns:
        Dict: Detailed tool information including schema and function reference
    """
    if tool_name not in tool_schemas:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    try:
        tool_schema = tool_schemas[tool_name]
        tool_function = tool_store.get(tool_name)
        
        # Get function docstring and signature info
        function_info = {
            "name": tool_name,
            "schema": tool_schema,
            "available": tool_function is not None,
            "docstring": getattr(tool_function, "__doc__", None) if tool_function else None,
        }
        
        return function_info
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tool '{tool_name}': {str(e)}")


@router.get("/categories/list")
def get_tool_categories():
    """
    Get tools organized by categories based on their functionality.
    
    Returns:
        Dict: Tools organized by categories
    """
    try:
        categories = {
            "data": [],
            "web": [],
            "utility": [],
            "communication": [],
            "search": [],
            "other": []
        }
        
        # Categorize tools based on their names and descriptions
        for tool_name, tool_schema in tool_schemas.items():
            function_info = tool_schema.get("function", {})
            description = function_info.get("description", "").lower()
            
            tool_info = {
                "name": tool_name,
                "description": function_info.get("description", "No description available")
            }
            
            # Categorize based on tool name and description
            if any(keyword in tool_name.lower() for keyword in ["customer", "order", "location", "add_customer"]):
                categories["data"].append(tool_info)
            elif any(keyword in tool_name.lower() for keyword in ["web", "url", "markdown"]):
                categories["web"].append(tool_info)
            elif any(keyword in tool_name.lower() for keyword in ["search", "query", "retriever"]):
                categories["search"].append(tool_info)
            elif any(keyword in tool_name.lower() for keyword in ["print", "console"]):
                categories["communication"].append(tool_info)
            elif any(keyword in tool_name.lower() for keyword in ["add", "weather", "forecast"]):
                categories["utility"].append(tool_info)
            else:
                categories["other"].append(tool_info)
        
        # Add category counts
        result = {}
        for category, tools in categories.items():
            result[category] = {
                "tools": tools,
                "count": len(tools)
            }
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error categorizing tools: {str(e)}")


@router.get("/schemas/openai")
def get_openai_schemas():
    """
    Get all tool schemas in OpenAI function calling format.
    This is useful for agents that need to register tools.
    
    Returns:
        Dict: All tool schemas in OpenAI format
    """
    try:
        return {
            "schemas": tool_schemas,
            "total_count": len(tool_schemas),
            "format": "openai_function_calling"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving OpenAI schemas: {str(e)}")


@router.get("/health")
def tools_health_check():
    """
    Health check endpoint for tools system.
    Verifies that all tools are properly loaded and accessible.
    
    Returns:
        Dict: Health status of tools system
    """
    try:
        # Check if tool_store and tool_schemas are properly loaded
        store_count = len(tool_store) if tool_store else 0
        schema_count = len(tool_schemas) if tool_schemas else 0
        
        # Check for mismatches between store and schemas
        missing_in_store = []
        missing_in_schemas = []
        
        if tool_schemas and tool_store:
            for tool_name in tool_schemas:
                if tool_name not in tool_store:
                    missing_in_store.append(tool_name)
            
            for tool_name in tool_store:
                if tool_name not in tool_schemas:
                    missing_in_schemas.append(tool_name)
        
        health_status = {
            "status": "healthy" if store_count > 0 and schema_count > 0 else "unhealthy",
            "tool_store_count": store_count,
            "tool_schemas_count": schema_count,
            "tools_available": store_count > 0 and schema_count > 0,
            "issues": {
                "missing_in_store": missing_in_store,
                "missing_in_schemas": missing_in_schemas
            }
        }
        
        return health_status
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking tools health: {str(e)}")
