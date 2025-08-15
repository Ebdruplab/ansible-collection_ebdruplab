#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_environment_update
short_description: Update an existing environment in a Semaphore project
version_added: "1.0.0"
description:
  - Updates an environment in a Semaphore project.
  - Plain vars live in C(env) (environment vars) and C(json) (extra vars).
  - C(extra_variables) is an alias for C(json) (provide one or the other).
  - Secrets target C(env) or C(var). Aliases C(json), C(extra_vars), C(extra_variables) map to C(var).
  - Secrets are always sent with C(operation=create).
options:
  host: {type: str, required: true}
  port: {type: int, required: true}
  project_id: {type: int, required: true}
  environment_id: {type: int, required: true}
  environment:
    type: dict
    required: true
    suboptions:
      name: {type: str}
      password: {type: str}
      env: {type: raw}
      json: {type: raw}
      extra_variables: {type: raw}
      secrets:
        type: list
        elements: dict
        suboptions:
          id: {type: int}
          name: {type: str, required: true}
          secret: {type: str, required: true, no_log: true}
          type:
            type: str
            required: true
            choices: [env, var, json, extra_vars, extra_variables]
  session_cookie: {type: str, no_log: true}
  api_token: {type: str, no_log: true}
  validate_certs: {type: bool, default: true}
author: ["Kristian Ebdrup (@kris9854)"]
"""

EXAMPLES = r"""
- name: Update env (rename, change vars, add secret to extra vars)
  ebdruplab.semaphoreui.project_environment_update:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    environment_id: 2
    environment:
      name: "Updated Env"
      env: { APP_MODE: "updated" }
      extra_variables: { retries: 5 }
      secrets:
        - name: "API_TOKEN"
          secret: "{{ vault_api_token }}"
          type: extra_variables   # alias -> sent as 'var'
"""

RETURN = r"""
environment:
  description: Updated environment object, or the payload if the server returns 204.
  type: dict
status:
  description: HTTP status code.
  type: int
"""

def _ensure_json_string(module, data, field):
    """If dict -> JSON string; if str -> must be valid JSON."""
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
            module.fail_json(msg=f"Field '{field}' must be valid JSON or dict: {e}")
    else:
        module.fail_json(msg=f"Field '{field}' must be dict or JSON string.")

def _normalize_secret_type(stype):
    """Map aliases to API-accepted types: env | var."""
    return {
        "env": "env",
        "var": "var",
        "json": "var",
        "extra_vars": "var",
        "extra_variables": "var",
    }.get(stype)

def _normalize_secrets(module, secrets):
    if secrets is None:
        return None
    if not isinstance(secrets, list):
        module.fail_json(msg="Field 'secrets' must be a list.")
    out = []
    for i, s in enumerate(secrets):
        if not isinstance(s, dict):
            module.fail_json(msg=f"Secret at index {i} must be a dict.")
        name = s.get("name")
        stype = _normalize_secret_type(s.get("type"))
        sval = s.get("secret")
        if not name:
            module.fail_json(msg=f"Secret at index {i} missing 'name'.")
        if stype not in ("env", "var"):
            module.fail_json(msg=f"Secret '{name}' invalid type; use env/var (aliases json/extra_vars/extra_variables map to var).")
        if sval in (None, ""):
            module.fail_json(msg=f"Secret '{name}' missing 'secret' value.")
        entry = {
            "name": name,
            "secret": sval,
            "type": stype,
            "operation": "create",
        }
        # Only send id if explicitly > 0
        if isinstance(s.get("id"), int) and s["id"] > 0:
            entry["id"] = s["id"]
        out.append(entry)
    return out

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            environment_id=dict(type='int', required=True),
            environment=dict(
                type='dict',
                required=True,
                options=dict(
                    name=dict(type='str', required=False),
                    password=dict(type='str', required=False, no_log=True),
                    env=dict(type='raw', required=False),
                    json=dict(type='raw', required=False),
                    extra_variables=dict(type='raw', required=False),
                    secrets=dict(
                        type='list', required=False, elements='dict',
                        options=dict(
                            id=dict(type='int', required=False),
                            name=dict(type='str', required=True),
                            secret=dict(type='str', required=True, no_log=True),
                            type=dict(type='str', required=True, choices=['env','var','json','extra_vars','extra_variables']),
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
    environment_id = module.params["environment_id"]
    env_update = dict(module.params["environment"] or {})
    validate_certs = module.params["validate_certs"]

    env_update["project_id"] = project_id
    env_update["id"] = environment_id

    # extra_variables -> json (mutually exclusive)
    has_json = env_update.get("json") is not None
    has_extra = env_update.get("extra_variables") is not None
    if has_json and has_extra:
        module.fail_json(msg="Provide either 'json' or 'extra_variables', not both.")
    if has_extra and not has_json:
        env_update["json"] = env_update.pop("extra_variables")

    _ensure_json_string(module, env_update, "env")
    _ensure_json_string(module, env_update, "json")

    if "secrets" in env_update:
        env_update["secrets"] = _normalize_secrets(module, env_update.get("secrets"))

    # Ensure buckets exist if secrets target them
    if env_update.get("secrets"):
        targets = {s["type"] for s in env_update["secrets"]}
        if "env" in targets and "env" not in env_update:
            env_update["env"] = "{}"
        if "var" in targets and "json" not in env_update:
            env_update["json"] = "{}"

    url = f"{host}:{port}/api/project/{project_id}/environment/{environment_id}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    try:
        body = json.dumps(env_update).encode("utf-8")
        response_body, status, _ = semaphore_put(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status == 204:
            module.exit_json(changed=True, environment=env_update, status=status)

        if status != 200:
            error = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else str(response_body)
            module.fail_json(msg=f"PUT failed with status {status}: {error}", status=status)

        text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else response_body
        try:
            updated_env = json.loads(text) if isinstance(text, str) else text
        except Exception:
            updated_env = {"raw": text}

        module.exit_json(changed=True, environment=updated_env, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
