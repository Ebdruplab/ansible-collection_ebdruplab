#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers

DOCUMENTATION = r"""
---
module: project_template_list
short_description: List templates in a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves a list of templates from a specific Semaphore project.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (including protocol).
    type: str
    required: true
  port:
    description:
      - Port on which the Semaphore server is listening.
    type: int
    required: true
  project_id:
    description:
      - ID of the project to list templates for.
    type: int
    required: true
  session_cookie:
    description:
      - Session cookie for authentication (obtained from login module).
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token for authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate SSL certificates.
    type: bool
    required: false
    default: true
  sort:
    description:
      - Field to sort by (e.g., C(name), C(type), etc.).
    type: str
    required: false
  order:
    description:
      - Sort order (ascending or descending).
    type: str
    required: false
    choices: ["asc", "desc"]
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: List templates in a project (sorted by name ascending)
  ebdruplab.semaphoreui.project_template_list:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    sort: name
    order: asc
"""

RETURN = r"""
templates:
  description: List of templates in the specified project.
  type: list
  elements: dict
  returned: success
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
            sort=dict(type='str', required=False),
            order=dict(type='str', required=False, choices=['asc', 'desc']),
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=True
    )

    host = module.params['host'].rstrip('/')
    port = module.params['port']
    project_id = module.params['project_id']
    sort = module.params.get('sort')
    order = module.params.get('order')
    validate_certs = module.params['validate_certs']
    session_cookie = module.params.get('session_cookie')
    api_token = module.params.get('api_token')

    url = f"{host}:{port}/api/project/{project_id}/templates"
    query_params = []
    if sort:
        query_params.append(f"sort={sort}")
    if order:
        query_params.append(f"order={order}")
    if query_params:
        url += '?' + '&'.join(query_params)

    try:
        headers = get_auth_headers(session_cookie=session_cookie, api_token=api_token)
        headers['Content-Type'] = 'application/json'

        response_body, status, _ = semaphore_get(
            url,
            validate_certs=validate_certs,
            headers=headers
        )

        if status != 200:
            module.fail_json(msg=f"Failed to list templates: HTTP {status}", status=status)

        templates = response_body if isinstance(response_body, list) else []
        module.exit_json(changed=False, templates=templates)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

