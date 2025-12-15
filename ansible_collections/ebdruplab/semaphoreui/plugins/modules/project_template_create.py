#!/usr/bin/python
# -*- coding: utf-8 -*-
# MIT License

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
short_description: Create a Semaphore template and reliably apply prompt flags
version_added: "1.0.0"
description:
  - Creates a Semaphore template.
  - Applies prompt_* flags using a full PUT update to avoid GUI state reversion.
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
  session_cookie:
    type: str
    no_log: true
  api_token:
    type: str
    no_log: true
  validate_certs:
    type: bool
    default: true
author:
  - Kristian Ebdrup (@kris9854)
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
