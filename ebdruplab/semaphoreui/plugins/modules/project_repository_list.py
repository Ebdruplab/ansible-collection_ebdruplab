from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_repository_list
short_description: List repositories in a Semaphore project
description:
  - Retrieves a list of all repositories configured under a specific Semaphore project.
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
  sort:
    type: str
    required: false
    choices: ["name", "git_url"]
  order:
    type: str
    required: false
    choices: ["asc", "desc"]
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: List repositories in a project
  ebdruplab.semaphoreui.project_repository_list:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
'''

RETURN = r'''
repositories:
  description: List of project repositories
  returned: success
  type: list
  elements: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            project_id=dict(type='int', required=True),
            sort=dict(type='str', required=False, choices=["name", "git_url"]),
            order=dict(type='str', required=False, choices=["asc", "desc"]),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    sort = module.params.get("sort")
    order = module.params.get("order")

    # Build query string
    query = []
    if sort:
        query.append(f"sort={sort}")
    if order:
        query.append(f"order={order}")
    query_string = f"?{'&'.join(query)}" if query else ""

    url = f"{host}:{port}/api/project/{project_id}/repositories{query_string}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_get(
            url, headers=headers, validate_certs=module.params["validate_certs"]
        )

        if status != 200:
            msg = response_body if isinstance(response_body, str) else response_body.decode()
            module.fail_json(msg=f"GET failed with status {status}: {msg}", status=status)

        data = json.loads(response_body) if response_body else []
        module.exit_json(changed=False, repositories=data)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
