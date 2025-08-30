#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r'''
---
module: project_template_create
short_description: Create a Semaphore template (job, deploy, or build) with surveys, vaults, and task params
version_added: "1.0.0"
description:
  - Creates a new template in a Semaphore project.
  - Supports surveys (string, integer, secret, enum), vault attachments, and task parameter overrides.
  - For job templates (i.e. when C(type) is omitted, C(None), C(""), or C("job")), Semaphore does not accept C(task_params).
    This module will automatically drop C(task_params) for job templates to avoid API 400 errors.
options:
  host:
    description:
      - Full host address of the Semaphore server (including scheme).
    type: str
    required: true
  port:
    description:
      - Port of the Semaphore server (e.g. 3000).
    type: int
    required: true
  project_id:
    description:
      - ID of the project where the template will be created.
    type: int
    required: true
  template:
    description:
      - Template definition dictionary.
    type: dict
    required: true
    suboptions:
      name:
        description: Template name.
        type: str
        required: true
      app:
        description: Application type. Defaults to C(ansible) if omitted.
        type: str
        required: false
      playbook:
        description: Playbook path in the repo.
        type: str
        required: true
      repository_id:
        description: Repository ID.
        type: int
        required: true
      inventory_id:
        description: Inventory ID.
        type: int
        required: true
      environment_id:
        description: Environment ID.
        type: int
      view_id:
        description: Board view ID.
        type: int
      type:
        description:
          - Template type. Use C(job), C(deploy), C(build), or omit/empty for "None".
        type: str
        choices: [job, deploy, build, ""]
      description:
        description: Human description.
        type: str
      git_branch:
        description: Git branch override.
        type: str
      arguments:
        description:
          - JSON string for arguments as stored by Semaphore UI.
          - If a list or dict is provided, it will be JSON-encoded.
          - If omitted/empty, defaults to C("[]").
        type: raw
      allow_override_args_in_task:
        type: bool
      allow_override_branch_in_task:
        type: bool
      allow_parallel_tasks:
        type: bool
      suppress_success_alerts:
        type: bool
      limit:
        type: str
      tags:
        description: Template tags string (not to be confused with task_params.tags).
        type: str
      skip_tags:
        type: str
      vault_password:
        type: str
      start_version:
        type: str
      prompt_inventory:
        type: bool
      prompt_limit:
        type: bool
      prompt_tags:
        type: bool
      prompt_skip_tags:
        type: bool
      prompt_vault_password:
        type: bool
      prompt_arguments:
        type: bool
      prompt_branch:
        type: bool
      prompt_environment:
        type: bool
      survey_vars:
        description:
          - List of survey variable definitions.
        type: list
        elements: dict
        suboptions:
          name:
            type: str
            required: true
          title:
            type: str
            required: true
          type:
            description: Survey type.
            type: str
            choices: [string, int, secret, enum]
            required: true
          description:
            type: str
          required:
            type: bool
            default: false
          default_value:
            type: raw
          values:
            description:
              - For C(enum) only, list of name/value objects.
            type: list
            elements: dict
            suboptions:
              name:
                type: str
                required: true
              value:
                type: raw
                required: true
      task_params:
        description:
          - Task parameter overrides. Ignored for job templates (Semaphore API limitation).
        type: dict
        suboptions:
          allow_debug:
            type: bool
          allow_override_inventory:
            type: bool
          allow_override_limit:
            type: bool
          allow_override_tags:
            type: bool
          allow_override_skip_tags:
            type: bool
          tags:
            type: list
            elements: str
      vaults:
        description:
          - List of vault attachments for the template.
          - Provide IDs via C(vault_key_id). Entries without a valid C(vault_key_id) are dropped.
        type: list
        elements: dict
        suboptions:
          type:
            type: str
            choices: [password, key, script]
            required: true
          vault_key_id:
            description: ID of the vault key to attach.
            type: int
          name:
            type: str
          script:
            type: raw
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
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Create template with surveys and task params
  ebdruplab.semaphoreui.project_template_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 55
    template:
      name: "Deploy Web"
      app: "ansible"
      playbook: "deploy.yml"
      repository_id: 48
      inventory_id: 121
      environment_id: 93
      view_id: 82
      type: "job"
      description: "A sample deployment"
      arguments: []     # will be encoded to "[]"
      allow_override_args_in_task: true
      allow_override_branch_in_task: true
      allow_parallel_tasks: true
      task_params:
        allow_debug: true
        allow_override_inventory: true
        allow_override_limit: true
        allow_override_skip_tags: true
        allow_override_tags: true
        tags: ["blue", "db"]
      survey_vars:
        - name: "release_version"
          title: "Release version"
          type: "string"
          description: "Version to deploy"
          required: true
          default_value: "1.0.0"
        - name: "batch_size"
          title: "Batch size"
          type: "integer"
          default_value: 5
        - name: "api_key"
          title: "API key"
          type: "secret"
          required: true
        - name: "env"
          title: "Environment"
          type: "enum"
          required: true
          values:
            - { name: "staging", value: "stg" }
            - { name: "production", value: "prod" }
      vaults:
        - type: password
          vault_key_id: 251
'''

RETURN = r'''
template:
  description: The created template object.
  type: dict
  returned: success
status:
  description: HTTP status code from the Semaphore API.
  type: int
  returned: always
'''


TYPE_NORMALIZE = {
    None: "",
    "": "",
    "none": "",
    "None": "",
    "job": "",   # Semaphore represents "job" as "" internally
    "deploy": "deploy",
    "build": "build",
}

# NOTE: API examples show "int" (not "integer").
SURVEY_TYPES = {"string", "int", "secret", "enum"}
VAULT_TYPES = {"password", "key", "script"}  # added "key" to match documented choices

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


def _json_stringify_arguments(value):
    """
    Normalize 'arguments' to the JSON string format the Semaphore UI stores.
    Defaults to "[]" when not provided.
    """
    if value is None:
        return "[]"
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return "[]"
        try:
            json.loads(s)
            return s
        except Exception:
            # Treat scalar string as a single argument
            return json.dumps([value])
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    # Any other scalar: wrap as single arg
    return json.dumps([str(value)])


def _normalize_task_params(tp):
    tp = dict(tp or {})
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
    if not svars:
        return []
    out = []
    for idx, sv in enumerate(svars, 1):
        if not isinstance(sv, dict):
            module.fail_json(msg=f"survey_vars[{idx}] must be a dict")

        name = sv.get("name")
        title = sv.get("title")
        stype = sv.get("type")

        if not name or not title or not stype:
            module.fail_json(msg=f"survey_vars[{idx}] requires 'name', 'title', and 'type'")

        # Normalize survey type: accept "integer"/"number" but send "int" to the API
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
    if not vaults:
        return []
    out = []
    for idx, v in enumerate(vaults, 1):
        if not isinstance(v, dict):
            module.fail_json(msg=f"vaults[{idx}] must be a dict")

        vtype = v.get("type")
        if vtype not in VAULT_TYPES:
            module.fail_json(msg=f"vaults[{idx}].type must be one of {sorted(VAULT_TYPES)}")

        vkid = v.get("vault_key_id")
        if vkid is None or str(vkid).strip() == "":
            # API wants a valid ID; skip incomplete entries
            continue
        try:
            vkid = int(vkid)
        except Exception:
            module.fail_json(msg=f"vaults[{idx}].vault_key_id must be an integer")

        item = {
            "type": vtype,
            "vault_key_id": vkid,
        }
        if "name" in v and v["name"] is not None:
            item["name"] = str(v["name"])
        if "script" in v:
            item["script"] = v["script"]
        out.append(item)
    return out


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
    validate_certs = p['validate_certs']

    tpl = dict(p['template'] or {})
    tpl['project_id'] = project_id
    tpl['app'] = tpl.get('app', 'ansible')

    for field in ['name', 'playbook', 'inventory_id', 'repository_id']:
        if not tpl.get(field):
            module.fail_json(msg=f"Missing required template field: {field}")

    # Required ints
    try:
        tpl['inventory_id'] = int(tpl['inventory_id'])
        tpl['repository_id'] = int(tpl['repository_id'])
    except (ValueError, TypeError):
        module.fail_json(msg="inventory_id and repository_id must be valid integers.")

    # Optional ints
    for opt_int in ['environment_id', 'view_id', 'build_template_id']:
        if opt_int in tpl and tpl[opt_int] not in (None, ''):
            try:
                tpl[opt_int] = int(tpl[opt_int])
            except (ValueError, TypeError):
                module.fail_json(msg=f"{opt_int} must be an integer if provided.")

    # Type normalization
    raw_type = tpl.get('type', '')
    norm_type = TYPE_NORMALIZE.get(
        raw_type if raw_type in ("", "job", "deploy", "build", None) else str(raw_type).lower(),
        None
    )
    if norm_type is None:
        module.fail_json(msg="template.type must be one of '', job, deploy, build (or omit/None).")
    tpl['type'] = norm_type  # "" for job

    # Arguments normalization
    tpl['arguments'] = _json_stringify_arguments(tpl.get('arguments'))

    # Normalize substructures
    if 'task_params' in tpl:
        tpl['task_params'] = _normalize_task_params(tpl.get('task_params'))

    if 'survey_vars' in tpl:
        tpl['survey_vars'] = _validate_and_normalize_surveys(tpl.get('survey_vars'), module)

    if 'vaults' in tpl:
        norm_vaults = _validate_and_normalize_vaults(tpl.get('vaults'), module)
        if norm_vaults:
            tpl['vaults'] = norm_vaults
        else:
            tpl.pop('vaults', None)

    # Booleans
    for bkey in [
        'allow_override_args_in_task',
        'allow_override_branch_in_task',
        'allow_parallel_tasks',
        'suppress_success_alerts',
        'prompt_inventory',
        'prompt_limit',
        'prompt_tags',
        'prompt_skip_tags',
        'prompt_vault_password',
        'prompt_arguments',
        'prompt_branch',
        'prompt_environment',
        'autorun',
    ]:
        if bkey in tpl and tpl[bkey] is not None:
            tpl[bkey] = bool(tpl[bkey])

    # Drop false-y prompt_* flags (Semaphore often omits false prompt keys)
    _drop_falsey_prompts(tpl)

    # Convert list tags to newline-delimited strings
    if isinstance(tpl.get('tags'), list):
        tpl['tags'] = "\n".join([str(x) for x in tpl['tags']])
    if isinstance(tpl.get('skip_tags'), list):
        tpl['skip_tags'] = "\n".join([str(x) for x in tpl['skip_tags']])

    # IMPORTANT: task_params are not accepted for job templates
    if tpl.get('type', '') == "":

      tpl.pop('task_params', None)
      tpl.pop('survey_vars', None)  # job templates also reject surveys (avoids API 400)

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token")
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    url = f"{host}:{port}/api/project/{project_id}/templates"

    try:
        body = json.dumps(tpl).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url=url,
            body=body,
            headers=headers,
            validate_certs=validate_certs
        )

        if status not in (200, 201):
            text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else str(response_body)
            module.fail_json(
                msg=f"Failed to create template: HTTP {status} - {text}",
                status=status,
                debug={"url": url, "payload": tpl},
            )

        text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else response_body
        try:
            created = json.loads(text) if isinstance(text, str) else text
        except Exception:
            created = {"raw": text}

        module.exit_json(changed=True, template=created, status=status)

    except Exception as e:
        # Surface useful debugging context even when module_utils raises for 4xx
        module.fail_json(msg=str(e), debug={"url": url, "payload": tpl})

if __name__ == '__main__':
    main()
