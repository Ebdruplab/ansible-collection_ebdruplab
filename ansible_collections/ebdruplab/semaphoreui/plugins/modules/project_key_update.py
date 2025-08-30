#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_key_update
short_description: Update an access key in Semaphore
version_added: "2.0.2"
description:
  - Updates an existing access key in Semaphore via C(PUT /api/project/{project_id}/keys/{key_id}).
  - Supports SSH and login/password key types and can override stored secrets.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (including protocol).
      - Example C(http://localhost) or C(https://semaphore.example.com).
    type: str
    required: true
  port:
    description:
      - Port of the Semaphore server, for example C(3000).
    type: int
    required: true
  project_id:
    description:
      - ID of the project containing the key.
    type: int
    required: true
  key_id:
    description:
      - ID of the access key to update.
    type: int
    required: true
  name:
    description:
      - New name of the key.
    type: str
    required: true
  type:
    description:
      - Type of the access key.
    type: str
    choices: ["ssh", "login_password"]
    required: true
  ssh:
    description:
      - SSH key details, required when I(type=ssh).
    type: dict
    required: false
    no_log: true
    suboptions:
      login:
        description:
          - SSH login username.
        type: str
        required: true
      passphrase:
        description:
          - Optional SSH key passphrase.
        type: str
        required: false
        no_log: true
      private_key:
        description:
          - Private SSH key content.
        type: str
        required: true
        no_log: true
  login_password:
    description:
      - Login/password details, required when I(type=login_password).
    type: dict
    required: false
    no_log: true
    suboptions:
      login:
        description:
          - Login username.
        type: str
        required: true
      password:
        description:
          - Login password.
        type: str
        required: true
        no_log: true
  override_secret:
    description:
      - Whether to override the stored secret material.
    type: bool
    default: true
  session_cookie:
    description:
      - Session cookie for authentication.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - Bearer token for authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - Whether to validate TLS certificates.
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Update SSH key by ID (session cookie)
  ebdruplab.semaphoreui.project_key_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    key_id: 3
    name: "Repo Deploy Key"
    type: "ssh"
    ssh:
      login: "git"
      private_key: "{{ lookup('file', '~/.ssh/id_rsa') }}"
    override_secret: true

- name: Update login/password key by ID (API token)
  ebdruplab.semaphoreui.project_key_update:
    host: https://semaphore.example.com
    port: 443
    api_token: "{{ semaphore_api_token }}"
    project_id: 1
    key_id: 5
    name: "Docker Registry"
    type: "login_password"
    login_password:
      login: "registry-user"
      password: "{{ registry_password }}"
    override_secret: true
    validate_certs: true
'''

RETURN = r'''
changed:
  description: Whether the key was updated.
  type: bool
  returned: always
status:
  description: HTTP status code returned by the API.
  type: int
  returned: success
project_id:
  description: Project ID used in the request.
  type: int
  returned: success
key_id:
  description: Key ID that was updated.
  type: int
  returned: success
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            key_id=dict(type='int', required=True),
            name=dict(type='str', required=True),
            type=dict(type='str', required=True, choices=["ssh", "login_password"]),
            ssh=dict(
                type='dict',
                required=False,
                no_log=True,
                options=dict(
                    login=dict(type='str', required=True),
                    passphrase=dict(type='str', required=False, no_log=True),
                    private_key=dict(type='str', required=True, no_log=True),
                ),
            ),
            login_password=dict(
                type='dict',
                required=False,
                no_log=True,
                options=dict(
                    login=dict(type='str', required=True),
                    password=dict(type='str', required=True, no_log=True),
                ),
            ),
            override_secret=dict(type='bool', default=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True,
    )

    p = module.params
    host = p["host"].rstrip("/")
    port = p["port"]
    project_id = p["project_id"]
    key_id = p["key_id"]
    key_type = p["type"]
    validate_certs = p["validate_certs"]

    if key_type == "ssh" and not p.get("ssh"):
        module.fail_json(msg="ssh data is required when type is 'ssh'")
    if key_type == "login_password" and not p.get("login_password"):
        module.fail_json(msg="login_password data is required when type is 'login_password'")

    url = f"{host}:{port}/api/project/{project_id}/keys/{key_id}"

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token"),
    )
    headers["Content-Type"] = "application/json"

    payload = {
        "id": key_id,
        "name": p["name"],
        "type": key_type,
        "project_id": project_id,
        "override_secret": p["override_secret"],
    }
    if key_type == "ssh":
        payload["ssh"] = p["ssh"]
    elif key_type == "login_password":
        payload["login_password"] = p["login_password"]

    if module.check_mode:
        module.exit_json(changed=True, status=204, project_id=project_id, key_id=key_id)

    try:
        body = json.dumps(payload).encode("utf-8")
        _, status, _ = semaphore_put(
            url=url,
            body=body,
            headers=headers,
            validate_certs=validate_certs,
        )
        if status not in (200, 204):
            module.fail_json(msg=f"Failed to update key: HTTP {status}", status=status)
        module.exit_json(changed=True, status=status, project_id=project_id, key_id=key_id)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
