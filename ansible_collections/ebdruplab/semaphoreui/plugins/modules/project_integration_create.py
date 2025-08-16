#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_integration_create
short_description: Create a Semaphore project integration
version_added: "2.0.0"
description:
  - Creates an integration under a Semaphore project that triggers a template.
  - Auth methods match the UI: C(None), C(GitHub Webhooks), C(Bitbucket Webhooks), C(Token), C(HMAC), C(BasicAuth).
  - C(auth_header) applies only to C(Token) and C(HMAC); defaults to C(token) if omitted.
  - C(searchable) is always sent as C(false).
  - C(task_params.debug_level) is always C(4); C(diff) and C(dry_run) default to C(false).
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
  integration:
    type: dict
    required: true
    suboptions:
      name:
        type: str
        required: true
      template_id:
        type: int
        required: true
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
- name: Create integration (HMAC auth)
  ebdruplab.semaphoreui.project_integration_create:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 226
    integration:
      name: "Example Integration name"
      template_id: 1
      auth_method: "HMAC"
      auth_header: "token"          # only used for Token/HMAC; defaults to "token" if omitted
      auth_secret_id: 3
      task_params:
        diff: false
        dry_run: true
"""

RETURN = r"""
integration:
  type: dict
  returned: success
status:
  type: int
  returned: always
"""

# Map UI labels -> API values
AUTH_MAP = {
    "None": "none",
    "GitHub Webhooks": "github_webhooks",
    "Bitbucket Webhooks": "bitbucket_webhooks",
    "Token": "token",
    "HMAC": "hmac",
    "BasicAuth": "basic",
}

def _normalize_task_params(tp):
    tp = tp or {}
    return {
        "debug_level": 4,                             # always 4
        "diff": bool(tp.get("diff", False)),
        "dry_run": bool(tp.get("dry_run", False)),
    }

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            integration=dict(
                type="dict",
                required=True,
                options=dict(
                    name=dict(type="str", required=True),
                    template_id=dict(type="int", required=True),
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
    validate_certs = module.params["validate_certs"]

    integ = dict(module.params["integration"] or {})
    integ["project_id"] = project_id
    integ["searchable"] = False                       # always false

    # Auth normalization
    ui_method = integ.get("auth_method")
    if ui_method is not None:
        api_method = AUTH_MAP.get(ui_method)
        if not api_method:
            module.fail_json(msg="Unsupported auth_method.")
        integ["auth_method"] = api_method
    # auth_header only valid for Token/HMAC; default to "token"
    if integ.get("auth_method") in ("token", "hmac"):
        integ["auth_header"] = integ.get("auth_header", "token")
    else:
        integ.pop("auth_header", None)

    # task_params with enforced defaults
    integ["task_params"] = _normalize_task_params(integ.get("task_params"))

    # Final payload (ensure ints/bools are proper)
    try:
        integ["template_id"] = int(integ["template_id"])
    except Exception:
        module.fail_json(msg="integration.template_id must be an integer")

    url = f"{host}:{port}/api/project/{project_id}/integrations"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    try:
        body = json.dumps(integ).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url=url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status not in (200, 201):
            text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else str(response_body)
            module.fail_json(msg=f"Failed to create integration: HTTP {status} - {text}", status=status)

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
