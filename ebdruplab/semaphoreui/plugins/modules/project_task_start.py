from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_task_start
short_description: Start a task using a Semaphore template
version_added: "1.0.0"
description:
  - Starts a new task/job in Semaphore by triggering a run based on a template.
options:
  host:
    type: str
    required: true
    description: Hostname or IP of the Semaphore server (e.g. http://localhost).
  port:
    type: int
    required: true
    description: Port of the Semaphore API (e.g. 3000).
  project_id:
    type: int
    required: true
    description: Project ID that owns the template and task.
  task:
    type: dict
    required: true
    description:
      Dictionary with task options. Must include template_id, inventory_id,
      repository_id, and environment_id. Optional: debug, override_args, start_version.
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
- name: Start a task using a template
  ebdruplab.semaphoreui.project_task_start:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 123
    task:
      template_id: 1
      inventory_id: 1
      repository_id: 1
      environment_id: 1
      debug: true
      override_args: ""
      start_version: ""
'''

RETURN = r'''
task:
  description: The started task object
  returned: success
  type: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            task=dict(type='dict', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]
    session_cookie = module.params.get("session_cookie")
    api_token = module.params.get("api_token")
    task = module.params["task"]

    # Validate and coerce numeric fields
    try:
        project_id = int(module.params["project_id"])
        for field in ["template_id", "inventory_id", "repository_id", "environment_id"]:
            if field not in task or task[field] is None:
                module.fail_json(msg=f"Missing required task field: {field}")
            task[field] = int(task[field])
    except Exception as e:
        module.fail_json(msg=f"Invalid numeric value in task: {e}")

    url = f"{host}:{port}/api/project/{project_id}/tasks"

    headers = get_auth_headers(session_cookie=session_cookie, api_token=api_token)
    headers["Content-Type"] = "application/json"

    try:
        payload = json.dumps(task).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url,
            body=payload,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 201):
            decoded = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to start task: HTTP {status} - {decoded}", status=status)

        result = json.loads(response_body.decode()) if isinstance(response_body, bytes) else json.loads(response_body)
        module.exit_json(changed=True, task=result)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

