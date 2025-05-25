#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_repository_list
short_description: List repositories in a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves a list of all repositories configured under a specific Semaphore project.
options:
  host:
    type: str
    required: true
    description: Hostname or IP of the Semaphore server (including http or https).
  port:
    type: int
    required: true
    description: Port on which the Semaphore API is accessible.
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
  sort:
    type: str
    required: false
    choices: ["name", "git_url"]
    description: Field to sort the results by.
  order:
    type: str
    required: false
    choices: ["asc", "desc"]
    description: Sort order.
  validate_certs:
    type: bool
    default: true
    description: Whether to validate TLS certificates.
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: List repositories in a project
  ebdruplab.semaphoreui.project_repository_list:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    sort: name
    order: asc
'''

RETURN = r'''
repositories:
  description: List of project repositories
  returned: success
  type: list
  elements: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            project_id=dict(type='int', required=True),
            sort=dict(type='str', required=False, choices=["name", "git_url"]),
            order=dict(type='str', required=False, choices=["asc", "desc"]),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    sort = module.params.get("sort")
    order = module.params.get("order")
    validate_certs = module.params["validate_certs"]

    # Construct query string
    query = []
    if sort:
        query.append(f"sort={sort}")
    if order:
        query.append(f"order={order}")
    query_string = f"?{'&'.join(query)}" if query else ""

    url = f"{host}:{port}/api/project/{project_id}/repositories{query_string}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(
            url=url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            error = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"GET failed with status {status}: {error}", status=status)

        repositories = json.loads(response_body) if response_body else []
        module.exit_json(changed=False, repositories=repositories)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

