from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_repository_create
short_description: Create a repository in a Semaphore project
version_added: "1.0.0"
description:
  - This module sends a POST request to Semaphore to create a new repository under a specified project.
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
- name: Create a project repository
  ebdruplab.semaphoreui.project_repository_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    repository:
      name: "MyRepo"
      git_url: "git@example.com"
      git_branch: "main"
      ssh_key_id: 2
'''

RETURN = r'''
repository:
  description: Created repository object
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
            repository=dict(type='dict', required=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    p = module.params
    repo = p["repository"]
    host = p["host"].rstrip("/")
    port = p["port"]
    project_id = p["project_id"]
    validate_certs = p["validate_certs"]

    try:
        ssh_key_id = int(repo["ssh_key_id"])
    except (ValueError, TypeError):
        module.fail_json(msg="Invalid ssh_key_id: must be an integer")

    url = f"{host}:{port}/api/project/{project_id}/repositories"

    payload = {
        "id": 0,
        "name": repo["name"],
        "git_url": repo["git_url"],
        "git_branch": repo["git_branch"],
        "ssh_key_id": ssh_key_id,
        "project_id": project_id
    }

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
            validate_certs=validate_certs
        )

        if status not in (200, 201):
            msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"POST failed with status {status}: {msg}", status=status)

        result = json.loads(response_body)
        module.exit_json(changed=True, repository=result)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

