"""
Input/Output Validation

Provides schema validation for agent inputs and outputs using Pydantic.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError


def validate_input(
    data: dict[str, Any],
    schema: dict[str, Any] | None,
) -> tuple[bool, list[str]]:
    """
    Validate input data against a JSON schema.

    If schema is None, validation always passes (no schema enforcement).

    Args:
        data: Input data to validate
        schema: JSON schema dict, or None to skip validation

    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if validation passed
        - error_messages: List of validation error strings (empty if valid)
    """
    if schema is None:
        # No schema provided, skip validation
        return True, []

    try:
        # Use Pydantic to validate against the schema
        # This assumes the schema is a valid Pydantic model schema
        # For simpler JSON schema validation, we could use jsonschema library
        # but Pydantic provides better integration with the rest of the codebase

        # For now, we'll do basic type checking
        # A more complete implementation would use jsonschema or convert to Pydantic model
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})

        errors = []

        # Check required fields
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Check field types (basic validation)
        for field, value in data.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type:
                    actual_type = type(value).__name__
                    type_map = {
                        "string": "str",
                        "integer": "int",
                        "number": ["int", "float"],
                        "boolean": "bool",
                        "array": "list",
                        "object": "dict",
                    }
                    expected_python_types = type_map.get(expected_type, expected_type)
                    if isinstance(expected_python_types, list):
                        if actual_type not in expected_python_types:
                            errors.append(
                                f"Field '{field}': expected {expected_type}, got {actual_type}"
                            )
                    elif actual_type != expected_python_types:
                        errors.append(
                            f"Field '{field}': expected {expected_type}, got {actual_type}"
                        )

        if errors:
            return False, errors
        return True, []

    except Exception as e:
        return False, [f"Schema validation error: {str(e)}"]


def validate_output(
    data: dict[str, Any],
    schema: dict[str, Any] | None,
) -> tuple[bool, list[str]]:
    """
    Validate output data against a JSON schema.

    If schema is None, validation always passes (no schema enforcement).

    Args:
        data: Output data to validate
        schema: JSON schema dict, or None to skip validation

    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if validation passed
        - error_messages: List of validation error strings (empty if valid)
    """
    # Output validation uses the same logic as input validation
    return validate_input(data, schema)
