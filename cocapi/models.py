"""
Pydantic model generation for cocapi responses
"""

import logging
from typing import Any, Dict, Union

try:
    from pydantic import BaseModel, create_model

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = None


def create_dynamic_model(
    response: Dict[str, Any], endpoint_type: str
) -> Union[Dict[str, Any], Any]:
    """
    Create a dynamic Pydantic model from JSON response

    Args:
        response: The JSON response data
        endpoint_type: Type of endpoint (clan, player, etc.)

    Returns:
        Either a Pydantic model instance or the original dict
    """
    if not PYDANTIC_AVAILABLE:
        logging.warning("Pydantic not available - returning dict response")
        return response

    if response.get("result") == "error":
        return response

    try:
        # Generate model name
        model_name = _generate_model_name(endpoint_type)

        # Determine field types from response
        field_definitions = _analyze_response_structure(response)

        # Create dynamic model
        DynamicModel = create_model(model_name, **field_definitions)

        # Create and return model instance
        return DynamicModel(**response)

    except Exception as e:
        logging.warning(f"Failed to create dynamic model: {e}")
        return response


def _generate_model_name(endpoint_type: str) -> str:
    """Generate a model name from endpoint type"""
    # Clean up endpoint type for class naming
    clean_type = endpoint_type.replace("/", "_").replace("-", "_")
    parts = clean_type.split("_")
    # Capitalize each part and join
    return "".join(word.capitalize() for word in parts if word) + "Model"


def _analyze_response_structure(data: Any, depth: int = 0) -> Dict[str, Any]:
    """Analyze response structure to determine field types"""
    if depth > 5:  # Prevent infinite recursion
        return {"value": (Any, ...)}

    field_definitions = {}

    if isinstance(data, dict):
        for key, value in data.items():
            if key.startswith("_"):  # Skip private fields
                continue

            field_type = _infer_field_type(value, depth + 1)
            # Make all fields optional to handle API variations
            field_definitions[key] = (field_type, None)

    elif isinstance(data, list) and data:
        # For lists, analyze the first item to infer structure
        first_item = data[0]
        if isinstance(first_item, dict):
            # Create a nested model for list items
            nested_fields = _analyze_response_structure(first_item, depth + 1)
            if nested_fields:
                # This would create a nested model, but for simplicity we'll use Any
                field_definitions["items"] = (Any, None)
        else:
            field_definitions["items"] = (Any, None)

    return field_definitions


def _infer_field_type(value: Any, depth: int = 0) -> Any:
    """Infer the appropriate type for a field value"""
    if value is None:
        return Any
    elif isinstance(value, bool):
        return bool
    elif isinstance(value, int):
        return int
    elif isinstance(value, float):
        return float
    elif isinstance(value, str):
        return str
    elif isinstance(value, list):
        return list  # For simplicity, just use list
    elif isinstance(value, dict):
        return dict  # For simplicity, use dict instead of nested models
    else:
        return Any


def validate_pydantic_available() -> bool:
    """Check if Pydantic is available for dynamic model creation"""
    return PYDANTIC_AVAILABLE


def get_pydantic_info() -> Dict[str, Any]:
    """Get information about Pydantic availability and version"""
    if not PYDANTIC_AVAILABLE:
        return {
            "available": False,
            "version": None,
            "message": "Pydantic not installed. Install with: pip install 'cocapi[pydantic]'",
        }

    try:
        import pydantic

        return {
            "available": True,
            "version": pydantic.VERSION,
            "message": "Pydantic available for dynamic model generation",
        }
    except Exception as e:
        return {
            "available": False,
            "version": None,
            "message": f"Pydantic import error: {e}",
        }
