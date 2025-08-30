#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_template_update
short_description: Update a Semaphore template (job/deploy/build) with surveys, vaults, and task params
version_added: "1.0.0"
description:
  - Updates an existing template in a specified Semaphore project.
  - Ensures the body contains C(id) and C(project_id) matching the URL params.
  - Coerces numeric identifiers to integers, normalizes C(arguments) to a JSON string, joins list-style tags with newlines, and prunes null fields.
  - Supports C(task_params) (including list C(tags)), and validates/normalizes C(survey_vars).
  - For job templates (i.e. when C(type) is omitted, C(None), C(""), or C("job")), Semaphore does not accept C(task_params)
    and may reject C(allow_parallel_tasks); this module will drop these to avoid API 400 errors.
  - On update, C(vaults) entries can include C(id), C(name), C(type), C(vault_key_id), and C(script). If the list is empty or
    undefined, the field is omitted to avoid API errors.

options:
  host:
    description:
      - Hostname or IP of the Semaphore server (including protocol).
      - Example: C(http://localhost) or C(https://semaphore.example.com)
    type: str
    required: true
  port:
    description:
      - Port of the Semaphore server (typically 3000).
    type: int
    required: true
  project_id:
    description:
      - ID of the project the template belongs to.
    type: int
    required: true
  template_id:
    description:
      - ID of the template to update.
    type: int
    required: true
  template:
    description:
      - Template payload with updated fields.
    type: dict
    required: true
    suboptions:
      name:
        description: Template name.
        type: str
        required: true
      app:
        description: Application type (e.g., C(ansible)).
        type: str
        required: true
      playbook:
        description: Playbook path in the repository.
        type: str
        required: true
      id:
        description: Template ID (will be set automatically to C(template_id)).
        type: int
      project_id:
        description: Project ID (will be set automatically to C(project_id)).
        type: int
      repository_id:
        description: Repository ID.
        type: int
      inventory_id:
        description: Inventory ID.
        type: int
      environment_id:
        description: Environment ID.
        type: int
      view_id:
        description: Board View ID.
        type: int
      build_template_id:
        description: Build template ID (for build pipelines).
        type: int
      type:
        description: One of C(job), C(deploy), C(build) or empty (job is represented as an empty string by the API).
        type: str
        choices: ["", "job", "deploy", "build"]
      description:
        description: Human-friendly description.
        type: str
      git_branch:
        description: Git branch override.
        type: str
      limit:
        description: Ansible limit value.
        type: str
      tags:
        description: Newline-delimited string of tags (list will be joined automatically).
        type: raw
      skip_tags:
        description: Newline-delimited string of skip-tags (list will be joined automatically).
        type: raw
      vault_password:
        description: Ansible vault password (string value).
        type: str
      start_version:
        description: Starting version (required by API for type C(build)).
        type: str
      allow_override_args_in_task:
        description: Allow overriding arguments at task start.
        type: bool
      allow_override_branch_in_task:
        description: Allow overriding branch at task start.
        type: bool
      allow_parallel_tasks:
        description: Allow running tasks in parallel.
        type: bool
      suppress_success_alerts:
        description: Suppress success alerts.
        type: bool
      autorun:
        description: Auto-run newly created tasks.
        type: bool
      prompt_inventory:
        description: Prompt for inventory.
        type: bool
      prompt_limit:
        description: Prompt for Ansible limit.
        type: bool
      prompt_tags:
        description: Prompt for Ansible tags.
        type: bool
      prompt_skip_tags:
        description: Prompt for Ansible skip-tags.
        type: bool
      prompt_vault_password:
        description: Prompt for Ansible vault password.
        type: bool
      prompt_arguments:
        description: Prompt for arguments.
        type: bool
      prompt_branch:
        description: Prompt for Git branch.
        type: bool
      prompt_environment:
        description: Prompt for environment.
        type: bool
      arguments:
        description:
          - Arguments as the UI stores them (JSON string).
          - Lists/dicts will be encoded; scalars wrapped into a single-element JSON list.
          - Defaults to C("[]") when omitted/empty.
        type: raw
      task_params:
        description:
          - Task parameter overrides. Ignored for job templates (API limitation).
        type: dict
        suboptions:
          allow_debug: {type: bool, description: Allow debug mode}
          allow_override_inventory: {type: bool}
          allow_override_limit: {type: bool}
          allow_override_tags: {type: bool}
          allow_override_skip_tags: {type: bool}
          tags:
            description: UI label tags for tasks.
            type: list
            elements: str
      vaults:
        description:
          - List of vault references attached to the template.
          - On update, you may include existing items by C(id) and/or specify new ones via C(vault_key_id).
        type: list
        elements: dict
        suboptions:
          id:
            description: Existing vault attachment ID (omit when adding a new one).
            type: int
          name:
            description: Friendly name/label for the vault reference.
            type: str
          type:
            description: Vault reference type.
            type: str
            choices: [password, script]
            required: true
          vault_key_id:
            description: Vault key ID to attach.
            type: int
          script:
            description: Script path/identifier for C(type=script).
            type: raw
      survey_vars:
        description:
          - Survey definitions. API expects C(type) to be one of C(string), C(int), C(secret), or C(enum).
          - This module accepts synonyms like C(integer)/C(number) and maps them to C(int).
        type: list
        elements: dict
        suboptions:
          name: {type: str, required: true, description: Internal variable name}
          title: {type: str, required: true, description: Human label}
          description: {type: str, description: Help text}
          type:
            type: str
            choices: [string, int, secret, enum]
            required: true
            description: Survey type (use C(int) for integers).
          required: {type: bool, default: false}
          default_value: {type: raw}
          values:
            description: Only for C(enum); list of name/value pairs.
            type: list
            elements: dict
            suboptions:
              name: {type: str, required: true}
              value: {type: raw, required: true}

  session_cookie:
    description: Session cookie for authentication.
    type: str
    required: false
    no_log: true
  api_token:
    description: API token for authentication.
    type: str
    required: false
    no_log: true
  validate_certs:
    description: Whether to validate TLS certificates.
    type: bool
    default: true

author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Update a Semaphore template
  ebdruplab.semaphoreui.project_template_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 1
    template_id: 7
    template:
      name: "Updated Template"
      app: "ansible"
      playbook: "deploy.yml"
      repository_id: 1
      inventory_id: 1
      environment_id: 1
      view_id: 1
      type: "job"
      description: "Keep ids/body in sync with URL"
      arguments: []
      tags: [web, blue]
      skip_tags: [db]
      allow_override_args_in_task: false
      allow_override_branch_in_task: true
      allow_parallel_tasks: true
      suppress_success_alerts: true
      limit: "localhost"
      task_params:
        allow_debug: true
        allow_override_inventory: true
        allow_override_limit: true
        allow_override_tags: true
        allow_override_skip_tags: true
        tags: ["ops", "nightly"]
      survey_vars:
        - name: "batch_size"
          title: "Batch size"
          type: "int"
          default_value: 5
        - name: "env"
          title: "Environment"
          type: "enum"
          required: true
          values:
            - { name: "staging", value: "stg" }
            - { name: "production", value: "prod" }
      vaults:
        - id: 12
          type: password
          name: "Project Vault Password"
        - type: script
          name: "exist"
          script: "extension-client"

- name: Update with string JSON arguments and tags
  ebdruplab.semaphoreui.project_template_update:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 42
    template_id: 99
    template:
      name: "Nightly Check"
      app: "ansible"
      playbook: "playbooks/check.yml"
      repository_id: 10
      inventory_id: 11
      type: ""
      arguments: "[]"
      tags: "ops\nnightly"
"""

RETURN = r"""
template:
  description: The updated template object (empty on 204).
  type: dict
  returned: success
status:
  description: HTTP status code from the Semaphore API.
  type: int
  returned: always
debug:
  description: Debug data (only when a non-2xx is returned).
  type: dict
  returned: on failure
"""

TYPE_NORMALIZE = {
    None: "",
    "": "",
    "none": "",
    "None": "",
    "job": "",
    "deploy": "deploy",
    "build": "build",
}

SURVEY_TYPES = {"string", "int", "secret", "enum"}
VAULT_TYPES = {"password", "script"}

def _as_text(b):
    if isinstance(b, (bytes, bytearray)):
        try:
            return b.decode()
        except Exception:
            return str(b)
    return b

def _int_or_none(val):
    if val is None or val == "":
        return None
    try:
        return int(val)
    except Exception:
        return None

def _normalize_arguments(v):
    # Always a JSON string; default to "[]"
    if v is None:
        return "[]"
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return "[]"
        try:
            json.loads(s)
            return s
        except Exception:
            return json.dumps([v])
    # Unknown scalar -> treat as single argument
    return json.dumps([str(v)])

def _normalize_tag_block(v):
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        return "\n".join([str(x) for x in v])
    return str(v)

def _normalize_task_params(tp):
    if not isinstance(tp, dict):
        return None
    out = {
        "allow_debug": bool(tp.get("allow_debug", False)),
        "allow_override_inventory": bool(tp.get("allow_override_inventory", False)),
        "allow_override_limit": bool(tp.get("allow_override_limit", False)),
        "allow_override_tags": bool(tp.get("allow_override_tags", False)),
        "allow_override_skip_tags": bool(tp.get("allow_override_skip_tags", False)),
        "tags": [],
    }
    tags = tp.get("tags", [])
    if isinstance(tags, str):
        out["tags"] = [t for t in [x.strip() for x in tags.split(",")] if t]
    elif isinstance(tags, list):
        out["tags"] = [str(t) for t in tags]
    return out

def _validate_and_normalize_surveys(svars, module):
    if svars is None:
        return None
    if not isinstance(svars, list):
        module.fail_json(msg="template.survey_vars must be a list when provided.")
    out = []
    for idx, sv in enumerate(svars, 1):
        if not isinstance(sv, dict):
            module.fail_json(msg=f"survey_vars[{idx}] must be a dict")
        name = sv.get("name")
        title = sv.get("title")
        stype = sv.get("type")
        if not name or not title or not stype:
            module.fail_json(msg=f"survey_vars[{idx}] requires 'name', 'title', and 'type'")
        stype_l = str(stype).lower()
        if stype_l in ("integer", "number"):
            stype_l = "int"
        if stype_l not in SURVEY_TYPES:
            module.fail_json(msg=f"survey_vars[{idx}].type must be one of {sorted(SURVEY_TYPES)}")
        required = bool(sv.get("required", False))
        desc = sv.get("description", "")
        default_value = sv.get("default_value", None)

        if stype_l == "int":
            if default_value is not None:
                try:
                    default_value = int(default_value)
                except Exception:
                    module.fail_json(msg=f"survey_vars[{idx}].default_value must be integer-compatible")
            values = None
        elif stype_l in ("string", "secret"):
            if default_value is not None and not isinstance(default_value, (str, int, float)):
                module.fail_json(msg=f"survey_vars[{idx}].default_value must be scalar")
            if isinstance(default_value, (int, float)):
                default_value = str(default_value)
            values = None
        else:  # enum
            values = sv.get("values", [])
            if not isinstance(values, list) or len(values) == 0:
                module.fail_json(msg=f"survey_vars[{idx}].values must be a non-empty list for enum type")
            norm_vals = []
            for j, ev in enumerate(values, 1):
                if not isinstance(ev, dict) or "name" not in ev or "value" not in ev:
                    module.fail_json(msg=f"survey_vars[{idx}].values[{j}] must have 'name' and 'value'")
                norm_vals.append({"name": str(ev["name"]), "value": ev["value"]})
            values = norm_vals

        out_item = {
            "name": str(name),
            "title": str(title),
            "type": stype_l,
            "description": str(desc) if desc is not None else "",
            "required": required,
        }
        if default_value is not None:
            out_item["default_value"] = default_value
        if values is not None:
            out_item["values"] = values
        out.append(out_item)
    return out

def _validate_and_normalize_vaults(vaults, module):
    if vaults is None:
        return None
    if not isinstance(vaults, list):
        module.fail_json(msg="template.vaults must be a list when provided.")
    validated = []
    for i, v in enumerate(vaults, 1):
        if not isinstance(v, dict):
            module.fail_json(msg=f"template.vaults[{i}] must be a dict.")
        vtype = v.get("type")
        if not isinstance(vtype, str) or vtype not in VAULT_TYPES:
            module.fail_json(msg=f"template.vaults[{i}].type must be one of {sorted(VAULT_TYPES)}")
        item = {"type": vtype}
        # Existing attachment id (optional on update; include if present)
        vid = _int_or_none(v.get("id"))
        if vid is not None:
            item["id"] = vid
        # Optional helpers
        if "name" in v and v["name"] is not None:
            item["name"] = str(v["name"])
        vkid = _int_or_none(v.get("vault_key_id"))
        if vkid is not None:
            item["vault_key_id"] = vkid
        if "script" in v:
            item["script"] = v["script"]
        validated.append(item)
    return validated

def _prune_nones(d):
    return {k: v for k, v in d.items() if v is not None}

PROMPT_KEYS = [
    "prompt_inventory",
    "prompt_limit",
    "prompt_tags",
    "prompt_skip_tags",
    "prompt_vault_password",
    "prompt_arguments",
    "prompt_branch",
    "prompt_environment",
]

def _drop_falsey_prompts(d):
    for k in PROMPT_KEYS:
        if not d.get(k):
            d.pop(k, None)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            template_id=dict(type='int', required=True),
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
    port = int(p['port'])
    project_id = int(p['project_id'])
    template_id = int(p['template_id'])
    tpl = dict(p['template'] or {})
    validate_certs = p['validate_certs']

    # Required fields for update body
    for req in ('name', 'app', 'playbook'):
        if not tpl.get(req):
            module.fail_json(msg=f"Missing required template field: {req}")

    # Coerce integer fields
    for key in ('repository_id', 'inventory_id', 'environment_id', 'view_id', 'build_template_id'):
        if key in tpl and tpl[key] is not None:
            coerced = _int_or_none(tpl[key])
            if coerced is None and key in ('repository_id', 'inventory_id'):
                module.fail_json(msg=f"{key} must be an integer")
            if coerced is None:
                tpl.pop(key, None)
            else:
                tpl[key] = coerced

    # Type normalization
    raw_type = tpl.get('type', "")
    norm_type = TYPE_NORMALIZE.get(
        raw_type if raw_type in ("", "job", "deploy", "build", None) else str(raw_type).lower(),
        None
    )
    if norm_type is None:
        module.fail_json(msg="template.type must be one of '', job, deploy, build (or omit/None).")
    tpl['type'] = norm_type  # "" for job

    # Arguments & tag blocks
    tpl['arguments'] = _normalize_arguments(tpl.get('arguments'))

    if 'tags' in tpl:
        tags = _normalize_tag_block(tpl.get('tags'))
        if tags:
            tpl['tags'] = tags
        else:
            tpl.pop('tags', None)

    if 'skip_tags' in tpl:
        skip_tags = _normalize_tag_block(tpl.get('skip_tags'))
        if skip_tags:
            tpl['skip_tags'] = skip_tags
        else:
            tpl.pop('skip_tags', None)

    # task_params (drop for job)
    if 'task_params' in tpl:
        tpl['task_params'] = _normalize_task_params(tpl.get('task_params'))

    # survey_vars (validate & normalize)
    if 'survey_vars' in tpl:
        norm_sv = _validate_and_normalize_surveys(tpl.get('survey_vars'), module)
        if norm_sv is not None:
            tpl['survey_vars'] = norm_sv

    # vaults (validate & normalize)
    if 'vaults' in tpl:
        norm_vaults = _validate_and_normalize_vaults(tpl.get('vaults'), module)
        if norm_vaults:
            tpl['vaults'] = norm_vaults
        else:
            tpl.pop('vaults', None)

    # Sync ids
    tpl['id'] = template_id
    tpl['project_id'] = project_id

    # Booleans
    for bkey in [
        'allow_override_args_in_task',
        'allow_override_branch_in_task',
        'allow_parallel_tasks',
        'suppress_success_alerts',
        'autorun',
        'prompt_inventory',
        'prompt_limit',
        'prompt_tags',
        'prompt_skip_tags',
        'prompt_vault_password',
        'prompt_arguments',
        'prompt_branch',
        'prompt_environment',
    ]:
        if bkey in tpl and tpl[bkey] is not None:
            tpl[bkey] = bool(tpl[bkey])

    # Drop false-y prompt_* flags
    _drop_falsey_prompts(tpl)

    # IMPORTANT: job-type quirks
    if tpl.get('type', '') == "":
        tpl.pop('task_params', None)
        tpl.pop('allow_parallel_tasks', None)

    tpl = _prune_nones(tpl)

    headers = get_auth_headers(
        session_cookie=p.get('session_cookie'),
        api_token=p.get('api_token'),
    )
    headers['Content-Type'] = 'application/json'
    headers.setdefault('Accept', 'application/json')

    url = f"{host}:{port}/api/project/{project_id}/templates/{template_id}"

    try:
        body = json.dumps(tpl).encode('utf-8')
        response_body, status, _ = semaphore_put(
            url=url,
            body=body,
            headers=headers,
            validate_certs=validate_certs,
        )

        if status not in (200, 201, 204):
            module.fail_json(
                msg=f"PUT failed with status {status}: {_as_text(response_body)}",
                status=status,
                debug={
                    'url': url,
                    'url_project_id': project_id,
                    'url_template_id': template_id,
                    'body_project_id': tpl.get('project_id'),
                    'body_id': tpl.get('id'),
                    'payload': tpl,
                },
            )

        if status == 204 or not response_body:
            module.exit_json(changed=True, template={}, status=status)

        text = _as_text(response_body)
        try:
            result = json.loads(text) if isinstance(text, str) else text
        except Exception:
            result = {'raw': text}

        module.exit_json(changed=True, template=result, status=status)

    except Exception as e:
        module.fail_json(msg=str(e), debug={'url': url, 'payload': tpl})

if __name__ == '__main__':
    main()
