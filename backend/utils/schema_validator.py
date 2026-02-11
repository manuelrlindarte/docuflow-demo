import json
from pathlib import Path

import jsonschema

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


def load_schema(schema_name: str) -> dict:
    schema_path = SCHEMAS_DIR / f"{schema_name}.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(payload: dict, schema_name: str) -> tuple[bool, str]:
    try:
        schema = load_schema(schema_name)
        jsonschema.validate(instance=payload, schema=schema)
        return True, ""
    except jsonschema.ValidationError as e:
        return False, e.message
    except Exception as e:
        return False, f"Schema error: {str(e)}"


def validate_or_raise(payload: dict, schema_name: str) -> dict:
    ok, err = validate_schema(payload, schema_name)
    if not ok:
        raise ValueError(f"Schema validation failed [{schema_name}]: {err}")
    return payload
