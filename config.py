import os
from typing import Any, Dict, Optional


DEFAULTS: Dict[str, Any] = {
    "handshake.clientId": "client-0001",
    "handshake.token": "",
    "handshake.autoSend": True,
    "handshake.applyResponseToState": False,
}


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


def get_config(runtime: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Merge runtime config > environment vars > defaults."""
    runtime = runtime or {}
    cfg: Dict[str, Any] = {}

    # clientId
    if runtime.get("handshake.clientId") is not None:
        cfg["handshake.clientId"] = runtime["handshake.clientId"]
    else:
        cfg["handshake.clientId"] = os.getenv("HANDSHAKE_CLIENTID", DEFAULTS["handshake.clientId"])

    # token
    if runtime.get("handshake.token") is not None:
        cfg["handshake.token"] = runtime["handshake.token"]
    else:
        cfg["handshake.token"] = os.getenv("HANDSHAKE_TOKEN", DEFAULTS["handshake.token"])

    # autoSend
    if runtime.get("handshake.autoSend") is not None:
        cfg["handshake.autoSend"] = bool(runtime["handshake.autoSend"])
    else:
        cfg["handshake.autoSend"] = _env_bool("HANDSHAKE_AUTOSEND", DEFAULTS["handshake.autoSend"])

    # applyResponseToState
    if runtime.get("handshake.applyResponseToState") is not None:
        cfg["handshake.applyResponseToState"] = bool(runtime["handshake.applyResponseToState"])
    else:
        cfg["handshake.applyResponseToState"] = _env_bool(
            "HANDSHAKE_APPLYRESPONSE", DEFAULTS["handshake.applyResponseToState"]
        )

    return cfg
