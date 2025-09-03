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
  - "Updates an existing template in a specified Semaphore project."
  - "Ensures the body contains C(id) and C(project_id) matching the URL params."
  - "Coerces numeric identifiers to integers, normalizes C(arguments) to a JSON string, joins list-style tags with newlines, and prunes null fields."
  - "Supports C(task_params) (including list C(tags), C(skip_tags), C(limit)), and validates/normalizes C(survey_vars)."
  - "Accepts common aliases (camelCase & legacy names) and maps them to canonical API fields, e.g. C(allow_parallel_tasks) -> C(allow_parallel)."
  - "For job templates (i.e. when C(type) is omitted, C(None), C(\"\"), or C(\"job\")), Semaphore may reject C(task_params) and surveys; this module drops those to avoid API 400 errors."
  - "On update, C(vaults) entries can include C(id), C(name), C(type), C(vault_key_id), and C(script). If the list is empty or undefined, the field is omitted to avoid API errors."

options:
  host:
    description:
      - "Hostname or IP of the Semaphore server (including protocol)."
      - "Example: C(http://localhost) or C(https://semaphore.example.com)"
    type: str
    required: true
  port:
    description:
      - "Port of the Semaphore server (typically C(3000))."
    type: int
    required: true
  project_id:
    description:
      - "ID of the project the template belongs to."
    type: int
    required: true
  template_id:
    description:
      - "ID of the template to update."
    type: int
    required: true
  template:
    description:
      - "Template payload with updated fields that should be applied to the existing template."
    type: dict
    required: true
    suboptions:
      name:
        description: "Human-readable template name."
        type: str
        required: true
      app:
        description: "Application type (for example, C(ansible))."
        type: str
        required: true
      playbook:
        description: "Path to the playbook within the repository."
        type: str
        required: true
      id:
        description: "Template ID; will be set automatically from C(template_id)."
        type: int
      project_id:
        description: "Project ID; will be set automatically from C(project_id)."
        type: int
      repository_id:
        description: "Repository ID that the template uses."
        type: int
      inventory_id:
        description: "Inventory ID used by the template."
        type: int
      environment_id:
        description: "Environment ID associated with the template."
        type: int
      view_id:
        description: "Board View ID used for organizing templates."
        type: int
      build_template_id:
        description: "Build template ID used in build pipelines."
        type: int
      type:
        description: "One of C(job), C(deploy), C(build) or empty string; API represents C(job) as an empty string."
        type: str
        choices: ["", "job", "deploy", "build"]
      description:
        description: "Human-friendly description for the template."
        type: str
      git_branch:
        description: "Default Git branch to use when running the template."
        type: str
      limit:
        description: "Ansible limit (string form) at template level."
        type: str
      tags:
        description: "Newline-delimited string of tags; if a list is provided it will be joined with newlines."
        type: raw
      skip_tags:
        description: "Newline-delimited string of skip-tags; if a list is provided it will be joined with newlines."
        type: raw
      vault_password:
        description: "Ansible Vault password value."
        type: str
      start_version:
        description: "Starting version (required by API for C(type=build))."
        type: str
      allow_override_args_in_task:
        description: "Allow overriding arguments at task start."
        type: bool
      allow_override_branch_in_task:
        description: "Allow overriding Git branch at task start."
        type: bool
      allow_parallel_tasks:
        description: "Alias accepted by this module; will be sent to API as C(allow_parallel)."
        type: bool
      suppress_success_alerts:
        description: "If true, suppress success alerts for tasks started from this template."
        type: bool
      autorun:
        description: "If true, automatically run newly created tasks for this template."
        type: bool
      prompt_inventory:
        description: "Prompt for inventory when starting a task (may be ignored by some servers)."
        type: bool
      prompt_limit:
        description: "Prompt for limit when starting a task (may be ignored by some servers)."
        type: bool
      prompt_tags:
        description: "Prompt for tags when starting a task (may be ignored by some servers)."
        type: bool
      prompt_skip_tags:
        description: "Prompt for skip-tags when starting a task (may be ignored by some servers)."
        type: bool
      prompt_vault_password:
        description: "Prompt for Vault password when starting a task (often unsupported; sent for completeness)."
        type: bool
      prompt_arguments:
        description: "Prompt for arguments when starting a task (may be ignored by some servers)."
        type: bool
      prompt_branch:
        description: "Prompt for branch when starting a task (may be ignored by some servers)."
        type: bool
      prompt_environment:
        description: "Prompt for environment when starting a task (often unsupported; sent for completeness)."
        type: bool
      arguments:
        description:
          - "Arguments as the UI stores them (JSON string)."
          - "Lists/dicts will be JSON-encoded; scalars are wrapped into a single-element JSON list."
          - "Defaults to C(\"[]\") when omitted or empty."
        type: raw
      task_params:
        description:
          - "Task parameter overrides. For job templates, some servers reject this on update; the module may omit it."
        type: dict
        suboptions:
          allow_debug:
            description: "Allow debug mode for tasks created from this template."
            type: bool
          allow_override_inventory:
            description: "Allow overriding inventory at task start."
            type: bool
          allow_override_limit:
            description: "Allow overriding limit at task start."
            type: bool
          allow_override_tags:
            description: "Allow overriding tags at task start."
            type: bool
          allow_override_skip_tags:
            description: "Allow overriding skip-tags at task start."
            type: bool
          tags:
            description: "Task-level labels; may be string (comma- or newline-delimited) or list of strings."
            type: raw
          skip_tags:
            description: "Task-level skip-tags; may be string (comma- or newline-delimited) or list of strings."
            type: raw
          limit:
            description: "Task-level limit hosts; may be string (comma- or newline-delimited) or list of strings."
            type: raw
      vaults:
        description:
          - "List of vault references attached to the template."
          - "On update, you may include existing items by C(id) and/or specify new ones via C(vault_key_id)."
        type: list
        elements: dict
        suboptions:
          id:
            description: "Existing vault attachment ID (when referring to an already attached item)."
            type: int
          name:
            description: "Optional display name for the vault attachment."
            type: str
          type:
            description: "Vault reference type (password, key, or script)."
            type: str
            choices: [password, key, script]
            required: true
          vault_key_id:
            description: "ID of the vault key in Semaphore (required for password/key types when adding new attachments)."
            type: int
          script:
            description: "Script content or reference (used when C(type=script)); server-specific behavior."
            type: raw
      survey_vars:
        description:
          - "Survey definitions shown when starting a task."
          - "API expects C(type) to be one of C(string), C(int), C(secret), or C(enum). C(integer)/C(number) are mapped to C(int)."
        type: list
        elements: dict
        suboptions:
          name:
            description: "Internal variable name for the survey field."
            type: str
            required: true
          title:
            description: "Human-friendly label shown in the survey dialog."
            type: str
            required: true
          description:
            description: "Help text displayed under the field."
            type: str
          type:
            description: "Field type for this survey variable."
            type: str
            choices: [string, int, secret, enum]
            required: true
          required:
            description: "Whether the value must be provided by the user."
            type: bool
            default: false
          default_value:
            description: "Default value for the field (not used for C(secret) fields)."
            type: raw
          values:
            description: "Only for C(enum) fields; list of selectable name/value pairs."
            type: list
            elements: dict
            suboptions:
              name:
                description: "Display name for the enum option."
                type: str
                required: true
              value:
                description: "Submitted value for the enum option."
                type: raw
                required: true

  session_cookie:
    description: "Session cookie for authentication."
    type: str
    required: false
    no_log: true
  api_token:
    description: "API token for authentication."
    type: str
    required: false
    no_log: true
  validate_certs:
    description: "Whether to validate TLS certificates."
    type: bool
    default: true

author:
  - "Kristian Ebdrup (@kris9854)"
"""



EXAMPLES = r"""
- name: Update a JOB template (type is empty string), set prompts & tags
  ebdruplab.semaphoreui.project_template_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 55
    template_id: 223
    template:
      name: "Example Playbook"
      app: "ansible"
      playbook: "playbooks/pb-semaphore-example.yml"
      type: ""                     # job -> API uses empty string
      description: "Updated description"
      git_branch: "main"
      limit: "localhost"
      tags: ["setup", "init"]      # will be joined into newline-separated string
      skip_tags: ["db"]
      allow_parallel_tasks: true   # alias; module sends as allow_parallel
      prompt_inventory: true
      prompt_limit: true
      prompt_tags: true
      prompt_skip_tags: true
      prompt_arguments: true
      prompt_branch: true
  register: update_job


- name: Update a DEPLOY template with task_params and surveys
  ebdruplab.semaphoreui.project_template_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 55
    template_id: 224
    template:
      name: "Deploy Service"
      app: "ansible"
      playbook: "playbooks/deploy.yml"
      type: "deploy"
      description: "Deploys the service"
      git_branch: "release"
      tags: ["deploy", "web"]
      task_params:
        allow_debug: true
        allow_override_inventory: false
        allow_override_limit: false
        allow_override_tags: false
        allow_override_skip_tags: false
        tags: ["canary", "blue-green"]   # task-level labels
        skip_tags: "db,cache"            # string accepted; module normalizes
        limit: ["web01", "web02"]        # string/list accepted; module normalizes
      survey_vars:
        - name: "target_env"
          title: "Target environment"
          type: "enum"
          required: true
          values:
            - { name: "dev",  value: "dev" }
            - { name: "prod", value: "prod" }
  register: update_deploy


- name: Update a BUILD template with start_version and vaults
  ebdruplab.semaphoreui.project_template_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 55
    template_id: 225
    template:
      name: "Build Artifact"
      app: "ansible"
      playbook: "playbooks/build.yml"
      type: "build"
      description: "Builds the application artifact"
      start_version: "1.0.0.1"
      git_branch: "release"
      arguments: '["--no-cache"]'        # JSON string or list accepted
      tags: "ci\nbuild"                  # already newline-delimited
      vaults:
        - id: 555                        # keep existing vault attachment
          type: password
          name: "Existing Project Vault"
        - type: password                 # add a new vault attachment
          vault_key_id: 469
          name: "Project Vault Password"
        - type: script                   # script-style attachment (server-specific behavior)
          name: "extension-client"
          script: "extension-client"
  register: update_build


- name: Update using API token instead of session cookie (minimal patch)
  ebdruplab.semaphoreui.project_template_update:
    host: https://semaphore.example.com
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 55
    template_id: 226
    template:
      name: "Ops Playbook"
      app: "ansible"
      playbook: "playbooks/ops.yml"
      tags: ["ops", "maintenance"]
      skip_tags: "slow,expensive"
  register: update_token_auth


- name: Update with camelCase aliases (module maps to canonical API fields)
  ebdruplab.semaphoreui.project_template_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 55
    template_id: 227
    template:
      name: "Example With Aliases"
      app: "ansible"
      playbook: "playbooks/pb.yml"
      type: ""
      allowParallelTasks: true          # alias of allow_parallel
      gitBranch: "main"                 # alias of git_branch
      taskParams:                       # alias of task_params (ignored for job type)
        allowDebug: true
        tagsList: ["audit"]
      surveyVars:                       # alias of survey_vars (ignored for job type)
        - { name: "release_version", title: "Release version", type: "string", default: "1.0.0" }
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
VAULT_TYPES = {"password", "key", "script"}

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
    """
    Accept list or string and normalize to newline-delimited string as expected by the API.
    Strings with commas are split, whitespace is trimmed, and empty entries removed.
    """
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        items = [str(x).strip() for x in v if str(x).strip()]
    else:
        text = str(v).replace(",", "\n")
        items = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(items) if items else None

def _split_to_list(v):
    """
    Accept list or string and normalize to list[str].
    For strings, split on commas and newlines, trim whitespace, drop empties.
    """
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if str(x).strip()]
    text = str(v).replace(",", "\n")
    return [ln.strip() for ln in text.splitlines() if ln.strip()]

def _normalize_task_params(tp):
    if not isinstance(tp, dict):
        return None
    # accept aliases inside task_params
    tp = dict(tp)
    tp_alias_map = {
        "allow_debug": ["allowDebug"],
        "allow_override_inventory": ["allowOverrideInventory"],
        "allow_override_limit": ["allowOverrideLimit"],
        "allow_override_tags": ["allowOverrideTags"],
        "allow_override_skip_tags": ["allowOverrideSkipTags"],
        "tags": ["tagList", "tags_list", "tagsList"],
        "skip_tags": ["skipTags"],
        "limit": ["hosts", "hostList", "limits"],
    }
    for canon, aliases in tp_alias_map.items():
        for a in aliases:
            if canon not in tp and a in tp:
                tp[canon] = tp.pop(a)

    out = {
        "allow_debug": bool(tp.get("allow_debug", False)),
        "allow_override_inventory": bool(tp.get("allow_override_inventory", False)),
        "allow_override_limit": bool(tp.get("allow_override_limit", False)),
        "allow_override_tags": bool(tp.get("allow_override_tags", False)),
        "allow_override_skip_tags": bool(tp.get("allow_override_skip_tags", False)),
        "tags": _split_to_list(tp.get("tags")),
        "skip_tags": _split_to_list(tp.get("skip_tags")),
        "limit": _split_to_list(tp.get("limit")),
    }
    return out

def _merge_template_blocks_into_task_params(tpl):
    """
    If template-level limit/tags/skip_tags exist, ensure task_params has list-form defaults.
    This helps when servers only respect list-style values under task_params.
    """
    tp = _normalize_task_params(tpl.get("task_params") or {})
    # Only inject when missing/empty
    if not tp.get("limit"):
        tp["limit"] = _split_to_list(tpl.get("limit"))
    if not tp.get("tags"):
        tp["tags"] = _split_to_list(tpl.get("tags"))
    if not tp.get("skip_tags"):
        tp["skip_tags"] = _split_to_list(tpl.get("skip_tags"))
    return tp

def _validate_and_normalize_surveys(svars, module):
    if svars is None:
        return None
    if not isinstance(svars, list):
        module.fail_json(msg="template.survey_vars must be a list when provided.")
    out = []
    for idx, sv in enumerate(svars, 1):
        if not isinstance(sv, dict):
            module.fail_json(msg=f"survey_vars[{idx}] must be a dict")

        # alias: default -> default_value
        if "default_value" not in sv and "default" in sv:
            sv["default_value"] = sv.get("default")

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

        values = None
        if stype_l == "int":
            # Many server builds store int defaults as STRING values (e.g., "5"), not numeric.
            if default_value is not None:
                try:
                    default_value = str(int(default_value))
                except Exception:
                    module.fail_json(msg=f"survey_vars[{idx}].default_value must be integer-compatible")
        elif stype_l == "string":
            if default_value is not None and not isinstance(default_value, (str, int, float)):
                module.fail_json(msg=f"survey_vars[{idx}].default_value must be scalar")
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
    if vaults is None:
        return None
    if not isinstance(vaults, list):
        module.fail_json(msg="template.vaults must be a list when provided.")
    validated = []
    for i, v in enumerate(vaults, 1):
        if not isinstance(v, dict):
            module.fail_json(msg=f"template.vaults[{i}] must be a dict.")

        # nested alias: vaultKeyId -> vault_key_id
        if "vault_key_id" not in v and "vaultKeyId" in v:
            v["vault_key_id"] = v.pop("vaultKeyId")

        vtype = v.get("type")
        if not isinstance(vtype, str) or vtype not in VAULT_TYPES:
            module.fail_json(msg=f"template.vaults[{i}].type must be one of {sorted(VAULT_TYPES)}")

        item = {"type": vtype}

        vid = _int_or_none(v.get("id"))
        if vid is not None:
            item["id"] = vid

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

def _apply_aliases(tpl):
    """
    Accept common alternative spellings and camelCase for known fields.
    Maps them to canonical API names and removes the aliases.
    """
    alias_map = {
        # booleans / toggles
        "allow_parallel": ["allow_parallel_tasks", "allowParallel", "allowParallelTasks"],
        "allow_override_args_in_task": ["allow_override_args", "allowOverrideArgsInTask", "allowOverrideArgs"],
        "allow_override_branch_in_task": ["allow_override_branch", "allowOverrideBranchInTask", "allowOverrideBranch"],
        "suppress_success_alerts": ["suppress_success_alert", "suppressSuccessAlerts", "suppressSuccessAlert"],
        "autorun": ["auto_run", "autoRun"],

        # strings / ids
        "git_branch": ["branch", "gitBranch"],
        "start_version": ["startVersion"],
        "skip_tags": ["skipTags"],
        "tags": ["tagList", "tags_list", "tagsList"],
        "arguments": ["args", "extra_args", "extra_cli_args", "cli_args"],
        "limit": ["hosts_limit", "host_limit", "hostsLimit", "hostLimit"],

        # ids
        "repository_id": ["repositoryId"],
        "inventory_id": ["inventoryId"],
        "environment_id": ["environmentId"],
        "view_id": ["viewId"],
        "build_template_id": ["buildTemplateId"],

        # nested objects
        "task_params": ["taskParams"],
        "survey_vars": ["surveyVars", "surveys"],

        # misc
        "type": ["template_type", "templateType"],
        "app": ["application", "appType"],
        "vault_password": ["vaultPassword"],
    }

    for canon, aliases in alias_map.items():
        for a in aliases:
            if canon not in tpl and a in tpl:
                tpl[canon] = tpl.pop(a)

    # Nested: task_params
    if isinstance(tpl.get("task_params"), dict):
        tp = tpl["task_params"]
        tp_alias_map = {
            "allow_debug": ["allowDebug"],
            "allow_override_inventory": ["allowOverrideInventory"],
            "allow_override_limit": ["allowOverrideLimit"],
            "allow_override_tags": ["allowOverrideTags"],
            "allow_override_skip_tags": ["allowOverrideSkipTags"],
            "tags": ["tagList", "tags_list", "tagsList"],
            "skip_tags": ["skipTags"],
            "limit": ["hosts", "hostList", "limits"],
        }
        for canon, aliases in tp_alias_map.items():
            for a in aliases:
                if canon not in tp and a in tp:
                    tp[canon] = tp.pop(a)
        tpl["task_params"] = tp

    # Nested: survey_vars
    if isinstance(tpl.get("survey_vars"), list):
        for sv in tpl["survey_vars"]:
            if isinstance(sv, dict) and "default_value" not in sv and "default" in sv:
                sv["default_value"] = sv.pop("default")

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

    # Accept common aliases before validations
    _apply_aliases(tpl)

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

    # Arguments & tag blocks (template-level)
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

    if 'limit' in tpl and tpl['limit'] is not None:
        # keep as plain string for the template; task_params will get list form
        tpl['limit'] = str(tpl['limit'])

    # task_params (ensure list-form tags/skip_tags/limit)
    # NOTE: many servers only respect list-style values inside task_params during runs.
    if 'task_params' in tpl:
        tpl['task_params'] = _merge_template_blocks_into_task_params(tpl)
    else:
        # If user didn't pass task_params, still derive them from template-level blocks so they stick.
        derived_tp = _merge_template_blocks_into_task_params(tpl)
        # only include if any list is non-empty or any allow_* flag is present
        if any(derived_tp.get(k) for k in ('tags', 'skip_tags', 'limit')) or any(
            derived_tp.get(k) for k in (
                'allow_debug','allow_override_inventory','allow_override_limit',
                'allow_override_tags','allow_override_skip_tags'
            )
        ):
            tpl['task_params'] = derived_tp

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

    # Booleans (normalize both canonical & legacy names)
    for bkey in [
        'allow_override_args_in_task',
        'allow_override_branch_in_task',
        'allow_parallel',           # canonical
        'allow_parallel_tasks',     # alias (will be mapped below)
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

    # Prefer canonical allow_parallel if both variants exist
    if 'allow_parallel' not in tpl and 'allow_parallel_tasks' in tpl:
        tpl['allow_parallel'] = tpl.pop('allow_parallel_tasks')
    else:
        tpl.pop('allow_parallel_tasks', None)

    # Drop false-y prompt_* flags
    _drop_falsey_prompts(tpl)

    # IMPORTANT: job-type quirks
    if tpl.get('type', '') == "":
        tpl.pop('task_params', None)
        tpl.pop('survey_vars', None)  # some servers reject surveys for job-type on update
        # keep allow_parallel (API represents job as "" but accepts allow_parallel)

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
