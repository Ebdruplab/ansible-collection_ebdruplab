from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers

DOCUMENTATION = r'''
---
module: project_task_cancel
short_description: Cancel a running Semaphore task
version_added: "1.0.0"
description:
  - Sends a cancellation request for a specific running task in a Semaphore project.
options:
  host:
    type: str
    required: true
    description: Hostname or IP of the Semaphore server (e.g. http://localhost).
  port:
    type: int
    required: true
    description: Port where Semaphore API is listening (e.g. 3000).
  project_id:
    type: int
    required: true
    description: ID of the project containing the task.
  task_id:
    type: int
    required: true
    description: ID of the task to cancel.
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
- name: Cancel a running task
  ebdruplab.semaphoreui.project_task_cancel:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    task_id: 42
'''

RETURN = r'''
cancelled:
  description: Whether the task was successfully cancelled
  type: bool
  returned: always
status:
  description: HTTP status code
  type: int
  returned: always
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
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    task_id = module.params["task_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/tasks/{task_id}/cancel"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_post(
            url=url,
            body=b"{}",  # Ensure an empty JSON object is sent
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 204:
            msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to cancel task: HTTP {status} - {msg}", status=status)

        module.exit_json(changed=True, cancelled=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

