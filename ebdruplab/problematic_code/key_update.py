from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_key_update
short_description: Update an access key in Semaphore
version_added: "1.0.0"
description:
  - Updates an existing SSH access key in a Semaphore project.
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
  key_id:
    type: int
    required: true
  name:
    type: str
    required: true
  key:
    type: str
    required: true
    description: New SSH private key.
  ssh_login:
    type: str
    required: false
    default: "root"
    description: Login user for the SSH key.
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
- name: Update SSH access key
  ebdruplab.semaphoreui.project_key_update:
    host: localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    key_id: 42
    name: "My Updated Key"
    key: "{{ lookup('file', 'my_key.pem') }}"
    ssh_login: root
'''

RETURN = r'''
changed:
  type: bool
  description: Whether the key was updated.
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            key_id=dict(type='int', required=True),
            name=dict(type='str', required=True),
            key=dict(type='str', required=True),
            ssh_login=dict(type='str', required=False, default="root"),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    key_id = module.params["key_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/keys/{key_id}"

    payload = {
        "name": module.params["name"],
        "type": "ssh",
        "ssh": {
            "login": module.params["ssh_login"],
            "private_key": module.params["key"]
        }
    }

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(payload).encode("utf-8")
        _, status, _ = semaphore_put(
            url=url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 204:
            module.fail_json(msg=f"Failed to update key: HTTP {status}")

        module.exit_json(changed=True)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
