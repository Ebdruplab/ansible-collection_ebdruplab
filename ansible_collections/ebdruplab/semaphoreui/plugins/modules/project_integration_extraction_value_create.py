#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_integration_extraction_value_create
short_description: Create an extracted value for a Semaphore integration
version_added: "2.0.0"
description:
  - Adds an extracted value rule to a specific integration in a Semaphore project.

options:
  host:
    description:
      - Base URL of the Semaphore server (e.g. C(http://localhost)).
    type: str
    required: true
  port:
    description:
      - Port where the Semaphore API is exposed (e.g. C(3000)).
    type: int
    required: true
  project_id:
    description:
      - ID of the project that owns the integration.
    type: int
    required: true
  integration_id:
    description:
      - ID of the integration to attach the extracted value to.
    type: int
    required: true
  value:
    description:
      - Definition of the extracted value to create.
    type: dict
    required: true
    suboptions:
      id:
        description:
          - Optional client-supplied ID; usually omitted.
        type: int
      name:
        description:
          - Human-readable name of the extraction rule.
        type: str
        required: true
      value_source:
        description:
          - Where to read the value from in the incoming request.
        type: str
        choices: [body, headers, query]
        default: body
      body_data_type:
        description:
          - Data type of the request body when C(value_source=body).
        type: str
        choices: [json, text]
        default: json
      key:
        description:
          - Key or path to extract (e.g. C(payload.user.id), header/query key).
        type: str
        required: true
      variable:
        description:
          - Variable name to store the extracted value under.
        type: str
        required: true
      variable_type:
        description:
          - Target variable bucket.
        type: str
        choices: [environment, extra]
        default: environment
  session_cookie:
    description:
      - Session cookie for authentication. Use this or C(api_token).
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - Bearer API token for authentication. Use this or C(session_cookie).
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Validate TLS certificates when using HTTPS.
    type: bool
    default: true

author:
  - "Kristian Ebdrup (@kris9854)"
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            integration_id=dict(type="int", required=True),
            value=dict(
                type="dict",
                required=True,
                options=dict(
                    id=dict(type="int", required=False),
                    name=dict(type="str", required=True),
                    value_source=dict(type="str", required=False, default="body"),
                    body_data_type=dict(type="str", required=False, default="json"),
                    key=dict(type="str", required=True),
                    variable=dict(type="str", required=True),
                    variable_type=dict(type="str", required=False, default="environment"),
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
    v = dict(module.params["value"] or {})

    payload = {
        "id": v.get("id", 0) or 0,
        "name": v["name"],
        "value_source": v.get("value_source", "body"),
        "body_data_type": v.get("body_data_type", "json"),
        "key": v["key"],
        "variable": v["variable"],
        "variable_type": v.get("variable_type", "environment"),
        "integration_id": integration_id,
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
            module.fail_json(msg=f"POST failed with status {status}: {text}", status=status)

        text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else response_body
        try:
            obj = json.loads(text) if isinstance(text, str) else text
        except Exception:
            obj = {"raw": text}

        module.exit_json(changed=True, extracted_value=obj, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
