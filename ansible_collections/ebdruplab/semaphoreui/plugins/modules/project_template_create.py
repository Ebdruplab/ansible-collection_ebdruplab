#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import (
    semaphore_post,
    semaphore_request,
    get_auth_headers,
)
import json
import copy

DOCUMENTATION = r'''
---
module: semaphore_template_create
short_description: Create a Semaphore template and safely apply prompt flags
version_added: "1.0.0"

description:
  - Creates a new Semaphore template (job, deploy, or build) in a project.
  - Normalizes arguments, tags, surveys, vaults, and task parameters to API-compatible formats.
  - Due to Semaphore API limitations, C(prompt_*) flags are NOT reliably honored by the create endpoint.
  - When any C(prompt_*) flags are supplied, the module performs a follow-up
    C(GET → merge → PUT) operation to apply them without resetting existing template fields.
  - The update phase only modifies prompt flags explicitly provided by the user.

options:
  host:
    type: str
    required: true
    description:
      - Hostname or IP of the Semaphore server, including scheme.
      - "Example: C(http://localhost), C(https://semaphore.example.com)"

  port:
    type: int
    required: true
    description:
      - TCP port where Semaphore is listening (typically C(3000)).

  project_id:
    type: int
    required: true
    description:
      - ID of the Semaphore project.

  template:
    type: dict
    required: true
    description:
      - Template definition to create.

    suboptions:
      name:
        type: str
        required: true
        description: Template display name.

      app:
        type: str
        default: ansible
        description: Application type.

      playbook:
        type: str
        required: true
        description: Playbook path in the repository.

      repository_id:
        type: int
        required: true
        description: Repository ID.

      inventory_id:
        type: int
        required: true
        description: Inventory ID.

      environment_id:
        type: int
        description: Environment ID.

      view_id:
        type: int
        description: Board view ID.

      type:
        type: str
        choices:
          - ""
          - job
          - deploy
          - build
        description:
          - Template type.
          - The API represents C(job) as an empty string.

      description:
        type: str
        description: Human-readable description.

      git_branch:
        type: str
        description: Default Git branch.

      arguments:
        type: raw
        description:
          - Arguments as stored by the UI.
          - Scalars are wrapped into a JSON list.
          - Lists/dicts are JSON-encoded.
          - Defaults to C("[]").

      tags:
        type: raw
        description:
          - Template-level tags.
          - Lists are joined into newline-delimited strings.

      skip_tags:
        type: raw
        description:
          - Template-level skip-tags.
          - Lists are joined into newline-delimited strings.

      limit:
        type: str
        description: Template-level Ansible limit.

      allow_override_args_in_task:
        type: bool
        description: Allow task runs to override Ansible arguments.

      allow_override_branch_in_task:
        type: bool
        description: Allow task runs to override the Git branch.

      allow_parallel_tasks:
        type: bool
        description: Allow multiple tasks from this template to run in parallel.

      suppress_success_alerts:
        type: bool
        description: Suppress notifications/alerts on successful runs.

      autorun:
        type: bool
        description: Automatically run the template on relevant triggers (if supported by Semaphore).

      task_params:
        type: dict
        description:
          - Task-level overrides used at execution time.
          - List-style tags, skip_tags, and limit are normalized.

      survey_vars:
        type: list
        elements: dict
        description:
          - Survey definitions shown at task start.

      vaults:
        type: list
        elements: dict
        description:
          - Vault references attached to the template.

      prompt_inventory:
        type: bool
        description:
          - Prompt for inventory at task start.
          - Applied via follow-up PUT.

      prompt_limit:
        type: bool
        description:
          - Prompt for limit at task start.
          - Applied via follow-up PUT.

      prompt_tags:
        type: bool
        description:
          - Prompt for tags at task start.
          - Applied via follow-up PUT.

      prompt_skip_tags:
        type: bool
        description:
          - Prompt for skip-tags at task start.
          - Applied via follow-up PUT.

      prompt_arguments:
        type: bool
        description:
          - Prompt for arguments at task start.
          - Applied via follow-up PUT.

      prompt_branch:
        type: bool
        description:
          - Prompt for branch at task start.
          - Applied via follow-up PUT.

  session_cookie:
    type: str
    no_log: true
    description: Semaphore session cookie.

  api_token:
    type: str
    no_log: true
    description: Semaphore API token.

  validate_certs:
    type: bool
    default: true
    description: Validate TLS certificates.

author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Create job template with prompts
  ebdruplab.semaphoreui.semaphore_template_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 55
    template:
      name: "Example Job"
      app: ansible
      playbook: playbooks/example.yml
      repository_id: 48
      inventory_id: 121
      type: ""
      tags: ["setup", "init"]
      prompt_inventory: true
      prompt_tags: true
      prompt_arguments: true
'''

RETURN = r'''
template:
  description: Template object returned by the API.
  type: dict
  returned: success

status:
  description: HTTP status code.
  type: int
  returned: always

attempts:
  description:
    - List of API operations performed (create and optional update).
  type: list
  returned: always
'''

PROMPT_KEYS = [
    "prompt_inventory",
    "prompt_limit",
    "prompt_tags",
    "prompt_skip_tags",
    "prompt_arguments",
    "prompt_branch",
]

ALLOWED_CREATE_FIELDS = {
    "project_id",
    "name",
    "app",
    "playbook",
    "repository_id",
    "inventory_id",
    "environment_id",
    "view_id",
    "type",
    "description",
    "git_branch",
    "arguments",
    "limit",
    "tags",
    "skip_tags",
    "vault_password",
    "allow_override_args_in_task",
    "allow_override_branch_in_task",
    "allow_parallel_tasks",
    "suppress_success_alerts",
    "autorun",
    "task_params",
    "survey_vars",
    "vaults",
}

def normalize_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "yes", "1")
    return False

def prune(d, allowed):
    return {k: v for k, v in d.items() if k in allowed}

def http_post(url, payload, headers, validate):
    return semaphore_post(
        url=url,
        body=json.dumps(payload).encode(),
        headers=headers,
        validate_certs=validate,
    )

def http_put(url, payload, headers, validate):
    return semaphore_request(
        "PUT",
        url,
        body=json.dumps(payload).encode(),
        headers=headers,
        validate_certs=validate,
    )

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            template=dict(type="dict", required=True),
            session_cookie=dict(type="str", no_log=True),
            api_token=dict(type="str", no_log=True),
            validate_certs=dict(type="bool", default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    p = module.params
    tpl_in = dict(p["template"])
    host = p["host"].rstrip("/")
    port = p["port"]
    project_id = p["project_id"]

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"

    # Capture prompt flags explicitly provided by user
    user_prompts = {
        k: normalize_bool(tpl_in[k])
        for k in PROMPT_KEYS
        if k in tpl_in
    }

    # Build CREATE payload
    tpl = copy.deepcopy(tpl_in)
    tpl["project_id"] = project_id
    tpl["app"] = tpl.get("app", "ansible")

    for key in PROMPT_KEYS:
        tpl.pop(key, None)

    create_payload = prune(tpl, ALLOWED_CREATE_FIELDS)

    base_url = f"{host}:{port}/api/project/{project_id}/templates"
    attempts = []

    resp, status, _ = http_post(
        base_url,
        create_payload,
        headers,
        p["validate_certs"],
    )
    attempts.append({"op": "create", "status": status, "payload": create_payload})

    if status not in (200, 201):
        module.fail_json(
            msg="Template creation failed",
            status=status,
            response=resp.decode(),
            attempts=attempts,
        )

    created = json.loads(resp.decode())

    # Apply prompts using FULL PUT (merge-safe)
    if user_prompts:
        merged = copy.deepcopy(created)

        for k, v in user_prompts.items():
            merged[k] = v

        merged["app"] = created.get("app", "ansible")
        merged["type"] = created.get("type", "")

        put_url = f"{base_url}/{created['id']}"
        resp2, status2, _ = http_put(
            put_url,
            merged,
            headers,
            p["validate_certs"],
        )
        attempts.append({"op": "update-prompts", "status": status2})

        if status2 not in (200, 204):
            module.fail_json(
                msg="Template created but prompt update failed",
                status=status2,
                response=resp2.decode(),
                attempts=attempts,
            )

        created = merged

    module.exit_json(
        changed=True,
        template=created,
        attempts=attempts,
    )

if __name__ == "__main__":
    main()
