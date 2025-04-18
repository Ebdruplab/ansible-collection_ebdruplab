from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: template_create
short_description: Create a Semaphore template
version_added: "1.0.0"
description:
  - Creates a new template in Semaphore.
options:
  host:
    type: str
    required: true
    description: Hostname or IP of the Semaphore server (excluding protocol).
  port:
    type: int
    required: true
    description: Port of the Semaphore server (e.g., 3000).
  project_id:
    type: int
    required: true
    description: ID of the project in which to create the template.
  template:
    type: dict
    required: true
    description: Dictionary describing the template. Must include required fields like name, app, playbook, etc.
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
        required: false
        default: "job"
      view_id:
        type: str
        required: false
        description: ID or name of the view to group the template in. Defaults to "Empty".
      allow_override_args_in_task:
        type: bool
        required: false
        default: false
      survey_vars:
        type: list
        elements: dict
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
    description: Whether to validate TLS certificates.
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Create a template and set it to the "Empty" view
  ebdruplab.semaphoreui.template_create:
    host: localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    template:
      name: "My Template"
      app: "ansible"
      playbook: "playbook.yml"
      inventory_id: 1
      repository_id: 1
      type: "job"
      view_id: "Empty"
      allow_override_args_in_task: false
      survey_vars: []
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

    url = f"{host}:{port}/api/project/{project_id}/templates"

    # Validate required template fields
    required_fields = ["name", "app", "playbook", "inventory_id", "repository_id"]
    missing = [f for f in required_fields if f not in template or template[f] in [None, ""]]
    if missing:
        module.fail_json(msg=f"Missing required fields in template: {', '.join(missing)}")

    # Default values
    if "view_id" not in template or not template["view_id"]:
        template["view_id"] = "Empty"
    if "type" not in template:
        template["type"] = "job"
    if "allow_override_args_in_task" not in template:
        template["allow_override_args_in_task"] = False
    if "survey_vars" not in template:
        template["survey_vars"] = []

    # Ensure project_id is included
    template["project_id"] = project_id

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
            msg = response_body if isinstance(response_body, str) else response_body.decode()
            module.fail_json(msg=f"Failed to create template: HTTP {status} - {msg}", status=status)

        result = json.loads(response_body)
        module.exit_json(changed=True, template=result)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
