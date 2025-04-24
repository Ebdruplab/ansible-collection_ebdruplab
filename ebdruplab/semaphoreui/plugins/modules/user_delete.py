from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r'''
---
module: user_delete
short_description: Delete a user in Semaphore
description:
  - Deletes a user by user ID in the Semaphore system.
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
    description: The ID of the user to delete
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
- name: Delete a user by ID
  ebdruplab.semaphoreui.user_delete:
    host: http://localhost
    port: 3000
    user_id: 5
    session_cookie: "{{ login_result.session_cookie }}"
'''

RETURN = r'''
deleted:
  description: Whether the user was successfully deleted
  returned: always
  type: bool
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            user_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
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

    try:
        _, status, _ = semaphore_delete(
            url, headers=headers, validate_certs=validate_certs
        )

        if status != 204:
            module.fail_json(msg=f"Failed to delete user: HTTP {status}")

        module.exit_json(changed=True, deleted=True)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

