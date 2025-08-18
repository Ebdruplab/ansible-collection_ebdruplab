#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_integration_matcher_create
short_description: Create a matcher for a Semaphore project integration
version_added: "2.0.0"
description:
  - Adds a matcher rule to an existing integration under a Semaphore project.
  - A matcher inspects an incoming request or payload and determines whether to trigger the linked template.

options:
  host:
    description:
      - Base URL of the Semaphore server including scheme (e.g. C(http://localhost)).
    type: str
    required: true
  port:
    description:
      - Port where the Semaphore API is exposed (e.g. C(3000)).
    type: int
    required: true
  project_id:
    description:
      - ID of the project the integration belongs to.
    type: int
    required: true
  integration_id:
    description:
      - ID of the integration to attach the matcher to.
    type: int
    required: true
  matcher:
    description:
      - Matcher definition to create.
    type: dict
    required: true
    suboptions:
      name:
        description:
          - Human-friendly matcher name.
        type: str
        required: true
      match_type:
        description:
          - Location to match such as C(body), C(headers), or C(query).
        type: str
        required: true
      method:
        description:
          - Match method such as C(equals), C(contains), or C(regex)).
        type: str
        required: true
      body_data_type:
        description:
          - Data type for body matching, e.g. C(json) or C(text).
          - Only relevant when C(match_type=body).
        type: str
      key:
        description:
          - Key or path to inspect (e.g. JSON path, header key, or query key).
        type: str
      value:
        description:
          - Value to compare against.
        type: str
  session_cookie:
    description:
      - Session cookie for authentication. Use this or C(api_token).
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - Bearer token for authentication. Use this or C(session_cookie).
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate TLS certificates when using HTTPS.
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
            matcher=dict(
                type="dict",
                required=True,
                options=dict(
                    name=dict(type="str", required=True),
                    match_type=dict(type="str", required=True),
                    method=dict(type="str", required=True),
                    body_data_type=dict(type="str", required=False),
                    key=dict(type="str", required=False),
                    value=dict(type="str", required=False),
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

    m = dict(module.params["matcher"] or {})

    # Build payload (include path-scoped integration_id to satisfy APIs that expect it in body)
    payload = {
        "integration_id": integration_id,
        "name": m.get("name"),
        "match_type": m.get("match_type"),
        "method": m.get("method"),
    }
    if m.get("body_data_type"):
        payload["body_data_type"] = m["body_data_type"]
    if m.get("key") is not None:
        payload["key"] = m["key"]
    if m.get("value") is not None:
        payload["value"] = m["value"]

    # Basic sanity
    missing = [k for k in ("name", "match_type", "method") if not payload.get(k)]
    if missing:
        module.fail_json(msg=f"matcher is missing required fields: {', '.join(missing)}")

    # Default body_data_type when matching body and not provided
    if payload.get("match_type") == "body" and "body_data_type" not in payload:
        payload["body_data_type"] = "json"

    url = f"{host}:{port}/api/project/{project_id}/integrations/{integration_id}/matchers"
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

        module.exit_json(changed=True, matcher=obj, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
