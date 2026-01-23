"""
Thinking/Reasoning configuration for LLM providers.

This module centralizes the configuration for thinking/reasoning features
across different LLM providers. Each provider has different parameters and
defaults for enabling thinking mode.

Provider-specific settings:
- Gemini: thinking_budget (int), thinking_level (str: minimal/low/medium/high)
- OpenAI: reasoning_summary (str: auto/concise/detailed)
- Bedrock: thinking_budget_tokens (int, min 1024)
"""

from typing import Any, Dict, Optional

from ..models.text_generation.core.interfaces import TextGenerationType


# Default thinking configuration per provider
THINKING_DEFAULTS: Dict[str, Dict[str, Any]] = {
    TextGenerationType.GEMINI: {
        # Gemini 3: use thinking_level (minimal, low, medium, high)
        # Gemini 2.5: use thinking_budget (number of tokens)
        # Default to high for best reasoning quality
        "thinking_level": "high",
    },
    TextGenerationType.OPENAI: {
        # OpenAI reasoning models (o1, o3, o4-mini) use reasoning summary
        # Options: auto, concise, detailed
        "reasoning_summary": "auto",
    },
    TextGenerationType.BEDROCK: {
        # Claude extended thinking uses budget_tokens
        # Minimum is 1024, recommended starting point
        "thinking_budget_tokens": 1024,
    },
    TextGenerationType.ON_PREM: {
        # On-prem models may not support thinking
        # No defaults needed
    },
}


def apply_thinking_defaults(
    config: Dict[str, Any],
    provider_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apply provider-specific thinking defaults to the config.

    If enable_thinking is True and provider-specific settings are not provided,
    this function will add the appropriate defaults for the provider.

    Args:
        config: The original config dictionary
        provider_type: The provider type (e.g., "gemini_textgen", "openai_textgen")
                      If not provided, will try to get from config["type"]

    Returns:
        A new config dictionary with thinking defaults applied
    """
    if not config:
        return config

    # Make a copy to avoid mutating the original
    result = config.copy()

    # Only apply defaults if thinking is enabled
    if not result.get("enable_thinking"):
        return result

    # Get provider type from config if not provided
    provider_type = provider_type or result.get("type")
    if not provider_type:
        return result

    # Get defaults for this provider
    defaults = THINKING_DEFAULTS.get(provider_type, {})

    # Apply defaults only for keys not already in config
    for key, value in defaults.items():
        if key not in result:
            result[key] = value

    return result

