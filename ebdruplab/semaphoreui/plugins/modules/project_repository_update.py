from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_repository_update
short_description: Update a repository in a Semaphore project
description:
  - Sends a PUT request to update an existing repository for a specified Semaphore project.
options:
  host:
    type: str
    required: true
  port:
    type: int
    required: true
  session_cookie:
    type: str
    required: false
    no_log: true
  api_token:
    type: str
    required: false
    no_log: true
  project_id:
    type: int
    required: true
  repository_id:
    type: int
    required: true
  repository:
    type: dict
    required: true
    options:
      name:
        type: str
        required: true
      git_url:
        type: str
        required: true
      git_branch:
        type: str
        required: true
      ssh_key_id:
        type: int
        required: true
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Update a repository
  ebdruplab.semaphoreui.project_repository_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    repository_id: 123
    repository:
      name: "Updated Repo"
      git_url: "git@example.com"
      git_branch: "main"
      ssh_key_id: 0
'''

RETURN = r'''
repository:
  description: The updated repository object
  returned: success
  type: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            project_id=dict(type='int', required=True),
            repository_id=dict(type='int', required=True),
            repository=dict(type='dict', required=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    repository_id = module.params["repository_id"]
    repo = module.params["repository"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/repository/{repository_id}"

    # Construct payload for update
    payload = {
        "id": 0,
        "name": repo["name"],
        "git_url": repo["git_url"],
        "git_branch": repo["git_branch"],
        "ssh_key_id": repo["ssh_key_id"],
        "project_id": project_id
    }

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_put(
            url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status not in (200, 201):
            msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"PUT failed with status {status}: {msg}", status=status)

        result = json.loads(response_body.decode()) if isinstance(response_body, bytes) else json.loads(response_body)
        module.exit_json(changed=True, repository=result)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()

