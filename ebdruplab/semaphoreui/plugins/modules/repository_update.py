from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: repository_update
short_description: Update a Semaphore repository
version_added: "1.0.0"
description:
  - Updates an existing repository inside a Semaphore project.
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
    description: ID of the project containing the repository.
  repository_id:
    type: int
    required: true
    description: ID of the repository to update.
  repository:
    type: dict
    required: true
    description: Dictionary describing the updated repository.
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
- name: Update a Semaphore repository
  ebdruplab.semaphoreui.repository_update:
    host: localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    repository_id: 3
    repository:
      name: "Updated Repo"
      git_url: "https://github.com/updated/repo.git"
      git_branch: "develop"
'''

RETURN = r'''
repository:
  description: The updated repository object.
  type: dict
  returned: success
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            repository_id=dict(type='int', required=True),
            repository=dict(type='dict', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    host = module.params["host"]
    port = module.params["port"]
    project_id = module.params["project_id"]
    repository_id = module.params["repository_id"]
    repo = module.params["repository"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/repositories/{repository_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    # Ensure required fields are present
    required_fields = ["name", "git_url", "git_branch"]
    missing = [f for f in required_fields if f not in repo or not repo[f]]
    if missing:
        module.fail_json(msg=f"Missing required repository fields: {', '.join(missing)}")

    # Add project_id for completeness
    repo["project_id"] = project_id

    try:
        body = json.dumps(repo).encode("utf-8")
        response_body, status, _ = semaphore_put(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            msg = response_body if isinstance(response_body, str) else response_body.decode()
            module.fail_json(msg=f"Failed to update repository: HTTP {status} - {msg}", status=status)

        result = json.loads(response_body)
        module.exit_json(changed=True, repository=result)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
