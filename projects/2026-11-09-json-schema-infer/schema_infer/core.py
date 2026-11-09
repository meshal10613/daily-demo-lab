"""Core inference and validation logic for JSON schemas."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from schema_infer.detector import detect_string_format


def get_json_type(val: Any) -> str:
    """Return JSON schema primitive type name."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "boolean"
    if isinstance(val, int):
        return "integer"
    if isinstance(val, float):
        return "number"
    if isinstance(val, str):
        return "string"
    if isinstance(val, list):
        return "array"
    if isinstance(val, dict):
        return "object"
    return "string"


class SchemaInferrer:
    """Infers JSON Schema Draft-07 definitions from example documents."""

    def __init__(self, detect_formats: bool = True, strict_required: bool = True):
        self.detect_formats = detect_formats
        self.strict_required = strict_required

    def infer(self, samples: Sequence[Any], title: Optional[str] = None) -> Dict[str, Any]:
        """Infer schema across a list of sample objects."""
        if not samples:
            schema = {"$schema": "http://json-schema.org/draft-07/schema#"}
            if title:
                schema["title"] = title
            return schema

        merged = self._merge_nodes(samples)
        root: Dict[str, Any] = {"$schema": "http://json-schema.org/draft-07/schema#"}
        if title:
            root["title"] = title
        root.update(merged)
        return root

    def _merge_nodes(self, values: Sequence[Any]) -> Dict[str, Any]:
        """Derive schema for a list of values belonging to the same position/property."""
        if not values:
            return {}

        by_type: Dict[str, List[Any]] = defaultdict(list)
        for val in values:
            t = get_json_type(val)
            by_type[t].append(val)

        type_names = sorted(by_type.keys())

        # Handle integers vs numbers: if both present, merge into number
        if "integer" in type_names and "number" in type_names:
            type_names.remove("integer")
            by_type["number"].extend(by_type.pop("integer"))

        schema: Dict[str, Any] = {}
        if len(type_names) == 1:
            schema["type"] = type_names[0]
        else:
            schema["type"] = type_names

        # Process object definitions
        if "object" in by_type:
            obj_samples = by_type["object"]
            schema.update(self._infer_object(obj_samples))

        # Process array definitions
        if "array" in by_type:
            arr_samples = by_type["array"]
            schema.update(self._infer_array(arr_samples))

        # Process string formats if applicable
        if "string" in by_type and self.detect_formats:
            formats = {detect_string_format(s) for s in by_type["string"]}
            # Format must match for all string samples (ignoring empty strings)
            non_empty_strings = [s for s in by_type["string"] if s != ""]
            if non_empty_strings:
                non_empty_formats = {detect_string_format(s) for s in non_empty_strings}
                if len(non_empty_formats) == 1 and None not in non_empty_formats:
                    schema["format"] = list(non_empty_formats)[0]

        return schema

    def _infer_object(self, objects: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(objects)
        prop_values: Dict[str, List[Any]] = defaultdict(list)
        prop_counts: Dict[str, int] = defaultdict(int)

        for obj in objects:
            for k, v in obj.items():
                prop_counts[k] += 1
                prop_values[k].append(v)

        properties: Dict[str, Any] = {}
        required: List[str] = []

        for prop_name in sorted(prop_values.keys()):
            properties[prop_name] = self._merge_nodes(prop_values[prop_name])
            if self.strict_required and prop_counts[prop_name] == total:
                required.append(prop_name)

        result: Dict[str, Any] = {"properties": properties}
        if required:
            result["required"] = sorted(required)
        return result

    def _infer_array(self, arrays: Sequence[List[Any]]) -> Dict[str, Any]:
        all_items: List[Any] = []
        for arr in arrays:
            all_items.extend(arr)

        if not all_items:
            return {"items": {}}

        item_schema = self._merge_nodes(all_items)
        return {"items": item_schema}


def infer_schema(samples: Union[Any, Sequence[Any]], title: Optional[str] = None, detect_formats: bool = True, strict_required: bool = True) -> Dict[str, Any]:
    """Convenience function to infer a JSON schema from a sample or list of samples."""
    inferrer = SchemaInferrer(detect_formats=detect_formats, strict_required=strict_required)
    if not isinstance(samples, (list, tuple)):
        samples = [samples]
    return inferrer.infer(samples, title=title)


def validate_instance(instance: Any, schema: Dict[str, Any], path: str = "$") -> Tuple[bool, List[str]]:
    """Validate a JSON instance against an inferred or standard Draft-07 schema.
    
    Returns (is_valid, list_of_error_messages).
    """
    errors: List[str] = []

    target_type = schema.get("type")
    if target_type:
        allowed_types = [target_type] if isinstance(target_type, str) else target_type
        actual_type = get_json_type(instance)
        
        # Handle integer accepted as number
        match = actual_type in allowed_types or (actual_type == "integer" and "number" in allowed_types)
        if not match:
            errors.append(f"{path}: Expected type {allowed_types}, got {actual_type}")
            return False, errors

    # String format check
    fmt = schema.get("format")
    if fmt and isinstance(instance, str) and instance:
        detected = detect_string_format(instance)
        if detected != fmt:
            errors.append(f"{path}: Value '{instance}' does not match format '{fmt}'")

    # Object validation
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        required = schema.get("required", [])
        for req in required:
            if req not in instance:
                errors.append(f"{path}: Missing required property '{req}'")

        for k, v in instance.items():
            if k in props:
                _, sub_errors = validate_instance(v, props[k], f"{path}.{k}")
                errors.extend(sub_errors)

    # Array validation
    if isinstance(instance, list) and "items" in schema:
        item_schema = schema["items"]
        if item_schema:
            for idx, item in enumerate(instance):
                _, sub_errors = validate_instance(item, item_schema, f"{path}[{idx}]")
                errors.extend(sub_errors)

    return len(errors) == 0, errors
