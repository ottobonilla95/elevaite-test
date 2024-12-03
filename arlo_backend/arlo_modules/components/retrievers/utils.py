import time

def reformulate_question(query: str, chat_history: list) -> str:
    """
    Reformulate the user's question based on the last 7 chat history messages for better context.
    
    Args:
    query: The current user query.
    chat_history: List of previous chat messages (both user and assistant).
    
    Returns:
    A reformulated question that includes relevant context from the chat history.
    """

    if not chat_history:
        return query

    recent_history = chat_history[-7:]
    
    # Extract relevant context from the recent history
    past_context = " ".join([msg['content'] for msg in recent_history if msg['role'] == 'user'])
    # print("##############################################")
    # print("past_context =========> ", past_context)
    
    # Reformulate the question using this context
    reformulated_query = f"Based on recent conversation: {past_context} -> {query}"
    # print("##############################################")
    # print("reformulated_query =========> ", reformulated_query)
    
    return reformulated_query


# Function for streaming output
def stream_output(answer):
    for word in answer.split(" "):
        yield word + " "
        time.sleep(0.02)