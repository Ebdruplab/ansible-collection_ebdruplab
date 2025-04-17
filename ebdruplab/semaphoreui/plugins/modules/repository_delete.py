from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r'''
---
module: repository_delete
short_description: Delete a repository in Semaphore
version_added: "1.0.0"
description:
  - Deletes a repository from a Semaphore project using the repository ID.
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
    description: ID of the project that owns the repository.
  repository_id:
    type: int
    required: true
    description: ID of the repository to delete.
  session_cookie:
    type: str
    required: false
    no_log: true
    description: Session cookie from login.
  api_token:
    type: str
    required: false
    no_log: true
    description: API token to use instead of session.
  validate_certs:
    type: bool
    default: true
    description: Whether to validate TLS certificates.
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Delete repository
  ebdruplab.semaphoreui.repository_delete:
    host: localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    repository_id: 4
'''

RETURN = r'''
deleted:
  description: Whether the repository was successfully deleted
  type: bool
  returned: always
status:
  description: HTTP response code
  type: int
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            repository_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"]
    port = module.params["port"]
    project_id = module.params["project_id"]
    repository_id = module.params["repository_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/repositories/{repository_id}"

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

        if status not in (200, 204):
            module.fail_json(msg=f"Failed to delete repository: HTTP {status}", status=status)

        module.exit_json(changed=True, deleted=True, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
