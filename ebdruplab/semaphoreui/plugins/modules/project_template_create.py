#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_template_create
short_description: Create a Semaphore template (task, deploy or build)
version_added: "1.0.0"
description:
  - Creates a new template in Semaphore with support for full configuration including build linkage, arguments, vaults, and survey variables.
options:
  host:
    description:
      - Full host address of the Semaphore server (including http or https).
    type: str
    required: true
  port:
    description:
      - Port of the Semaphore server (e.g., 3000).
    type: int
    required: true
  project_id:
    description:
      - ID of the project where the template will be created.
    type: int
    required: true
  template:
    description:
      - Template definition dictionary.
    type: dict
    required: true
  session_cookie:
    description:
      - Session cookie used for authentication.
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - API token used for authentication.
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
- name: Create a new Semaphore template
  ebdruplab.semaphoreui.project_template_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    template:
      name: "Deploy Web"
      app: "ansible"
      playbook: "deploy.yml"
      inventory_id: 1
      repository_id: 1
      environment_id: 1
      type: "job"
      view_id: 1
      description: "A sample deployment"
      vaults: []
      arguments: "[]"
'''

RETURN = r'''
template:
  description: The created template object.
  type: dict
  returned: success
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            template=dict(type='dict', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=False,
    )

    p = module.params
    tpl = p['template']
    tpl['project_id'] = p['project_id']

    # Validate required fields
    required_fields = ['name', 'app', 'playbook', 'inventory_id', 'repository_id']
    for field in required_fields:
        if not tpl.get(field):
            module.fail_json(msg=f"Missing required template field: {field}")

    # Safe type coercion for required integer fields
    try:
        tpl['inventory_id'] = int(tpl['inventory_id'])
        tpl['repository_id'] = int(tpl['repository_id'])
    except (ValueError, TypeError):
        module.fail_json(msg="inventory_id and repository_id must be valid integers.")

    # Optional integer fields with defaults
    try:
        tpl['environment_id'] = int(tpl.get('environment_id', 1) or 1)
        tpl['view_id'] = int(tpl.get('view_id', 1) or 1)
        tpl['build_template_id'] = int(tpl.get('build_template_id', 0) or 0)
    except (ValueError, TypeError):
        module.fail_json(msg="Optional IDs must be valid integers if provided.")

    # Default field values
    defaults = {
        "type": "",
        "description": "",
        "git_branch": "",
        "limit": "",
        "tags": "",
        "skip_tags": "",
        "vault_password": "",
        "start_version": "",
        "allow_override_args_in_task": False,
        "suppress_success_alerts": False,
        "autorun": False,
        "prompt_inventory": False,
        "prompt_limit": False,
        "prompt_tags": False,
        "prompt_skip_tags": False,
        "prompt_vault_password": False,
        "prompt_arguments": False,
        "prompt_branch": False,
        "prompt_environment": False,
        "vaults": [],
        "survey_vars": []
    }
    for key, value in defaults.items():
        tpl.setdefault(key, value)

    # Validate and sanitize arguments
    tpl['arguments'] = tpl.get('arguments', "[]")
    try:
        json.loads(tpl['arguments'])
    except (TypeError, ValueError):
        module.fail_json(msg="template.arguments must be a valid JSON string (e.g. '[]').")

    # Validate vaults
    validated_vaults = []
    for v in tpl.get("vaults", []):
        if not isinstance(v, dict) or "id" not in v or "type" not in v:
            module.fail_json(msg="Each vault must be a dictionary with 'id' and 'type'.")
        try:
            v["id"] = int(v["id"])
        except (ValueError, TypeError):
            module.fail_json(msg=f"Vault 'id' must be an integer, got: {v['id']}")
        validated_vaults.append(v)
    tpl["vaults"] = validated_vaults

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    base_url = p['host'].replace('http://', '').replace('https://', '').rstrip('/')
    url = f"http://{base_url}:{p['port']}/api/project/{p['project_id']}/templates"

    try:
        body = json.dumps(tpl).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url=url,
            body=body,
            headers=headers,
            validate_certs=p["validate_certs"]
        )

        if status not in (200, 201):
            msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to create template: HTTP {status} - {msg}", status=status)

        module.exit_json(changed=True, template=json.loads(response_body))

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
