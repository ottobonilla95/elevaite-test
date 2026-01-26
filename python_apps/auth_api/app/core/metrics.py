from __future__ import annotations

# Minimal, safe metrics helpers for Redis instrumentation and endpoint metrics.
# Uses OpenTelemetry Metrics API if available; otherwise becomes a no-op.

from typing import Optional, Dict

try:
    from opentelemetry.metrics import get_meter  # type: ignore
except Exception:  # pragma: no cover
    get_meter = None  # type: ignore


class _NoOpCounter:
    def add(self, *_args, **_kwargs):
        pass


class _NoOpHistogram:
    def record(self, *_args, **_kwargs):
        pass


class _Metrics:
    def __init__(self) -> None:
        if get_meter is None:
            self._meter = None
        else:
            try:
                self._meter = get_meter("auth-api")
            except Exception:
                self._meter = None

        # Redis-level metrics
        self.redis_hits = self._create_counter(
            "auth_redis_hits", "Count of Redis fast-path hits"
        )
        self.redis_misses = self._create_counter(
            "auth_redis_misses", "Count of Redis fast-path misses"
        )
        self.redis_errors = self._create_counter(
            "auth_redis_errors", "Count of Redis errors"
        )
        self.redis_debounce_acquired = self._create_counter(
            "auth_redis_debounce_acquired", "Count of debounce acquisitions"
        )
        self.redis_debounce_skipped = self._create_counter(
            "auth_redis_debounce_skipped", "Count of debounce skips"
        )
        self.redis_bulk_extend = self._create_counter(
            "auth_redis_bulk_extend",
            "Count of sessions targeted for bulk TTL extension",
        )
        self.redis_session_mark = self._create_counter(
            "auth_redis_session_mark", "Count of session marks in Redis"
        )
        self.redis_session_remove = self._create_counter(
            "auth_redis_session_remove", "Count of session removals from Redis"
        )
        self.redis_available = self._create_counter(
            "auth_redis_available",
            "Count of Redis availability signals (1x per process)",
        )
        self.redis_unavailable = self._create_counter(
            "auth_redis_unavailable",
            "Count of Redis unavailability signals (1x per process)",
        )

        # Endpoint metrics
        self.extend_session_success = self._create_counter(
            "auth_extend_session_success",
            "Count of successful extend-session responses",
        )
        self.extend_session_failure = self._create_counter(
            "auth_extend_session_failure", "Count of failed extend-session responses"
        )
        self.extend_session_db_fallback = self._create_counter(
            "auth_extend_session_db_fallback",
            "Count of times extend-session fell back to DB",
        )
        self.extend_session_db_write_through = self._create_counter(
            "auth_extend_session_db_write_through",
            "Count of DB write-through commits during extend-session",
        )
        self.extend_session_latency_ms = self._create_histogram(
            "auth_extend_session_latency_ms", "Latency of extend-session endpoint in ms"
        )

    def _create_counter(self, name: str, description: str):
        if self._meter is None:
            return _NoOpCounter()
        try:
            return self._meter.create_counter(name, unit="1", description=description)  # type: ignore[attr-defined]
        except Exception:
            # Older/newer API mismatches or missing SDK: fallback to no-op
            return _NoOpCounter()

    def _create_histogram(self, name: str, description: str):
        if self._meter is None:
            return _NoOpHistogram()
        try:
            return self._meter.create_histogram(
                name, unit="ms", description=description
            )  # type: ignore[attr-defined]
        except Exception:
            return _NoOpHistogram()

    def _attrs(
        self,
        operation: str,
        tenant_id: Optional[str] = None,
        extra: Optional[Dict[str, str]] = None,
    ):
        attrs = {"operation": operation}
        if tenant_id:
            attrs["tenant_id"] = tenant_id
        if extra:
            attrs.update(extra)
        return attrs

    # Redis helpers
    def hit(self, operation: str, tenant_id: Optional[str] = None):
        self.redis_hits.add(1, attributes=self._attrs(operation, tenant_id))  # type: ignore[arg-type]

    def miss(self, operation: str, tenant_id: Optional[str] = None):
        self.redis_misses.add(1, attributes=self._attrs(operation, tenant_id))  # type: ignore[arg-type]

    def error(self, operation: str, tenant_id: Optional[str] = None):
        self.redis_errors.add(1, attributes=self._attrs(operation, tenant_id))  # type: ignore[arg-type]

    def debounce_acquired(self, operation: str, tenant_id: Optional[str] = None):
        self.redis_debounce_acquired.add(
            1, attributes=self._attrs(operation, tenant_id)
        )  # type: ignore[arg-type]

    def debounce_skipped(self, operation: str, tenant_id: Optional[str] = None):
        self.redis_debounce_skipped.add(1, attributes=self._attrs(operation, tenant_id))  # type: ignore[arg-type]

    def bulk_extended(self, tenant_id: Optional[str], count: int):
        self.redis_bulk_extend.add(
            count, attributes=self._attrs("extend_all", tenant_id)
        )  # type: ignore[arg-type]

    def session_marked(self, tenant_id: Optional[str]):
        self.redis_session_mark.add(
            1, attributes=self._attrs("mark_session", tenant_id)
        )  # type: ignore[arg-type]

    def session_removed(self, tenant_id: Optional[str]):
        self.redis_session_remove.add(
            1, attributes=self._attrs("remove_session", tenant_id)
        )  # type: ignore[arg-type]

    def availability(self, available: bool):
        # No attributes; one-time signal is good enough
        if available:
            self.redis_available.add(1)
        else:
            self.redis_unavailable.add(1)

    # Endpoint helpers
    def endpoint_success(self, tenant_id: Optional[str] = None):
        self.extend_session_success.add(
            1, attributes={"tenant_id": tenant_id} if tenant_id else None
        )  # type: ignore[arg-type]

    def endpoint_failure(self, tenant_id: Optional[str] = None):
        self.extend_session_failure.add(
            1, attributes={"tenant_id": tenant_id} if tenant_id else None
        )  # type: ignore[arg-type]

    def endpoint_db_fallback(self, tenant_id: Optional[str] = None):
        self.extend_session_db_fallback.add(
            1, attributes={"tenant_id": tenant_id} if tenant_id else None
        )  # type: ignore[arg-type]

    def endpoint_db_write_through(self, tenant_id: Optional[str] = None):
        self.extend_session_db_write_through.add(
            1, attributes={"tenant_id": tenant_id} if tenant_id else None
        )  # type: ignore[arg-type]

    def endpoint_latency_ms(self, value_ms: float, tenant_id: Optional[str] = None):
        self.extend_session_latency_ms.record(
            value_ms, attributes={"tenant_id": tenant_id} if tenant_id else None
        )  # type: ignore[arg-type]


metrics = _Metrics()
