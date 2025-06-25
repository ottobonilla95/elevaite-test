
from pathlib import Path
import logging
from typing import Dict, Any, List
from hippo_config import HippoRAGConfig
from retrieval_hybrid import PPRPassageRetriever
import openai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv(".env")

origins = [
    "http://127.0.0.1:3002",
    "*"
    ]


class GroupedAnswerGenerator:
    def __init__(self, config: HippoRAGConfig):
        self.config = config
        self.retriever = PPRPassageRetriever(config)
        self.llm_model = "gpt-4o"
        self.max_response_tokens = 1000

    def group_by_subject(self, passages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        grouped = {}
        for p in passages:
            subj = p.get("subject", "Unknown")
            pred = p.get("predicate", "")
            obj = p.get("object", "")
            if subj not in grouped:
                grouped[subj] = []
            fact_line = f"{pred} {obj}".strip()
            if fact_line and fact_line not in grouped[subj]:
                grouped[subj].append(fact_line)
        return grouped

    def format_prompt(self, query: str, grouped_chunks: Dict[str, List[str]]) -> str:
        parts = [
            "You are a helpful assistant answering questions based on the following structured context.",
            "Group-wise SR facts are shown below. If no resolution information is found, say so clearly.",
            "",
            "CONTEXT:"
        ]
        for sr_id, facts in grouped_chunks.items():
            parts.append(f"SR {sr_id}:")
            for fact in facts:
                parts.append(f" - {fact}")
            parts.append("")

        parts.append(f"QUESTION: {query}")
        parts.append("ANSWER:")
        return "\\n".join(parts)

    def generate_answer(self, query: str) -> Dict[str, Any]:
        try:
            passages = self.retriever.retrieve(query, max_results=40)
            if not passages:
                return {"query": query, "answer": "No relevant information found.", "success": False}

            grouped = self.group_by_subject(passages)
            prompt = self.format_prompt(query, grouped)

            response = self.config.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_response_tokens,
                temperature=0.3
            )

            answer = response.choices[0].message.content
            return {
                "query": query,
                "answer": answer,
                "chunks_used": len(passages),
                "grouped_answers": grouped,
                "success": True
            }
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return {"query": query, "answer": str(e), "success": False}

app = FastAPI()
config = HippoRAGConfig()
generator = GroupedAnswerGenerator(config)

@app.post("/query-sr")
def query_kb(query: str):
    # query = "What are the SR tickets closed on 2024-11-06 and who resolved them?"
    # query = "Which SRs were resolved between 2024-11-05 and 2024-11-07?"
    # query = "Which SRs closed in Florida and who handled them?"
    # query = "What tickets were handled by Jason Hechler?"
    # query = "machine type for 15790474"
    # query = "Who resolved tickets from Centerville?"
    # query = "Which technician handled SRs in both TX and GA?"
    # query = "Which machine types were most frequent in CA for tickets closed in Nov 2024?"
    # query = "SRs closed on 2024-11-06"
    # query = "what is the SR number for 3AC00590900"
    # query = "List all SRs resolved by Jason Hechler"
    # query = "what are the part number replaced recently with date?"
    # print(request)
    # query = request.get("query")
    print("Query: ", query)
    
    result = generator.generate_answer(query)
    print("\\n==============================")
    print(f"Query: {result['query']}")
    print(f"Answer: {result['answer']}")
    print("==============================\\n")
    return result


if __name__ == "__main__":
    query_kb("what are the part number replaced recently with date?")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization'],
    )
    uvicorn.run(app, host="0.0.0.0", port=8007)

