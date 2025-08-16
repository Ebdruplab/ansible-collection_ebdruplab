#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_integration_update
short_description: Update a Semaphore project integration
version_added: "2.0.0"
description:
  - Updates an existing integration under a Semaphore project.
  - Auth methods match the UI: C(None), C(GitHub Webhooks), C(Bitbucket Webhooks), C(Token), C(HMAC), C(BasicAuth)).
  - C(auth_header) is only applicable for C(Token) and C(HMAC); defaults to C(token) if omitted.
  - C(searchable) is always sent as C(false).
  - C(task_params.debug_level) is always forced to C(4); C(diff) and C(dry_run) default to C(false) if provided.
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
  integration:
    type: dict
    required: true
    suboptions:
      name:
        type: str
      template_id:
        type: int
      auth_method:
        type: str
        choices: ["None", "GitHub Webhooks", "Bitbucket Webhooks", "Token", "HMAC", "BasicAuth"]
      auth_header:
        type: str
      auth_secret_id:
        type: int
      task_params:
        type: dict
        suboptions:
          diff:
            type: bool
            default: false
          dry_run:
            type: bool
            default: false
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
- name: Update integration (switch to Token auth and enable diff)
  ebdruplab.semaphoreui.project_integration_update:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 226
    integration_id: 1
    integration:
      name: "Example Integration name"
      template_id: 1
      auth_method: "Token"
      auth_header: "token"   # only for Token/HMAC; defaults to "token"
      auth_secret_id: 3
      task_params:
        diff: true
        dry_run: false
"""

RETURN = r"""
integration:
  description: Server response (or the sent payload if HTTP 204).
  type: dict
  returned: success
status:
  description: HTTP status code.
  type: int
  returned: always
"""

# UI label -> API value
AUTH_MAP = {
    "None": "none",
    "GitHub Webhooks": "github_webhooks",
    "Bitbucket Webhooks": "bitbucket_webhooks",
    "Token": "token",
    "HMAC": "hmac",
    "BasicAuth": "basic",
}

def _normalize_task_params(tp):
    if not tp:
        return {"debug_level": 4, "diff": False, "dry_run": False}
    return {
        "debug_level": 4,                       # always 4
        "diff": bool(tp.get("diff", False)),
        "dry_run": bool(tp.get("dry_run", False)),
    }

def _opt_int(module, obj, key):
    if key in obj and obj[key] is not None:
        try:
            obj[key] = int(obj[key])
        except Exception:
            module.fail_json(msg=f"{key} must be an integer")

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            integration_id=dict(type="int", required=True),
            integration=dict(
                type="dict",
                required=True,
                options=dict(
                    name=dict(type="str", required=False),
                    template_id=dict(type="int", required=False),
                    auth_method=dict(type="str", required=False, choices=list(AUTH_MAP.keys())),
                    auth_header=dict(type="str", required=False),
                    auth_secret_id=dict(type="int", required=False),
                    task_params=dict(
                        type="dict",
                        required=False,
                        options=dict(
                            diff=dict(type="bool", required=False, default=False),
                            dry_run=dict(type="bool", required=False, default=False),
                        ),
                    ),
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

    payload = dict(module.params["integration"] or {})
    payload["project_id"] = project_id
    payload["id"] = integration_id
    payload["searchable"] = False                 # always false

    # Normalize ints if present
    _opt_int(module, payload, "template_id")
    _opt_int(module, payload, "auth_secret_id")

    # Normalize auth method & header
    if "auth_method" in payload and payload["auth_method"] is not None:
        api_method = AUTH_MAP.get(payload["auth_method"])
        if not api_method:
            module.fail_json(msg="Unsupported auth_method")
        payload["auth_method"] = api_method
    if payload.get("auth_method") in ("token", "hmac"):
        payload["auth_header"] = payload.get("auth_header", "token")
    else:
        payload.pop("auth_header", None)

    # Normalize task_params if provided
    if "task_params" in payload:
        payload["task_params"] = _normalize_task_params(payload.get("task_params"))

    url = f"{host}:{port}/api/project/{project_id}/integrations/{integration_id}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_put(
            url=url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status == 204:
            module.exit_json(changed=True, integration=payload, status=status)

        if status != 200:
            text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else str(response_body)
            module.fail_json(msg=f"Failed to update integration: HTTP {status} - {text}", status=status)

        text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else response_body
        try:
            integration_obj = json.loads(text) if isinstance(text, str) else text
        except Exception:
            integration_obj = {"raw": text}

        module.exit_json(changed=True, integration=integration_obj, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
