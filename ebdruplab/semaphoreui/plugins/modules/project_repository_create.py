from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_repository_create
short_description: Create a repository in a Semaphore project
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
  - Kristian Ebdrup @kris9854
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
      ssh_key_id: 0
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

    host = module.params["host"]
    port = module.params["port"]
    project_id = module.params["project_id"]
    repository = module.params["repository"]

    # Inject project_id into the payload body to match URL expectation
    repository["project_id"] = project_id

    url = f"{host}:{port}/api/project/{project_id}/repositories"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(repository).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url, body=body, headers=headers, validate_certs=module.params["validate_certs"]
        )

        if status not in (200, 201):
            module.fail_json(msg=f"POST failed with status {status}: {response_body}")

        created_repo = json.loads(response_body)
        module.exit_json(changed=True, repository=created_repo)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
