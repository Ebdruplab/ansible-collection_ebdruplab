from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: user_password_update
short_description: Update a user's password in Semaphore
version_added: "1.0.0"
description:
  - Updates the password for a specific Semaphore user.
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
  password:
    type: str
    required: true
    no_log: true
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
- name: Update user password
  ebdruplab.semaphoreui.user_password_update:
    host: http://localhost
    port: 3000
    user_id: 2
    session_cookie: "{{ login_result.session_cookie }}"
    password: "newpassword123"
'''

RETURN = r'''
status:
  description: HTTP status code of the update response
  returned: always
  type: int
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            user_id=dict(type='int', required=True),
            password=dict(type='str', required=True, no_log=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    user_id = module.params["user_id"]
    validate_certs = module.params["validate_certs"]
    password = module.params["password"]

    url = f"{host}:{port}/api/users/{user_id}/password"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    payload = {"password": password}

    try:
        body = json.dumps(payload).encode("utf-8")
        _, status, _ = semaphore_post(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 204:
            module.fail_json(msg=f"Failed to update password: HTTP {status}", status=status)

        module.exit_json(changed=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

