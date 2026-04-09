#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers, exit_check_mode
import json

DOCUMENTATION = r"""
---
module: project_integration_extraction_value_create
short_description: Create an extracted value for a Semaphore integration
version_added: "2.0.0"
description:
  - Create a new extraction rule for a Semaphore project integration.
  - Extraction rules map data from an incoming integration request to a Semaphore task variable.
  - This module is intended for creating missing rules. If you need to modify an existing rule,
    use M(ebdruplab.semaphoreui.project_integration_extraction_value_update).

options:
  host:
    description:
      - Base URL of the Semaphore server, including the scheme.
      - "Example: C(http://localhost)."
    type: str
    required: true
  port:
    description:
      - TCP port where the Semaphore API is exposed.
    type: int
    required: true
  project_id:
    description:
      - Numeric ID of the project that owns the integration.
    type: int
    required: true
  integration_id:
    description:
      - Numeric ID of the integration that should receive the new extraction rule.
    type: int
    required: true
  value:
    description:
      - Definition of the extracted value rule to create.
    type: dict
    required: true
    suboptions:
      id:
        description:
          - Optional client-supplied ID.
          - Normally omitted and left to the Semaphore API.
        type: int
      name:
        description:
          - Human-readable display name for the extraction rule.
        type: str
        required: true
      value_source:
        description:
          - Where to read the value from in the incoming integration request.
        type: str
        choices: [body, headers, query]
        default: body
      body_data_type:
        description:
          - Format of the request body when O(value.value_source=body).
          - Ignored by Semaphore for non-body sources.
        type: str
        choices: [json, text]
        default: json
      key:
        description:
          - Key, header name, query parameter, or JSON path to read from the incoming request.
          - "Example: C(payload.user.id) or C(X-Branch)."
        type: str
        required: true
      variable:
        description:
          - Destination variable name to store the extracted value under.
        type: str
        required: true
      variable_type:
        description:
          - Destination variable bucket in Semaphore.
          - The value is passed through to the API as provided by the module input.
        type: str
        choices: [environment, extra]
        default: environment
  session_cookie:
    description:
      - Session cookie used for authentication.
      - Use this or O(api_token).
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - Bearer API token used for authentication.
      - Use this or O(session_cookie).
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

EXAMPLES = r"""
- name: Create a header extraction rule
  ebdruplab.semaphoreui.project_integration_extraction_value_create:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    integration_id: 11
    value:
      name: "Extract Branch"
      value_source: "headers"
      key: "X-Branch"
      variable: "git_branch"
      variable_type: "environment"

- name: Create a body extraction rule
  ebdruplab.semaphoreui.project_integration_extraction_value_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    integration_id: 11
    value:
      name: "Extract User ID"
      value_source: "body"
      body_data_type: "json"
      key: "payload.user.id"
      variable: "USER_ID"
      variable_type: "environment"
"""

RETURN = r"""
extracted_value:
  description:
    - Extracted value object returned by the Semaphore API.
  type: dict
  returned: success
status:
  description:
    - HTTP status code returned by the API.
  type: int
  returned: always
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
        supports_check_mode=True,
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
        if module.check_mode:
            exit_check_mode(module)

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
