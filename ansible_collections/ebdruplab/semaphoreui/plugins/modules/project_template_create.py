#!/usr/bin/python
# -*- coding: utf-8 -*-

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
module: project_template_create
short_description: Create a Semaphore template and apply UI-style task_params override flags
version_added: "1.0.0"

description:
  - Creates a Semaphore template in a project.
  - Supports UI-style payloads that include C(task_params.allow_override_*) flags (as observed from the GUI).
  - Optionally maps user-friendly C(prompt_*) keys to C(task_params.allow_override_*) keys.
  - Performs a merge-safe C(GET → merge → PUT) after creation to ensure override flags persist on Semaphore versions
    that ignore them during create or partially persist task_params.

options:
  host:
    type: str
    required: true
    description:
      - Hostname or IP of the Semaphore server, including scheme.
      - 'Example: C(http://localhost) or C(https://semaphore.example.com).'


  port:
    type: int
    required: true
    description:
      - TCP port where Semaphore is listening (typically C(3000)).

  project_id:
    type: int
    required: true
    description:
      - Semaphore project ID.

  template:
    type: dict
    required: true
    description:
      - Template definition to create.
      - The module will normalize IDs, arguments, type, and UI-style override flags.

    suboptions:
      name:
        type: str
        required: true
        description:
          - Template display name.

      playbook:
        type: str
        required: true
        description:
          - Playbook path in the repository.

      repository_id:
        type: int
        required: true
        description:
          - Repository ID containing the playbook.

      inventory_id:
        type: int
        required: true
        description:
          - Inventory ID to associate with the template.

      environment_id:
        type: int
        description:
          - Environment ID (optional).

      view_id:
        type: int
        description:
          - View/board ID (optional).

      type:
        type: str
        choices:
          - ""
          - job
          - deploy
          - build
        description:
          - Template type.
          - Semaphore represents C(job) as an empty string in the API payload; the module normalizes this.

      app:
        type: str
        default: ansible
        description:
          - Application type (typically C(ansible)).

      git_branch:
        type: str
        description:
          - Default Git branch.

      description:
        type: str
        description:
          - Human-readable description.

      arguments:
        type: raw
        description:
          - Template arguments.
          - Semaphore stores this as a JSON string (for example C("[]") or C("[\"-vvv\"]")).
          - If you pass a list/dict/scalar, it will be JSON-encoded.

      allow_override_args_in_task:
        type: bool
        description:
          - Allow overriding C(arguments) at task execution time (Semaphore prompt/override behavior).

      task_params:
        type: dict
        description:
          - UI-style task parameter overrides used at execution time.
          - This module supports and normalizes selected keys that Semaphore GUI is observed to send.

        suboptions:
          allow_override_tags:
            type: bool
            description:
              - Allow overriding tags at task execution time.

          allow_override_skip_tags:
            type: bool
            description:
              - Allow overriding skip-tags at task execution time.

          allow_override_limit:
            type: bool
            description:
              - Allow overriding limit at task execution time.

          allow_override_inventory:
            type: bool
            description:
              - Allow overriding inventory at task execution time (if supported by your Semaphore build).

          tags:
            type: raw
            description:
              - Default tags.
              - Strings are normalized to a single-item list; lists are passed through.

          skip_tags:
            type: raw
            description:
              - Default skip-tags.
              - Strings are normalized to a single-item list; lists are passed through.

          limit:
            type: raw
            description:
              - Default limit.
              - Strings are normalized to a single-item list; lists are passed through.

      prompt_tags:
        type: bool
        description:
          - Convenience flag mapped to C(task_params.allow_override_tags).

      prompt_skip_tags:
        type: bool
        description:
          - Convenience flag mapped to C(task_params.allow_override_skip_tags).

      prompt_limit:
        type: bool
        description:
          - Convenience flag mapped to C(task_params.allow_override_limit).

      prompt_inventory:
        type: bool
        description:
          - Convenience flag mapped to C(task_params.allow_override_inventory).

      prompt_arguments:
        type: bool
        description:
          - Convenience flag mapped to C(allow_override_args_in_task).

  session_cookie:
    type: str
    no_log: true
    description:
      - Semaphore session cookie.

  api_token:
    type: str
    no_log: true
    description:
      - Semaphore API token.

  validate_certs:
    type: bool
    default: true
    description:
      - Validate TLS certificates.

author:
  - Kristian Ebdrup (@kris9854)
'''

EXAMPLES = r'''
- name: Create template with UI-style override flags
  ebdruplab.semaphoreui.project_template_create:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_token }}"
    project_id: 1
    template:
      name: "ff"
      playbook: "f"
      repository_id: 1
      inventory_id: 1
      environment_id: 1
      type: ""
      arguments: "[]"
      task_params:
        allow_override_tags: true
        allow_override_limit: true
        tags: ["t"]
        limit: ["t"]

- name: Create template using convenience prompt_* flags
  ebdruplab.semaphoreui.project_template_create:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_token }}"
    project_id: 1
    template:
      name: "ff"
      playbook: "f"
      repository_id: 1
      inventory_id: 1
      environment_id: 1
      type: ""
      prompt_tags: true
      prompt_limit: true
      prompt_arguments: true
'''

RETURN = r'''
template:
  description: Template object as last applied (merged PUT payload).
  type: dict
  returned: success

status:
  description: HTTP status code from the final API operation.
  type: int
  returned: always

attempts:
  description:
    - List of API operations performed (create, optional get-after-create, update-merge).
  type: list
  returned: always

request:
  description:
    - Payload used for the initial create request (after normalization/pruning).
  type: dict
  returned: always
'''

PROMPT_MAP_TASK_PARAMS = {
    "prompt_tags": "allow_override_tags",
    "prompt_skip_tags": "allow_override_skip_tags",
    "prompt_limit": "allow_override_limit",
    "prompt_inventory": "allow_override_inventory",
}

ALLOWED_CREATE_FIELDS = {
    "project_id",
    "inventory_id",
    "repository_id",
    "environment_id",
    "view_id",
    "name",
    "playbook",
    "arguments",
    "description",
    "app",
    "git_branch",
    "type",
    "allow_override_args_in_task",
    "task_params",
}

ALLOWED_TASK_PARAMS_KEYS = {
    "allow_override_tags",
    "allow_override_skip_tags",
    "allow_override_limit",
    "allow_override_inventory",
    "tags",
    "skip_tags",
    "limit",
}


def as_text(x):
    if x is None:
        return ""
    if isinstance(x, (bytes, bytearray)):
        return x.decode("utf-8", errors="replace")
    return str(x)


def normalize_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "yes", "1", "on")
    if isinstance(val, int):
        return val != 0
    return False


def normalize_int(module, obj, key, required=False):
    if key not in obj or obj.get(key) is None:
        if required:
            module.fail_json(msg=f"Missing required field: template.{key}")
        return
    try:
        iv = int(obj[key])
    except (TypeError, ValueError):
        module.fail_json(msg=f"Invalid integer for template.{key}: {obj[key]!r}")
    if required and iv <= 0:
        module.fail_json(msg=f"template.{key} must be > 0 (got {iv})")
    obj[key] = iv


def normalize_arguments(val):
    if val is None:
        return "[]"
    if isinstance(val, str):
        return val
    return json.dumps(val)


def normalize_type(val):
    if val is None:
        return ""
    if val == "job":
        return ""
    return val


def prune(d, allowed):
    return {k: v for k, v in d.items() if k in allowed}


def normalize_task_params(tp):
    if not isinstance(tp, dict):
        return {}

    out = {}
    for k, v in tp.items():
        if k not in ALLOWED_TASK_PARAMS_KEYS:
            continue

        if k.startswith("allow_override_"):
            out[k] = normalize_bool(v)
            continue

        # tags/skip_tags/limit: GUI commonly sends arrays; normalize string to list
        if isinstance(v, str):
            out[k] = [v]
        elif isinstance(v, list):
            out[k] = v
        else:
            out[k] = v

    return out


def http_post(url, payload, headers, validate):
    return semaphore_post(
        url=url,
        body=json.dumps(payload).encode("utf-8"),
        headers=headers,
        validate_certs=validate,
    )


def http_get(url, headers, validate):
    return semaphore_request(
        "GET",
        url,
        body=None,
        headers=headers,
        validate_certs=validate,
    )


def http_put(url, payload, headers, validate):
    return semaphore_request(
        "PUT",
        url,
        body=json.dumps(payload).encode("utf-8"),
        headers=headers,
        validate_certs=validate,
    )


def apply_prompt_mappings(tpl):
    tp = tpl.get("task_params")
    tp = tp if isinstance(tp, dict) else {}

    if "prompt_arguments" in tpl:
        tpl["allow_override_args_in_task"] = normalize_bool(tpl.pop("prompt_arguments"))

    for pk, tk in PROMPT_MAP_TASK_PARAMS.items():
        if pk in tpl:
            tp[tk] = normalize_bool(tpl.pop(pk))

    tpl["task_params"] = tp
    return tpl


def merge_for_put(server_obj, desired_payload):
    merged = copy.deepcopy(server_obj)

    for k, v in desired_payload.items():
        if k == "task_params":
            merged_tp = merged.get("task_params")
            merged_tp = merged_tp if isinstance(merged_tp, dict) else {}
            v = v if isinstance(v, dict) else {}
            for tk, tv in v.items():
                merged_tp[tk] = tv
            merged["task_params"] = merged_tp
        else:
            merged[k] = v

    merged["app"] = merged.get("app") or desired_payload.get("app") or "ansible"
    merged["type"] = merged.get("type", desired_payload.get("type", ""))
    return merged


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
    host = p["host"].rstrip("/")
    port = p["port"]
    project_id = p["project_id"]

    headers = get_auth_headers(
        session_cookie=p.get("session_cookie"),
        api_token=p.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"

    tpl = copy.deepcopy(p["template"])
    tpl["project_id"] = project_id
    tpl["app"] = tpl.get("app", "ansible")

    normalize_int(module, tpl, "repository_id", required=True)
    normalize_int(module, tpl, "inventory_id", required=True)
    normalize_int(module, tpl, "environment_id", required=False)
    normalize_int(module, tpl, "view_id", required=False)

    tpl["type"] = normalize_type(tpl.get("type", ""))
    tpl["arguments"] = normalize_arguments(tpl.get("arguments"))

    if "allow_override_args_in_task" in tpl:
        tpl["allow_override_args_in_task"] = normalize_bool(tpl["allow_override_args_in_task"])

    tpl = apply_prompt_mappings(tpl)
    tpl["task_params"] = normalize_task_params(tpl.get("task_params"))

    create_payload = prune(tpl, ALLOWED_CREATE_FIELDS)

    base_url = f"{host}:{port}/api/project/{project_id}/templates"
    attempts = []

    resp, status, _ = http_post(base_url, create_payload, headers, p["validate_certs"])
    attempts.append({"op": "create", "status": status, "request": create_payload})

    if status not in (200, 201):
        module.fail_json(
            msg="Template creation failed",
            status=status,
            response=as_text(resp),
            attempts=attempts,
        )

    created = json.loads(as_text(resp))
    tpl_id = created.get("id")
    if not tpl_id:
        module.exit_json(changed=True, status=status, template=created, attempts=attempts, request=create_payload)

    get_url = f"{base_url}/{tpl_id}"
    resp_g, status_g, _ = http_get(get_url, headers, p["validate_certs"])
    attempts.append({"op": "get-after-create", "status": status_g})

    server_obj = created
    if status_g in (200, 201):
        try:
            server_obj = json.loads(as_text(resp_g))
        except Exception:
            server_obj = created

    merged = merge_for_put(server_obj, create_payload)

    resp_u, status_u, _ = http_put(get_url, merged, headers, p["validate_certs"])
    attempts.append({"op": "update-merge", "status": status_u})

    if status_u not in (200, 204):
        module.fail_json(
            msg="Template created but merge update failed",
            status=status_u,
            response=as_text(resp_u),
            attempts=attempts,
        )

    module.exit_json(
        changed=True,
        status=status_u,
        template=merged,
        attempts=attempts,
        request=create_payload,
    )


if __name__ == "__main__":
    main()
