#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_request, get_auth_headers
import json
import copy

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
  - "For job templates (i.e. when C(type) is omitted, C(None), C(\"\"), or C(\"job\")), some Semaphore versions may reject C(task_params), C(arguments), or surveys; this module always drops C(task_params) for job templates and can optionally drop C(arguments) and C(survey_vars) via C(allow_job_arguments) and C(allow_job_surveys)."
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
  allow_job_surveys:
    description:
      - "Whether to include C(survey_vars) when updating job templates (C(type) omitted, C(None), C(\"\") or C(\"job\"))."
      - "If C(false), C(survey_vars) will be dropped from the payload for job templates to avoid API 400 errors on older Semaphore versions."
    type: bool
    default: true
  allow_job_arguments:
    description:
      - "Whether to include C(arguments) when updating job templates (C(type) omitted, C(None), C(\"\") or C(\"job\"))."
      - "If C(false), C(arguments) will be dropped from the payload for job templates to avoid API errors on servers that reject arguments for job templates."
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
      surveyVars:                       # alias of survey_vars (may be dropped for job type if allow_job_surveys is false)
        - { name: "release_version", title: "Release version", type: "string", default: "1.0.0" }


- name: Job template using legacy-safe behavior (drop surveys & arguments)
  ebdruplab.semaphoreui.project_template_update:
    host: http://localhost
    port: 3000
    session_cookie: "{{ login_result.session_cookie }}"
    project_id: 55
    template_id: 228
    allow_job_surveys: false
    allow_job_arguments: false
    template:
      name: "Legacy Job"
      app: "ansible"
      playbook: "playbooks/legacy.yml"
      type: ""
      arguments: ["--verbose"]
      survey_vars:
        - { name: "env", title: "Environment", type: "string", default_value: "dev" }
  register: update_legacy_job
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
attempts:
  description: List of attempts (GET + PUT payloads and fallback PUT payloads).
  type: list
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


def _as_text(b):
    if isinstance(b, (bytes, bytearray)):
        try:
            return b.decode()
        except Exception:
            return str(b)
    return b


def _to_bool(val):
    """
    Safe bool coercion:
      - bool -> bool
      - "true/false/yes/no/1/0" -> bool
      - other strings -> False (conservative)
      - numbers -> bool(val)
      - None -> None (so we can distinguish "unset" from false)
    """
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        s = val.strip().lower()
        if s in ("true", "yes", "y", "1", "on"):
            return True
        if s in ("false", "no", "n", "0", "off", ""):
            return False
        # Unknown string: be conservative
        return False
    return bool(val)


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
    if tp is None:
        return None
    if not isinstance(tp, dict):
        return None

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
        "allow_debug": bool(_to_bool(tp.get("allow_debug", False))),
        "allow_override_inventory": bool(_to_bool(tp.get("allow_override_inventory", False))),
        "allow_override_limit": bool(_to_bool(tp.get("allow_override_limit", False))),
        "allow_override_tags": bool(_to_bool(tp.get("allow_override_tags", False))),
        "allow_override_skip_tags": bool(_to_bool(tp.get("allow_override_skip_tags", False))),
        "tags": _split_to_list(tp.get("tags")),
        "skip_tags": _split_to_list(tp.get("skip_tags")),
        "limit": _split_to_list(tp.get("limit")),
    }
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

        required = bool(_to_bool(sv.get("required", False)))
        desc = sv.get("description", "")
        default_value = sv.get("default_value", None)

        values = None
        if stype_l == "int":
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
            default_value = None
        else:
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


def _apply_aliases(tpl):
    """
    Accept common alternative spellings and camelCase for known fields.
    Maps them to canonical API names and removes the aliases.
    """
    alias_map = {
        "allow_parallel": ["allow_parallel_tasks", "allowParallel", "allowParallelTasks"],
        "allow_override_args_in_task": ["allow_override_args", "allowOverrideArgsInTask", "allowOverrideArgs"],
        "allow_override_branch_in_task": ["allow_override_branch", "allowOverrideBranchInTask", "allowOverrideBranch"],
        "suppress_success_alerts": ["suppress_success_alert", "suppressSuccessAlerts", "suppressSuccessAlert"],
        "autorun": ["auto_run", "autoRun"],

        "git_branch": ["branch", "gitBranch"],
        "start_version": ["startVersion"],
        "skip_tags": ["skipTags"],
        "tags": ["tagList", "tags_list", "tagsList"],
        "arguments": ["args", "extra_args", "extra_cli_args", "cli_args"],
        "limit": ["hosts_limit", "host_limit", "hostsLimit", "hostLimit"],

        "repository_id": ["repositoryId"],
        "inventory_id": ["inventoryId"],
        "environment_id": ["environmentId"],
        "view_id": ["viewId"],
        "build_template_id": ["buildTemplateId"],

        "task_params": ["taskParams"],
        "survey_vars": ["surveyVars", "surveys"],

        "type": ["template_type", "templateType"],
        "app": ["application", "appType"],
        "vault_password": ["vaultPassword"],
    }

    for canon, aliases in alias_map.items():
        for a in aliases:
            if canon not in tpl and a in tpl:
                tpl[canon] = tpl.pop(a)

    if isinstance(tpl.get("survey_vars"), list):
        for sv in tpl["survey_vars"]:
            if isinstance(sv, dict) and "default_value" not in sv and "default" in sv:
                sv["default_value"] = sv.pop("default")


def _prune_none(d):
    return {k: v for k, v in d.items() if v is not None}


def _http_get(url, headers, validate_certs):
    return semaphore_request("GET", url, body=None, headers=headers, validate_certs=validate_certs)


def _http_put(url, payload, headers, validate_certs):
    body = json.dumps(payload).encode("utf-8")
    return semaphore_request("PUT", url, body=body, headers=headers, validate_certs=validate_certs)


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
            allow_job_surveys=dict(type='bool', default=True),
            allow_job_arguments=dict(type='bool', default=True),
        ),
        required_one_of=[['session_cookie', 'api_token']],
        supports_check_mode=False,
    )

    p = module.params
    host = p['host'].rstrip('/')
    port = int(p['port'])
    project_id = int(p['project_id'])
    template_id = int(p['template_id'])
    validate_certs = p['validate_certs']
    allow_job_surveys = p['allow_job_surveys']
    allow_job_arguments = p['allow_job_arguments']

    user_tpl = dict(p['template'] or {})
    original_user_keys = set(user_tpl.keys())

    _apply_aliases(user_tpl)

    headers = get_auth_headers(
        session_cookie=p.get('session_cookie'),
        api_token=p.get('api_token'),
    )
    headers['Content-Type'] = 'application/json'
    headers.setdefault('Accept', 'application/json')

    url = f"{host}:{port}/api/project/{project_id}/templates/{template_id}"
    attempts = []

    # 1) GET existing template (baseline for merge-safe PUT)
    resp_body, status, _ = _http_get(url, headers, validate_certs)
    attempts.append({"op": "get", "status": status, "url": url})

    if status not in (200,):
        module.fail_json(
            msg=f"GET template failed with status {status}: {_as_text(resp_body)}",
            status=status,
            attempts=attempts,
            debug={"url": url},
        )

    existing_text = _as_text(resp_body)
    try:
        existing = json.loads(existing_text) if isinstance(existing_text, str) else existing_text
    except Exception:
        module.fail_json(
            msg="GET returned non-JSON body; cannot safely merge for PUT.",
            status=status,
            attempts=attempts,
            debug={"raw": existing_text},
        )

    if not isinstance(existing, dict):
        module.fail_json(
            msg="GET returned unexpected structure (expected JSON object).",
            status=status,
            attempts=attempts,
            debug={"existing_type": str(type(existing))},
        )

    # 2) Normalize user-provided fields (ONLY those they provided)
    # Required fields for update remain required by your module contract:
    for req in ('name', 'app', 'playbook'):
        if not user_tpl.get(req):
            module.fail_json(msg=f"Missing required template field: {req}")

    # Normalize type (based on user input if provided; otherwise keep existing)
    if "type" in user_tpl or "type" in original_user_keys:
        raw_type = user_tpl.get('type', "")
        norm_type = TYPE_NORMALIZE.get(
            raw_type if raw_type in ("", "job", "deploy", "build", None) else str(raw_type).lower(),
            None
        )
        if norm_type is None:
            module.fail_json(msg="template.type must be one of '', job, deploy, build (or omit/None).")
        user_tpl['type'] = norm_type

    # Coerce integer fields only if user provided them
    for key in ('repository_id', 'inventory_id', 'environment_id', 'view_id', 'build_template_id'):
        if key in user_tpl:
            coerced = _int_or_none(user_tpl.get(key))
            if coerced is None and key in ('repository_id', 'inventory_id'):
                module.fail_json(msg=f"{key} must be an integer")
            if coerced is None:
                user_tpl.pop(key, None)
            else:
                user_tpl[key] = coerced

    # Normalize arguments if user provided them
    if "arguments" in user_tpl:
        user_tpl["arguments"] = _normalize_arguments(user_tpl.get("arguments"))

    # Normalize tags/skip_tags if user provided them
    if "tags" in user_tpl:
        tags = _normalize_tag_block(user_tpl.get("tags"))
        if tags is None:
            user_tpl.pop("tags", None)
        else:
            user_tpl["tags"] = tags

    if "skip_tags" in user_tpl:
        skip_tags = _normalize_tag_block(user_tpl.get("skip_tags"))
        if skip_tags is None:
            user_tpl.pop("skip_tags", None)
        else:
            user_tpl["skip_tags"] = skip_tags

    if "limit" in user_tpl and user_tpl["limit"] is not None:
        user_tpl["limit"] = str(user_tpl["limit"])

    # Normalize task_params only if user provided it
    if "task_params" in user_tpl:
        user_tpl["task_params"] = _normalize_task_params(user_tpl.get("task_params"))

    # Normalize survey_vars only if user provided it
    if "survey_vars" in user_tpl:
        user_tpl["survey_vars"] = _validate_and_normalize_surveys(user_tpl.get("survey_vars"), module)

    # Normalize vaults only if user provided it
    if "vaults" in user_tpl:
        norm_vaults = _validate_and_normalize_vaults(user_tpl.get("vaults"), module)
        if norm_vaults:
            user_tpl["vaults"] = norm_vaults
        else:
            user_tpl.pop("vaults", None)

    # Normalize booleans only if user provided them.
    bool_keys = [
        'allow_override_args_in_task',
        'allow_override_branch_in_task',
        'allow_parallel',
        'suppress_success_alerts',
        'autorun',
    ] + PROMPT_KEYS

    for bk in bool_keys:
        if bk in user_tpl:
            bval = _to_bool(user_tpl.get(bk))
            # Preserve explicit None? For bools, treat None as "unset" and drop.
            if bval is None:
                user_tpl.pop(bk, None)
            else:
                user_tpl[bk] = bval

    # 3) Merge user changes into existing object (full PUT semantics)
    merged = copy.deepcopy(existing)

    # Ensure IDs match URL
    merged["id"] = template_id
    merged["project_id"] = project_id

    # Apply user-provided fields onto merged
    # IMPORTANT: Only apply prompt_* if user explicitly provided them
    for k, v in user_tpl.items():
        if k in PROMPT_KEYS and k not in original_user_keys and k not in user_tpl:
            # Defensive; should never hit due to dict iteration
            continue
        merged[k] = v

    # Keep allow_parallel alias stable
    if "allow_parallel_tasks" in merged:
        merged.pop("allow_parallel_tasks", None)

    # If user did NOT provide prompt keys, ensure we do not accidentally null them
    # (merge already protects this as we start from existing)

    # 4) Job-type compatibility handling (apply AFTER merge)
    eff_type = merged.get("type", "")
    if eff_type is None:
        eff_type = ""
    if str(eff_type).lower() == "job":
        eff_type = ""
    merged["type"] = eff_type

    # For job templates: optionally drop surveys/arguments based on module flags
    # BUT do not drop unless the user was trying to set them or options require it.
    if merged.get("type", "") == "":
        if not allow_job_surveys and "survey_vars" in merged:
            merged.pop("survey_vars", None)
        if not allow_job_arguments and "arguments" in merged:
            merged.pop("arguments", None)

    merged = _prune_none(merged)

    # 5) PUT (with fallback strategy if the server rejects some fields)
    def do_put(payload, op):
        rb, st, _ = _http_put(url, payload, headers, validate_certs)
        attempts.append({"op": op, "status": st, "url": url, "payload": payload})
        return rb, st

    resp2, status2 = do_put(merged, "put-merged")

    # Fallbacks primarily for older servers rejecting job-template extras
    if status2 == 400 and merged.get("type", "") == "":
        # FB1: drop task_params
        fb1 = copy.deepcopy(merged)
        fb1.pop("task_params", None)
        resp2, status2 = do_put(fb1, "put-fb1-drop-task_params")

        # FB2: also drop survey_vars
        if status2 == 400:
            fb2 = copy.deepcopy(fb1)
            fb2.pop("survey_vars", None)
            resp2, status2 = do_put(fb2, "put-fb2-drop-survey_vars")

        # FB3: also drop arguments
        if status2 == 400:
            fb3 = copy.deepcopy(fb2)
            fb3.pop("arguments", None)
            resp2, status2 = do_put(fb3, "put-fb3-drop-arguments")

    if status2 not in (200, 201, 204):
        module.fail_json(
            msg=f"PUT failed with status {status2}: {_as_text(resp2)}",
            status=status2,
            attempts=attempts,
            debug={
                "url": url,
                "url_project_id": project_id,
                "url_template_id": template_id,
            },
        )

    if status2 == 204 or not resp2:
        module.exit_json(changed=True, template={}, status=status2, attempts=attempts)

    text = _as_text(resp2)
    try:
        result = json.loads(text) if isinstance(text, str) else text
    except Exception:
        result = {"raw": text}

    module.exit_json(changed=True, template=result, status=status2, attempts=attempts)


if __name__ == '__main__':
    main()