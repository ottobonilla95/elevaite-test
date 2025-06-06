import logging
import sys
from typing import Dict, Optional
from opentelemetry import trace


class ColorizedFormatter(logging.Formatter):
    # ANSI color codes
    COLORS: Dict[str, str] = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
        "BOLD": "\033[1m",  # Bold
    }

    def __init__(self, use_colors: Optional[bool] = None):
        """
        Initialize the colorized formatter.

        Args:
            use_colors: Whether to use colors. If None, auto-detect based on terminal support.
        """
        # Auto-detect color support if not specified
        if use_colors is None:
            use_colors = self._supports_color()

        self.use_colors = use_colors

        base_format = "%(asctime)s | [ElevAIte Logger] | %(levelname)s | %(message)s"
        super().__init__(base_format, datefmt="%Y-%m-%d %H:%M:%S")

    def _supports_color(self) -> bool:
        """Check if the terminal supports colors."""
        # Check if we're in a terminal that supports colors
        if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
            return False

        # Check for common environment variables that indicate color support
        import os

        term = os.environ.get("TERM", "").lower()
        colorterm = os.environ.get("COLORTERM", "").lower()

        # Common terminals that support colors
        color_terms = ["xterm", "xterm-color", "xterm-256color", "screen", "tmux"]

        return (
            any(ct in term for ct in color_terms)
            or colorterm in ["truecolor", "24bit"]
            or "color" in term
        )

    def _get_trace_context(self) -> str:
        try:
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                span_context = current_span.get_span_context()
                if span_context.is_valid:
                    trace_id = format(span_context.trace_id, "032x")
                    span_id = format(span_context.span_id, "016x")
                    return f" | trace_id={trace_id[:16]}... span_id={span_id[:8]}..."
        except Exception:
            pass

        return ""

    def format(self, record: logging.LogRecord) -> str:
        # Get the base formatted message
        formatted = super().format(record)

        trace_context = self._get_trace_context()
        if trace_context:
            parts = formatted.split(" | ")
            if len(parts) >= 4:
                parts.insert(3, trace_context.strip(" | "))
                formatted = " | ".join(parts)

        if not self.use_colors:
            return formatted

        # Apply colors to the level name
        level_name = record.levelname
        color = self.COLORS.get(level_name, "")
        reset = self.COLORS["RESET"]
        bold = self.COLORS["BOLD"]

        # Replace the level name with a colorized version
        if color:
            colored_level = f"{color}{bold}{level_name}{reset}"
            formatted = formatted.replace(level_name, colored_level, 1)

        return formatted
