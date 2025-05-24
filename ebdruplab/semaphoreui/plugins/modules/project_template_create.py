from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_template_create
short_description: Create a Semaphore template
version_added: "1.0.0"
description:
  - Creates a new template in Semaphore with support for all API fields like vaults, survey_vars, and metadata.
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
  template:
    type: dict
    required: true
    description: Dictionary defining the template fields to submit to the API.
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
author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Create a template with full metadata
  ebdruplab.semaphoreui.project_template_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    template:
      name: "Deploy App"
      app: "ansible"
      playbook: "deploy.yml"
      inventory_id: 1
      repository_id: 1
      environment_id: 1
      type: "deploy"
      arguments: "[\"--limit app\"]"
      description: "Deploy playbook with tagging"
      vaults: []
      survey_vars: []
'''

RETURN = r'''
template:
  description: The created template object.
  type: dict
  returned: success
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
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    p = module.params
    template = p["template"]
    host = p["host"].rstrip("/")
    port = p["port"]
    project_id = p["project_id"]
    validate_certs = p["validate_certs"]

    required_fields = ["name", "app", "playbook", "inventory_id", "repository_id"]
    missing = [f for f in required_fields if f not in template or template[f] in [None, ""]]
    if missing:
        module.fail_json(msg=f"Missing required fields in template: {', '.join(missing)}")

    # Defaults
    defaults = {
        "type": "job",
        "view_id": 1,
        "environment_id": 1,
        "allow_override_args_in_task": False,
        "suppress_success_alerts": False,
        "autorun": False,
        "survey_vars": [],
        "vaults": [],
        "description": "",
    }

    for key, val in defaults.items():
        template.setdefault(key, val)

    # Remove fields that should not be submitted if empty
    for key in ["arguments", "vault_password", "tags", "skip_tags", "git_branch", "limit", "start_version"]:
        if key in template and (template[key] is None or template[key] == ""):
            template.pop(key)

    # Ensure proper data types
    for field in ["inventory_id", "repository_id", "environment_id", "view_id", "build_template_id"]:
        if field in template and template[field] not in [None, ""]:
            try:
                template[field] = int(template[field])
            except Exception:
                template[field] = 0

    for list_field in ["vaults", "survey_vars"]:
        if isinstance(template.get(list_field), str):
            try:
                template[list_field] = json.loads(template[list_field])
            except Exception as e:
                module.fail_json(msg=f"{list_field} must be valid JSON: {e}")

    template["project_id"] = project_id
    url = f"{host}:{port}/api/project/{project_id}/templates"

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token")
    )
    headers["Content-Type"] = "application/json"

    try:
        body = json.dumps(template).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url=url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 201):
            msg = response_body.decode() if isinstance(response_body, bytes) else str(response_body)
            module.fail_json(msg=f"Failed to create template: HTTP {status} - {msg}", status=status)

        module.exit_json(changed=True, template=json.loads(response_body))

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()

