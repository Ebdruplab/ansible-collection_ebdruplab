from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: schedule_update
short_description: Update a schedule in a Semaphore project
version_added: "1.0.0"
description:
  - Updates a schedule for a given project in Semaphore by ID.
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
  schedule:
    type: dict
    required: true
    description: Updated schedule object to send
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
- name: Update a schedule
  ebdruplab.semaphoreui.schedule_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    schedule_id: 5
    schedule:
      name: "Updated Schedule"
      cron_format: "0 * * * *"
      template_id: 1
      active: true
'''

RETURN = r'''
updated:
  description: Whether the schedule was successfully updated
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
            schedule_id=dict(type='int', required=True),
            schedule=dict(type='dict', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]
    session_cookie = module.params.get("session_cookie")
    api_token = module.params.get("api_token")
    schedule = module.params["schedule"]

    # Validate numeric parameters
    try:
        project_id = int(module.params["project_id"])
        schedule_id = int(module.params["schedule_id"])
    except Exception as e:
        module.fail_json(msg=f"Invalid numeric input: {str(e)}")

    url = f"{host}:{port}/api/project/{project_id}/schedules/{schedule_id}"

    try:
        headers = get_auth_headers(session_cookie=session_cookie, api_token=api_token)
        headers["Content-Type"] = "application/json"

        body = json.dumps(schedule).encode("utf-8")

        _, status, _ = semaphore_put(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 204):
            module.fail_json(msg=f"PUT failed with status {status}", status=status)

        module.exit_json(changed=True, updated=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

