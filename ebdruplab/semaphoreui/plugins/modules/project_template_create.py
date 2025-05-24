from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_template_create
short_description: Create a Semaphore template (task, deploy or build)
version_added: "1.0.0"
description:
  - Creates a new template in Semaphore with support for full configuration including build linkage, arguments, vaults, and survey variables.
options:
  host:
    type: str
    required: true
    description: Hostname or IP address of the Semaphore server.
  port:
    type: int
    required: true
    description: Port of the Semaphore server.
  project_id:
    type: int
    required: true
    description: ID of the Semaphore project to create the template under.
  template:
    type: dict
    required: true
    description: Template definition dictionary.
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
    description: Whether to verify SSL certificates.
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Create a basic template
  ebdruplab.semaphoreui.project_template_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    template:
      name: "Deploy Web"
      app: "ansible"
      playbook: "deploy.yml"
      inventory_id: 1
      repository_id: 1

- name: Create a full-featured build template
  ebdruplab.semaphoreui.project_template_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    template:
      name: "Build Pipeline"
      app: "ansible"
      playbook: "build.yml"
      inventory_id: 1
      repository_id: 1
      environment_id: 1
      view_id: 1
      description: "Pipeline to build and deploy"
      git_branch: "main"
      arguments: "[]"
      vault_password: ""
      allow_override_args_in_task: false
      suppress_success_alerts: false
      autorun: false
      type: "build"
      start_version: ""
      build_template_id: 0
      vaults: []
      survey_vars: []
'''

RETURN = r'''
template:
  description: The created template object.
  returned: success
  type: dict
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            template=dict(type='dict', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=False,
    )

    p = module.params
    host = p['host'].rstrip('/')
    port = p['port']
    project_id = p['project_id']
    tpl = p['template']
    validate_certs = p['validate_certs']

    # Required fields
    required = ['name', 'app', 'playbook', 'inventory_id', 'repository_id']
    missing = [k for k in required if not tpl.get(k)]
    if missing:
        module.fail_json(msg=f"Missing required fields in template: {', '.join(missing)}")

    # Type conversions and defaults
    tpl['project_id'] = project_id
    tpl['type'] = tpl.get('type', '') or ''  # default to ""
    tpl['view_id'] = int(tpl.get('view_id') or 1)
    tpl['environment_id'] = int(tpl.get('environment_id') or 1)
    tpl['build_template_id'] = int(tpl.get('build_template_id') or 0)

    tpl['arguments'] = tpl.get('arguments', "[]")
    tpl['start_version'] = tpl.get('start_version', "")
    tpl['description'] = tpl.get('description', "")
    tpl['git_branch'] = tpl.get('git_branch', "")
    tpl['limit'] = tpl.get('limit', "")
    tpl['tags'] = tpl.get('tags', "")
    tpl['skip_tags'] = tpl.get('skip_tags', "")
    tpl['vault_password'] = tpl.get('vault_password', "")

    tpl['allow_override_args_in_task'] = tpl.get('allow_override_args_in_task', False)
    tpl['suppress_success_alerts'] = tpl.get('suppress_success_alerts', False)
    tpl['autorun'] = tpl.get('autorun', False)

    tpl['vaults'] = tpl.get('vaults') or []
    tpl['survey_vars'] = tpl.get('survey_vars') or []

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token")
    )
    headers["Content-Type"] = "application/json"
    url = f"{host}:{port}/api/project/{project_id}/templates"

    try:
        body = json.dumps(tpl).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url=url, body=body, headers=headers, validate_certs=validate_certs
        )

        if status not in (200, 201):
            msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to create template: HTTP {status} - {msg}", status=status)

        module.exit_json(changed=True, template=json.loads(response_body))

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

