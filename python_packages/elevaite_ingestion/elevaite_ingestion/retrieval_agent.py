from swarm import Swarm, Agent
import json
from dotenv import load_dotenv

load_dotenv()

# -------- Config Utilities --------
CONFIG_PATH = "config.json"


def load_config():
    with open(CONFIG_PATH, "r") as file:
        return json.load(file)


def save_config(config):
    with open(CONFIG_PATH, "w") as file:
        json.dump(config, file, indent=4)


config = load_config()

# -------- Stage Setup Functions --------


def load_stage_setup():
    return {
        "message": (
            "To load your files, choose between:\n"
            "- AWS S3 (cloud bucket)\n"
            "- Local folder on your system"
        ),
        "options": ["S3", "Local"],
    }


def parse_stage_setup():
    parser_options = list(config.get("parsing", {}).get("parsers", {}).keys())
    return {
        "message": (
            "Parsing stage configuration:\n"
            "1. Auto Parser: Automatically selects a parser.\n"
            "2. Custom Parser: You choose the document type (e.g., PDF, DOCX) and tool.\n\n"
            "Which mode do you want to proceed with?"
        ),
        "options": ["auto_parser", "custom_parser"],
        "document_types": parser_options,
    }


def parse_tool_selection(doc_type):
    tools = (
        config.get("parsing", {})
        .get("parsers", {})
        .get(doc_type, {})
        .get("available_tools", [])
    )
    if not tools:
        return {
            "message": f"For {doc_type.upper()} files, we are providing no tool options. The parser will use the default or basic extraction logic.",
            "options": [],
        }
    else:
        return {
            "message": f"For {doc_type.upper()} files, we support the following tools: {', '.join(tools)}. Please select one.",
            "options": tools,
        }


def chunk_stage_setup():
    return {
        "message": "Choose a chunking strategy:\n- semantic_chunking\n- recursive_chunking\n- sentence_chunking",
        "options": list(config.get("chunking", {}).get("strategies", {}).keys()),
    }


def embedding_stage_setup():
    return {
        "message": "Select an embedding provider (OpenAI, Cohere, Local, etc.)",
        "options": list(config.get("embedding", {}).get("providers", {}).keys()),
    }


def vectorstore_stage_setup():
    options = list(config.get("vector_db", {}).get("databases", {}).keys())
    default = config.get("vector_db", {}).get("default_db")
    if default in options:
        message = f"Qdrant vectorstore is currently selected and configured as your default. Do you want to keep it or change to a different one? Available options: {', '.join(options)}"
    else:
        message = f"Choose a vector DB: {', '.join(options)}"

    def save_choice(user_choice):
        config["vector_db"]["default_db"] = user_choice
        save_config(config)
        return f"✅ Vectorstore stage configured with `{user_choice}`. Configuration saved."

    return {"message": message, "options": options, "callback": save_choice}


# -------- Agent Definitions --------

load_agent = Agent(
    name="LoadStageAgent",
    instructions="Help configure the loading stage: ask the user to choose S3 or Local, and collect relevant info.",
    functions=[load_stage_setup],
)

parse_agent = Agent(
    name="ParseStageAgent",
    instructions="Guide the user through choosing auto or custom parser. If custom, ask for document type and then tool if available.",
    functions=[parse_stage_setup, parse_tool_selection],
)

chunk_agent = Agent(
    name="ChunkStageAgent",
    instructions="Help choose the chunking strategy. Explain each one and collect the user's choice.",
    functions=[chunk_stage_setup],
)

embedding_agent = Agent(
    name="EmbeddingStageAgent",
    instructions="Help configure the embedding provider and model. Collect provider and model info.",
    functions=[embedding_stage_setup],
)

vectorstore_agent = Agent(
    name="VectorStoreStageAgent",
    instructions="Help the user choose a vector database (Qdrant, Pinecone, Chroma). Save the selection in the config file.",
    functions=[vectorstore_stage_setup],
)

# -------- Return Agent Functions --------


def get_load_agent():
    return load_agent


def get_parse_agent():
    return parse_agent


def get_chunk_agent():
    return chunk_agent


def get_embedding_agent():
    return embedding_agent


def get_vectorstore_agent():
    return vectorstore_agent


# -------- Lead Agent (Orchestrator) --------

lead_agent = Agent(
    name="LeadOrchestratorAgent",
    instructions="""
        You are the lead AI agent that guides users through configuring a multi-stage retrieval pipeline.
        Guide the user through each stage (Loading, Parsing, Chunking, Embedding, Vectorstore).
        Call the corresponding stage agent via tools to show options and get input.
        If custom parser is selected, ask for document type, then call the tool selection function.
        After all stages are configured, show a summary and ask for confirmation to proceed.
    """,
    functions=[
        get_load_agent,
        get_parse_agent,
        get_chunk_agent,
        get_embedding_agent,
        get_vectorstore_agent,
    ],
)

# -------- Run the Swarm --------

client = Swarm()

messages = [{"role": "user", "content": "I want to build a retrieval pipeline."}]

while True:
    response = client.run(agent=lead_agent, messages=messages)
    reply = response.messages[-1]["content"]
    print("🤖:", reply)

    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    messages.append({"role": "user", "content": user_input})
