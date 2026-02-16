"""
Pipeline Coordinator

Executes pipelines by managing agent instantiation, policy enforcement,
and data flow between stages.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from ano_core.errors import AgentExecutionError, PolicyViolationError
from ano_core.logging import get_agent_logger
from ano_core.types import AgentContext, AgentInput, AgentOutput

from pipeline.pipeline import Pipeline, PipelineResult, Stage

logger = get_agent_logger(__name__)


class PipelineCoordinator:
    """
    Executes a pipeline, managing agent instantiation and data flow.

    Handles:
    - Agent instantiation from registry
    - Policy pre/post checks (if policy engine provided)
    - Sequential and parallel execution
    - Context passing between stages
    - Error handling and rollback
    """

    def __init__(
        self,
        pipeline: Pipeline,
        registry: Any,
        policy_engine: Any | None = None,
    ) -> None:
        """
        Initialize the coordinator.

        Args:
            pipeline: Pipeline to execute
            registry: AgentRegistry for instantiating agents
            policy_engine: Optional PolicyEngine for enforcement
        """
        self.pipeline = pipeline
        self.registry = registry
        self.policy_engine = policy_engine

        # Validate pipeline against registry
        missing = self.pipeline.validate(registry)
        if missing:
            raise ValueError(
                f"Pipeline '{pipeline.name}' references missing agents: {missing}"
            )

        logger.info(
            f"PipelineCoordinator initialized for pipeline '{pipeline.name}'"
        )

    async def run(
        self,
        initial_input: dict[str, Any],
        context: AgentContext,
    ) -> PipelineResult:
        """
        Execute the full pipeline.

        For each stage:
        1. Instantiate agents from registry
        2. Run policy pre-check (if policy engine provided)
        3. Execute agent(s) - parallel if stage.parallel
        4. Run policy post-check (if policy engine provided)
        5. Pass outputs to next stage via context.upstream_outputs

        Args:
            initial_input: Initial input data for the pipeline
            context: Agent context (org profile, pipeline state)

        Returns:
            PipelineResult with success status, outputs, and timing
        """
        start_time = time.perf_counter()
        result = PipelineResult(success=False)
        current_input = initial_input.copy()

        logger.info(f"Starting pipeline '{self.pipeline.name}' execution")

        try:
            for stage in self.pipeline.stages:
                logger.info(
                    f"Executing stage '{stage.name}' "
                    f"({'parallel' if stage.parallel else 'sequential'})"
                )

                try:
                    stage_outputs = await self._execute_stage(
                        stage, current_input, context
                    )

                    # Merge stage outputs into overall result
                    result.outputs.update(stage_outputs)
                    result.stages_completed.append(stage.name)

                    # Update context with outputs for next stage
                    context.upstream_outputs.update(stage_outputs)

                    logger.info(
                        f"Stage '{stage.name}' completed successfully with "
                        f"{len(stage_outputs)} agent outputs"
                    )

                except Exception as e:
                    result.stages_failed.append(stage.name)
                    result.error = str(e)

                    logger.error(
                        f"Stage '{stage.name}' failed: {e}",
                        exc_info=True,
                    )

                    # If stage is required, stop pipeline
                    if stage.required:
                        logger.error(
                            f"Required stage '{stage.name}' failed, "
                            f"aborting pipeline"
                        )
                        break
                    else:
                        logger.warning(
                            f"Optional stage '{stage.name}' failed, continuing"
                        )

            # Pipeline succeeds if all required stages completed
            result.success = len(result.stages_failed) == 0 or not any(
                stage.required and stage.name in result.stages_failed
                for stage in self.pipeline.stages
            )

        except Exception as e:
            result.error = f"Pipeline execution error: {e}"
            logger.error(result.error, exc_info=True)

        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            result.duration_ms = duration_ms

            logger.info(
                f"Pipeline '{self.pipeline.name}' finished in {duration_ms:.2f}ms - "
                f"Success: {result.success}, "
                f"Completed: {len(result.stages_completed)}, "
                f"Failed: {len(result.stages_failed)}"
            )

        return result

    async def _execute_stage(
        self,
        stage: Stage,
        stage_input: dict[str, Any],
        context: AgentContext,
    ) -> dict[str, Any]:
        """
        Execute a single stage.

        Args:
            stage: Stage to execute
            stage_input: Input data for this stage
            context: Execution context

        Returns:
            Dictionary mapping agent names to their outputs

        Raises:
            AgentExecutionError: If agent execution fails
            PolicyViolationError: If policy check fails
        """
        stage_outputs: dict[str, Any] = {}

        if stage.parallel and len(stage.agents) > 1:
            # Execute agents in parallel
            tasks = [
                self._execute_agent(agent_name, stage_input, context)
                for agent_name in stage.agents
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for agent_name, result in zip(stage.agents, results):
                if isinstance(result, Exception):
                    raise AgentExecutionError(
                        f"Agent '{agent_name}' failed: {result}"
                    )
                stage_outputs[agent_name] = result
        else:
            # Execute agents sequentially
            for agent_name in stage.agents:
                output = await self._execute_agent(agent_name, stage_input, context)
                stage_outputs[agent_name] = output

                # Make this agent's output available to next agent in stage
                context.upstream_outputs[agent_name] = output

        return stage_outputs

    async def _execute_agent(
        self,
        agent_name: str,
        agent_input_data: dict[str, Any],
        context: AgentContext,
    ) -> AgentOutput:
        """
        Execute a single agent with policy checks.

        Args:
            agent_name: Name of the agent to execute
            agent_input_data: Input data for the agent
            context: Execution context

        Returns:
            AgentOutput from the agent

        Raises:
            AgentExecutionError: If agent execution fails
            PolicyViolationError: If policy check fails
        """
        logger.debug(f"Executing agent '{agent_name}'")

        # Get agent instance from registry
        agent = self.registry.get_agent(agent_name)
        if agent is None:
            raise AgentExecutionError(f"Agent '{agent_name}' not found in registry")

        # Build agent input
        agent_input = AgentInput(
            data=agent_input_data,
            context=context,
        )

        # Pre-execution policy check
        if self.policy_engine:
            logger.debug(f"Running pre-execution policy check for '{agent_name}'")
            pre_check = await self.policy_engine.check_pre_execution(
                agent_name, agent_input
            )
            if not pre_check.passed:
                raise PolicyViolationError(
                    f"Pre-execution policy check failed for '{agent_name}': "
                    f"{pre_check.violations}"
                )

        # Execute agent
        try:
            output = await agent.execute(agent_input)
        except Exception as e:
            raise AgentExecutionError(
                f"Agent '{agent_name}' execution failed: {e}"
            ) from e

        # Post-execution policy check
        if self.policy_engine:
            logger.debug(f"Running post-execution policy check for '{agent_name}'")
            post_check = await self.policy_engine.check_post_execution(
                agent_name, agent_input, output
            )
            if not post_check.passed:
                raise PolicyViolationError(
                    f"Post-execution policy check failed for '{agent_name}': "
                    f"{post_check.violations}"
                )

        logger.debug(f"Agent '{agent_name}' completed successfully")
        return output
