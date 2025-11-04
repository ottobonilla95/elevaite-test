"""
Tests for Files Router

Tests all file upload and processing endpoints:
- POST /files/upload - Upload file with optional auto-processing
"""

import pytest
import io
from pathlib import Path
from unittest.mock import AsyncMock, patch, mock_open, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def sample_text_file():
    """Sample text file for upload testing"""
    content = b"This is a test file content.\nLine 2\nLine 3"
    return io.BytesIO(content)


@pytest.fixture
def sample_pdf_file():
    """Sample PDF file (mock binary content)"""
    # Mock PDF header
    content = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + b"Mock PDF content" * 100
    return io.BytesIO(content)


@pytest.fixture
def sample_image_file():
    """Sample image file (mock binary content)"""
    # Mock PNG header
    content = b"\x89PNG\r\n\x1a\n" + b"Mock image data" * 50
    return io.BytesIO(content)


@pytest.fixture
def mock_workflow_config():
    """Mock workflow configuration for auto-processing"""
    return {
        "id": "workflow-123",
        "name": "File Processing Workflow",
        "steps": [
            {"id": "step1", "type": "file_reader", "config": {}},
            {"id": "step2", "type": "data_processing", "config": {}},
        ],
    }


class TestUploadFile:
    """Tests for POST /files/upload endpoint"""

    def test_upload_file_success(self, authenticated_client: TestClient, sample_text_file, tmp_path):
        """Test successfully uploading a file"""
        with patch("workflow_engine_poc.routers.files.Path") as mock_path_class:
            # Mock the upload directory
            mock_upload_dir = MagicMock()
            mock_path_class.return_value = mock_upload_dir
            mock_upload_dir.mkdir = MagicMock()
            mock_upload_dir.__truediv__ = lambda self, other: tmp_path / other

            with patch("builtins.open", mock_open()) as mock_file:
                response = authenticated_client.post(
                    "/files/upload",
                    files={"file": ("test.txt", sample_text_file, "text/plain")},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["message"] == "File uploaded successfully"
                assert data["filename"] == "test.txt"
                assert "file_path" in data
                assert "file_size" in data
                assert data["file_size"] > 0
                assert "upload_timestamp" in data

    def test_upload_file_with_different_extensions(self, authenticated_client: TestClient, tmp_path):
        """Test uploading files with different extensions"""
        test_files = [
            ("document.pdf", b"PDF content", "application/pdf"),
            ("image.png", b"PNG content", "image/png"),
            ("data.json", b'{"key": "value"}', "application/json"),
            ("script.py", b"print('hello')", "text/x-python"),
        ]

        for filename, content, content_type in test_files:
            file_obj = io.BytesIO(content)

            with patch("workflow_engine_poc.routers.files.Path") as mock_path_class:
                mock_upload_dir = MagicMock()
                mock_path_class.return_value = mock_upload_dir
                mock_upload_dir.mkdir = MagicMock()
                mock_upload_dir.__truediv__ = lambda self, other: tmp_path / other

                with patch("builtins.open", mock_open()):
                    response = authenticated_client.post(
                        "/files/upload",
                        files={"file": (filename, file_obj, content_type)},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["filename"] == filename
                    assert data["file_size"] == len(content)

    def test_upload_large_file(self, authenticated_client: TestClient, tmp_path):
        """Test uploading a large file"""
        # Create a 5MB mock file
        large_content = b"x" * (5 * 1024 * 1024)
        large_file = io.BytesIO(large_content)

        with patch("workflow_engine_poc.routers.files.Path") as mock_path_class:
            mock_upload_dir = MagicMock()
            mock_path_class.return_value = mock_upload_dir
            mock_upload_dir.mkdir = MagicMock()
            mock_upload_dir.__truediv__ = lambda self, other: tmp_path / other

            with patch("builtins.open", mock_open()):
                response = authenticated_client.post(
                    "/files/upload",
                    files={"file": ("large_file.bin", large_file, "application/octet-stream")},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["file_size"] == 5 * 1024 * 1024

    def test_upload_file_with_special_characters_in_name(self, authenticated_client: TestClient, tmp_path):
        """Test uploading file with special characters in filename"""
        special_filenames = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.multiple.dots.txt",
        ]

        for filename in special_filenames:
            file_obj = io.BytesIO(b"test content")

            with patch("workflow_engine_poc.routers.files.Path") as mock_path_class:
                mock_upload_dir = MagicMock()
                mock_path_class.return_value = mock_upload_dir
                mock_upload_dir.mkdir = MagicMock()
                mock_upload_dir.__truediv__ = lambda self, other: tmp_path / other

                with patch("builtins.open", mock_open()):
                    response = authenticated_client.post(
                        "/files/upload",
                        files={"file": (filename, file_obj, "text/plain")},
                    )

                    assert response.status_code == 200
                    assert response.json()["filename"] == filename

    def test_upload_file_with_auto_process_false(self, authenticated_client: TestClient, sample_text_file, tmp_path):
        """Test uploading file with auto_process=False"""
        with patch("workflow_engine_poc.routers.files.Path") as mock_path_class:
            mock_upload_dir = MagicMock()
            mock_path_class.return_value = mock_upload_dir
            mock_upload_dir.mkdir = MagicMock()
            mock_upload_dir.__truediv__ = lambda self, other: tmp_path / other

            with patch("builtins.open", mock_open()):
                response = authenticated_client.post(
                    "/files/upload",
                    files={"file": ("test.txt", sample_text_file, "text/plain")},
                    data={"auto_process": "false", "workflow_id": "workflow-123"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "auto_processing" not in data

    def test_upload_file_with_auto_process_true(
        self, authenticated_client: TestClient, sample_text_file, mock_workflow_config, tmp_path
    ):
        """Test uploading file with auto_process=True"""
        with patch("workflow_engine_poc.routers.files.Path") as mock_path_class:
            mock_upload_dir = MagicMock()
            mock_path_class.return_value = mock_upload_dir
            mock_upload_dir.mkdir = MagicMock()
            mock_upload_dir.__truediv__ = lambda self, other: tmp_path / other

            with patch("builtins.open", mock_open()):
                # Mock database and workflow engine
                mock_database = AsyncMock()
                mock_database.get_workflow = AsyncMock(return_value=mock_workflow_config)
                authenticated_client.app.state.database = mock_database

                mock_engine = AsyncMock()
                mock_engine.execute_workflow = AsyncMock()
                authenticated_client.app.state.workflow_engine = mock_engine

                with patch("asyncio.create_task") as mock_create_task:
                    response = authenticated_client.post(
                        "/files/upload",
                        files={"file": ("test.txt", sample_text_file, "text/plain")},
                        data={"auto_process": "true", "workflow_id": "workflow-123"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "auto_processing" in data
                    assert data["auto_processing"]["workflow_id"] == "workflow-123"
                    assert data["auto_processing"]["status"] == "started"
                    assert "execution_id" in data["auto_processing"]

                    # Verify workflow execution was triggered
                    mock_create_task.assert_called_once()

    def test_upload_file_auto_process_workflow_not_found(
        self, authenticated_client: TestClient, sample_text_file, tmp_path
    ):
        """Test auto-process when workflow doesn't exist"""
        with patch("workflow_engine_poc.routers.files.Path") as mock_path_class:
            mock_upload_dir = MagicMock()
            mock_path_class.return_value = mock_upload_dir
            mock_upload_dir.mkdir = MagicMock()
            mock_upload_dir.__truediv__ = lambda self, other: tmp_path / other

            with patch("builtins.open", mock_open()):
                # Mock database returning None (workflow not found)
                mock_database = AsyncMock()
                mock_database.get_workflow = AsyncMock(return_value=None)
                authenticated_client.app.state.database = mock_database

                response = authenticated_client.post(
                    "/files/upload",
                    files={"file": ("test.txt", sample_text_file, "text/plain")},
                    data={"auto_process": "true", "workflow_id": "nonexistent-workflow"},
                )

                assert response.status_code == 200
                data = response.json()
                # File should still upload successfully, just no auto-processing
                assert "auto_processing" not in data

    def test_upload_file_without_workflow_id(self, authenticated_client: TestClient, sample_text_file, tmp_path):
        """Test auto-process without workflow_id"""
        with patch("workflow_engine_poc.routers.files.Path") as mock_path_class:
            mock_upload_dir = MagicMock()
            mock_path_class.return_value = mock_upload_dir
            mock_upload_dir.mkdir = MagicMock()
            mock_upload_dir.__truediv__ = lambda self, other: tmp_path / other

            with patch("builtins.open", mock_open()):
                response = authenticated_client.post(
                    "/files/upload",
                    files={"file": ("test.txt", sample_text_file, "text/plain")},
                    data={"auto_process": "true"},  # No workflow_id
                )

                assert response.status_code == 200
                data = response.json()
                assert "auto_processing" not in data

    def test_upload_file_creates_directory(self, authenticated_client: TestClient, sample_text_file, tmp_path):
        """Test that upload creates directory if it doesn't exist"""
        with patch("workflow_engine_poc.routers.files.Path") as mock_path_class:
            mock_upload_dir = MagicMock()
            mock_path_class.return_value = mock_upload_dir
            mock_upload_dir.__truediv__ = lambda self, other: tmp_path / other

            with patch("builtins.open", mock_open()):
                response = authenticated_client.post(
                    "/files/upload",
                    files={"file": ("test.txt", sample_text_file, "text/plain")},
                )

                assert response.status_code == 200
                # Verify mkdir was called with exist_ok=True
                mock_upload_dir.mkdir.assert_called_once_with(exist_ok=True)

    def test_upload_file_error_handling(self, authenticated_client: TestClient, sample_text_file):
        """Test error handling when file upload fails"""
        with patch("workflow_engine_poc.routers.files.Path") as mock_path_class:
            mock_upload_dir = MagicMock()
            mock_path_class.return_value = mock_upload_dir
            mock_upload_dir.mkdir = MagicMock()
            mock_upload_dir.__truediv__ = MagicMock(side_effect=Exception("Disk full"))

            response = authenticated_client.post(
                "/files/upload",
                files={"file": ("test.txt", sample_text_file, "text/plain")},
            )

            assert response.status_code == 500
            assert "Disk full" in response.json()["detail"]

    def test_upload_empty_file(self, authenticated_client: TestClient, tmp_path):
        """Test uploading an empty file"""
        empty_file = io.BytesIO(b"")

        with patch("workflow_engine_poc.routers.files.Path") as mock_path_class:
            mock_upload_dir = MagicMock()
            mock_path_class.return_value = mock_upload_dir
            mock_upload_dir.mkdir = MagicMock()
            mock_upload_dir.__truediv__ = lambda self, other: tmp_path / other

            with patch("builtins.open", mock_open()):
                response = authenticated_client.post(
                    "/files/upload",
                    files={"file": ("empty.txt", empty_file, "text/plain")},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["file_size"] == 0

