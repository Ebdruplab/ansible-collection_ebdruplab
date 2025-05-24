from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_task_list
short_description: List tasks in a Semaphore project
description:
  - Retrieves a list of all tasks related to the given project in chronological order.
options:
  host:
    type: str
    required: true
  port:
    type: int
    required: true
  session_cookie:
    type: str
    required: false
    no_log: true
  api_token:
    type: str
    required: false
    no_log: true
  project_id:
    type: int
    required: true
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: List all tasks in a project
  ebdruplab.semaphoreui.project_task_list:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
'''

RETURN = r'''
tasks:
  description: List of tasks for the project
  returned: success
  type: list
  elements: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            project_id=dict(type='int', required=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/tasks"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(
            url, headers=headers, validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"GET failed with status {status}", response=response_body)

        try:
            tasks = json.loads(response_body)
        except json.JSONDecodeError as e:
            module.fail_json(msg=f"Failed to decode JSON: {e}", raw=response_body)

        if not isinstance(tasks, list):
            module.fail_json(msg="Expected response to be a list of tasks", raw=response_body)

        module.exit_json(changed=False, tasks=tasks)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()

