#!/usr/bin/env python3
"""Minimal MCP stdio server for secret-safe AppFactory operations.

The server deliberately exposes secret references and build results, never secret values.
"""

import json
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone


PROJECT_ID = os.environ.get("APPFACTORY_PROJECT_ID", "appfactory-admin")
REGISTRY_PATH = Path(os.environ.get("APPFACTORY_LOCAL_REGISTRY", Path(__file__).with_name(".app-registry.json")))


def load_registry():
    if not REGISTRY_PATH.exists():
        return {}
    try:
        return json.loads(REGISTRY_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_registry(registry):
    temporary_path = REGISTRY_PATH.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(registry, indent=2, sort_keys=True))
    temporary_path.replace(REGISTRY_PATH)


def reply(request_id, result=None, error=None):
    message = {"jsonrpc": "2.0", "id": request_id}
    message["error" if error else "result"] = error or result
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def secret_reference_exists(secret_name):
    # Secret values are intentionally never read by this starter tool.
    return bool(secret_name and secret_name.startswith("projects/"))


def handle(request):
    request_id = request.get("id")
    method = request.get("method")
    if method == "initialize":
        return reply(request_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "appfactory", "version": "0.1.0"}})
    if method == "notifications/initialized":
        return
    if method == "tools/list":
        tools = [
            {"name": "list_apps", "description": "List safe AppFactory app metadata.", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "get_app_status", "description": "Read safe AppFactory app metadata.", "inputSchema": {"type": "object", "properties": {"app_id": {"type": "string"}}, "required": ["app_id"]}},
            {"name": "register_app", "description": "Register safe app metadata; secret values are not accepted.", "inputSchema": {"type": "object", "properties": {"app_id": {"type": "string"}, "metadata": {"type": "object"}}, "required": ["app_id", "metadata"]}},
            {"name": "prepare_android_build", "description": "Check signing secret references without exposing secret values.", "inputSchema": {"type": "object", "properties": {"app_id": {"type": "string"}, "keystore_secret": {"type": "string"}, "keystore_password_secret": {"type": "string"}, "key_alias_secret": {"type": "string"}, "key_password_secret": {"type": "string"}}, "required": ["app_id", "keystore_secret", "keystore_password_secret", "key_alias_secret", "key_password_secret"]}},
            {"name": "build_signed_android", "description": "Build and sign an Android artifact using protected secrets; returns artifact metadata only.", "inputSchema": {"type": "object", "properties": {"app_id": {"type": "string"}, "version_code": {"type": "integer"}}, "required": ["app_id", "version_code"]}},
        ]
        return reply(request_id, {"tools": tools})
    if method != "tools/call":
        return reply(request_id, error={"code": -32601, "message": "Method not found"})
    name = request.get("params", {}).get("name")
    arguments = request.get("params", {}).get("arguments", {})
    app_id = arguments.get("app_id", "")
    registry = load_registry()
    if name == "list_apps":
        result = {"project_id": PROJECT_ID, "apps": [{"app_id": key, **value} for key, value in registry.items()], "secret_values_exposed": False}
        return reply(request_id, {"content": [{"type": "text", "text": json.dumps(result)}]})
    if not app_id or "/" in app_id:
        return reply(request_id, error={"code": -32602, "message": "app_id must be a non-empty slug"})
    if name == "get_app_status":
        result = {"app_id": app_id, "project_id": PROJECT_ID, "status": "metadata-ready" if app_id in registry else "not-registered", "metadata": registry.get(app_id, {}), "secret_values_exposed": False}
    elif name == "register_app":
        metadata = arguments.get("metadata", {})
        if any("secret" in key.lower() and "name" not in key.lower() for key in metadata):
            return reply(request_id, error={"code": -32602, "message": "Use secret resource names; secret values are not accepted"})
        registry[app_id] = {**metadata, "updated_at": datetime.now(timezone.utc).isoformat()}
        save_registry(registry)
        result = {"app_id": app_id, "project_id": PROJECT_ID, "status": "registered", "fields_saved": sorted(metadata.keys()), "secret_values_exposed": False}
    elif name == "prepare_android_build":
        fields = ["keystore_secret", "keystore_password_secret", "key_alias_secret", "key_password_secret"]
        result = {"app_id": app_id, "ready": all(secret_reference_exists(arguments.get(field)) for field in fields), "checked_secret_references": len(fields), "secret_values_exposed": False}
    elif name == "build_signed_android":
        result = {"app_id": app_id, "status": "build-dispatch-placeholder", "build_id": str(uuid.uuid4()), "version_code": arguments.get("version_code"), "requested_at": datetime.now(timezone.utc).isoformat(), "secret_values_exposed": False}
    else:
        return reply(request_id, error={"code": -32601, "message": f"Unknown tool: {name}"})
    return reply(request_id, {"content": [{"type": "text", "text": json.dumps(result)}]})


for line in sys.stdin:
    try:
        handle(json.loads(line))
    except Exception as exc:
        reply(None, error={"code": -32603, "message": str(exc)})
