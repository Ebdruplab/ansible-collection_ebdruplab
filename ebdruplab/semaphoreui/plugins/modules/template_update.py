from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: template_update
short_description: Update a Semaphore template
version_added: "1.0.0"
description:
  - Updates an existing template in a specified Semaphore project.
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
  template_id:
    type: int
    required: true
  template:
    type: dict
    required: true
    description: Template payload with updated fields.
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
- name: Update a Semaphore template
  ebdruplab.semaphoreui.template_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    template_id: 7
    template:
      name: "Updated Template"
      playbook: "updated_playbook.yml"
      type: "job"
      inventory_id: null
      repository_id: null
      environment_id: null
      allow_override_args_in_task: false
      survey_vars: []
'''

RETURN = r'''
updated:
  description: Whether the template was updated
  type: bool
  returned: always
status:
  description: HTTP status code from the Semaphore API
  type: int
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            template_id=dict(type='int', required=True),
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
    template_id = module.params["template_id"]
    payload = module.params["template"]
    validate_certs = module.params["validate_certs"]
    session_cookie = module.params.get("session_cookie")
    api_token = module.params.get("api_token")

    url = f"{host}:{port}/api/project/{project_id}/templates/{template_id}"

    try:
        headers = get_auth_headers(session_cookie=session_cookie, api_token=api_token)
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")

        _, status, _ = semaphore_put(url, body=body, headers=headers, validate_certs=validate_certs)

        if status not in (200, 204):
            module.fail_json(msg=f"PUT failed with status {status}")

        module.exit_json(changed=True, updated=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

