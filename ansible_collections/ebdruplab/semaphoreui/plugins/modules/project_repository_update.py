#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_repository_update
short_description: Update a repository in a Semaphore project
version_added: "1.0.0"
description:
  - Updates an existing repository for a specified Semaphore project.
  - Ensures the body contains C(id) and C(project_id) matching the URL params to satisfy strict API servers.
options:
  host:
    type: str
    required: true
    description: Hostname or IP of the Semaphore server (with http/https).
  port:
    type: int
    required: true
    description: Port on which Semaphore is running.
  session_cookie:
    type: str
    required: false
    no_log: true
    description: Session cookie for authentication.
  api_token:
    type: str
    required: false
    no_log: true
    description: API token for authentication.
  project_id:
    type: int
    required: true
    description: ID of the Semaphore project.
  repository_id:
    type: int
    required: true
    description: ID of the repository to update.
  repository:
    type: dict
    required: true
    description: Repository fields to update.
    suboptions:
      name:
        type: str
        required: true
      git_url:
        type: str
        required: true
      git_branch:
        type: str
        required: true
      ssh_key_id:
        type: int
        required: true
  validate_certs:
    type: bool
    default: true
    description: Whether to validate TLS certificates.
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Update a repository
  ebdruplab.semaphoreui.project_repository_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    repository_id: 123
    repository:
      name: "Updated Repo"
      git_url: "git@example.com"
      git_branch: "main"
      ssh_key_id: 0
'''

RETURN = r'''
repository:
  description: The updated repository object returned by the API (empty when 204).
  type: dict
  returned: success
status:
  description: HTTP status code.
  type: int
  returned: always
debug:
  description: Echo of URL/body IDs to help diagnose 400 mismatches.
  type: dict
  returned: on failure or when status not in (200,201,204)
'''

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
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            project_id=dict(type='int', required=True),
            repository_id=dict(type='int', required=True),
            repository=dict(type='dict', required=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    p = module.params
    host = p["host"].rstrip("/")
    port = int(p["port"])
    project_id = int(p["project_id"])
    repository_id = int(p["repository_id"])
    validate_certs = p["validate_certs"]
    repo = dict(p["repository"] or {})

    # Validate fields
    for key in ("name", "git_url", "git_branch", "ssh_key_id"):
        if key not in repo:
            module.fail_json(msg=f"Missing required repository field: {key}")

    try:
        ssh_key_id = int(repo["ssh_key_id"])
    except Exception:
        module.fail_json(msg="repository.ssh_key_id must be an integer")

    # Force body IDs to match URL params
    repo["id"] = repository_id
    repo["project_id"] = project_id

    url = f"{host}:{port}/api/project/{project_id}/repositories/{repository_id}"

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    # Final payload matches API example shape
    payload = {
        "id": repository_id,
        "name": repo["name"],
        "project_id": project_id,
        "git_url": repo["git_url"],
        "git_branch": repo["git_branch"],
        "ssh_key_id": ssh_key_id,
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        resp_body, status, _ = semaphore_put(
            url=url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status not in (200, 201, 204):
            module.fail_json(
                msg=f"PUT failed with status {status}: {_as_text(resp_body)}",
                status=status,
                debug={
                    "url": url,
                    "url_repository_id": repository_id,
                    "url_project_id": project_id,
                    "body_id": payload.get("id"),
                    "body_project_id": payload.get("project_id"),
                },
            )

        if status == 204 or not resp_body:
            module.exit_json(changed=True, repository={}, status=status)

        text = _as_text(resp_body)
        try:
            result = json.loads(text) if isinstance(text, str) else text
        except Exception:
            result = {"raw": text}

        module.exit_json(changed=True, repository=result, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
