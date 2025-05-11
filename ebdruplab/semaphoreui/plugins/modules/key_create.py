from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: key_create
short_description: Create an access key in Semaphore
version_added: "1.0.0"
description:
  - Creates a new access key in Semaphore that supports either SSH or login/password authentication.
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
    description: ID of the project to create the key in.
  name:
    type: str
    required: true
    description: Name of the key.
  type:
    type: str
    required: true
    choices: ["ssh", "login_password"]
    description: Type of the access key.
  ssh:
    type: dict
    required: false
    description: SSH key details (required if type is ssh).
    options:
      login:
        type: str
        required: true
      passphrase:
        type: str
        required: false
        no_log: true
      private_key:
        type: str
        required: true
        no_log: true
  login_password:
    type: dict
    required: false
    description: Login/password details (required if type is login_password).
    options:
      login:
        type: str
        required: true
      password:
        type: str
        required: true
        no_log: true
  override_secret:
    type: bool
    required: false
    default: true
    description: Whether to override the secret.
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
    description: Whether to validate TLS certificates.
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Create an SSH key
  ebdruplab.semaphoreui.key_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    name: "SSH Key"
    type: "ssh"
    ssh:
      login: "git"
      private_key: "{{ lookup('file', '~/.ssh/id_rsa') }}"

- name: Create a login/password key
  ebdruplab.semaphoreui.key_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    name: "Basic Auth"
    type: "login_password"
    login_password:
      login: "admin"
      password: "supersecret"
'''

RETURN = r'''
key:
  description: The created access key object.
  type: dict
  returned: success
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            name=dict(type='str', required=True),
            type=dict(type='str', required=True, choices=["ssh", "login_password"]),
            ssh=dict(
                type='dict',
                required=False,
                options=dict(
                    login=dict(type='str', required=True),
                    passphrase=dict(type='str', required=False, no_log=True),
                    private_key=dict(type='str', required=True, no_log=True),
                )
            ),
            login_password=dict(
                type='dict',
                required=False,
                options=dict(
                    login=dict(type='str', required=True),
                    password=dict(type='str', required=True, no_log=True),
                )
            ),
            override_secret=dict(type='bool', default=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    p = module.params
    url = f"{p['host'].rstrip('/')}:{p['port']}/api/project/{p['project_id']}/keys"

    payload = {
        "name": p["name"],
        "type": p["type"],
        "project_id": p["project_id"],
        "override_secret": p["override_secret"]
    }

    if p["type"] == "ssh":
        if not p["ssh"]:
            module.fail_json(msg="Parameter 'ssh' is required when type is 'ssh'.")
        payload["ssh"] = p["ssh"]

    elif p["type"] == "login_password":
        if not p["login_password"]:
            module.fail_json(msg="Parameter 'login_password' is required when type is 'login_password'.")
        payload["login_password"] = p["login_password"]

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url=url,
            body=body,
            headers=headers,
            validate_certs=p["validate_certs"]
        )

        if status not in (200, 201):
            error_msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to create key: HTTP {status} - {error_msg}", status=status)

        key = json.loads(response_body) if response_body else {}
        module.exit_json(changed=True, key=key)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
