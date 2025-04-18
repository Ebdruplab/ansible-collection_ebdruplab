from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: key_update
short_description: Update an access key in Semaphore
version_added: "1.0.0"
description:
  - Updates an existing access key in a specific Semaphore project.
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
    description: ID of the project containing the key.
  key_id:
    type: int
    required: true
    description: ID of the key to update.
  name:
    type: str
    required: true
    description: New name for the key.
  key:
    type: str
    required: true
    description: New SSH public key string.
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
- name: Update access key in Semaphore
  ebdruplab.semaphoreui.key_update:
    host: localhost
    port: 3000
    project_id: 1
    key_id: 5
    session_cookie: "{{ login_result.session_cookie }}"
    name: "Updated Key Name"
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC..."
'''

RETURN = r'''
key:
  description: The updated key object.
  type: dict
  returned: success
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
        "key": module.params["key"]
    }

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_put(
            url=url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to update key: HTTP {status} - {msg}", status=status)

        result = json.loads(response_body.decode()) if isinstance(response_body, bytes) else json.loads(response_body)
        module.exit_json(changed=True, key=result)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
