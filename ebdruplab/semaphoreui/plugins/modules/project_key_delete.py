from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r'''
---
module: project_key_delete
short_description: Delete an access key in Semaphore
version_added: "1.0.0"
description:
  - Deletes an access key stored in Semaphore.
options:
  host:
    type: str
    required: true
    description: Hostname or IP of the Semaphore server (excluding protocol).
  port:
    type: int
    required: true
    description: Port of the Semaphore server (e.g., 3000).
  project_id:
    type: int
    required: true
    description: ID of the project the key belongs to.
  key_id:
    type: int
    required: true
    description: ID of the access key to delete.
  session_cookie:
    type: str
    required: false
    no_log: true
    description: Session cookie from a previous login.
  api_token:
    type: str
    required: false
    no_log: true
    description: API token to authenticate instead of session cookie.
  validate_certs:
    type: bool
    default: true
    description: Whether to validate TLS certificates.
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Delete an access key in Semaphore
  ebdruplab.semaphoreui.project_key_delete:
    host: localhost
    port: 3000
    project_id: 1
    key_id: 42
    session_cookie: "{{ login_result.session_cookie }}"
'''

RETURN = r'''
changed:
  description: Whether the key was successfully deleted.
  type: bool
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            key_id=dict(type='int', required=True),
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

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )

    try:
        _, status, _ = semaphore_delete(
            url=url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 204:
            module.fail_json(msg=f"Failed to delete key: HTTP {status}", status=status)

        module.exit_json(changed=True)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
