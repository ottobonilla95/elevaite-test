import os
import asyncio
from typing import List, Tuple, Any, Dict
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text
from rapidfuzz import process
import dotenv
from data_classes import Agent
from datetime import datetime
from prompts  import refinement_agent_system_prompt
from utils import function_schema, client
import uuid

dotenv.load_dotenv(".env")

# Type aliases for clarity
InputTuple = Tuple[str, str, str]   # (table_name, column_name, value)
OutputTuple = Tuple[str, str, Tuple[str, ...]]  # (table_name, column_name, (matches, ...))


@function_schema
async def sql_matching_values(
    user_inputs: List[InputTuple],
    threshold: int = 70,
    top_n: int = 3
) -> List[OutputTuple]:
    """
    Given (table_name, column_name, value), returns up to 3 exact match values
    from the database using fuzzy matching. Schema-aware: validates table and column.

    Args:
        user_inputs (List[Tuple]): List of (table, column, value)
        threshold (int): Minimum fuzzy match score
        top_n (int): Max number of matches to return per field

    Returns:
        List[OutputTuple]: [(table_name, column_name, (match1, match2,...)), ...]
    """

    database_url = os.getenv("SQLALCHEMY_DATABASE_URL")
    if not database_url:
        return [("error", "config", ("Database URL not configured",))]

    try:
        engine = create_async_engine(database_url, echo=False, future=True)
        results: List[OutputTuple] = []

        async with engine.begin() as connection:
            # Step 1: Load schema once
            schema_query = text("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
            """)
            schema_result = await connection.execute(schema_query)
            schema_pairs = {(row[0], row[1]) for row in schema_result.fetchall()}  # set of (table, column)

            # Step 2: Process each user input
            for table, column, value in user_inputs:
                if (table, column) not in schema_pairs:
                    results.append((table, column, (f"error: invalid (table, column)",)))
                    continue

                try:
                    # Fetch distinct values for this column (limit to avoid huge scans)
                    query = text(f"""
                        SELECT DISTINCT {column}
                        FROM {table}
                        WHERE {column} IS NOT NULL
                        LIMIT 5000
                    """)
                    db_result = await connection.execute(query)
                    values = [str(row[0]) for row in db_result.fetchall() if row[0] is not None]

                    if not values:
                        results.append((table, column, ()))
                        continue

                    # Fuzzy match
                    matches = process.extract(value, values, limit=top_n)
                    strong_matches = tuple([m[0] for m in matches if m[1] >= threshold])

                    results.append((table, column, strong_matches))

                except Exception as inner_e:
                    results.append((table, column, (f"error: {str(inner_e)}",)))

        return results

    except Exception as e:
        return [("error", "execution", (str(e),))]

    finally:
        await engine.dispose()


class QueryRefinementAgent(Agent):
    async def execute(self, query: Any, qid: str, session_id: str, chat_history: Any, user_id: str,
                      agent_flow_id: str) -> Any:
        """
        Query refinement agent to help users query the sr_data_agent_table.
        """
        tries = 0
        max_tries = self.max_retries
        start_time = datetime.now()
        system_prompt = self.system_prompt.prompt
        final_response = ""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": "Use the chat history as context and refine this query: " + query})

        while tries < max_tries:
            tries += 1
            try:
                # Call the LLM with the messages
                response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=messages,
                    tools=[self.functions[0]],
                    temperature=0.3,
                    tool_choice="auto",
                    max_tokens=2000,
                    stream=False
                )

                # Process the response
                message = response.choices[0].message
                
                if message.tool_calls:
                    # Add assistant message with tool calls
                    messages.append({
                        "role": "assistant", 
                        "content": None, 
                        "tool_calls": message.tool_calls
                    })
                    
                    for tool_call in message.tool_calls:
                        if tool_call.function.name == "sql_matching_values":
                            import json
                            args = json.loads(tool_call.function.arguments)
                            result = await sql_matching_values(**args)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result)
                            })
                    
                    # Continue to next iteration to let LLM decide next action
                    continue
                else:
                    # Direct response without tool calls - this is the final response
                    final_response = message.content
                    break  # Exit the retry loop

            except Exception as e:
                if tries >= max_tries:
                    final_response = f"Failed to process your request after {max_tries} attempts. Error: {str(e)}"
                    break
                # Continue to retry if not reached max tries
                await asyncio.sleep(1)

        return final_response


refinement_agent = QueryRefinementAgent(
            name="QueryRefinementAgent",
            agent_id=uuid.uuid4(),
            system_prompt=refinement_agent_system_prompt,
            persona="Helper",
            functions=[sql_matching_values.openai_schema],
            routing_options={"respond": "Respond to the user"},
            short_term_memory=True,
            long_term_memory=False,
            reasoning=False,
            response_type="json",
            max_retries=3,
            timeout=None,
            deployed=False,
            status="active",
            priority=None,
            failure_strategies=["retry"],
            session_id=None,
            last_active=datetime.now(),
            collaboration_mode="single",
        )

