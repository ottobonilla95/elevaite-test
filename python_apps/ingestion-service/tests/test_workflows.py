"""
Tests for DBOS ingestion workflows.

Tests the workflow execution and HTTP callback completion notifications.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
from datetime import datetime, timezone

from ingestion_service.workflows import execute_ingestion_pipeline, send_completion_event
from ingestion_service.models import IngestionJob, JobStatus


class TestExecuteIngestionPipeline:
    """Tests for execute_ingestion_pipeline function.

    These tests mock the elevaite_ingestion stage functions to avoid
    requiring real AWS credentials and external services.
    """

    @pytest.mark.asyncio
    async def test_execute_pipeline_returns_expected_structure(self):
        """Test that pipeline execution returns expected structure when stages succeed"""
        import sys

        config = {
            "mode": "s3",
            "aws": {"input_bucket": "test-bucket", "intermediate_bucket": "test-intermediate"},
        }

        # Create mock stage results
        mock_parse_result = {"STAGE_2: PARSING": {"STATUS": "Completed", "TOTAL_FILES": 5}}
        mock_chunk_result = {"STAGE_3: CHUNKING": {"STATUS": "Completed", "TOTAL_CHUNKS": 50}}
        mock_embed_result = {"STAGE_4: EMBEDDING": {"STATUS": "Completed", "TOTAL_EMBEDDINGS": 50}}
        mock_vectordb_result = {"STAGE_5: VECTORSTORE": {"STATUS": "Completed", "INDEX_ID": "test-index"}}

        # Create mock modules
        mock_parse_module = MagicMock()
        mock_parse_module.execute_pipeline = MagicMock(return_value=mock_parse_result)

        mock_chunk_module = MagicMock()
        mock_chunk_module.execute_chunking_pipeline = AsyncMock(return_value=mock_chunk_result)

        mock_embed_module = MagicMock()
        mock_embed_module.execute_embedding_pipeline = MagicMock(return_value=mock_embed_result)

        mock_vectordb_module = MagicMock()
        mock_vectordb_module.execute_vector_db_pipeline = MagicMock(return_value=mock_vectordb_result)

        # Patch sys.modules to inject our mocks
        with patch.dict(
            sys.modules,
            {
                "elevaite_ingestion.stage.parse_stage.parse_main": mock_parse_module,
                "elevaite_ingestion.stage.chunk_stage.chunk_main": mock_chunk_module,
                "elevaite_ingestion.stage.embed_stage.embed_main": mock_embed_module,
                "elevaite_ingestion.stage.vectorstore_stage.vectordb_main": mock_vectordb_module,
            },
        ):
            with patch("ingestion_service.workflows._build_pipeline_config"):
                result = await execute_ingestion_pipeline(config)

        # Verify the result structure
        assert "files_processed" in result
        assert "chunks_created" in result
        assert "embeddings_generated" in result
        assert "index_ids" in result
        assert "stages" in result

        # Verify extracted values
        assert result["files_processed"] == 5
        assert result["chunks_created"] == 50
        assert result["embeddings_generated"] == 50
        assert "test-index" in result["index_ids"]

    @pytest.mark.asyncio
    async def test_execute_pipeline_handles_stage_failure(self):
        """Test that pipeline raises exception when a stage fails"""
        import sys

        config = {"mode": "s3"}

        # Create mock parse result that indicates failure
        mock_parse_result = {"STAGE_2: PARSING": {"STATUS": "Failed", "TOTAL_FILES": 0}}
        mock_parse_module = MagicMock()
        mock_parse_module.execute_pipeline = MagicMock(return_value=mock_parse_result)

        with patch.dict(
            sys.modules,
            {
                "elevaite_ingestion.stage.parse_stage.parse_main": mock_parse_module,
            },
        ):
            with patch("ingestion_service.workflows._build_pipeline_config"):
                with pytest.raises(Exception) as exc_info:
                    await execute_ingestion_pipeline(config)

                assert "Parsing stage failed" in str(exc_info.value)


class TestSendCompletionEvent:
    """Tests for send_completion_event function (HTTP callback version)"""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_send_event_success(self, mock_client_class):
        """Test successful HTTP callback dispatch"""
        # Setup mock HTTP client
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        callback_topic = "wf:exec-123:step-456:ingestion_done"
        dbos_workflow_id = "dbos-wf-789"
        event_payload = {
            "job_id": str(uuid.uuid4()),
            "status": "SUCCEEDED",
            "result_summary": {"files_processed": 10},
        }

        await send_completion_event(callback_topic, dbos_workflow_id, event_payload)

        # Verify HTTP POST was called with correct URL
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        # URL should be constructed from callback_topic: /api/executions/{exec_id}/steps/{step_id}/callback
        assert "exec-123" in call_args[0][0]
        assert "step-456" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_send_event_no_callback_topic(self):
        """Test that missing callback_topic is handled gracefully"""
        # Should not raise exception and should return early
        await send_completion_event(None, None, {"status": "SUCCEEDED"})
        await send_completion_event("", None, {"status": "SUCCEEDED"})

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_send_event_invalid_topic_format(self, mock_client_class):
        """Test that invalid callback_topic format is handled gracefully"""
        # Should not call HTTP client if topic format is invalid
        await send_completion_event("invalid-topic", None, {"status": "SUCCEEDED"})
        mock_client_class.assert_not_called()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_send_event_failure_logged(self, mock_client_class):
        """Test that HTTP callback failures are logged but don't raise"""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client_class.return_value = mock_client

        # Should not raise exception
        await send_completion_event("wf:exec-123:step-456:done", None, {"status": "SUCCEEDED"})


class TestRunIngestionJob:
    """Tests for run_ingestion_job workflow logic.

    These tests use the _run_ingestion_job_impl function directly to avoid
    DBOS initialization requirements. The DBOS-decorated wrapper is tested
    in integration tests.
    """

    @pytest.mark.asyncio
    async def test_successful_job_execution(self, engine):
        """Test successful job execution flow"""
        from sqlmodel import Session, SQLModel
        from ingestion_service.workflows import _run_ingestion_job_impl

        # Create tables in test engine
        SQLModel.metadata.create_all(engine)

        # Create a test job in the database
        job_id = uuid.uuid4()
        with Session(engine) as session:
            job = IngestionJob(
                id=job_id,
                config={"source": "s3", "bucket": "test"},
                status=JobStatus.PENDING,
                callback_topic="wf:exec-123:step-456:done",
            )
            session.add(job)
            session.commit()

        # Mock pipeline execution and HTTP callback
        with (
            patch("ingestion_service.workflows.execute_ingestion_pipeline") as mock_execute,
            patch("ingestion_service.workflows.send_completion_event") as mock_send_event,
        ):
            mock_execute.return_value = {
                "files_processed": 10,
                "chunks_created": 500,
                "embeddings_generated": 500,
            }
            mock_send_event.return_value = None

            # Execute workflow implementation directly with test engine
            result = await _run_ingestion_job_impl(str(job_id), db_engine=engine)

        # Verify result
        assert result["job_id"] == str(job_id)
        assert result["status"] == "SUCCEEDED"
        assert result["result_summary"]["files_processed"] == 10

        # Verify completion event was sent
        mock_send_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_not_found(self, engine):
        """Test handling of non-existent job"""
        from sqlmodel import SQLModel
        from ingestion_service.workflows import _run_ingestion_job_impl

        # Create tables in test engine
        SQLModel.metadata.create_all(engine)

        job_id = str(uuid.uuid4())

        result = await _run_ingestion_job_impl(job_id, db_engine=engine)

        assert result["status"] == "FAILED"
        assert "not found" in result["error_message"].lower()

    @pytest.mark.asyncio
    async def test_pipeline_execution_failure(self, engine):
        """Test handling of pipeline execution failure"""
        from sqlmodel import Session, SQLModel
        from ingestion_service.workflows import _run_ingestion_job_impl

        # Create tables in test engine
        SQLModel.metadata.create_all(engine)

        # Create a test job
        job_id = uuid.uuid4()
        with Session(engine) as session:
            job = IngestionJob(
                id=job_id,
                config={"source": "s3"},
                status=JobStatus.PENDING,
                callback_topic="wf:exec-123:step-456:done",
            )
            session.add(job)
            session.commit()

        # Mock pipeline failure
        with (
            patch("ingestion_service.workflows.execute_ingestion_pipeline") as mock_execute,
            patch("ingestion_service.workflows.send_completion_event") as mock_send_event,
        ):
            mock_execute.side_effect = Exception("Pipeline error")
            mock_send_event.return_value = None

            result = await _run_ingestion_job_impl(str(job_id), db_engine=engine)

        # Verify failure result
        assert result["status"] == "FAILED"
        assert "Pipeline error" in result["error_message"]

        # Verify failure event was sent
        mock_send_event.assert_called_once()

        # Verify job status in database
        with Session(engine) as session:
            job = session.get(IngestionJob, job_id)
            assert job.status == JobStatus.FAILED
            assert "Pipeline error" in job.error_message
