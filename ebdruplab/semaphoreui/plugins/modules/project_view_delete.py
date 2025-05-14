from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_delete, get_auth_headers

DOCUMENTATION = r'''
---
module: project_view_delete
short_description: Delete a view in Semaphore
version_added: "1.0.0"
description:
  - Deletes a view from a Semaphore project.
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
    description: ID of the project containing the view.
  view_id:
    type: int
    required: true
    description: ID of the view to delete.
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
- name: Delete a view
  ebdruplab.semaphoreui.project_view_delete:
    host: localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    view_id: 10
'''

RETURN = r'''
changed:
  description: Whether the view was successfully deleted.
  type: bool
  returned: always
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            view_id=dict(type='int', required=True),
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
    view_id = module.params["view_id"]
    validate_certs = module.params["validate_certs"]

    url = f"{host}:{port}/api/project/{project_id}/views/{view_id}"

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

        if status != 204:
            module.fail_json(msg=f"Failed to delete view: HTTP {status}", status=status)

        module.exit_json(changed=True)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
