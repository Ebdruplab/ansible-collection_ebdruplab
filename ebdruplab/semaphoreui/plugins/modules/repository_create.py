from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: repository_create
short_description: Create a repository in Semaphore
version_added: "1.0.0"
description:
  - Creates a new repository within a Semaphore project.
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
    description: ID of the project to create the repository in.
  name:
    type: str
    required: true
    description: Name of the repository.
  git_url:
    type: str
    required: true
    description: Git URL of the repository.
  git_branch:
    type: str
    required: true
    description: Branch of the repository.
  ssh_key_id:
    type: int
    required: true
    description: ID of the SSH key to access the repository.
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
- name: Create repository
  ebdruplab.semaphoreui.repository_create:
    host: localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    name: "My Repo"
    git_url: "https://github.com/example/repo.git"
    git_branch: "main"
    ssh_key_id: 1
'''

RETURN = r'''
repository:
  description: The created repository object.
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
            git_url=dict(type='str', required=True),
            git_branch=dict(type='str', required=True),
            ssh_key_id=dict(type='int', required=True),
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
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/repositories"

    repo_data = {
        "name": module.params["name"],
        "git_url": module.params["git_url"],
        "git_branch": module.params["git_branch"],
        "ssh_key_id": module.params["ssh_key_id"],
        "project_id": project_id
    }

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(repo_data).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 201):
            msg = response_body if isinstance(response_body, str) else response_body.decode()
            module.fail_json(msg=f"Failed to create repository: HTTP {status} - {msg}", status=status)

        result = json.loads(response_body)
        module.exit_json(changed=True, repository=result)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()