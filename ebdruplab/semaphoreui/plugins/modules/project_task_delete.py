from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r'''
---
module: project_task_delete
short_description: Delete a task from a Semaphore project
description:
  - Deletes a task (including its output) from the specified Semaphore project.
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
  task_id:
    type: int
    required: true
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Delete a task from a project
  ebdruplab.semaphoreui.project_task_delete:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    task_id: 8
'''

RETURN = r'''
msg:
  description: Status message
  returned: always
  type: str
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            project_id=dict(type='int', required=True),
            task_id=dict(type='int', required=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    task_id = module.params["task_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/tasks/{task_id}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        _, status, _ = semaphore_delete(
            url, headers=headers, validate_certs=validate_certs
        )

        if status != 204:
            module.fail_json(msg=f"DELETE failed with status {status}")

        module.exit_json(changed=True, msg="Task deleted successfully.")

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

