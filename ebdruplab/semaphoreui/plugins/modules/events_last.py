from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: events_last
short_description: Get last 200 events from Semaphore
version_added: "1.0.0"
description:
  - Fetches the last 200 events related to Semaphore and projects the user is part of.
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
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Fetch last 200 events
  ebdruplab.semaphoreui.events_last:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"
'''

RETURN = r'''
events:
  description: List of the last 200 events
  returned: always
  type: list
  elements: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/events/last"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(url, headers=headers, validate_certs=validate_certs)

        if status != 200:
            module.fail_json(msg=f"Failed to fetch last events: HTTP {status}", response=response_body)

        try:
            events = json.loads(response_body)
        except json.JSONDecodeError:
            module.fail_json(msg="Invalid JSON response", raw=response_body)

        module.exit_json(changed=False, events=events)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

