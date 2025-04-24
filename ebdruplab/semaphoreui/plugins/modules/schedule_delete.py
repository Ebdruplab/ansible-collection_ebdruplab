from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r'''
---
module: schedule_delete
short_description: Delete a schedule from a Semaphore project
version_added: "1.0.0"
description:
  - Deletes a schedule from the specified Semaphore project using the schedule ID.
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
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Delete a schedule
  ebdruplab.semaphoreui.schedule_delete:
    host: http://localhost
    port: 3000
    api_token: "your_token"
    project_id: 1
    schedule_id: 9
'''

RETURN = r'''
deleted:
  description: Whether the schedule was deleted successfully
  type: bool
  returned: always
status:
  description: HTTP response status code
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
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    schedule_id = module.params["schedule_id"]
    validate_certs = module.params["validate_certs"]
    session_cookie = module.params.get("session_cookie")
    api_token = module.params.get("api_token")

    url = f"{host}:{port}/api/project/{project_id}/schedules/{schedule_id}"

    try:
        headers = get_auth_headers(session_cookie=session_cookie, api_token=api_token)

        _, status, _ = semaphore_delete(url, headers=headers, validate_certs=validate_certs)

        if status != 204:
            module.fail_json(msg=f"Failed to delete schedule: HTTP {status}", status=status)

        module.exit_json(changed=True, deleted=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

