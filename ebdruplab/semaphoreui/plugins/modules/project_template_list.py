from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers

DOCUMENTATION = r'''
---
module: project_template_list
short_description: List templates in a Semaphore project
version_added: "1.0.0"
description:
  - Retrieves a list of templates from a specific Semaphore project.
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
    description: ID of the project to list templates from.
  session_cookie:
    type: str
    required: false
    no_log: true
    description: Session cookie from a previous login call.
  api_token:
    type: str
    required: false
    no_log: true
    description: API token to authenticate instead of session cookie.
  validate_certs:
    type: bool
    default: true
    description: Whether to validate TLS certificates.
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: List templates in a project
  ebdruplab.semaphoreui.project_template_list:
    host: localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
'''

RETURN = r'''
templates:
  description: List of templates in the specified project.
  type: list
  returned: success
  elements: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    host = module.params["host"]
    port = module.params["port"]
    project_id = module.params["project_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/templates"

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
            module.fail_json(msg=f"Failed to list templates: HTTP {status}", status=status)

        templates = response_body if isinstance(response_body, list) else []

        module.exit_json(changed=False, templates=templates)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
