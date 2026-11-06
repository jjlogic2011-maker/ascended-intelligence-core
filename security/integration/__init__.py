"""TrustOS integration adapters (OpenAI-style tool interception).

Additive only. Interception is table stakes; product differentiation is the four gaps.
"""
from .interceptor import (
    ToolRequest,
    InterceptorResult,
    TrustOSInterceptor,
    build_default_interceptor,
    classify_tool,
    is_consequential,
    preview_policy,
)

__all__ = [
    "ToolRequest",
    "InterceptorResult",
    "TrustOSInterceptor",
    "build_default_interceptor",
    "classify_tool",
    "is_consequential",
    "preview_policy",
]
