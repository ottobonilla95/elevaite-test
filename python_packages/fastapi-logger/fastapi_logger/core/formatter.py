"""Colorized formatter for the Elevaite Logger."""

import logging
import sys
from typing import Dict


class ColorizedFormatter(logging.Formatter):
    """A formatter that adds colors to log levels and puts date first."""
    
    # ANSI color codes
    COLORS: Dict[str, str] = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m',     # Reset
        'BOLD': '\033[1m',      # Bold
    }
    
    def __init__(self, use_colors: bool = None):
        """
        Initialize the colorized formatter.
        
        Args:
            use_colors: Whether to use colors. If None, auto-detect based on terminal support.
        """
        # Auto-detect color support if not specified
        if use_colors is None:
            use_colors = self._supports_color()
        
        self.use_colors = use_colors
        
        # Format: Date first, then level, then logger name, then message
        base_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        super().__init__(base_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    def _supports_color(self) -> bool:
        """Check if the terminal supports colors."""
        # Check if we're in a terminal that supports colors
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
        
        # Check for common environment variables that indicate color support
        import os
        term = os.environ.get('TERM', '').lower()
        colorterm = os.environ.get('COLORTERM', '').lower()
        
        # Common terminals that support colors
        color_terms = ['xterm', 'xterm-color', 'xterm-256color', 'screen', 'tmux']
        
        return (
            any(ct in term for ct in color_terms) or
            colorterm in ['truecolor', '24bit'] or
            'color' in term
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        # Get the base formatted message
        formatted = super().format(record)
        
        if not self.use_colors:
            return f"[elevAIte] {formatted}"
        
        # Apply colors to the level name
        level_name = record.levelname
        color = self.COLORS.get(level_name, '')
        reset = self.COLORS['RESET']
        bold = self.COLORS['BOLD']
        
        # Replace the level name with a colorized version
        if color:
            colored_level = f"{color}{bold}{level_name:<8}{reset}"
            formatted = formatted.replace(f"{level_name:<8}", colored_level, 1)
        
        return f"[elevAIte] {formatted}"
