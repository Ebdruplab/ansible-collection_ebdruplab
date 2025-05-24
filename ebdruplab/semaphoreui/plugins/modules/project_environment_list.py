from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_environment_list
short_description: List environments in a Semaphore project
description:
  - Retrieves all environments associated with a given Semaphore project.
version_added: "1.0.0"
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
  sort:
    type: str
    default: name
    choices: ['name']
  order:
    type: str
    default: desc
    choices: ['asc', 'desc']
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
author: Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: List environments
  ebdruplab.semaphoreui.project_environment_list:
    host: http://localhost
    port: 3000
    project_id: 1
    session_cookie: "{{ login_result.session_cookie }}"
'''

RETURN = r'''
environments:
  description: List of environment objects
  returned: always
  type: list
  elements: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            sort=dict(type='str', default='name'),
            order=dict(type='str', default='desc'),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    sort = module.params["sort"]
    order = module.params["order"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/environment?sort={sort}&order={order}"
    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token")
    )

    try:
        response_body, status, _ = semaphore_get(
            url=url,
            headers=headers,
            validate_certs=validate_certs
        )

        if status != 200:
            module.fail_json(msg=f"Failed to list environments: HTTP {status}", status=status)

        environments = json.loads(response_body)
        module.exit_json(changed=False, environments=environments)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

