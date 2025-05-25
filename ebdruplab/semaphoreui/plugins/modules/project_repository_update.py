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
  - Sends a PUT request to update an existing repository for a specified Semaphore project.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (with http or https).
    type: str
    required: true
  port:
    description:
      - Port on which Semaphore is running.
    type: int
    required: true
  session_cookie:
    description:
      - Session cookie for authentication.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token for authentication.
    type: str
    required: false
    no_log: true
  project_id:
    description:
      - ID of the Semaphore project.
    type: int
    required: true
  repository_id:
    description:
      - ID of the repository to update.
    type: int
    required: true
  repository:
    description:
      - Dictionary describing the repository fields to update.
    type: dict
    required: true
    suboptions:
      name:
        description:
          - The name of the repository.
        type: str
        required: true
      git_url:
        description:
          - Git URL of the repository.
        type: str
        required: true
      git_branch:
        description:
          - Default Git branch to use.
        type: str
        required: true
      ssh_key_id:
        description:
          - ID of the SSH key to use with the repository.
        type: int
        required: true
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    type: bool
    default: true
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
  description:
    - The updated repository object returned by the API. If no body is returned, this is an empty dict.
  type: dict
  returned: success
status:
  description:
    - HTTP status code returned by the Semaphore API.
  type: int
  returned: always
'''

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
    port = p["port"]
    project_id = p["project_id"]
    repository_id = p["repository_id"]
    validate_certs = p["validate_certs"]
    repo = p["repository"]

    url = f"{host}:{port}/api/project/{project_id}/repositories/{repository_id}"

    payload = {
        "id": repository_id,
        "project_id": project_id,
        "name": repo["name"],
        "git_url": repo["git_url"],
        "git_branch": repo["git_branch"],
        "ssh_key_id": repo["ssh_key_id"]
    }

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_put(
            url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status not in (200, 201, 204):
            msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"PUT failed with status {status}: {msg}", status=status)

        if status == 204 or not response_body:
            module.exit_json(changed=True, repository={}, status=status)

        result = json.loads(response_body.decode()) if isinstance(response_body, bytes) else json.loads(response_body)
        module.exit_json(changed=True, repository=result, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

