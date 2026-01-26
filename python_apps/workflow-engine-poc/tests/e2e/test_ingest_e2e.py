import os
import uuid
import json
import pytest

from fastapi.testclient import TestClient
from workflow_engine_poc.main import app


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OPENAI_API_KEY for embedding")
def test_e2e_file_to_qdrant_multipart(tmp_path):
    # Prepare a small text file to upload via multipart
    sample = tmp_path / "sample.txt"
    sample.write_text("Hello world. This is a small document for embedding and storage.")

    # Initialize app state similar to other API tests (ensure steps/DB are ready)
    from workflow_engine_poc.step_registry import StepRegistry
    from workflow_engine_poc.workflow_engine import WorkflowEngine
    from workflow_engine_poc.db.database import get_database

    # Manually initialize app state for testing (avoids relying on lifespan)

    # Fallback init if missing
    try:
        if not getattr(app.state, "database", None):
            # get_database is async; run quickly
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
        # If event loop already running (rare in pytest here), skip and trust lifespan
        pass

    client = TestClient(app)

    # Define a workflow that relies on trigger file attachment (no file_path in config)
    wf = {
        "name": "E2E Ingest (multipart)",
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
                "name": "Chunk Text",
                "dependencies": ["read"],
                "step_order": 3,
                "config": {"strategy": "sliding_window", "chunk_size": 50, "overlap": 10},
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
                    "collection_name": f"e2e_{uuid.uuid4().hex[:8]}",
                    "qdrant_host": os.getenv("QDRANT_HOST", "http://localhost"),
                    "qdrant_port": int(os.getenv("QDRANT_PORT", "6333")),
                },
                "input_mapping": {
                    "embeddings": "embed.embeddings",
                    "chunks": "chunk.chunks",
                    "file_name": "read.file_name",
                },
            },
        ],
    }

    # Create the workflow
    resp = client.post("/workflows", json=wf)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    created_id = data["id"]

    # Build multipart request: payload must be a JSON string
    payload = json.dumps(
        {
            "wait": True,
            "trigger": {"kind": "file"},
            # force local backend to execute synchronously within this process
            # Optional metadata/input_data could be added here
        }
    )

    with open(sample, "rb") as f:
        files = [
            ("files", (sample.name, f, "text/plain")),
        ]
        data = {"payload": payload}
        exec_resp = client.post(f"/workflows/{created_id}/execute/local", files=files, data=data)

    assert exec_resp.status_code == 200, exec_resp.text
    result = exec_resp.json()

    # Validate step outputs from response
    step_io = result.get("step_io_data", {}) or {}

    read = step_io.get("read")
    assert read and read.get("success") is True and read.get("content_length", 0) > 0

    chunk = step_io.get("chunk")
    assert chunk and chunk.get("chunk_count", 0) > 0 and len(chunk.get("chunks", [])) == chunk.get("chunk_count")

    embed = step_io.get("embed")
    assert embed and embed.get("embedding_count", 0) == chunk.get("chunk_count")

    store = step_io.get("store")
    assert store and store.get("stored_count", 0) == embed.get("embedding_count") and store.get("storage_type") == "qdrant"
