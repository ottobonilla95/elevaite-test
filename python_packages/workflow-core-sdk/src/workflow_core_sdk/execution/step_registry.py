from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class StepRegistryProtocol(Protocol):
    """Interface for a step registry used by workflow engines.

    This protocol mirrors the API shape used in the PoC so we can gradually
    port the concrete implementation into the SDK without breaking callers.
    """

    async def register_step(self, step_config: Dict[str, Any]) -> str:  # pragma: no cover - interface
        ...

    async def execute_step(  # pragma: no cover - interface
        self,
        step_type: str,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: Any,
    ) -> Any: ...

    async def register_builtin_steps(self) -> None:  # pragma: no cover - interface
        ...
