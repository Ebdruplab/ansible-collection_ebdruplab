#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_template_update
short_description: Update a Semaphore template
version_added: "1.0.0"
description:
  - Updates an existing template in a specified Semaphore project.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (including protocol).
    type: str
    required: true
  port:
    description:
      - Port of the Semaphore server (typically 3000).
    type: int
    required: true
  project_id:
    description:
      - ID of the project the template belongs to.
    type: int
    required: true
  template_id:
    description:
      - ID of the template to update.
    type: int
    required: true
  template:
    description:
      - Template payload with updated fields.
    type: dict
    required: true
  session_cookie:
    description:
      - Session cookie used to authenticate.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token used to authenticate.
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate SSL certificates.
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Update a Semaphore template
  ebdruplab.semaphoreui.project_template_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    template_id: 7
    template:
      name: "Updated Template"
      app: "ansible"
      playbook: "deploy.yml"
      inventory_id: 1
      repository_id: 1
      environment_id: 1
      view_id: 1
      type: "job"
      allow_override_args_in_task: false
      suppress_success_alerts: true
      arguments: "--check"
      limit: "localhost"
      tags: "frontend"
      skip_tags: "db"
      vault_password: "vault"
      prompt_debug: true
"""

RETURN = r"""
updated:
  description: Whether the template was updated.
  type: bool
  returned: always
status:
  description: HTTP status code from the Semaphore API.
  type: int
  returned: always
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            template_id=dict(type='int', required=True),
            template=dict(type='dict', required=True),
            session_cookie=dict(type='str', no_log=True),
            api_token=dict(type='str', no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=False
    )

    host = module.params['host'].rstrip('/')
    port = module.params['port']
    project_id = module.params['project_id']
    template_id = module.params['template_id']
    template = module.params['template']
    validate_certs = module.params['validate_certs']

    # Inject required identifiers
    template['id'] = template_id
    template['project_id'] = project_id

    url = f"{host}:{port}/api/project/{project_id}/templates/{template_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get('session_cookie'),
        api_token=module.params.get('api_token')
    )
    headers['Content-Type'] = 'application/json'

    try:
        body = json.dumps(template).encode('utf-8')
        response_body, status, _ = semaphore_put(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 204):
            msg = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else str(response_body)
            module.fail_json(msg=f"Failed to update template: HTTP {status} - {msg}", status=status)

        module.exit_json(changed=True, updated=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

