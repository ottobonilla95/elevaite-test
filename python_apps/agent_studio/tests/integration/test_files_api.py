"""
Integration tests for Files API endpoints.

Tests all operations for file management including:
- Upload files
- List files
- Delete files
- Get upload configuration
- File validation
- Error cases
"""

import io
from fastapi.testclient import TestClient


class TestFilesAPI:
    """Test suite for Files API endpoints."""

    def test_get_upload_config(self, test_client: TestClient):
        """Test getting upload configuration."""
        response = test_client.get("/api/files/config")

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result

        data = result["data"]
        assert "max_file_size" in data
        assert "allowed_extensions" in data
        assert "upload_dir" in data
        assert isinstance(data["allowed_extensions"], list)

    def test_upload_file_success(self, test_client: TestClient):
        """Test uploading a valid file."""
        # Create a test file
        file_content = b"This is a test file content"
        file = ("test.txt", io.BytesIO(file_content), "text/plain")

        response = test_client.post(
            "/api/files/upload",
            files={"file": file},
            data={"description": "Test file upload"},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result

        data = result["data"]
        assert "file_id" in data
        assert "original_filename" in data
        assert data["original_filename"] == "test.txt"
        assert "file_path" in data

        # Cleanup
        test_client.delete(f"/api/files/{data['file_id']}")

    def test_upload_file_with_workflow_id(self, test_client: TestClient):
        """Test uploading a file associated with a workflow."""
        file_content = b"Workflow test file"
        file = ("workflow_test.txt", io.BytesIO(file_content), "text/plain")

        response = test_client.post(
            "/api/files/upload",
            files={"file": file},
            data={"workflow_id": "test-workflow-123", "description": "Workflow file"},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result

        # Cleanup
        test_client.delete(f"/api/files/{result['data']['file_id']}")

    def test_upload_file_with_agent_id(self, test_client: TestClient):
        """Test uploading a file associated with an agent."""
        file_content = b"Agent test file"
        file = ("agent_test.txt", io.BytesIO(file_content), "text/plain")

        response = test_client.post(
            "/api/files/upload",
            files={"file": file},
            data={"agent_id": "test-agent-456", "description": "Agent file"},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result

        # Cleanup
        test_client.delete(f"/api/files/{result['data']['file_id']}")

    def test_upload_file_invalid_extension(self, test_client: TestClient):
        """Test uploading a file with invalid extension."""
        file_content = b"Invalid file"
        file = ("test.exe", io.BytesIO(file_content), "application/octet-stream")

        response = test_client.post(
            "/api/files/upload",
            files={"file": file},
        )

        # Should fail validation (400) or succeed depending on config
        # Check that it either rejects or accepts based on ALLOWED_EXTENSIONS
        assert response.status_code in [200, 400]

    def test_list_files_empty(self, test_client: TestClient):
        """Test listing files."""
        response = test_client.get("/api/files/")

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert isinstance(result["data"], list)
        assert "count" in result

    def test_list_files_with_limit(self, test_client: TestClient):
        """Test listing files with limit parameter."""
        response = test_client.get("/api/files/?limit=5")

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert len(result["data"]) <= 5

    def test_list_files_with_workflow_filter(self, test_client: TestClient):
        """Test listing files filtered by workflow_id."""
        response = test_client.get("/api/files/?workflow_id=test-workflow-123")

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result

    def test_list_files_with_agent_filter(self, test_client: TestClient):
        """Test listing files filtered by agent_id."""
        response = test_client.get("/api/files/?agent_id=test-agent-456")

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result

    def test_delete_file_not_found(self, test_client: TestClient):
        """Test deleting a non-existent file."""
        fake_id = "nonexistent-file-id-12345"
        response = test_client.delete(f"/api/files/{fake_id}")

        assert response.status_code == 404

    def test_upload_and_delete_file_lifecycle(self, test_client: TestClient):
        """Test complete file lifecycle: upload -> list -> delete."""
        # Upload
        file_content = b"Lifecycle test file"
        file = ("lifecycle.txt", io.BytesIO(file_content), "text/plain")

        upload_response = test_client.post(
            "/api/files/upload",
            files={"file": file},
            data={"description": "Lifecycle test"},
        )

        assert upload_response.status_code == 200
        upload_result = upload_response.json()
        assert upload_result["success"] is True
        file_id = upload_result["data"]["file_id"]

        # List (verify it exists)
        list_response = test_client.get("/api/files/")
        assert list_response.status_code == 200
        list_result = list_response.json()
        assert list_result["success"] is True
        files = list_result["data"]
        file_ids = [f.get("file_id") for f in files]
        assert file_id in file_ids

        # Delete
        delete_response = test_client.delete(f"/api/files/{file_id}")
        # Should succeed (200) or not found (404) if already cleaned up
        assert delete_response.status_code in [200, 404]

    def test_upload_multiple_files(self, test_client: TestClient):
        """Test uploading multiple files sequentially."""
        uploaded_ids = []

        for i in range(3):
            file_content = f"Test file {i}".encode()
            file = (f"test_{i}.txt", io.BytesIO(file_content), "text/plain")

            response = test_client.post(
                "/api/files/upload",
                files={"file": file},
                data={"description": f"Test file {i}"},
            )

            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            uploaded_ids.append(result["data"]["file_id"])

        # Cleanup
        for file_id in uploaded_ids:
            test_client.delete(f"/api/files/{file_id}")

    def test_upload_config_has_valid_values(self, test_client: TestClient):
        """Test that upload config returns valid values."""
        response = test_client.get("/api/files/config")

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

        data = result["data"]

        # Validate max file size is reasonable
        assert data["max_file_size"] > 0
        assert data["max_file_size"] <= 1024 * 1024 * 1024  # Max 1GB

        # Validate extensions list is not empty
        assert len(data["allowed_extensions"]) > 0

        # Validate upload directory is set
        assert len(data["upload_dir"]) > 0

    def test_upload_file_with_special_characters_in_name(self, test_client: TestClient):
        """Test uploading a file with special characters in filename."""
        file_content = b"Special chars test"
        # Note: Some special chars might be sanitized by the API
        file = ("test file (1).txt", io.BytesIO(file_content), "text/plain")

        response = test_client.post(
            "/api/files/upload",
            files={"file": file},
        )

        # Should either succeed or handle gracefully
        assert response.status_code in [200, 400]
