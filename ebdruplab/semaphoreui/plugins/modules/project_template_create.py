from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_template_create
short_description: Create a Semaphore template
version_added: "1.0.0"
description:
  - Creates a new template in Semaphore.
options:
  host:
    type: str
    required: true
  port:
    type: int
    required: true
  project_id:
    type: int
    required: true
  template:
    type: dict
    required: true
    description: Dictionary defining the template.
    suboptions:
      name:
        type: str
        required: true
      app:
        type: str
        required: true
      playbook:
        type: str
        required: true
      inventory_id:
        type: int
        required: true
      repository_id:
        type: int
        required: true
      environment_id:
        type: int
        required: false
      type:
        type: str
        default: "job"
      view_id:
        type: int
        required: false
      allow_override_args_in_task:
        type: bool
        default: false
      suppress_success_alerts:
        type: bool
        default: false
      survey_vars:
        type: list
        elements: dict
        required: false
      arguments:
        type: str
        required: false
      limit:
        type: str
        required: false
      tags:
        type: str
        required: false
      skip_tags:
        type: str
        required: false
      vault_password:
        type: str
        required: false
      prompt_inventory:
        type: bool
        required: false
      prompt_limit:
        type: bool
        required: false
      prompt_tags:
        type: bool
        required: false
      prompt_skip_tags:
        type: bool
        required: false
      prompt_vault_password:
        type: bool
        required: false
      prompt_arguments:
        type: bool
        required: false
      prompt_branch:
        type: bool
        required: false
      prompt_environment:
        type: bool
        required: false
  session_cookie:
    type: str
    required: false
    no_log: true
  api_token:
    type: str
    required: false
    no_log: true
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Create a Semaphore template with runtime prompts
  ebdruplab.semaphoreui.project_template_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    template:
      name: "My Template"
      app: "ansible"
      playbook: "playbooks/site.yml"
      inventory_id: 1
      repository_id: 1
      environment_id: 1
      arguments: "--diff"
      limit: "app*"
      tags: "setup"
      skip_tags: "debug"
      vault_password: "my-vault"
      prompt_inventory: true
      prompt_limit: true
      prompt_tags: true
      prompt_skip_tags: true
      prompt_vault_password: true
      prompt_arguments: true
      prompt_branch: true
      prompt_environment: true
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
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    template = module.params["template"]
    validate_certs = module.params["validate_certs"]

    required_fields = ["name", "app", "playbook", "inventory_id", "repository_id"]
    missing = [f for f in required_fields if f not in template or template[f] in [None, ""]]
    if missing:
        module.fail_json(msg=f"Missing required fields in template: {', '.join(missing)}")

    for field in ["inventory_id", "repository_id", "view_id", "environment_id"]:
        if field in template and template[field] is not None:
            template[field] = int(template[field])

    defaults = {
        "type": "job",
        "view_id": 1,
        "allow_override_args_in_task": False,
        "suppress_success_alerts": False,
        "survey_vars": [],
    }

    for key, val in defaults.items():
        template.setdefault(key, val)

    template["project_id"] = project_id

    url = f"{host}:{port}/api/project/{project_id}/templates"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(template).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 201):
            msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to create template: HTTP {status} - {msg}", status=status)

        module.exit_json(changed=True, template=json.loads(response_body))

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

