from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_create
short_description: Create a new Semaphore project
version_added: "1.0.0"
description:
  - Sends a POST request to create a new Semaphore project.
options:
  host:
    type: str
    required: true
    description: Hostname of the Semaphore server (without protocol).
  port:
    type: int
    required: true
    description: Port of the Semaphore server (typically 3000).
  session_cookie:
    type: str
    required: false
    no_log: true
  api_token:
    type: str
    required: false
    no_log: true
  name:
    type: str
    required: true
    description: Name of the project to create.
  alert:
    type: bool
    default: false
  alert_chat:
    type: str
    default: 'Ansible'
  max_parallel_tasks:
    type: int
    default: 0
  demo:
    type: bool
    default: false
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Create a new Semaphore project
  ebdruplab.semaphoreui.project_create:
    host: localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    name: "ebdruplab integration test"
'''

RETURN = r'''
project:
  description: Details of the created project.
  type: dict
  returned: success
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            name=dict(type='str', required=True),
            alert=dict(type='bool', default=False),
            alert_chat=dict(type='str', default='Ansible'),
            max_parallel_tasks=dict(type='int', default=0),
            demo=dict(type='bool', default=False),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    host = module.params['host']
    port = module.params['port']
    url = f"{host}:{port}/api/projects/"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    project_data = {
        "name": module.params["name"],
        "alert": module.params["alert"],
        "alert_chat": module.params["alert_chat"],
        "max_parallel_tasks": module.params["max_parallel_tasks"],
        "demo": module.params["demo"],
        "type": ""
    }

    try:
        body = json.dumps(project_data).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url,
            body=body,
            headers=headers,
            validate_certs=module.params["validate_certs"]
        )

        if status not in (200, 201):
            module.fail_json(msg=f"Failed to create project: HTTP {status} - {response_body.decode()}")

        project = json.loads(response_body)
        module.exit_json(changed=True, project=project)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
