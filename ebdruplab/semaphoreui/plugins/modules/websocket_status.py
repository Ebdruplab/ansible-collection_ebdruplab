# plugins/modules/websocket_status.py

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get

DOCUMENTATION = r'''
---
module: websocket_status
short_description: Check WebSocket support on the Semaphore server
version_added: "1.0.0"
description:
  - Sends GET to /ws and checks if it's reachable (authentication not required)
options:
  host:
    type: str
    required: true
  port:
    type: int
    required: true
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Check WebSocket endpoint
  ebdruplab.semaphoreui.websocket_status:
    host: http://localhost
    port: 3000
'''

RETURN = r'''
reachable:
  description: Whether the /ws endpoint responded successfully
  returned: always
  type: bool
status:
  description: HTTP status code
  returned: always
  type: int
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            validate_certs=dict(type='bool', default=True),
        ),
        supports_check_mode=True
    )

    url = f"{module.params['host']}:{module.params['port']}/api/ws"

    try:
        _, status, _ = semaphore_get(url, validate_certs=module.params["validate_certs"])
        module.exit_json(changed=False, reachable=(status == 200), status=status)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
