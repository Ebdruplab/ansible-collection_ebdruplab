from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r'''
---
module: project_environment_delete
short_description: Delete an environment in a Semaphore project
version_added: "1.0.0"
description:
  - Deletes a specific environment from a Semaphore project.
options:
  host:
    type: str
    required: true
    description: Hostname or IP of the Semaphore server (with protocol).
  port:
    type: int
    required: true
    description: Port where the Semaphore API is listening.
  project_id:
    type: int
    required: true
    description: ID of the Semaphore project.
  environment_id:
    type: int
    required: true
    description: ID of the environment to delete.
  session_cookie:
    type: str
    required: false
    no_log: true
    description: Session authentication cookie.
  api_token:
    type: str
    required: false
    no_log: true
    description: Bearer token for authentication.
  validate_certs:
    type: bool
    default: true
    description: Whether to validate TLS certificates.
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Delete a project environment
  ebdruplab.semaphoreui.project_environment_delete:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    environment_id: 5
'''

RETURN = r'''
deleted:
  description: Whether the environment was successfully deleted.
  type: bool
  returned: always
status:
  description: HTTP status code returned by the Semaphore API.
  type: int
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            environment_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=False
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    environment_id = module.params["environment_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/environment/{environment_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        _, status, _ = semaphore_delete(url, headers=headers, validate_certs=validate_certs)

        if status != 204:
            module.fail_json(msg=f"Failed to delete environment: HTTP {status}", status=status)

        module.exit_json(changed=True, deleted=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

