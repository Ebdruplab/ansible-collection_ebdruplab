#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 ebdruplab
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
import subprocess
import json

DOCUMENTATION = r"""
---
module: doc_lint
short_description: Lint Ansible module/role documentation using ansible-doc
version_added: "1.0.0"
description:
  - Invoke `ansible-doc --json` on a specified module or role and verify that required documentation fields exist.
  - Checks that the JSON output from ansible-doc contains a nonempty description and, if applicable, an options section.
options:
  name:
    description:
      - Fully qualified name of the module or role to lint (e.g., `community.general.mysql_user` or `my_role`).
      - Passed directly to `ansible-doc --json`.
    type: str
    required: true
  require_options:
    description:
      - If true, ensure that the JSON contains a nonempty "options" key (useful for modules).
    type: bool
    required: false
    default: false

author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
# 1) Lint documentation for a community module
- name: Lint docs for community.general.mysql_user
  ebdruplab.ansible_tools.doc_lint:
    name: "community.general.mysql_user"
    require_options: true
  register: lint_result

- name: Fail if documentation is missing required fields
  ansible.builtin.fail:
    msg: "Documentation lint failed: {{ lint_result.msg }}"
  when: lint_result.failed

# 2) Lint documentation for a local role (description only)
- name: Lint docs for my_role (no options required)
  ebdruplab.ansible_tools.doc_lint:
    name: "my_role"
  register: lint_result

- name: Debug lint success
  ansible.builtin.debug:
    msg: "Documentation lint passed for {{ lint_result.name }}"
"""

RETURN = r"""
name:
  description:
    - The name of the module or role that was linted.
  returned: always
  type: str
description:
  description:
    - The description string extracted from ansible-doc.
  returned: success
  type: str
options:
  description:
    - JSON object of options (if any, only returned when require_options is true and present).
  returned: when require_options is true and options exist
  type: dict
rc:
  description:
    - Return code from the `ansible-doc --json` command.
  returned: always
  type: int
stdout:
  description:
    - Raw JSON string output from `ansible-doc --json`.
  returned: always
  type: str
stderr:
  description:
    - Captured standard error from `ansible-doc --json`.
  returned: always
  type: str
msg:
  description:
    - Human-readable error message if the documentation is missing required fields or ansible-doc invocation fails.
  returned: on failure
  type: str
"""

def run_subprocess(cmd, module):
    """
    Wrapper to invoke subprocess, capture stdout/stderr, return (rc, stdout, stderr).
    If ansible-doc is not found or errors, fail via module.fail_json.
    """
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout, stderr
    except OSError as e:
        module.fail_json(msg=f"Failed to execute {cmd[0]}: {e}")

def main():
    module_args = dict(
        name=dict(type="str", required=True),
        require_options=dict(type="bool", required=False, default=False),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    name = module.params["name"]
    require_options = module.params["require_options"]

    # Build ansible-doc command with JSON output
    cmd = ["ansible-doc", "--json", name]

    rc, stdout, stderr = run_subprocess(cmd, module)

    result = {
        "rc": rc,
        "stdout": stdout,
        "stderr": stderr,
        "name": name,
    }

    # If ansible-doc failed to find or parse, error out
    if rc != 0:
        module.fail_json(msg=f"ansible-doc failed for {name} (rc={rc})", **result)

    # Parse JSON
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as e:
        module.fail_json(msg=f"Failed to parse JSON from ansible-doc: {e}", **result)

    # ansible-doc --json returns a dict keyed by name
    if name not in data:
        module.fail_json(msg=f"ansible-doc output missing key '{name}'", **result)

    doc_info = data[name]

    # Check description
    description = doc_info.get("description", "")
    if not description or not description.strip():
        module.fail_json(msg="Missing or empty description field", **result)

    result["description"] = description

    # If require_options, ensure options exist and nonempty
    if require_options:
        options = doc_info.get("options", {})
        if not options or not isinstance(options, dict) or len(options) == 0:
            module.fail_json(msg="Missing or empty options field", **result)
        result["options"] = options

    module.exit_json(changed=False, **result)

if __name__ == "__main__":
    main()

