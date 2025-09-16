from typing import Any, Callable, Dict, Optional


class StepRegistry:
    """Simple registry for step implementations."""

    def __init__(self) -> None:
        self._steps: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> None:
        if not callable(func):
            raise TypeError("step func must be callable")
        self._steps[name] = func

    def get(self, name: str) -> Optional[Callable[..., Any]]:
        return self._steps.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._steps

