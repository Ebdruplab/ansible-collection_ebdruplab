from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_events
short_description: Get events related to a specific Semaphore project
version_added: "1.0.0"
description:
  - Retrieves the list of events for the specified Semaphore project.
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
- name: Fetch events for a project
  ebdruplab.semaphoreui.project_events:
    host: http://localhost
    port: 3000
    project_id: 1
    api_token: "abcd1234"
'''

RETURN = r'''
events:
  description: List of events for the project
  returned: always
  type: list
  elements: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
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
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/events"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(url, headers=headers, validate_certs=validate_certs)

        if status != 200:
            module.fail_json(msg=f"Failed to fetch project events: HTTP {status}", response=response_body)

        try:
            events = json.loads(response_body)
            if not isinstance(events, list):
                raise ValueError("Response is not a list")
        except Exception as e:
            module.fail_json(msg="Invalid JSON response", raw=response_body)

        module.exit_json(changed=False, events=events)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

