"""Nsjail-based sandbox executor for secure code execution.

This module handles the actual execution of validated code within an Nsjail sandbox.
"""

import asyncio
import json
import logging
import os
import shutil
import stat
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SandboxResult:
    """Result from sandbox execution."""

    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int
    error: str | None = None


class SandboxExecutor:
    """Executes Python code in an Nsjail sandbox."""

    def __init__(
        self,
        nsjail_path: str | None = None,
        nsjail_config_path: str | None = None,
        sandbox_python_path: str | None = None,
        sandbox_tmp_dir: str | None = None,
    ):
        self.nsjail_path = nsjail_path or settings.nsjail_path
        self.nsjail_config_path = nsjail_config_path or settings.nsjail_config_path
        self.sandbox_python_path = sandbox_python_path or settings.sandbox_python_path
        self.sandbox_tmp_dir = sandbox_tmp_dir or settings.sandbox_tmp_dir

    def is_available(self) -> bool:
        """Check if Nsjail is available on the system."""
        return shutil.which(self.nsjail_path) is not None or Path(self.nsjail_path).exists()

    async def execute(
        self,
        code: str,
        timeout_seconds: int,
        memory_mb: int,
        input_data: dict | None = None,
    ) -> SandboxResult:
        """Execute code in the Nsjail sandbox.

        Args:
            code: Python code to execute
            timeout_seconds: Maximum execution time
            memory_mb: Maximum memory in MB
            input_data: Optional data to pass to the code as 'input_data' variable

        Returns:
            SandboxResult with stdout, stderr, exit_code, and timing
        """
        start_time = time.time()

        # Create a temporary directory for this execution
        with tempfile.TemporaryDirectory(prefix="sandbox_") as temp_dir:
            # Make temp directory traversable for nsjail bind mounts
            # nsjail with user namespaces needs o+x on parent dirs for bind mounts
            os.chmod(temp_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)  # 0755

            # Write the code to a temporary file
            code_file = Path(temp_dir) / "code.py"
            wrapper_code = self._create_wrapper_code(code, input_data)
            code_file.write_text(wrapper_code)

            # Make code file readable by all (needed for nsjail bind mount)
            os.chmod(code_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 0644

            try:
                result = await self._run_nsjail(
                    code_file=str(code_file),
                    timeout_seconds=timeout_seconds,
                    memory_mb=memory_mb,
                    temp_dir=temp_dir,
                )
            except Exception as e:
                logger.error(f"Sandbox execution failed: {e}")
                return SandboxResult(
                    stdout="",
                    stderr="",
                    exit_code=-1,
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    error=str(e),
                )

        execution_time_ms = int((time.time() - start_time) * 1000)
        result.execution_time_ms = execution_time_ms
        return result

    def _create_wrapper_code(self, code: str, input_data: dict | None) -> str:
        """Create wrapper code that injects input_data and handles output."""
        input_json = json.dumps(input_data) if input_data is not None else "None"

        wrapper = f"""
import json
import sys

# Inject input_data
input_data = {input_json}

# User code below
{code}
"""
        return wrapper

    async def _run_nsjail(
        self,
        code_file: str,
        timeout_seconds: int,
        memory_mb: int,
        temp_dir: str,
    ) -> SandboxResult:
        """Run the code file inside Nsjail."""
        # Check if nsjail is available - if not, run directly (for development)
        if not self.is_available():
            logger.warning("Nsjail not available, running code directly (UNSAFE - development only)")
            return await self._run_direct(code_file, timeout_seconds)

        # Build nsjail command
        memory_bytes = memory_mb * 1024 * 1024
        cmd = [
            self.nsjail_path,
            "--config",
            self.nsjail_config_path,
            "--time_limit",
            str(timeout_seconds + 5),  # Add buffer
            "--rlimit_as",
            str(memory_bytes),
            "--bindmount_ro",
            f"{code_file}:/tmp/code.py",
            "--",
            self.sandbox_python_path,
            "/tmp/code.py",
        ]

        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds + 10,  # Extra buffer for nsjail overhead
            )

            return SandboxResult(
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=process.returncode or 0,
                execution_time_ms=0,  # Will be set by caller
            )
        except asyncio.TimeoutError:
            if process is not None:
                process.kill()
            return SandboxResult(
                stdout="",
                stderr="",
                exit_code=-1,
                execution_time_ms=0,
                error="Execution timed out",
            )

    async def _run_direct(self, code_file: str, timeout_seconds: int) -> SandboxResult:
        """Run code directly without Nsjail (for development only).

        WARNING: This is NOT secure and should only be used in development.
        """
        cmd = ["python", code_file]

        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )

            return SandboxResult(
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=process.returncode or 0,
                execution_time_ms=0,
            )
        except asyncio.TimeoutError:
            if process is not None:
                process.kill()
            return SandboxResult(
                stdout="",
                stderr="",
                exit_code=-1,
                execution_time_ms=0,
                error="Execution timed out",
            )
