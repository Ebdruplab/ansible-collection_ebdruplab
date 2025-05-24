from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_task_logs
short_description: Retrieve logs for a Semaphore task
version_added: "1.0.0"
description:
  - Retrieves the output logs for a specific task in a Semaphore project.
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
  task_id:
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
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Get logs for a task
  ebdruplab.semaphoreui.project_task_logs:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    task_id: 42
'''

RETURN = r'''
logs:
  description: List of log entries for the task
  type: list
  elements: dict
  returned: success
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            task_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]

    try:
        project_id = int(module.params["project_id"])
        task_id = int(module.params["task_id"])
    except Exception as e:
        module.fail_json(msg=f"Invalid project_id or task_id: {e}")

    url = f"{host}:{port}/api/project/{project_id}/tasks/{task_id}/output"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(
            url=url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"Failed to retrieve task logs: HTTP {status}", status=status)

        logs = json.loads(response_body.decode()) if isinstance(response_body, bytes) else json.loads(response_body)
        module.exit_json(changed=False, logs=logs)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

