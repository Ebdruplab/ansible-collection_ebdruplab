# plugins/modules/schedule_create.py

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: schedule_create
short_description: Create a schedule for a Semaphore project
version_added: "1.0.0"
description:
  - Sends a POST request to create a new schedule for a specified project in Semaphore.
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
  schedule:
    type: dict
    required: true
    options:
      cron_format:
        type: str
        required: true
      template_id:
        type: int
        required: true
      name:
        type: str
        required: true
      active:
        type: bool
        default: true
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Create a schedule
  ebdruplab.semaphoreui.schedule_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    schedule:
      cron_format: "* * * * *"
      template_id: 1
      name: "My Schedule"
      active: true
'''

RETURN = r'''
schedule:
  description: Created schedule object
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
            project_id=dict(type='int', required=True),
            schedule=dict(type='dict', required=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    host = module.params["host"]
    port = module.params["port"]
    project_id = module.params["project_id"]
    schedule = module.params["schedule"]

    url = f"{host}:{port}/api/project/{project_id}/schedules"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    # Only send required fields to avoid backend validation errors
    payload = {
        "cron_format": schedule["cron_format"],
        "template_id": schedule["template_id"],
        "name": schedule["name"],
        "active": schedule.get("active", True)
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url,
            body=body,
            headers=headers,
            validate_certs=module.params["validate_certs"]
        )

        if status not in (200, 201):
            module.fail_json(msg=f"POST failed with status {status}: {response_body}")

        schedule_response = json.loads(response_body)
        module.exit_json(changed=True, schedule=schedule_response)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
