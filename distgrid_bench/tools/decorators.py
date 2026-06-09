from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def agent_tool(func: F) -> F:
    """Mark a callable as benchmark tool-compatible.

    The original project used the agent package's decorator. The benchmark keeps
    the marker lightweight so tools can be discovered by agents without pulling
    in any specific agent implementation.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    setattr(wrapper, "is_agent_tool", True)
    return wrapper  # type: ignore[return-value]

