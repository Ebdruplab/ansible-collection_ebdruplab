#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_environment_create
short_description: Create a Semaphore environment
version_added: "1.0.0"
description:
  - Creates an environment inside a Semaphore project using the project ID.
options:
  host:
    description:
      - The URL or IP of the Semaphore server (including http or https).
    required: true
    type: str
  port:
    description:
      - The port on which the Semaphore API is running.
    required: true
    type: int
  project_id:
    description:
      - ID of the Semaphore project to associate the environment with.
    required: true
    type: int
  environment:
    description:
      - A dictionary defining the environment including name, env, json, password, and secrets.
    required: true
    type: dict
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
- name: Create an environment in a project
  ebdruplab.semaphoreui.project_environment_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    environment:
      name: "Test Environment"
      password: "mysecret"
      env:
        KEY: "value"
      json:
        foo: "bar"
      secrets: []
"""

RETURN = r"""
environment:
  description: The created environment object.
  type: dict
  returned: success
  sample:
    id: 5
    name: Test Environment
    project_id: 1
    env: '{"KEY": "value"}'
    json: '{"foo": "bar"}'
    secrets: []

status:
  description: HTTP response status code from the Semaphore API.
  type: int
  returned: always
  sample: 201
"""

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            environment=dict(type='dict', required=True),
            session_cookie=dict(type='str', no_log=True, required=False),
            api_token=dict(type='str', no_log=True, required=False),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    environment = module.params["environment"]
    validate_certs = module.params["validate_certs"]
    session_cookie = module.params.get("session_cookie")
    api_token = module.params.get("api_token")

    # Ensure project_id is present in the payload
    environment["project_id"] = project_id

    # Convert env and json fields if they're dicts
    for field in ["env", "json"]:
        if field in environment:
            if isinstance(environment[field], dict):
                try:
                    environment[field] = json.dumps(environment[field])
                except Exception as e:
                    module.fail_json(msg=f"Failed to serialize '{field}' field: {e}")
            elif not isinstance(environment[field], str):
                module.fail_json(msg=f"'{field}' must be a valid JSON string or a dictionary.")

    url = f"{host}:{port}/api/project/{project_id}/environment"
    headers = get_auth_headers(session_cookie=session_cookie, api_token=api_token)
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(environment).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url=url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 201):
            error = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to create environment: HTTP {status} - {error}", status=status)

        environment_obj = json.loads(response_body)
        module.exit_json(changed=True, environment=environment_obj, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

