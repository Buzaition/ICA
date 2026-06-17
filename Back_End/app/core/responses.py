from typing import Any


def success_response(message: str = "Operation completed", data: Any = None) -> dict[str, Any]:
    return {"success": True, "message": message, "data": {} if data is None else data}

