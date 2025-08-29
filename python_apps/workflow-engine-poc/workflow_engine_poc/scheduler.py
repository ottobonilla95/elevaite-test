import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from .db.service import DatabaseService
from .db.database import get_db_session
from .routers.workflows import execute_workflow_by_id  # reuse endpoint logic

logger = logging.getLogger(__name__)


class WorkflowScheduler:
    def __init__(self, poll_interval_seconds: int = 15):
        self.poll_interval_seconds = poll_interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self, app):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop(app))
        logger.info("✅ WorkflowScheduler started (poll=%ss)", self.poll_interval_seconds)

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except Exception:
                pass
            self._task = None
        logger.info("🛑 WorkflowScheduler stopped")

    async def _run_loop(self, app):
        while self._running:
            try:
                await self._tick(app)
            except Exception as e:
                logger.warning(f"Scheduler tick error: {e}")
            await asyncio.sleep(self.poll_interval_seconds)

    async def _tick(self, app):
        # Scan workflows for schedules
        session = get_db_session()
        db = DatabaseService()
        workflows = db.list_workflows(session, limit=500, offset=0)
        now = datetime.now(timezone.utc)

        for wf in workflows:
            cfg = (wf.get("configuration") or {})
            steps = cfg.get("steps") or []
            trigger = next((s for s in steps if s.get("step_type") == "trigger"), None)
            trig_params = (trigger or {}).get("parameters") or {}
            schedule = trig_params.get("schedule") or {}
            if not (isinstance(schedule, dict) and schedule.get("enabled")):
                continue

            mode = (schedule.get("mode") or "interval").lower()
            backend = (schedule.get("backend") or "dbos").lower()
            jitter = int(schedule.get("jitter_seconds") or 0)

            # Track last_run in workflow global_config
            global_config = cfg.get("global_config") or {}
            last_run_iso = global_config.get("scheduler_last_run_at")
            last_run = None
            if isinstance(last_run_iso, str):
                try:
                    last_run = datetime.fromisoformat(last_run_iso.replace("Z", "+00:00"))
                except Exception:
                    last_run = None

            due = False
            next_after = None

            if mode == "interval":
                interval = max(5, int(schedule.get("interval_seconds") or 0))
                if not last_run:
                    due = True
                else:
                    next_after = last_run + timedelta(seconds=interval)
                    if now >= next_after:
                        due = True
            else:
                # cron mode not yet implemented: skip for now
                continue

            if not due:
                continue

            # Apply jitter if set
            if jitter > 0:
                await asyncio.sleep(random.randint(0, jitter))

            # Fire execution via internal engine path using the same router logic
            try:
                # Simulate a minimal request-like object for execute_workflow_by_id
                class DummyRequest:
                    def __init__(self, app):
                        self.app = app
                        self.headers = {"content-type": "application/json"}

                    async def json(self):
                        # No payload; use schedule defaults; source metadata for analytics
                        return {"metadata": {"source": "scheduler"}}

                req = DummyRequest(app)
                # Choose endpoint with backend path param
                await execute_workflow_by_id(  # type: ignore
                    workflow_id=wf["id"],
                    request=req,
                    backend=backend,
                )

                # Update last run timestamp in workflow configuration
                global_config["scheduler_last_run_at"] = now.isoformat()
                cfg["global_config"] = global_config
                db.save_workflow(session, wf["id"], cfg)
            except Exception as e:
                logger.warning(f"Failed to execute scheduled workflow {wf['id']}: {e}")

