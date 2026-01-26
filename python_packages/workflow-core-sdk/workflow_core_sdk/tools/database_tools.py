"""
Database Tools (ported from Agent Studio)

These tools provide mock implementations for Redis cache and PostgreSQL database operations.
In production, these would connect to actual database instances.

Environment variables:
- REDIS_URL: Redis connection URL (optional, uses mock data if not provided)
- POSTGRES_URL: PostgreSQL connection URL (optional, uses mock data if not provided)
"""

from __future__ import annotations

import json
from typing import Optional

from .decorators import function_schema


@function_schema
def redis_cache_operation(
    operation: str, key: str, value: Optional[str] = None, ttl: Optional[int] = None
) -> str:
    """
    Perform Redis cache operations for storing and retrieving data.

    Args:
        operation: The Redis operation to perform ('get', 'set', 'delete', 'exists', 'keys')
        key: The Redis key to operate on
        value: The value to set (required for 'set' operation)
        ttl: Time to live in seconds for 'set' operation (optional)

    Returns:
        str: Result of the Redis operation

    Examples:
        redis_cache_operation("set", "campaign:nike:performance", '{"ctr": 0.045, "clicks": 15420}', 3600)
        redis_cache_operation("get", "campaign:nike:performance")
        redis_cache_operation("delete", "campaign:nike:performance")
        redis_cache_operation("keys", "campaign:*")
        redis_cache_operation("exists", "user:session:12345")
    """
    # Mock implementation - in real scenario this would connect to Redis
    print(f"Redis operation: {operation} on key: {key}")

    if operation == "set":
        if value is None:
            return "Error: Value is required for SET operation"
        ttl_info = f" with TTL {ttl}s" if ttl else ""
        print(f"Setting key '{key}' = '{value}'{ttl_info}")
        return f"Successfully set key '{key}' in Redis{ttl_info}"

    elif operation == "get":
        # Mock cached data
        mock_cache = {
            "campaign:nike:performance": '{"ctr": 0.045, "clicks": 15420, "impressions": 342000}',
            "campaign:cocacola:metrics": '{"ctr": 0.038, "clicks": 12800, "impressions": 337000}',
            "user:session:12345": '{"user_id": 12345, "login_time": "2024-01-15T10:30:00Z"}',
            "targeting:config:tech_professionals": '{"age_range": ["25-44"], "interests": ["Technology"]}',
        }

        if key in mock_cache:
            return f"Retrieved from Redis - Key: '{key}', Value: {mock_cache[key]}"
        else:
            return f"Key '{key}' not found in Redis cache"

    elif operation == "delete":
        print(f"Deleting key '{key}' from Redis")
        return f"Successfully deleted key '{key}' from Redis"

    elif operation == "exists":
        # Mock existence check
        existing_keys = [
            "campaign:nike:performance",
            "user:session:12345",
            "targeting:config:tech_professionals",
        ]
        exists = key in existing_keys
        return f"Key '{key}' {'exists' if exists else 'does not exist'} in Redis"

    elif operation == "keys":
        # Mock pattern matching
        mock_keys = [
            "campaign:nike:performance",
            "campaign:cocacola:metrics",
            "campaign:disney:analytics",
            "user:session:12345",
            "targeting:config:tech_professionals",
        ]

        if "*" in key:
            pattern = key.replace("*", "")
            matching_keys = [k for k in mock_keys if k.startswith(pattern)]
            return f"Keys matching pattern '{key}': {matching_keys}"
        else:
            return f"Exact key search: {[key] if key in mock_keys else []}"

    else:
        return f"Error: Unsupported Redis operation '{operation}'. Supported: get, set, delete, exists, keys"


@function_schema
def postgres_query(
    query_type: str,
    table: str,
    conditions: Optional[str] = None,
    data: Optional[str] = None,
    limit: Optional[int] = 10,
) -> str:
    """
    Perform PostgreSQL database operations for campaign and user data.

    Args:
        query_type: Type of SQL operation ('select', 'insert', 'update', 'delete', 'count')
        table: Database table name (e.g., 'campaigns', 'users', 'targeting_configs', 'performance_metrics')
        conditions: WHERE clause conditions (e.g., 'brand = "nike" AND season = "summer"')
        data: JSON string with data for insert/update operations
        limit: Maximum number of results for select queries (default: 10)

    Returns:
        str: Result of the database operation

    Examples:
        postgres_query("select", "campaigns", "brand = 'nike' AND conversion_rate > 0.04", limit=5)
        postgres_query("insert", "campaigns", data='{"name": "Summer Campaign", "brand": "nike", "budget": 25000}')
        postgres_query("update", "campaigns", "id = 123", '{"status": "completed", "end_date": "2024-01-15"}')
        postgres_query("count", "campaigns", "industry = 'Fashion & Retail'")
        postgres_query("delete", "campaigns", "id = 456")
    """
    # Mock implementation - in real scenario this would connect to PostgreSQL
    print(f"PostgreSQL {query_type.upper()} operation on table '{table}'")
    if conditions:
        print(f"Conditions: {conditions}")
    if data:
        print(f"Data: {data}")

    # Mock database tables and data
    mock_campaigns = [
        {
            "id": 1,
            "name": "Summer Fashion 2024",
            "brand": "nike",
            "industry": "Fashion & Retail",
            "conversion_rate": 0.045,
            "budget": 25000,
            "status": "active",
        },
        {
            "id": 2,
            "name": "Holiday Beverages",
            "brand": "coca-cola",
            "industry": "Food & Beverage",
            "conversion_rate": 0.038,
            "budget": 18000,
            "status": "completed",
        },
        {
            "id": 3,
            "name": "Tech Innovation",
            "brand": "apple",
            "industry": "Technology & Telecommunications",
            "conversion_rate": 0.052,
            "budget": 35000,
            "status": "active",
        },
        {
            "id": 4,
            "name": "Automotive Excellence",
            "brand": "toyota",
            "industry": "Automotive",
            "conversion_rate": 0.041,
            "budget": 22000,
            "status": "paused",
        },
    ]

    mock_users = [
        {
            "id": 101,
            "username": "john_doe",
            "email": "john@example.com",
            "role": "campaign_manager",
            "created_at": "2024-01-10",
        },
        {
            "id": 102,
            "username": "jane_smith",
            "email": "jane@example.com",
            "role": "analyst",
            "created_at": "2024-01-12",
        },
    ]

    if query_type == "select":
        if table == "campaigns":
            results = mock_campaigns[:limit]
            result_text = f"SELECT results from '{table}' table:\n"
            for row in results:
                result_text += f"ID: {row['id']}, Name: {row['name']}, Brand: {row['brand']}, CTR: {row['conversion_rate']}, Budget: ${row['budget']}\n"
            return result_text
        elif table == "users":
            results = mock_users[:limit]
            result_text = f"SELECT results from '{table}' table:\n"
            for row in results:
                result_text += f"ID: {row['id']}, Username: {row['username']}, Email: {row['email']}, Role: {row['role']}\n"
            return result_text
        else:
            return f"Mock data not available for table '{table}'"

    elif query_type == "insert":
        return f"Successfully inserted new record into '{table}' table with data: {data}"

    elif query_type == "update":
        return f"Successfully updated records in '{table}' table where {conditions} with data: {data}"

    elif query_type == "delete":
        return f"Successfully deleted records from '{table}' table where {conditions}"

    elif query_type == "count":
        if table == "campaigns":
            count = len(mock_campaigns)
        elif table == "users":
            count = len(mock_users)
        else:
            count = 0
        return f"COUNT result for '{table}' table: {count} records"

    else:
        return f"Error: Unsupported query type '{query_type}'. Supported: select, insert, update, delete, count"


@function_schema
def sql_database(query: str, database: str = "default") -> str:
    """
    Execute SQL queries on a database.

    Args:
        query: SQL query to execute
        database: Database name to query (default: "default")

    Returns:
        str: Query results or execution status

    Examples:
        sql_database("SELECT * FROM campaigns WHERE budget > 20000")
        sql_database("INSERT INTO campaigns (name, budget) VALUES ('New Campaign', 30000)")
    """
    # Mock implementation
    print(f"Executing SQL query on database '{database}': {query}")

    # Simple query parsing for mock responses
    query_lower = query.lower().strip()

    if query_lower.startswith("select"):
        return json.dumps({
            "success": True,
            "rows": [
                {"id": 1, "name": "Campaign A", "budget": 25000},
                {"id": 2, "name": "Campaign B", "budget": 30000}
            ],
            "count": 2
        })
    elif query_lower.startswith("insert"):
        return json.dumps({
            "success": True,
            "message": "Record inserted successfully",
            "rows_affected": 1
        })
    elif query_lower.startswith("update"):
        return json.dumps({
            "success": True,
            "message": "Records updated successfully",
            "rows_affected": 1
        })
    elif query_lower.startswith("delete"):
        return json.dumps({
            "success": True,
            "message": "Records deleted successfully",
            "rows_affected": 1
        })
    else:
        return json.dumps({
            "success": False,
            "error": "Unsupported SQL operation"
        })


# Export store and schemas for aggregation in basic_tools
DATABASE_TOOL_STORE = {
    "redis_cache_operation": redis_cache_operation,
    "postgres_query": postgres_query,
    "sql_database": sql_database,
}

DATABASE_TOOL_SCHEMAS = {name: func.openai_schema for name, func in DATABASE_TOOL_STORE.items()}

