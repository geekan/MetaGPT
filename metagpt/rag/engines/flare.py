"""FLARE Engine.

Use llamaindex's FLAREInstructQueryEngine as FLAREEngine, which accepts other engines as parameters.
For example, Create a simple engine, and then pass it to FLAREEngine.
"""

from llama_index.core.query_engine import (  # noqa: F401
    FLAREInstructQueryEngine as FLAREEngine,
)
