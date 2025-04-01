#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.semaphore_api import list_projects

DOCUMENTATION = r"""
---
module: project_info
short_description: Retrieve list of projects from Semaphore UI
version_added: "1.0.0"
description:
  - Retrieves the list of all projects using the session cookie.
options:
  host:
    description:
      - The host of the Semaphore API (e.g. http://localhost)
    required: true
    type: str
  port:
    description:
      - The port of the Semaphore API (e.g. 3000)
    required: true
    type: int
  session_cookie:
    description:
      - Session cookie obtained from login module (e.g. semaphore=abc123)
    required: true
    type: str
  validate_certs:
    description:
      - Whether to validate SSL certificates
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
"""

EXAMPLES = r"""
- name: Get list of projects
  ebdruplab.semaphoreui.project_info:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.cookie }}"
  register: project_list
"""

RETURN = r"""
projects:
  description: List of projects as returned by the API
  returned: always
  type: list
  elements: dict
  sample: [{"id": 1, "name": "Test Project"}]
"""

def main():
    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='int', required=True),
        session_cookie=dict(type='str', required=True),
        validate_certs=dict(type='bool', default=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        projects = list_projects(
            host=module.params['host'],
            port=module.params['port'],
            session_cookie=module.params['session_cookie'],
            validate_certs=module.params['validate_certs']
        )
        module.exit_json(changed=False, projects=projects)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
