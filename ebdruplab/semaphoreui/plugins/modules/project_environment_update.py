#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_environment_update
short_description: Update an existing environment in a Semaphore project
version_added: "1.0.0"
description:
  - Updates the specified environment for a project in Semaphore.
options:
  host:
    description:
      - Hostname or IP of the Semaphore server (including http or https).
    required: true
    type: str
  port:
    description:
      - Port where the Semaphore API is running.
    required: true
    type: int
  project_id:
    description:
      - ID of the Semaphore project.
    required: true
    type: int
  environment_id:
    description:
      - ID of the environment to update.
    required: true
    type: int
  environment:
    description:
      - Dictionary describing the environment to update.
    required: true
    type: dict
  session_cookie:
    description:
      - Session authentication cookie.
    required: false
    type: str
    no_log: true
  api_token:
    description:
      - Bearer token for authentication.
    required: false
    type: str
    no_log: true
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
- name: Update an environment
  ebdruplab.semaphoreui.project_environment_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    environment_id: 2
    environment:
      name: "Updated Env"
      password: "updatedpass"
      env:
        KEY: "updated"
      json:
        key: "updated"
      secrets: []
"""

RETURN = r"""
environment:
  description: The updated environment object (if returned by the server).
  type: dict
  returned: success
status:
  description: HTTP response status code.
  type: int
  returned: always
"""

def serialize_json_field(field_value, field_name, module):
    """
    Ensures the field is a valid JSON string.
    Accepts dict or JSON string. Fails if input is invalid.
    """
    if isinstance(field_value, dict):
        return json.dumps(field_value)
    elif isinstance(field_value, str):
        try:
            json.loads(field_value)
            return field_value
        except json.JSONDecodeError:
            if "=" in field_value:
                key, value = field_value.split("=", 1)
                return json.dumps({key.strip(): value.strip()})
            else:
                module.fail_json(msg=f"Invalid JSON string in field '{field_name}': {field_value}")
    else:
        module.fail_json(msg=f"Unsupported type for field '{field_name}': {type(field_value)}")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            environment_id=dict(type='int', required=True),
            environment=dict(type='dict', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    environment_id = module.params["environment_id"]
    environment = module.params["environment"]
    validate_certs = module.params["validate_certs"]

    environment["project_id"] = project_id
    environment["id"] = environment_id

    for field in ["env", "json"]:
        if field in environment:
            environment[field] = serialize_json_field(environment[field], field, module)

    url = f"{host}:{port}/api/project/{project_id}/environment/{environment_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(environment).encode("utf-8")
        response_body, status, _ = semaphore_put(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 204):
            error = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"PUT failed with status {status}: {error}", status=status)

        updated_env = json.loads(response_body) if response_body else {}
        module.exit_json(changed=True, environment=updated_env, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

