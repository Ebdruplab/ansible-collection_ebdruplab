#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import (
    semaphore_post,
    semaphore_put,
    semaphore_get_json,
    get_auth_headers,
    sanitize_check_mode_value,
    exit_check_mode,
)
import json

DOCUMENTATION = r"""
---
module: project_create
short_description: Create or manage a Semaphore project
version_added: "1.0.0"
description:
  - C(state=present) looks up a project by name and creates it only when absent.
  - Supply C(id) with C(state=present) to update a specific project, including a rename.
  - C(state=create) explicitly creates a new project even when the name already exists.
options:
  host:
    description:
      - Hostname or IP address of the Semaphore server (including protocol).
    required: true
    type: str
  port:
    description:
      - Port of the Semaphore server (typically 3000).
    required: true
    type: int
  session_cookie:
    description:
      - Session cookie used for authentication.
    required: false
    type: str
    no_log: true
  api_token:
    description:
      - API token used for authentication.
    required: false
    type: str
    no_log: true
  name:
    description:
      - Name of the project to be created.
    required: true
    type: str
  alert:
    description:
      - Whether to enable alert notifications for the project.
    required: false
    type: bool
    default: false
  alert_chat:
    description:
      - Name of the chat integration for alerts.
    required: false
    type: str
    default: Ansible
  max_parallel_tasks:
    description:
      - Maximum number of parallel tasks allowed in the project.
    required: false
    type: int
    default: 0
  demo:
    description:
      - Whether the project is a demo project.
    required: false
    type: bool
    default: false
  state:
    description:
      - Desired lifecycle behavior.
      - C(present) finds a single matching project by name, updates it, or creates it when absent.
      - C(create) always creates a new project.
    type: str
    choices: [present, create]
    default: present
  id:
    description:
      - Existing project ID to manage with C(state=present).
      - Takes precedence over name lookup and enables safe renames.
    type: int
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    required: false
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Ensure a Semaphore project is present
  ebdruplab.semaphoreui.project_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    name: "ebdruplab integration test"

- name: Rename a project by its stable ID
  ebdruplab.semaphoreui.project_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    state: present
    id: 42
    name: "Renamed Project"

- name: Create project with token and custom settings
  ebdruplab.semaphoreui.project_create:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_token }}"
    name: "My Project"
    alert: true
    alert_chat: "#alerts"
    max_parallel_tasks: 5
    demo: false
"""

RETURN = r"""
project:
  description: The details of the created project.
  type: dict
  returned: success
  sample:
    id: 42
    name: "My Project"
    alert: true
    alert_chat: "#alerts"
    max_parallel_tasks: 5
    demo: false
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            name=dict(type='str', required=True),
            alert=dict(type='bool', default=False),
            alert_chat=dict(type='str', default='Ansible'),
            max_parallel_tasks=dict(type='int', default=0),
            demo=dict(type='bool', default=False),
            state=dict(type='str', choices=['present', 'create'], default='present'),
            id=dict(type='int', required=False),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params['host']
    port = module.params['port']
    url = f"{host}:{port}/api/projects/"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    project_data = {
        "name": module.params["name"],
        "alert": module.params["alert"],
        "alert_chat": module.params["alert_chat"],
        "max_parallel_tasks": module.params["max_parallel_tasks"],
        "demo": module.params["demo"],
        "type": ""
    }
    state = module.params['state']
    project_id = module.params.get('id')

    if state == 'create' and project_id:
        module.fail_json(msg="id is only valid when state=present")

    try:
        if state == 'present':
            if project_id:
                matches = [{'id': project_id}]
            else:
                projects, response_body, status, _ = semaphore_get_json(
                    url, headers=headers, validate_certs=module.params['validate_certs']
                )
                if status != 200 or not isinstance(projects, list):
                    module.fail_json(
                        msg=f"Failed to list projects for lookup: HTTP {status}",
                        status=status,
                        response=response_body,
                    )
                matches = [project for project in projects if project.get('name') == project_data['name']]
                if len(matches) > 1:
                    module.fail_json(
                        msg=(f"Project lookup for '{project_data['name']}' matched {len(matches)} resources; "
                             "specify id to select one explicitly.")
                    )

            if len(matches) == 1:
                project_id = matches[0].get('id')
                if not isinstance(project_id, int):
                    module.fail_json(msg="Matched project has no valid ID.")
                item_url = f"{host}:{port}/api/project/{project_id}"
                current, response_body, status, _ = semaphore_get_json(
                    item_url, headers=headers, validate_certs=module.params['validate_certs']
                )
                if status != 200 or not isinstance(current, dict):
                    module.fail_json(
                        msg=f"Failed to fetch matched project state: HTTP {status}",
                        status=status,
                        response=response_body,
                    )

                payload = {
                    key: current[key]
                    for key in ('name', 'alert', 'alert_chat', 'max_parallel_tasks', 'demo', 'type')
                    if key in current
                }
                managed_data = dict(project_data)
                # Semaphore normalizes this internal field differently across
                # versions. It is not user-configurable in this module, so do
                # not force a change merely to rewrite it.
                managed_data.pop('type', None)
                payload.update(managed_data)
                payload['id'] = project_id
                before = {key: current.get(key) for key in managed_data}
                after = {key: payload.get(key) for key in managed_data}
                changed = before != after

                if module.check_mode:
                    module.exit_json(
                        changed=changed,
                        check_mode=True,
                        before=sanitize_check_mode_value(before),
                        after=sanitize_check_mode_value(after),
                    )
                if not changed:
                    module.exit_json(changed=False, project=sanitize_check_mode_value(current), status=200)

                response_body, status, _ = semaphore_put(
                    item_url,
                    body=json.dumps(payload).encode('utf-8'),
                    headers=headers,
                    validate_certs=module.params['validate_certs'],
                )
                if status not in (200, 204):
                    module.fail_json(msg=f"Failed to update project: HTTP {status} - {response_body}", status=status)
                module.exit_json(changed=True, project=payload, status=status)

        body = json.dumps(project_data).encode("utf-8")
        if module.check_mode:
            exit_check_mode(module)

        response_body, status, _ = semaphore_post(
            url,
            body=body,
            headers=headers,
            validate_certs=module.params["validate_certs"]
        )

        if status not in (200, 201):
            module.fail_json(msg=f"Failed to create project: HTTP {status} - {response_body.decode()}")

        project = json.loads(response_body)
        module.exit_json(changed=True, project=project)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
