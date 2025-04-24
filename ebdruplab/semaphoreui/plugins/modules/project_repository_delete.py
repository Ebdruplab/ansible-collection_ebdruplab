from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r'''
---
module: project_repository_delete
short_description: Delete a repository from a Semaphore project
description:
  - Sends a DELETE request to remove a specific repository from a Semaphore project.
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
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup @kris9854
'''

EXAMPLES = r'''
- name: Delete a project repository
  ebdruplab.semaphoreui.project_repository_delete:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    repository_id: 123
'''

RETURN = r'''
msg:
  description: Status message
  returned: always
  type: str
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
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"]
    port = module.params["port"]
    project_id = module.params["project_id"]
    repository_id = module.params["repository_id"]

    url = f"{host}:{port}/api/project/{project_id}/repository/{repository_id}"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        response_body, status, _ = semaphore_delete(
            url, headers=headers, validate_certs=module.params["validate_certs"]
        )

        if status != 204:
            module.fail_json(msg=f"DELETE failed with status {status}", response=response_body)

        module.exit_json(changed=True, msg="Repository deleted successfully.")

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
