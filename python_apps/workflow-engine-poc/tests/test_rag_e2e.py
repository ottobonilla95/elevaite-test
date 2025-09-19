import os
import json
import uuid
import tempfile
import pytest

from fastapi.testclient import TestClient
from workflow_engine_poc.main import app


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OPENAI_API_KEY for embeddings and agent")
def test_full_rag_e2e_ingest_and_query(tmp_path):
    # Ensure app state is initialized with registry and engine
    from workflow_engine_poc.step_registry import StepRegistry
    from workflow_engine_poc.workflow_engine import WorkflowEngine
    from workflow_engine_poc.db.database import get_database

    # Skip if llm-gateway is not available for agent step
    try:
        from workflow_engine_poc.steps import ai_steps as _ai_steps

        if not getattr(_ai_steps, "LLM_GATEWAY_AVAILABLE", False):
            pytest.skip("llm-gateway not available; skipping agent portion of RAG test")
    except Exception:
        pytest.skip("llm-gateway import failed; skipping agent portion of RAG test")

    # Initialize app.state if not already
    try:
        if not getattr(app.state, "database", None):
            import asyncio

            async def _init():
                db = await get_database()
                step_registry = StepRegistry()
                await step_registry.register_builtin_steps()
                app.state.database = db
                app.state.step_registry = step_registry
                app.state.workflow_engine = WorkflowEngine(step_registry)

            asyncio.run(_init())
    except RuntimeError:
        # Event loop already running; assume lifespan handled
        pass

    client = TestClient(app)

    # Quick Qdrant reachability check; skip test if not running
    try:
        from qdrant_client import QdrantClient

        _qc = QdrantClient(url=os.getenv("QDRANT_HOST", "http://localhost"), port=int(os.getenv("QDRANT_PORT", "6333")))
        _ = _qc.get_collections()
    except Exception:
        pytest.skip("Qdrant not reachable on configured host/port; skipping RAG e2e test")

    # 1) Ingest workflow: file -> chunk -> embed -> store (Qdrant)
    collection_name = f"rag_{uuid.uuid4().hex[:8]}"

    # Prepare a simple text file with a fact we will query later
    sample = tmp_path / "rag_doc.txt"
    sample.write_text("The capital of France is Paris. This file is used for a RAG e2e test.")

    ingest_wf = {
        "name": "RAG Ingest",
        "execution_pattern": "sequential",
        "steps": [
            {"step_id": "trigger", "step_type": "trigger", "name": "Trigger", "step_order": 1},
            {
                "step_id": "read",
                "step_type": "file_reader",
                "name": "Read File",
                "dependencies": ["trigger"],
                "step_order": 2,
                "config": {},
            },
            {
                "step_id": "chunk",
                "step_type": "text_chunking",
                "name": "Chunk",
                "dependencies": ["read"],
                "step_order": 3,
                "config": {"strategy": "sliding_window", "chunk_size": 200, "overlap": 20},
                "input_mapping": {"content": "read.content", "parsed": "read.parsed"},
            },
            {
                "step_id": "embed",
                "step_type": "embedding_generation",
                "name": "Embed",
                "dependencies": ["chunk"],
                "step_order": 4,
                "config": {"provider": "openai"},
                "input_mapping": {"chunks": "chunk.chunks"},
            },
            {
                "step_id": "store",
                "step_type": "vector_storage",
                "name": "Store",
                "dependencies": ["embed"],
                "step_order": 5,
                "config": {
                    "storage_type": "qdrant",
                    "collection_name": collection_name,
                    "qdrant_host": os.getenv("QDRANT_HOST", "http://localhost"),
                    "qdrant_port": int(os.getenv("QDRANT_PORT", "6333")),
                },
                "input_mapping": {"embeddings": "embed.embeddings", "chunks": "chunk.chunks", "file_name": "read.file_name"},
            },
        ],
    }

    # Create ingest workflow
    resp = client.post("/workflows", json=ingest_wf)
    assert resp.status_code == 200, resp.text
    ingest_id = resp.json()["id"]

    # Execute ingest with multipart (attach file)
    payload = json.dumps({"wait": True, "trigger": {"kind": "file"}})
    with open(sample, "rb") as f:
        files = [("files", (sample.name, f, "text/plain"))]
        data = {"payload": payload}
        exec_resp = client.post(f"/workflows/{ingest_id}/execute/local", files=files, data=data)
    assert exec_resp.status_code == 200, exec_resp.text
    ingest_result = exec_resp.json()

    store_out = (ingest_result.get("step_io_data") or {}).get("store") or {}
    assert store_out.get("success") is True
    assert store_out.get("stored_count", 0) > 0

    # 2) Query workflow: chat trigger -> vector_search -> agent_execution
    query_wf = {
        "name": "RAG Query",
        "execution_pattern": "sequential",
        "steps": [
            {"step_id": "trigger", "step_type": "trigger", "name": "Trigger", "step_order": 1},
            {
                "step_id": "search",
                "step_type": "vector_search",
                "name": "Search",
                "dependencies": ["trigger"],
                "step_order": 2,
                "config": {
                    "db_type": "qdrant",
                    "collection_name": collection_name,
                    "qdrant_host": os.getenv("QDRANT_HOST", "http://localhost"),
                    "qdrant_port": int(os.getenv("QDRANT_PORT", "6333")),
                    "top_k": 3,
                    "provider": "openai",
                    "model": "text-embedding-ada-002",
                },
            },
            {
                "step_id": "answer",
                "step_type": "agent_execution",
                "name": "Answer",
                "dependencies": ["search"],
                "step_order": 3,
                "config": {
                    "agent_config": {
                        "agent_name": "RAG Agent",
                        "model": "gpt-4o-mini",
                        "system_prompt": (
                            "You are a RAG assistant. Use retrieved_chunks from context to answer the user's question. "
                            "Be concise."
                        ),
                        "temperature": 0.0,
                        "max_tokens": 200,
                    },
                    # Keep interactive default True; presence of current_message allows progression
                    "return_simplified": True,
                },
            },
        ],
    }

    resp2 = client.post("/workflows", json=query_wf)
    assert resp2.status_code == 200, resp2.text
    query_id = resp2.json()["id"]

    query_body = {
        "wait": True,
        "trigger": {"kind": "chat", "current_message": "What is the capital of France?"},
        "backend": "local",
    }
    qexec = client.post(f"/workflows/{query_id}/execute/local", json=query_body)
    assert qexec.status_code == 200, qexec.text

    qres = qexec.json()
    step_io = qres.get("step_io_data") or {}

    # Ensure vector search returned at least one chunk
    search_out = step_io.get("search") or {}
    assert search_out.get("success") is True
    assert (search_out.get("retrieved_count") or 0) >= 1

    # Ensure agent answered using the retrieved knowledge
    answer_out = step_io.get("answer") or {}
    text = (answer_out.get("response") or "").lower()
    assert "paris" in text, f"Agent response did not include expected fact. Response: {answer_out}"
