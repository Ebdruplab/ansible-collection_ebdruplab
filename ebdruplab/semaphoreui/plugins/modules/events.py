# plugins/modules/events.py

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: events
short_description: Get events from Semaphore
version_added: "1.0.0"
description:
  - Gets events related to Semaphore and projects the user is part of.
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
  last_only:
    type: bool
    default: false
    description: Fetch only the last 200 events
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Fetch all events
  ebdruplab.semaphoreui.events:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"

- name: Fetch last 200 events
  ebdruplab.semaphoreui.events:
    host: http://localhost
    port: 3000
    api_token: "abcd1234"
    last_only: true
'''

RETURN = r'''
events:
  description: List of events
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
            last_only=dict(type='bool', default=False),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    endpoint = "/events/last" if module.params['last_only'] else "/api/events"
    url = f"{module.params['host']}:{module.params['port']}{endpoint}"

    try:
        headers = get_auth_headers(
            module.params['session_cookie'],
            module.params['api_token']
        )
        response_body, status, _ = semaphore_get(
            url,
            headers=headers,
            validate_certs=module.params["validate_certs"]
        )

        if status != 200:
            module.fail_json(msg=f"Failed to fetch events: HTTP {status} - {response_body}", status=status)

        try:
            events = json.loads(response_body) if response_body else []
        except json.JSONDecodeError as e:
            module.fail_json(msg=f"Invalid JSON response: {str(e)}", raw=response_body)

        module.exit_json(changed=False, events=events)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
