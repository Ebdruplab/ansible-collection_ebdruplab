from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: schedule_get
short_description: Get a schedule by ID for a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves a specific schedule from a Semaphore project.
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
  schedule_id:
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
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Get a schedule
  ebdruplab.semaphoreui.schedule_get:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    schedule_id: 5
'''

RETURN = r'''
schedule:
  description: The schedule object retrieved from the API
  returned: always
  type: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            schedule_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    url = f"{module.params['host']}:{module.params['port']}/api/project/{module.params['project_id']}/schedules/{module.params['schedule_id']}"

    try:
        headers = get_auth_headers(
            session_cookie=module.params["session_cookie"],
            api_token=module.params["api_token"]
        )
        headers["Content-Type"] = "application/json"

        response, status, _ = semaphore_get(url, headers=headers, validate_certs=module.params["validate_certs"])

        if status != 200:
            module.fail_json(msg=f"Failed to fetch schedule: HTTP {status} - {response}")

        module.exit_json(changed=False, schedule=json.loads(response))

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
