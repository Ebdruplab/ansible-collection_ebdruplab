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
  port:
    type: int
    required: true
  project_id:
    type: int
    required: true
  template:
    type: dict
    required: true
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
- name: Create a Semaphore template
  ebdruplab.semaphoreui.template_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    template:
      name: "My Template"
      app: "ansible"
      playbook: "playbook.yml"
      repository_id: 1
      inventory_id: 1
      view_id: 1
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

    # Validate required fields
    required_fields = ["name", "app", "playbook", "inventory_id", "repository_id"]
    missing = [f for f in required_fields if f not in template or template[f] in [None, ""]]
    if missing:
        module.fail_json(msg=f"Missing required fields in template: {', '.join(missing)}")

    # Ensure correct data types
    for field in ["inventory_id", "repository_id", "view_id"]:
        if field in template and template[field] is not None:
            template[field] = int(template[field])

    # Apply defaults
    template.setdefault("type", "job")
    template.setdefault("view_id", 1)
    template.setdefault("allow_override_args_in_task", False)
    template.setdefault("suppress_success_alerts", False)
    template.setdefault("survey_vars", [])
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
            msg = response_body if isinstance(response_body, str) else response_body.decode()
            module.fail_json(msg=f"Failed to create template: HTTP {status} - {msg}", status=status)

        module.exit_json(changed=True, template=json.loads(response_body))

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

