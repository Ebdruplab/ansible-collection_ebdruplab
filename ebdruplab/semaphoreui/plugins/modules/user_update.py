from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: user_update
short_description: Update a Semaphore user
version_added: "1.0.0"
description:
  - Updates user information including name, email, alert, and admin flags.
options:
  host:
    type: str
    required: true
  port:
    type: int
    required: true
  user_id:
    type: int
    required: true
  name:
    type: str
    required: true
  username:
    type: str
    required: true
  email:
    type: str
    required: true
  alert:
    type: bool
    default: false
  admin:
    type: bool
    default: false
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
- name: Update user details
  ebdruplab.semaphoreui.user_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    user_id: 5
    name: "Jane Doe"
    username: "jane"
    email: "jane@example.com"
    alert: true
    admin: false
'''

RETURN = r'''
updated:
  description: Whether the user was successfully updated
  type: bool
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            user_id=dict(type='int', required=True),
            name=dict(type='str', required=True),
            username=dict(type='str', required=True),
            email=dict(type='str', required=True),
            alert=dict(type='bool', default=False),
            admin=dict(type='bool', default=False),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    user_id = module.params["user_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/users/{user_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    payload = {
        "name": module.params["name"],
        "username": module.params["username"],
        "email": module.params["email"],
        "alert": module.params["alert"],
        "admin": module.params["admin"],
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        _, status, _ = semaphore_put(
            url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status != 204:
            module.fail_json(msg=f"PUT failed with status {status}")

        module.exit_json(changed=True, updated=True)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

