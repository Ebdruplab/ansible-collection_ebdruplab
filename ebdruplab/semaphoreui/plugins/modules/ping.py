from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get

DOCUMENTATION = r'''
---
module: ping
short_description: Ping the Semaphore API
version_added: "1.0.0"
description:
  - Sends a GET request to /api/ping to check if the Semaphore API is reachable.
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
- name: Check connection to Semaphore
  ebdruplab.semaphoreui.ping:
    host: http://localhost
    port: 3000
'''

RETURN = r'''
result:
  description: API response, typically "pong"
  type: str
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            validate_certs=dict(type='bool', default=True)
        ),
        supports_check_mode=True
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/ping"

    try:
        response_body, status, _ = semaphore_get(url, validate_certs=validate_certs)
        if status != 200 or response_body.strip().lower() != "pong":
            module.fail_json(msg=f"Unexpected response: {response_body} (status {status})")
        module.exit_json(changed=False, result=response_body)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

