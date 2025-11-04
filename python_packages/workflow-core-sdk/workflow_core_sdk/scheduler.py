import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo
from croniter import croniter

from .db.service import DatabaseService
from .db.database import engine
from .services.execution_service import ExecutionService
from sqlmodel import Session

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
        # Scan workflows for schedules (open/close session promptly)
        db = DatabaseService()
        with Session(engine) as session:
            workflows = db.list_workflows(session, limit=500, offset=0)
        now = datetime.now(timezone.utc)

        for wf in workflows:
            prev_next_run_utc: Optional[datetime] = None
            cfg = wf.get("configuration") or {}
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
            elif mode == "cron":
                expr = (schedule.get("cron") or "").strip()
                if not expr:
                    continue
                tzname = schedule.get("timezone") or "UTC"
                try:
                    tz = ZoneInfo(tzname)
                except Exception:
                    tz = ZoneInfo("UTC")

                # Decide seconds position handling for 6-field crons (Quartz-style seconds first vs default seconds last)
                sab = bool(
                    schedule.get("seconds_at_beginning") or schedule.get("second_at_beginning")
                )  # seconds field is first when sab=True

                # Determine the next scheduled run (UTC) using croniter
                next_iso = global_config.get("scheduler_next_run_at")
                next_run_utc: Optional[datetime] = None
                if isinstance(next_iso, str):
                    try:
                        nr = datetime.fromisoformat(next_iso.replace("Z", "+00:00"))
                        next_run_utc = nr if nr.tzinfo else nr.replace(tzinfo=timezone.utc)
                    except Exception:
                        next_run_utc = None
                if not next_run_utc:
                    # Compute the next run from 'now' and persist it so future ticks can compare to a stable target
                    base_local = now.astimezone(tz)
                    try:
                        next_local = croniter(expr, base_local, second_at_beginning=sab).get_next(datetime)
                        if next_local.tzinfo is None:
                            next_local = next_local.replace(tzinfo=tz)
                        next_run_utc = next_local.astimezone(timezone.utc)
                        # Persist the computed next run immediately
                        global_config["scheduler_next_run_at"] = next_run_utc.isoformat()
                        cfg["global_config"] = global_config
                        # Save using a short-lived session to avoid pool starvation
                        from sqlmodel import Session as _Sess
                        from .db.database import engine as _eng

                        with _Sess(_eng) as _s:
                            db.save_workflow(_s, wf["id"], cfg)
                    except Exception as e:
                        logger.warning(f"Invalid cron '{expr}' on workflow {wf.get('id')}: {e}")
                        continue
                else:
                    # Guard: if persisted next_run is at or behind last_run, advance until strictly after 'now'
                    try:
                        if last_run and next_run_utc <= last_run:
                            base_local = last_run.astimezone(tz)
                            # Advance until after now (handles catch-up bursts)
                            while True:
                                tmp_local = croniter(expr, base_local, second_at_beginning=sab).get_next(datetime)
                                if tmp_local.tzinfo is None:
                                    tmp_local = tmp_local.replace(tzinfo=tz)
                                tmp_utc = tmp_local.astimezone(timezone.utc)
                                if tmp_utc > now:
                                    next_run_utc = tmp_utc
                                    break
                                base_local = tmp_local
                            global_config["scheduler_next_run_at"] = next_run_utc.isoformat()
                            cfg["global_config"] = global_config
                            from sqlmodel import Session as _Sess
                            from .db.database import engine as _eng

                            with _Sess(_eng) as _s:
                                db.save_workflow(_s, wf["id"], cfg)
                    except Exception:
                        pass
                # Remember the previously computed next_run_utc so we can advance from it after firing
                prev_next_run_utc = next_run_utc
                if now >= next_run_utc:
                    due = True
            else:
                continue

            if not due:
                continue

            # Apply jitter if set
            if jitter > 0:
                await asyncio.sleep(random.randint(0, jitter))

            # Fire execution via ExecutionService
            try:
                # Use a single short-lived DB session for both execution and update
                with Session(engine) as exec_session:
                    # Get workflow engine from app state
                    workflow_engine = app.state.workflow_engine

                    # Execute workflow using the service
                    await ExecutionService.execute_workflow(
                        workflow_id=wf["id"],
                        session=exec_session,
                        workflow_engine=workflow_engine,
                        backend=backend,
                        metadata={"source": "scheduler"},
                        wait=False,  # Don't wait for completion
                    )

                    # Update last run timestamp and next run using the same session
                    global_config["scheduler_last_run_at"] = now.isoformat()
                    if mode == "cron":
                        try:
                            tzname = schedule.get("timezone") or "UTC"
                            tz = ZoneInfo(tzname)
                        except Exception:
                            tz = ZoneInfo("UTC")
                        # seconds-at-beginning flag (Quartz-style): allow schedule to indicate seconds is the 1st field
                        sab = bool(schedule.get("seconds_at_beginning") or schedule.get("second_at_beginning"))
                        # Advance from the previously computed next_run to ensure monotonic stepping
                        # Use the actual time after the execution to avoid setting a next_run in the past
                        now_exec = datetime.now(timezone.utc)
                        base_local = prev_next_run_utc.astimezone(tz) if prev_next_run_utc else now_exec.astimezone(tz)
                        expr2 = (schedule.get("cron") or "").strip()
                        if expr2:
                            try:
                                upcoming_local = croniter(expr2, base_local, second_at_beginning=sab).get_next(datetime)
                                if upcoming_local.tzinfo is None:
                                    upcoming_local = upcoming_local.replace(tzinfo=tz)
                                upcoming_utc = upcoming_local.astimezone(timezone.utc)
                                # Ensure next_run is strictly in the future relative to now_exec
                                while upcoming_utc <= now_exec:
                                    upcoming_local = croniter(expr2, upcoming_local, second_at_beginning=sab).get_next(datetime)
                                    if upcoming_local.tzinfo is None:
                                        upcoming_local = upcoming_local.replace(tzinfo=tz)
                                    upcoming_utc = upcoming_local.astimezone(timezone.utc)
                                global_config["scheduler_next_run_at"] = upcoming_utc.isoformat()
                            except Exception:
                                pass
                    cfg["global_config"] = global_config
                    db.save_workflow(exec_session, wf["id"], cfg)
            except Exception as e:
                logger.warning(f"Failed to execute scheduled workflow {wf['id']}: {e}")
