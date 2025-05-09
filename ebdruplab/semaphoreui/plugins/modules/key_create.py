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
  port:
    type: int
    required: true
  project_id:
    type: int
    required: true
  name:
    type: str
    required: true
  type:
    type: str
    required: true
    choices: ["ssh", "login_password"]
  ssh:
    type: dict
    required: false
    options:
      login:
        type: str
        required: false
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
    options:
      login:
        type: str
        required: false
      password:
        type: str
        required: true
        no_log: true
  override_secret:
    type: bool
    required: false
    default: true
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
      private_key: "PRIVATE_KEY_HERE"

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
      password: "secret123"
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
                    login=dict(type='str'),
                    passphrase=dict(type='str', no_log=True),
                    private_key=dict(type='str', required=True, no_log=True),
                )
            ),
            login_password=dict(
                type='dict',
                required=False,
                options=dict(
                    login=dict(type='str'),
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

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    name = module.params["name"]
    key_type = module.params["type"]
    ssh_data = module.params.get("ssh")
    login_password_data = module.params.get("login_password")
    override_secret = module.params["override_secret"]
    session_cookie = module.params.get("session_cookie")
    api_token = module.params.get("api_token")
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/keys"

    headers = get_auth_headers(
        session_cookie=session_cookie,
        api_token=api_token
    )
    headers["Content-Type"] = "application/json"

    payload = {
        "name": name,
        "type": key_type,
        "project_id": project_id,
        "override_secret": override_secret,
    }

    if key_type == "ssh":
        if not ssh_data or not ssh_data.get("private_key"):
            module.fail_json(msg="Field 'ssh.private_key' is required when type is 'ssh'")
        payload["ssh"] = ssh_data

    elif key_type == "login_password":
        if not login_password_data or not login_password_data.get("password"):
            module.fail_json(msg="Field 'login_password.password' is required when type is 'login_password'")
        payload["login_password"] = login_password_data

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status not in (200, 201):
            msg = response_body if isinstance(response_body, str) else response_body.decode()
            module.fail_json(msg=f"Failed to create key: HTTP {status} - {msg}", status=status)

        key = json.loads(response_body)
        module.exit_json(changed=True, key=key)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

