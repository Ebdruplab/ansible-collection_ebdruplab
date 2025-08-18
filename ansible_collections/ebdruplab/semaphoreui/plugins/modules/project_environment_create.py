#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_environment_create
short_description: Create a Semaphore environment
version_added: "1.0.0"
description:
  - "Creates an environment inside a Semaphore project."
  - "Supports two buckets for plain variables: environment variables (C(env)) and extra variables (C(json))."
  - "C(extra_variables) is an alias for C(json) (provide one or the other)."
  - "Secrets target a bucket using C(type). Use C(env) for environment variables or C(var) for extra variables (aliases: C(json), C(extra_vars), C(extra_variables))."
  - "Secret operation is always C(create)."
options:
  host:
    description:
      - "Base URL (scheme + host) of the Semaphore server, e.g. C(http://localhost)."
    type: str
    required: true
  port:
    description:
      - "Port where the Semaphore API is exposed, e.g. C(3000)."
    type: int
    required: true
  project_id:
    description:
      - "ID of the project where the environment will be created."
    type: int
    required: true
  environment:
    description:
      - "Environment definition to create."
    type: dict
    required: true
    suboptions:
      name:
        description:
          - "Human-readable name of the environment."
        type: str
        required: true
      password:
        description:
          - "Optional password (vault password). Marked C(no_log) in the module args."
        type: str
      env:
        description:
          - "Environment variables. Accepts a dict or a valid JSON string."
        type: raw
      json:
        description:
          - "Extra variables. Accepts a dict or a valid JSON string."
        type: raw
      extra_variables:
        description:
          - "Alias of C(json). Provide either C(json) or C(extra_variables), not both."
        type: raw
      secrets:
        description:
          - "List of secret items to create. Each secret targets either the environment bucket (C(env)) or the extra vars bucket (C(var)/aliases)."
        type: list
        elements: dict
        suboptions:
          id:
            description:
              - "Optional ID for the secret item. If omitted, a default is used."
            type: int
          name:
            description:
              - "Secret key name as it will appear in the chosen bucket."
            type: str
            required: true
          secret:
            description:
              - "Secret value. Marked C(no_log) in the module args."
            type: str
            required: true
          type:
            description:
              - "Target bucket for the secret."
              - "Use C(env) for environment variables or C(var) for extra variables. Aliases C(json), C(extra_vars), and C(extra_variables) also map to C(var)."
            type: str
            required: true
            choices:
              - env
              - var
              - json
              - extra_vars
              - extra_variables
  session_cookie:
    description:
      - "Session cookie for authentication. Use this or C(api_token)."
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - "API token for authentication. Use this or C(session_cookie)."
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - "Whether to validate TLS certificates when using HTTPS."
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

def _ensure_json_string(module, data, field):
    """Accept dict or JSON string; serialize dict to JSON string."""
    if field not in data or data[field] is None:
        return
    val = data[field]
    if isinstance(val, dict):
        try:
            data[field] = json.dumps(val)
        except Exception as e:
            module.fail_json(msg=f"Failed to serialize '{field}' to JSON: {e}")
    elif isinstance(val, str):
        try:
            json.loads(val)
        except Exception as e:
            module.fail_json(msg=f"Field '{field}' must be valid JSON (string) or dict: {e}")
    else:
        module.fail_json(msg=f"Field '{field}' must be dict or JSON string.")

def _normalize_secret_type(stype):
    """Map aliases to API-accepted types: env | var."""
    alias_map = {
        'env': 'env',
        'var': 'var',
        'json': 'var',
        'extra_vars': 'var',
        'extra_variables': 'var',
    }
    return alias_map.get(stype)

def _normalize_secrets(module, secrets):
    if secrets is None:
        return None
    if not isinstance(secrets, list):
        module.fail_json(msg="Field 'secrets' must be a list of dicts.")
    out = []
    for i, item in enumerate(secrets):
        if not isinstance(item, dict):
            module.fail_json(msg=f"Secret at index {i} must be a dict.")
        name = item.get("name")
        secret_val = item.get("secret")
        stype = _normalize_secret_type(item.get("type"))
        if not name:
            module.fail_json(msg=f"Secret at index {i} missing 'name'.")
        if stype not in ("env", "var"):
            module.fail_json(msg=f"Secret '{name}' has invalid 'type'. Use env/var (aliases: json, extra_vars, extra_variables).")
        if secret_val is None or secret_val == "":
            module.fail_json(msg=f"Secret '{name}': 'secret' is required.")
        out.append({
            # API accepts id but it's optional; default to 0 if provided falsy
            "id": item.get("id", 0) or 0,
            "name": name,
            "secret": secret_val,
            "type": stype,           # env | var
            "operation": "create",
        })
    return out

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            environment=dict(
                type='dict',
                required=True,
                options=dict(
                    name=dict(type='str', required=True),
                    password=dict(type='str', required=False, no_log=True),
                    env=dict(type='raw', required=False),
                    json=dict(type='raw', required=False),
                    extra_variables=dict(type='raw', required=False),
                    secrets=dict(
                        type='list',
                        required=False,
                        elements='dict',
                        options=dict(
                            id=dict(type='int', required=False),
                            name=dict(type='str', required=True),
                            secret=dict(type='str', required=True, no_log=True),
                            type=dict(type='str', required=True, choices=['env', 'var', 'json', 'extra_vars', 'extra_variables']),
                        )
                    ),
                ),
            ),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    env_def = dict(module.params["environment"] or {})
    validate_certs = module.params["validate_certs"]

    # Attach project_id
    env_def["project_id"] = project_id

    # 'json' <-> 'extra_variables' (mutually exclusive)
    has_json = env_def.get("json") is not None
    has_extra = env_def.get("extra_variables") is not None
    if has_json and has_extra:
        module.fail_json(msg="Provide either 'json' or 'extra_variables', not both.")
    if has_extra and not has_json:
        env_def["json"] = env_def.pop("extra_variables")

    # Serialize env/json if dicts
    _ensure_json_string(module, env_def, "env")
    _ensure_json_string(module, env_def, "json")

    # Normalize secrets (force operation=create; map type aliases -> env|var)
    if "secrets" in env_def:
        env_def["secrets"] = _normalize_secrets(module, env_def.get("secrets"))

    url = f"{host}:{port}/api/project/{project_id}/environment"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    try:
        body = json.dumps(env_def).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url=url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 201):
            error = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else str(response_body)
            module.fail_json(msg=f"Failed to create environment: HTTP {status} - {error}", status=status)

        text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else response_body
        try:
            environment_obj = json.loads(text) if isinstance(text, str) else text
        except Exception:
            environment_obj = {"raw": text}

        module.exit_json(changed=True, environment=environment_obj, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
