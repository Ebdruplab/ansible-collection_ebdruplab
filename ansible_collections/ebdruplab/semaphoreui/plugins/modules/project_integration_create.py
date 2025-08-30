#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Kristian Ebdrup
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

DOCUMENTATION = r"""
---
module: project_integration_create
short_description: Create a Semaphore project integration
version_added: "2.0.0"
description:
  - "Creates an integration under a Semaphore project that triggers a template."
  - "Auth methods can be provided as UI labels (e.g. C(GitHub Webhooks)) or API slugs (e.g. C(github_webhooks), C(github))."
  - "C(auth_header) applies only to C(Token) and C(HMAC); defaults to C(token) for Token and C(X-Hub-Signature-256) for HMAC if omitted."
  - "C(searchable) is always sent as C(false)."
  - "C(task_params.debug_level) is always C(4); module preserves optional C(environment) and C(params) if provided."
options:
  host:
    description:
      - "Base URL (scheme + host) of the Semaphore server, e.g. C(http://localhost)."
    type: str
    required: true
  port:
    description:
      - "Port where the Semaphore API is exposed, e.g. C(3000)."
    type: int
    required: true
  project_id:
    description:
      - "ID of the project that will own the integration."
    type: int
    required: true
  integration:
    description:
      - "Integration definition to create."
    type: dict
    required: true
    suboptions:
      name:
        description:
          - "Human-readable name for the integration."
        type: str
        required: true
      template_id:
        description:
          - "ID of the template to trigger when the integration matches."
        type: int
        required: true
      auth_method:
        description:
          - "Authentication method to use (UI label or API slug)."
        type: str
        choices:
          - "None"
          - "GitHub Webhooks"
          - "Bitbucket Webhooks"
          - "Token"
          - "HMAC"
          - "BasicAuth"
          - "none"
          - "github"
          - "github_webhooks"
          - "bitbucket"
          - "bitbucket_webhooks"
          - "token"
          - "hmac"
          - "basic"
      auth_header:
        description:
          - "HTTP header that carries the auth secret. Only used for C(Token) and C(HMAC)."
        type: str
      auth_secret_id:
        description:
          - "ID of the secret used by the selected auth method."
        type: int
      task_params:
        description:
          - "Task flags. C(debug_level) is forced to C(4) by this module; C(environment) and C(params) are preserved."
        type: dict
        suboptions:
          diff:
            description:
              - "Show diffs in task output."
            type: bool
            default: false
          dry_run:
            description:
              - "Run in check mode (no changes)."
            type: bool
            default: false
          environment:
            description:
              - "JSON string or object passed to the task environment. Dicts/lists are JSON-encoded automatically."
            type: raw
          params:
            description:
              - "Arbitrary parameters object passed to the task."
            type: dict
  session_cookie:
    description:
      - "Session cookie for authentication. Use this or C(api_token)."
    type: str
    required: false
    no_log: true
  api_token:
    description:
      - "API token for authentication. Use this or C(session_cookie)."
    type: str
    required: false
    no_log: true
  validate_certs:
    description:
      - "Whether to validate TLS certificates when using HTTPS."
    type: bool
    default: true
author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
- name: Create integration (GitHub webhooks)
  ebdruplab.semaphoreui.project_integration_create:
    host: http://localhost
    port: 3000
    api_token: "{{ semaphore_api_token }}"
    project_id: 55
    integration:
      name: "Example Integration"
      template_id: 49
      auth_method: "GitHub Webhooks"   # also accepts "github" or "github_webhooks"
      auth_secret_id: 251
      task_params:
        diff: false
        dry_run: false
        environment: {}               # can be dict or JSON string
        params: {}                    # optional

- name: Create integration (Token header)
  ebdruplab.semaphoreui.project_integration_create:
    host: http://localhost
    port: 3000
    session_cookie: "{{ semaphore_session_cookie }}"
    project_id: 55
    integration:
      name: "Token-trigger"
      template_id: 49
      auth_method: "token"            # UI: "Token" also works
      auth_secret_id: 251
      auth_header: "X-Auth-Token"     # default would be "token"
"""

RETURN = r"""
integration:
  description: "Created integration object returned by the API."
  type: dict
  returned: success
status:
  description: "HTTP status code (201 or 200 on success)."
  type: int
  returned: always
"""

# UI label -> API slug
AUTH_MAP = {
    "None": "none",
    "GitHub Webhooks": "github_webhooks",
    "Bitbucket Webhooks": "bitbucket_webhooks",
    "Token": "token",
    "HMAC": "hmac",
    "BasicAuth": "basic",
}

# Accept common slugs/aliases too
AUTH_SLUGS = {
    "none": "none",
    "github": "github_webhooks",
    "github_webhooks": "github_webhooks",
    "bitbucket": "bitbucket_webhooks",
    "bitbucket_webhooks": "bitbucket_webhooks",
    "token": "token",
    "hmac": "hmac",
    "basic": "basic",
}

VALID_AUTH = set(AUTH_MAP.values())

def _normalize_task_params(tp):
    """
    Keep debug_level at 4, preserve diff/dry_run, and pass through environment/params.
    If environment is a dict/list, JSON-encode it (API often expects stringified JSON).
    """
    tp = tp or {}
    out = {
        "debug_level": 4,
        "diff": bool(tp.get("diff", False)),
        "dry_run": bool(tp.get("dry_run", False)),
    }

    if "environment" in tp:
        env = tp["environment"]
        if isinstance(env, (dict, list)):
            out["environment"] = json.dumps(env)
        else:
            out["environment"] = env  # assume user passed a string already

    if "params" in tp:
        out["params"] = tp["params"]

    return out

def _coerce_int(module, obj, key):
    if key in obj and obj[key] is not None:
        try:
            obj[key] = int(obj[key])
        except Exception:
            module.fail_json(msg=f"integration.{key} must be an integer")

def _normalize_auth_method(module, value):
    if value is None:
        return None

    # UI label?
    if value in AUTH_MAP:
        return AUTH_MAP[value]

    # slug/alias?
    if value in AUTH_SLUGS:
        return AUTH_SLUGS[value]

    # already a slug that's valid?
    if value in VALID_AUTH:
        return value

    module.fail_json(msg=f"Unsupported auth_method: {value}")

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            port=dict(type="int", required=True),
            project_id=dict(type="int", required=True),
            integration=dict(
                type="dict",
                required=True,
                options=dict(
                    name=dict(type="str", required=True),
                    template_id=dict(type="int", required=True),
                    auth_method=dict(type="str", required=False,
                                     choices=list(AUTH_MAP.keys()) + list(AUTH_SLUGS.keys())),
                    auth_header=dict(type="str", required=False),
                    auth_secret_id=dict(type="int", required=False),
                    task_params=dict(
                        type="dict",
                        required=False,
                        options=dict(
                            diff=dict(type="bool", required=False, default=False),
                            dry_run=dict(type="bool", required=False, default=False),
                            environment=dict(type="raw", required=False),
                            params=dict(type="dict", required=False),
                        ),
                    ),
                ),
            ),
            session_cookie=dict(type="str", required=False, no_log=True),
            api_token=dict(type="str", required=False, no_log=True),
            validate_certs=dict(type="bool", default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False,
    )

    host = module.params["host"].rstrip("/")
    port = module.params["port"]
    project_id = module.params["project_id"]
    validate_certs = module.params["validate_certs"]

    integ = dict(module.params["integration"] or {})
    integ["project_id"] = project_id
    integ["searchable"] = False  # always false

    # Coerce numeric IDs early
    _coerce_int(module, integ, "template_id")
    _coerce_int(module, integ, "auth_secret_id")

    # Normalize auth method (accept UI labels or slugs)
    if "auth_method" in integ and integ["auth_method"] is not None:
        integ["auth_method"] = _normalize_auth_method(module, integ["auth_method"])

    # Only keep/use auth_header for token/hmac; set smarter defaults
    if integ.get("auth_method") in ("token", "hmac"):
        default_header = "X-Hub-Signature-256" if integ["auth_method"] == "hmac" else "token"
        integ["auth_header"] = integ.get("auth_header", default_header)
    else:
        integ.pop("auth_header", None)

    # Task params with enforced defaults + pass-through
    integ["task_params"] = _normalize_task_params(integ.get("task_params"))

    # Endpoint
    url = f"{host}:{port}/api/project/{project_id}/integrations"

    headers = get_auth_headers(
        session_cookie=module.params.get("session_cookie"),
        api_token=module.params.get("api_token"),
    )
    headers["Content-Type"] = "application/json"
    headers.setdefault("Accept", "application/json")

    try:
        body = json.dumps(integ).encode("utf-8")
        response_body, status, _ = semaphore_post(
            url=url, body=body, headers=headers, validate_certs=validate_certs
        )

        # Success typically 201 or 200 (some servers may return 201 Created; others 200 OK with body)
        if status not in (200, 201):
            text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else str(response_body)
            module.fail_json(msg=f"Failed to create integration: HTTP {status} - {text}", status=status)

        text = response_body.decode() if isinstance(response_body, (bytes, bytearray)) else response_body
        try:
            integration_obj = json.loads(text) if isinstance(text, str) else text
        except Exception:
            integration_obj = {"raw": text}

        module.exit_json(changed=True, integration=integration_obj, status=status)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
