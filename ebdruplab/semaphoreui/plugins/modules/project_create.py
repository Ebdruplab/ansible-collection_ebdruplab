# plugins/modules/project_create.py

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
  name:
    type: str
    required: true
  alert:
    type: bool
    default: false
  alert_chat:
    type: str
    default: ''
  max_parallel_tasks:
    type: int
    default: 0
  type:
    type: str
    default: ''
  demo:
    type: bool
    default: false
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Create a new project
  ebdruplab.semaphoreui.project_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    name: "ebdruplab_integration_test_1"
'''

RETURN = r'''
project:
  description: Details of the created project
  returned: success
  type: dict
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
            alert_chat=dict(type='str', default=''),
            max_parallel_tasks=dict(type='int', default=0),
            type=dict(type='str', default=''),
            demo=dict(type='bool', default=False),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    url = f"{module.params['host']}:{module.params['port']}/api/projects"
    headers = get_auth_headers(
        module.params['session_cookie'],
        module.params['api_token']
    )
    headers["Content-Type"] = "application/json"

    project_data = {
        "name": module.params["name"],
        "alert": module.params["alert"],
        "alert_chat": module.params["alert_chat"],
        "max_parallel_tasks": module.params["max_parallel_tasks"],
        "type": module.params["type"],
        "demo": module.params["demo"]
    }

    try:
        body = json.dumps(project_data).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url,
            body=body,  # CORRECT keyword
            headers=headers,
            validate_certs=module.params["validate_certs"]
        )

        if status not in (200, 201):
            module.fail_json(msg=f"Failed to create project: HTTP {status} - {response_body}")

        project = json.loads(response_body)
        module.exit_json(changed=True, project=project)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
