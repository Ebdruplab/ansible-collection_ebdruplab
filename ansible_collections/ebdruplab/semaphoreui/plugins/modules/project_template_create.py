#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025
# MIT License

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, semaphore_request, get_auth_headers
import json
import copy

DOCUMENTATION = r'''
---
module: semaphore_template_create
short_description: Create a Semaphore template (job, deploy, or build) with surveys, vaults, prompts and task params
version_added: "1.0.0"
description:
  - Creates a new template in a Semaphore project.
  - Supports surveys (string, int, secret, enum), vault attachments, and task parameter overrides.
  - Accepts richer task_params (allow_debug, allow_override_*, and list-style limit/tags/skip_tags).
  - For job templates, some server builds may reject C(task_params.allow_debug) on create; the module retries once without it.
  - C(prompt_*) flags are not honored by the create endpoint on some servers; this module applies them with a follow-up PUT.
  - Normalizes integers, JSON arguments, tag lists (list or string -> newline string), and survey defs (drop defaults for secret).
options:
  host: {type: str, required: true}
  port: {type: int, required: true}
  project_id: {type: int, required: true}
  template:
    type: dict
    required: true
    suboptions:
      name: {type: str, required: true}
      app: {type: str, description: "Application type. Usually 'ansible'. Defaults to ansible."}
      playbook: {type: str, required: true}
      repository_id: {type: int, required: true}
      inventory_id: {type: int, required: true}
      environment_id: {type: int}
      view_id: {type: int}
      build_template_id: {type: int}
      type:
        type: str
        choices: [job, deploy, build, ""]
        description: "Omit/empty for job (API uses empty string)."
      description: {type: str}
      git_branch: {type: str}
      arguments:
        type: raw
        description:
          - JSON string as stored by UI.
          - Lists/dicts encoded to JSON; scalars wrapped into a one-element JSON list.
          - Defaults to "[]".
      allow_override_args_in_task: {type: bool}
      allow_override_branch_in_task: {type: bool}
      allow_parallel_tasks: {type: bool}
      suppress_success_alerts: {type: bool}
      autorun: {type: bool}
      limit: {type: str}
      tags:
        type: raw
        description: "Template tags (list or string). Lists -> newline-separated string."
      skip_tags:
        type: raw
        description: "Template skip-tags (list or string). Lists -> newline-separated string."
      vault_password: {type: str}
      start_version: {type: str, description: "Required for type=build (create only)."}
      # You may pass prompt_* in input; they will be applied via PUT after create.
      prompt_inventory: {type: bool}
      prompt_limit: {type: bool}
      prompt_tags: {type: bool}
      prompt_skip_tags: {type: bool}
      prompt_arguments: {type: bool}
      prompt_branch: {type: bool}
      # Some servers don't support these two at all; we ignore them if present.
      prompt_vault_password: {type: bool}
      prompt_environment: {type: bool}
      task_params:
        type: dict
        description: >
          Task parameter overrides. Server accepts allow_debug (even for job on many builds),
          allow_override_* flags, plus list-style limit/tags/skip_tags.
        suboptions:
          allow_debug: {type: bool}
          allow_override_inventory: {type: bool}
          allow_override_limit: {type: bool}
          allow_override_tags: {type: bool}
          allow_override_skip_tags: {type: bool}
          tags:
            type: raw
            description: "List or string; normalized to a list of strings."
          skip_tags:
            type: raw
            description: "List or string; normalized to a list of strings."
          limit:
            type: raw
            description: "List or string; normalized to a list of strings."
      survey_vars:
        type: list
        elements: dict
        suboptions:
          name: {type: str, required: true}
          title: {type: str, required: true}
          type:
            type: str
            choices: [string, int, secret, enum]
            required: true
          description: {type: str}
          required: {type: bool, default: false}
          default_value: {type: raw}
          values:
            type: list
            elements: dict
            description: "Only for enum"
            suboptions:
              name: {type: str, required: true}
              value: {type: raw, required: true}
      vaults:
        type: list
        elements: dict
        description:
          - Provide C(vault_key_id) for password/key attachments. Script entries may omit it.
        suboptions:
          type: {type: str, choices: [password, key, script], required: true}
          vault_key_id: {type: int}
          name: {type: str}
          script: {type: raw}
  session_cookie: {type: str, no_log: true}
  api_token: {type: str, no_log: true}
  validate_certs: {type: bool, default: true}
author: ["Kristian Ebdrup (@kris9854)"]
'''

EXAMPLES = r'''
- name: Create job template, then apply prompts via PUT
  ebdruplab.semaphoreui.semaphore_template_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 55
    template:
      name: "Example Playbook"
      app: "ansible"
      playbook: "playbooks/pb.yml"
      repository_id: 48
      inventory_id: 121
      environment_id: 93
      view_id: 82
      type: ""              # job
      description: "Runs the example playbook"
      git_branch: "main"
      arguments: []
      limit: "localhost"
      tags: ["setup", "init"]
      skip_tags: ["db"]
      allow_override_args_in_task: true
      allow_override_branch_in_task: true
      allow_parallel_tasks: true
      suppress_success_alerts: false
      task_params:
        allow_debug: true
        allow_override_inventory: true
        allow_override_limit: true
        allow_override_tags: true
        allow_override_skip_tags: true
      survey_vars:
        - { name: "release_version", title: "Release version", type: "string", required: true, default_value: "1.0.0" }
        - { name: "batch_size",      title: "Batch size",      type: "int",    required: false, default_value: 5 }
        - { name: "api_key",         title: "API key",         type: "secret", required: true }
        - name: "env"
          title: "Environment"
          type: "enum"
          required: true
          values:
            - {name: "staging", value: "stg"}
            - {name: "production", value: "prod"}
      prompt_inventory: true
      prompt_limit: true
      prompt_tags: true
      prompt_skip_tags: true
      prompt_arguments: true
      prompt_branch: true
'''

RETURN = r'''
template:
  description: Created template object (as returned by API).
  type: dict
status:
  description: HTTP status code.
  type: int
attempts:
  description: Payloads tried (create + optional fallbacks + optional prompt update).
  type: list
'''

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
VAULT_TYPES = {"password", "key", "script"}

PROMPT_KEYS_INPUT = [
    "prompt_inventory",
    "prompt_limit",
    "prompt_tags",
    "prompt_skip_tags",
    "prompt_arguments",
    "prompt_branch",
    "prompt_vault_password",
    "prompt_environment",
]
PROMPT_KEYS_SUPPORTED_ON_PUT = [
    "prompt_inventory",
    "prompt_limit",
    "prompt_tags",
    "prompt_skip_tags",
    "prompt_arguments",
    "prompt_branch",
]

ALLOWED_CREATE_FIELDS = {
    # identity/required
    "project_id", "name", "app", "playbook", "repository_id", "inventory_id",
    # common optional
    "environment_id", "view_id", "build_template_id", "type", "description", "git_branch",
    "arguments", "limit", "tags", "skip_tags", "vault_password", "start_version",
    # booleans
    "allow_override_args_in_task", "allow_override_branch_in_task",
    "allow_parallel_tasks", "suppress_success_alerts", "autorun",
    # complex
    "task_params", "survey_vars", "vaults",
}

def _json_stringify_arguments(value):
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
            return json.dumps([value])
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return json.dumps([str(value)])

def _normalize_tag_str(val):
    """Accept list or string. Produce a newline-separated string ('' if empty)."""
    if val is None:
        return ""
    if isinstance(val, list):
        items = [str(x).strip() for x in val if str(x).strip()]
    else:
        text = str(val).replace(",", "\n")
        items = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(items) if items else ""

def _str_or_seq_to_list(val):
    """List or string -> list[str], splitting on newlines/commas for strings."""
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    text = str(val).replace(",", "\n")
    return [ln.strip() for ln in text.splitlines() if ln.strip()]

def _normalize_task_params(tp):
    tp = dict(tp or {})
    out = {
        "allow_debug": bool(tp.get("allow_debug", False)),
        "allow_override_inventory": bool(tp.get("allow_override_inventory", False)),
        "allow_override_limit": bool(tp.get("allow_override_limit", False)),
        "allow_override_tags": bool(tp.get("allow_override_tags", False)),
        "allow_override_skip_tags": bool(tp.get("allow_override_skip_tags", False)),
        "limit": _str_or_seq_to_list(tp.get("limit", [])),
        "tags": _str_or_seq_to_list(tp.get("tags", [])),
        "skip_tags": _str_or_seq_to_list(tp.get("skip_tags", [])),
    }
    return out

def _merge_template_tags_into_task_params(tpl):
    """Ensure task_params gets default lists from template-level limit/tags/skip_tags if unset."""
    tp = _normalize_task_params(tpl.get("task_params"))
    if not tp.get("limit"):
        tp["limit"] = _str_or_seq_to_list(tpl.get("limit"))
    if not tp.get("tags"):
        tp["tags"] = _str_or_seq_to_list(tpl.get("tags"))
    if not tp.get("skip_tags"):
        tp["skip_tags"] = _str_or_seq_to_list(tpl.get("skip_tags"))
    return tp

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
        if not name or not title or stype in (None, ""):
            module.fail_json(msg=f"survey_vars[{idx}] requires 'name', 'title', and non-empty 'type'")

        stype_l = str(stype).lower()
        if stype_l in ("integer", "number"):
            stype_l = "int"
        if stype_l not in SURVEY_TYPES:
            module.fail_json(msg=f"survey_vars[{idx}].type must be one of {sorted(SURVEY_TYPES)}")

        required = bool(sv.get("required", False))
        desc = sv.get("description", "")
        default_value = sv.get("default_value", None)

        values = None
        if stype_l == "int":
            # Some server builds expect default_value serialized as a STRING even for ints.
            if default_value is not None:
                try:
                    default_value = str(int(default_value))
                except Exception:
                    module.fail_json(msg=f"survey_vars[{idx}].default_value must be integer-compatible")
        elif stype_l == "string":
            if default_value is not None and not isinstance(default_value, (str, int, float)):
                module.fail_json(msg=f"survey_vars[{idx}].default_value must be scalar for string")
            if isinstance(default_value, (int, float)):
                default_value = str(default_value)
        elif stype_l == "secret":
            # server rejects defaults for secret — drop it entirely
            default_value = None
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

        item = {"type": vtype}
        if vtype in {"password", "key"}:
            vkid = v.get("vault_key_id")
            if vkid is None or str(vkid).strip() == "":
                # Skip incomplete password/key attachments
                continue
            try:
                item["vault_key_id"] = int(vkid)
            except Exception:
                module.fail_json(msg=f"vaults[{idx}].vault_key_id must be an integer")
        elif vtype == "script":
            # Script entries may omit vault_key_id; pass through name/script if present
            if "name" in v and v["name"] is not None:
                item["name"] = str(v["name"])
            if "script" in v:
                item["script"] = v["script"]

        out.append(item)
    return out

def _prune_to_allowlist(d, allowed):
    return {k: v for k, v in d.items() if k in allowed}

def _post(url, payload, headers, validate_certs):
    body = json.dumps(payload).encode("utf-8")
    return semaphore_post(url=url, body=body, headers=headers, validate_certs=validate_certs)

def _put(url, payload, headers, validate_certs):
    body = json.dumps(payload).encode("utf-8")
    return semaphore_request("PUT", url, body=body, headers=headers, validate_certs=validate_certs)

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

    original_tpl = dict(p['template'] or {})
    tpl = dict(original_tpl)
    tpl['project_id'] = project_id
    tpl['app'] = tpl.get('app', 'ansible')

    # Required fields
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

    # Normalize type
    raw_type = tpl.get('type', '')
    norm_type = TYPE_NORMALIZE.get(
        raw_type if raw_type in ("", "job", "deploy", "build", None) else str(raw_type).lower(),
        None
    )
    if norm_type is None:
        module.fail_json(msg="template.type must be one of '', job, deploy, build (or omit/None).")
    tpl['type'] = norm_type  # "" for job

    # Normalize arguments
    tpl['arguments'] = _json_stringify_arguments(tpl.get('arguments'))

    # Normalize/validate complex fields
    if 'survey_vars' in tpl:
        tpl['survey_vars'] = _validate_and_normalize_surveys(tpl.get('survey_vars'), module)

    if 'vaults' in tpl:
        v = _validate_and_normalize_vaults(tpl.get('vaults'), module)
        if v:
            tpl['vaults'] = v
        else:
            tpl.pop('vaults', None)

    # Booleans
    for bkey in [
        'allow_override_args_in_task',
        'allow_override_branch_in_task',
        'allow_parallel_tasks',
        'suppress_success_alerts',
        'autorun',
    ]:
        if bkey in tpl and tpl[bkey] is not None:
            tpl[bkey] = bool(tpl[bkey])

    # Template-level tags/skip_tags strings (what the UI stores on the template)
    if 'tags' in tpl:
        tpl['tags'] = _normalize_tag_str(tpl.get('tags'))
    if 'skip_tags' in tpl:
        tpl['skip_tags'] = _normalize_tag_str(tpl.get('skip_tags'))

    # Ensure task_params carries default lists for limit/tags/skip_tags (what runs use)
    tpl['task_params'] = _merge_template_tags_into_task_params(tpl)

    # Remove UI/update-only fields and ANY prompt_* from the CREATE body
    tpl.pop('id', None)
    tpl.pop('tasks', None)
    for pk in PROMPT_KEYS_INPUT:
        tpl.pop(pk, None)

    # TYPE-SPECIFIC
    if tpl['type'] != 'build':
        tpl.pop('start_version', None)
        tpl.pop('build_template_id', None)

    # Prepare create payload
    create_payload = _prune_to_allowlist(tpl, ALLOWED_CREATE_FIELDS)

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token")
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    base_url = f"{host}:{port}/api/project/{project_id}/templates"

    attempts = []
    try:
        # Try 1: POST as-is
        resp_body, status, _ = _post(base_url, create_payload, headers, validate_certs)
        attempts.append({"op": "create", "payload": create_payload, "status": status})
        if status not in (200, 201):
            # Fallbacks for job templates on HTTP 400
            if status == 400 and create_payload.get("type", "") == "":
                # FB1: strip task_params.allow_debug only
                if "task_params" in create_payload and create_payload["task_params"].get("allow_debug"):
                    fb1 = copy.deepcopy(create_payload)
                    fb1["task_params"]["allow_debug"] = False
                    resp_body, status, _ = _post(base_url, fb1, headers, validate_certs)
                    attempts.append({"op": "create-fb1-strip-allow_debug", "payload": fb1, "status": status})
                    if status in (200, 201):
                        create_payload = fb1  # record winning payload

                # FB2: drop surveys and task_params entirely
                if status == 400 and ("survey_vars" in create_payload or "task_params" in create_payload):
                    fb2 = copy.deepcopy(create_payload)
                    fb2.pop("survey_vars", None)
                    fb2.pop("task_params", None)
                    resp_body, status, _ = _post(base_url, fb2, headers, validate_certs)
                    attempts.append({"op": "create-fb2-drop-surveys-task_params", "payload": fb2, "status": status})
                    if status in (200, 201):
                        create_payload = fb2

                # FB3: drop tags/skip_tags/limit from template
                if status == 400:
                    fb3 = copy.deepcopy(create_payload)
                    for k in ("tags", "skip_tags", "limit"):
                        fb3.pop(k, None)
                    resp_body, status, _ = _post(base_url, fb3, headers, validate_certs)
                    attempts.append({"op": "create-fb3-minimal", "payload": fb3, "status": status})
                    if status in (200, 201):
                        create_payload = fb3

        if status in (200, 201):
            text = resp_body.decode() if isinstance(resp_body, (bytes, bytearray)) else resp_body
            created = json.loads(text) if isinstance(text, str) else text

            # If caller passed any prompts, try to PUT them now.
            wants_prompts = any(k in original_tpl for k in PROMPT_KEYS_INPUT)
            if wants_prompts:
                update_payload = {}
                for pk in PROMPT_KEYS_SUPPORTED_ON_PUT:
                    if pk in original_tpl:
                        update_payload[pk] = bool(original_tpl[pk])

                if "allow_parallel_tasks" in original_tpl:
                    update_payload["allow_parallel_tasks"] = bool(original_tpl["allow_parallel_tasks"])

                # Include app & type to satisfy the server
                update_payload["app"] = created.get("app") or original_tpl.get("app", "ansible")
                update_payload["type"] = created.get("type", "")

                put_url = f"{host}:{port}/api/project/{project_id}/templates/{created.get('id')}"
                try:
                    resp_body2, status2, _ = _put(put_url, update_payload, headers, validate_certs)
                    attempts.append({"op": "update-prompts", "payload": update_payload, "status": status2})
                except Exception:
                    module.exit_json(
                        changed=True, template=created, status=status,
                        attempts=attempts,
                        warn="Template created; applying prompts via PUT failed (see attempts).",
                    )

            module.exit_json(changed=True, template=created, status=status, attempts=attempts)

        # Not handled: fail with details from the first response
        text = resp_body.decode() if isinstance(resp_body, (bytes, bytearray)) else str(resp_body)
        module.fail_json(
            msg=f"Failed to create template: HTTP {status} - {text}",
            status=status,
            debug={"url": base_url, "attempts": attempts},
        )

    except Exception as e:
        module.fail_json(msg=str(e), debug={"url": base_url, "attempts": attempts})

if __name__ == '__main__':
    main()
