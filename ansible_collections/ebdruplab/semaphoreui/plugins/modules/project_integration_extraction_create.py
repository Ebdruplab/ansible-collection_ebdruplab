#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_integration_extraction_create
short_description: Create an extracted value rule for a Semaphore integration
version_added: "2.0.0"
description:
  - Adds an "extracted value" to a project integration, e.g. read a key from the HTTP response body and store it in environment or extra vars.
options:
  host:
    type: str
    required: true
  port:
    type: int
    required: true
  project_id:
    type: int
    required: true
  integration_id:
    type: int
    required: true
  extraction:
    type: dict
    required: true
    suboptions:
      name:
        description: Human-friendly name for this extraction rule.
        type: str
        required: true
      value_source:
        description: Where to read the value from.
        type: str
        choices: [body, header, query, path]
        default: body
      body_data_type:
        description: Payload type when value_source=body.
        type: str
        choices: [json, text]
        default: json
      key:
        description: Key/selector (e.g. JSON pointer/path, header/query name).
        type: str
        required: true
      variable:
        description: Destination variable name to write to.
        type: str
        required: true
      variable_type:
        description: Destination bucket. Use C(environment) for env vars or C(json) for extra vars. Aliases: C(env)->environment, C(var/json/extra_vars/extra_variables)->json.
        type: str
        required: true
  session_cookie:
    type: str
    required: false
    no_log: true
  api_token:
    type: str
    required: false
    no_log: true
  validate_certs:
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Extract token from JSON body into env var
  ebdruplab.semaphoreui.project_integration_extraction_create:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    integration_id: 11
    extraction:
      name: "Access token"
      value_source: body
      body_data_type: json
      key: "access.token"
      variable: "ACCESS_TOKEN"
      variable_type: environment

- name: Extract run_id header into extra vars
  ebdruplab.semaphoreui.project_integration_extraction_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    integration_id: 11
    extraction:
      name: "Run ID"
      value_source: header
      key: "x-run-id"
      variable: "run_id"
      variable_type: json
"""

RETURN = r"""
extraction:
  description: Created extraction object.
  type: dict
  returned: success
status:
  description: HTTP status (201 on success).
  type: int
  returned: always
"""

def _normalize_variable_type(vt):
    """
    Map user-friendly aliases to API-expected values:
      - environment (env) -> environment
      - json / var / extra_vars / extra_variables -> json
    """
    if vt is None:
        return None
    vt_l = str(vt).strip().lower()
    if vt_l in ("environment", "env"):
        return "environment"
    if vt_l in ("json", "var", "extra_vars", "extra_variables"):
        return "json"
    return vt  # pass-through (server will validate)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            integration_id=dict(type="int", required=True),
            extraction=dict(
                type="dict",
                required=True,
                options=dict(
                    name=dict(type="str", required=True),
                    value_source=dict(type="str", required=False, choices=["body", "header", "query", "path"], default="body"),
                    body_data_type=dict(type="str", required=False, choices=["json", "text"], default="json"),
                    key=dict(type="str", required=True),
                    variable=dict(type="str", required=True),
                    variable_type=dict(type="str", required=True),
                ),
            ),
            session_cookie=dict(type="str", required=False, no_log=True),
            api_token=dict(type="str", required=False, no_log=True),
            validate_certs=dict(type="bool", default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    integration_id = module.params["integration_id"]
    validate_certs = module.params["validate_certs"]
    ex = dict(module.params["extraction"] or {})

    if not ex.get("name"):
        module.fail_json(msg="extraction.name is required")
    if not ex.get("key"):
        module.fail_json(msg="extraction.key is required")
    if not ex.get("variable"):
        module.fail_json(msg="extraction.variable is required")

    value_source = ex.get("value_source", "body")
    body_data_type = ex.get("body_data_type", "json")

    # Normalize destination bucket
    var_type = _normalize_variable_type(ex.get("variable_type"))
    if var_type not in ("environment", "json"):
        module.fail_json(msg="extraction.variable_type must be 'environment' or 'json' (aliases: env, var, extra_vars, extra_variables).")

    # Build payload (omit Nones)
    payload = {
        "name": str(ex["name"]),
        "value_source": value_source,
        "body_data_type": body_data_type if value_source == "body" else body_data_type,
        "key": str(ex["key"]),
        "variable": str(ex["variable"]),
        "variable_type": var_type,
        "integration_id": int(integration_id),
    }

    url = f"{host}:{port}/api/project/{project_id}/integrations/{integration_id}/values"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url=url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status not in (200, 201):
            text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else str(response_body)
            module.fail_json(msg=f"Failed to create extraction value: HTTP {status} - {text}", status=status)

        text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else response_body
        try:
            extraction_obj = json.loads(text) if isinstance(text, str) else text
        except Exception:
            extraction_obj = {"raw": text}

        module.exit_json(changed=True, extraction=extraction_obj, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
