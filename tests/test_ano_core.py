"""Tests for ano_core module — settings, types, errors, environment, logging."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from unittest.mock import patch

import pytest

from ano_core.environment import EnvironmentTier, TierRestrictions, get_tier_restrictions
from ano_core.errors import (
    ANOError,
    AgentExecutionError,
    ChannelError,
    ConfigurationError,
    LLMBackendError,
    PolicyViolationError,
    RegistryError,
)
from ano_core.logging import JsonFormatter, get_agent_logger, setup_logging
from ano_core.settings import AnoProfile, AnoSettings
from ano_core.types import (
    AgentContext,
    AgentInput,
    AgentMetadata,
    AgentOutput,
    OrgProfile,
    PolicyReport,
    PolicyViolation,
)


# --- Settings ---


class TestAnoSettings:
    def test_default_settings(self):
        settings = AnoSettings(ANO_ENV="development")
        assert settings.ANO_PROFILE == AnoProfile.MINIMAL
        assert settings.ANO_ENV == "development"
        assert settings.ANO_DEBUG is False
        assert settings.ANO_LOG_LEVEL == "INFO"
        assert settings.DEFAULT_LLM_PROVIDER == "anthropic"

    def test_features_property_empty(self):
        settings = AnoSettings(ANO_FEATURES="")
        assert settings.features == frozenset()

    def test_features_property_parses_csv(self):
        settings = AnoSettings(ANO_FEATURES="audit_trail,policy_presets,enhanced_compliance")
        assert settings.features == frozenset(
            {"audit_trail", "policy_presets", "enhanced_compliance"}
        )

    def test_has_feature(self):
        settings = AnoSettings(ANO_FEATURES="audit_trail,policy_presets")
        assert settings.has_feature("audit_trail") is True
        assert settings.has_feature("nonexistent") is False

    def test_profile_enum(self):
        assert AnoProfile.MINIMAL.value == "minimal"
        assert AnoProfile.MSR.value == "msr"


# --- Types ---


class TestOrgProfile:
    def test_create_minimal(self):
        profile = OrgProfile(org_name="Test Org", org_type="enterprise")
        assert profile.org_name == "Test Org"
        assert profile.org_type == "enterprise"
        assert profile.departments == []
        assert profile.concerns == []
        assert profile.metadata == {}

    def test_create_full(self):
        profile = OrgProfile(
            org_name="City of Springfield",
            org_type="municipal",
            state="Illinois",
            population="120000",
            departments=["IT", "Finance", "Public Works"],
            concerns=["data privacy", "transparency"],
        )
        assert len(profile.departments) == 3
        assert "data privacy" in profile.concerns


class TestAgentContext:
    def test_create(self, sample_org_profile):
        ctx = AgentContext(org_profile=sample_org_profile)
        assert ctx.pipeline_state == {}
        assert ctx.upstream_outputs == {}

    def test_with_upstream_outputs(self, sample_org_profile):
        ctx = AgentContext(
            org_profile=sample_org_profile,
            upstream_outputs={"researcher": {"findings": ["item1"]}},
        )
        assert "researcher" in ctx.upstream_outputs


class TestAgentInput:
    def test_create(self, sample_context):
        inp = AgentInput(data={"query": "test"}, context=sample_context)
        assert inp.data["query"] == "test"
        assert inp.policy_attachments == []


class TestAgentMetadata:
    def test_create(self):
        meta = AgentMetadata(
            agent_name="test-agent",
            version="1.0.0",
            started_at=datetime.now(),
            llm_calls=2,
            tokens_used=500,
        )
        assert meta.agent_name == "test-agent"
        assert meta.llm_calls == 2


class TestPolicyViolation:
    def test_create(self):
        violation = PolicyViolation(
            gate="test-success",
            severity="error",
            message="Tests failed",
            remediation="Run tests",
        )
        assert violation.gate == "test-success"
        assert violation.severity == "error"


class TestPolicyReport:
    def test_create_empty(self):
        report = PolicyReport()
        assert report.gates_passed == []
        assert report.gates_failed == []
        assert report.violations == []

    def test_create_with_violations(self):
        violation = PolicyViolation(
            gate="security",
            severity="error",
            message="Vuln found",
            remediation="Fix it",
        )
        report = PolicyReport(
            gates_passed=["test-success"],
            gates_failed=["security"],
            violations=[violation],
        )
        assert len(report.violations) == 1


class TestAgentOutput:
    def test_create(self):
        meta = AgentMetadata(
            agent_name="test",
            version="1.0.0",
            started_at=datetime.now(),
        )
        output = AgentOutput(
            result={"answer": "42"},
            metadata=meta,
        )
        assert output.result["answer"] == "42"
        assert output.policy_report is None


# --- Errors ---


class TestErrorHierarchy:
    def test_base_error(self):
        err = ANOError("test error")
        assert str(err) == "test error"
        assert err.message == "test error"

    def test_base_error_with_extras(self):
        err = ANOError("test error", code=42, context="testing")
        assert "code=42" in str(err)
        assert "context=testing" in str(err)

    def test_agent_execution_error(self):
        err = AgentExecutionError("failed", agent_name="test-agent")
        assert err.agent_name == "test-agent"
        assert "agent_name=test-agent" in str(err)
        assert isinstance(err, ANOError)

    def test_llm_backend_error(self):
        err = LLMBackendError("rate limited", provider="anthropic", status_code=429)
        assert err.provider == "anthropic"
        assert err.status_code == 429
        assert isinstance(err, ANOError)

    def test_policy_violation_error(self):
        err = PolicyViolationError("blocked", violations=[{"gate": "test"}])
        assert len(err.violations) == 1
        assert isinstance(err, ANOError)

    def test_registry_error(self):
        err = RegistryError("not found")
        assert isinstance(err, ANOError)

    def test_configuration_error(self):
        err = ConfigurationError("bad config")
        assert isinstance(err, ANOError)

    def test_channel_error(self):
        err = ChannelError("send failed")
        assert isinstance(err, ANOError)


# --- Environment ---


class TestEnvironmentTier:
    def test_enum_values(self):
        assert EnvironmentTier.DEVELOPMENT.value == "development"
        assert EnvironmentTier.TEST.value == "test"
        assert EnvironmentTier.PRODUCTION.value == "production"

    def test_development_restrictions(self):
        restrictions = get_tier_restrictions(EnvironmentTier.DEVELOPMENT)
        assert restrictions.requires_approval is False
        assert restrictions.max_concurrent_agents == 10
        assert "database_delete" in restrictions.allowed_operations
        assert restrictions.blocked_operations == []

    def test_test_restrictions(self):
        restrictions = get_tier_restrictions(EnvironmentTier.TEST)
        assert restrictions.requires_approval is True
        assert restrictions.max_concurrent_agents == 5
        assert "database_delete" in restrictions.blocked_operations

    def test_production_restrictions(self):
        restrictions = get_tier_restrictions(EnvironmentTier.PRODUCTION)
        assert restrictions.requires_approval is True
        assert restrictions.max_concurrent_agents == 3
        assert "database_write" in restrictions.blocked_operations
        assert "file_write" in restrictions.blocked_operations


# --- Logging ---


class TestLogging:
    def test_get_agent_logger(self):
        logger = get_agent_logger("test-agent")
        assert isinstance(logger, logging.LoggerAdapter)
        assert logger.extra["agent_name"] == "test-agent"

    def test_json_formatter(self):
        formatter = JsonFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        parsed = json.loads(result)
        assert parsed["message"] == "test message"
        assert parsed["level"] == "INFO"

    def test_setup_logging(self):
        setup_logging(level="WARNING", json_format=False)
        root = logging.getLogger()
        assert root.level == logging.WARNING
