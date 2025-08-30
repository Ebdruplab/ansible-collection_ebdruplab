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
short_description: Add an extracted value to a Semaphore integration
version_added: "2.0.0"
description: Create an extracted value rule for a project integration that pulls data from the request and stores it as an environment/json/header variable.

options:
  host:
    description: Base URL of the Semaphore server (e.g. http://localhost).
    type: str
    required: true
  port:
    description: Port where the Semaphore API is exposed (e.g. 3000).
    type: int
    required: true
  project_id:
    description: ID of the project that owns the integration.
    type: int
    required: true
  integration_id:
    description: ID of the integration to which the extracted value will be added.
    type: int
    required: true

  value:
    description: Extracted value rule to create.
    type: dict
    required: true
    suboptions:
      name:
        description: Display name of the extracted value rule.
        type: str
        required: true
      value_source:
        description: Source in the incoming request to read from.
        type: str
        required: true
        choices: [body, headers, query]
      body_data_type:
        description: How to interpret the body when value_source is body.
        type: str
        choices: [json, form, text]
      key:
        description: Key or path used to locate the value in the source.
        type: str
        required: true
      variable:
        description: Destination variable name to write to.
        type: str
        required: true
      variable_type:
        description: Destination bucket for the variable.
        type: str
        required: true
        choices: [environment, json, header]

  session_cookie:
    description: Session cookie for authentication. Use this or api_token.
    type: str
    required: false
    no_log: true
  api_token:
    description: Bearer API token for authentication. Use this or session_cookie.
    type: str
    required: false
    no_log: true
  validate_certs:
    description: Validate TLS certificates when using HTTPS.
    type: bool
    default: true

author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Create extracted value (body -> environment var)
  ebdruplab.semaphoreui.project_integration_extraction_create:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    integration_id: 11
    value:
      name: "grab message"
      value_source: "body"
      body_data_type: "json"
      key: "message"
      variable: "MSG"
      variable_type: "environment"
"""

RETURN = r"""
value:
  description: The created extracted value object returned by the API.
  type: dict
  returned: success
status:
  description: HTTP status code from the API response.
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
