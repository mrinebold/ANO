"""
Pipeline Module

Provides pipeline orchestration for multi-stage agent execution with
support for sequential and parallel execution, validation, and result tracking.
"""

from pipeline.pipeline import Pipeline, PipelineResult, Stage
from pipeline.coordinator import PipelineCoordinator

__all__ = [
    "Pipeline",
    "PipelineResult",
    "Stage",
    "PipelineCoordinator",
]
