#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_view_update
short_description: Update a Semaphore project view
version_added: "2.0.1"
description:
  - Updates an existing view via PUT /api/project/{project_id}/views/{view_id}.
  - Sends matching C(id) and C(project_id) in the body (strict API requires this).
options:
  host:
    description: Base URL (scheme + host), e.g. http://localhost
    type: str
    required: true
  port:
    description: API port, e.g. 3000
    type: int
    required: true
  project_id:
    description: Project ID
    type: int
    required: true
  view_id:
    description: View ID to update
    type: int
    required: true
  title:
    description: View title
    type: str
    required: true
  position:
    description: Optional position
    type: int
    required: false
  session_cookie:
    description: Session cookie for auth (use this or api_token)
    type: str
    required: false
    no_log: true
  api_token:
    description: API token for auth (use this or session_cookie)
    type: str
    required: false
    no_log: true
  validate_certs:
    description: Validate TLS certificates
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Update a view
  ebdruplab.semaphoreui.project_view_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    view_id: 10
    title: "Examples"
    position: 0
"""

RETURN = r"""
status:
  description: HTTP status code (204 on success)
  type: int
  returned: always
view:
  description: Updated view object if server returns a body; empty on 204
  type: dict
  returned: success
"""

def _as_text(b):
    if isinstance(b, (bytes, bytearray)):
        try:
            return b.decode()
        except Exception:
            return str(b)
    return b

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            view_id=dict(type="int", required=True),
            title=dict(type="str", required=True),
            position=dict(type="int", required=False),
            session_cookie=dict(type="str", required=False, no_log=True),
            api_token=dict(type="str", required=False, no_log=True),
            validate_certs=dict(type="bool", default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    p = module.params
    host = p["host"].rstrip("/")
    port = int(p["port"])
    project_id = int(p["project_id"])
    view_id = int(p["view_id"])
    title = p["title"]
    position = p.get("position", None)
    validate_certs = p["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/views/{view_id}"

    payload = {
        "id": view_id,              # MUST match URL
        "project_id": project_id,   # Some servers require this too
        "title": title,
    }
    if position is not None:
        payload["position"] = position

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    try:
        resp_body, status, _ = semaphore_put(
            url=url,
            body=json.dumps(payload).encode("utf-8"),
            headers=headers,
            validate_certs=validate_certs,
        )

        if status not in (200, 201, 204):
            module.fail_json(
                msg=f"PUT failed with status {status}: {_as_text(resp_body)}",
                status=status,
                debug=dict(url=url, body=payload),
            )

        if status == 204 or not resp_body:
            module.exit_json(changed=True, view={}, status=status)

        text = _as_text(resp_body)
        try:
            data = json.loads(text) if isinstance(text, str) else text
        except Exception:
            data = {"raw": text}

        module.exit_json(changed=True, view=data, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
