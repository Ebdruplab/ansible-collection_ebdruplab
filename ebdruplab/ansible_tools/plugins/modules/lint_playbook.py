#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 ebdruplab
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
import subprocess
import os

DOCUMENTATION = r"""
---
module: lint_playbook
short_description: Lint Ansible files (playbooks/roles) using ansible-lint
version_added: "1.0.0"
description:
  - Run `ansible-lint` against a directory or file to detect syntax and style issues.
  - Useful in CI/CD pipelines to fail early on lint violations.
options:
  path:
    description:
      - Path to a playbook, role, or directory containing Ansible YAML files to lint.
      - If a directory is given, all .yml/.yaml files under it will be checked.
    type: path
    required: true
  extra_args:
    description:
      - Additional command-line arguments to pass to `ansible-lint`.
      - For example, disable rules or specify a custom rules directory.
    type: list
    elements: str
    required: false
  exclude:
    description:
      - List of paths or patterns to exclude from linting.
      - Passed to `ansible-lint` with `-x` for each pattern.
    type: list
    elements: str
    required: false
  force:
    description:
      - If true, continue linting even if errors are found (return code still reflects failures).
      - Default behavior fails immediately on any lint error (non-zero return code).
    type: bool
    default: false

author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
# 1) Lint a single playbook file
- name: Lint playbook site.yml
  lint_playbook:
    path: "./site.yml"
  register: lint_result

- name: Fail if lint returned any issues
  ansible.builtin.fail:
    msg: "Lint errors: {{ lint_result.stderr }}"
  when: lint_result.rc != 0

# 2) Lint all playbooks under a directory, excluding vendor roles
- name: Lint all playbooks in repo, excluding vendor/
  lint_playbook:
    path: "./playbooks/"
    exclude:
      - "vendor/*"
  register: lint_result

# 3) Lint with custom extra arguments
- name: Lint with quiet mode and custom rules
  lint_playbook:
    path: "./roles/"
    extra_args:
      - "-q"
      - "-r"
      - "custom_rules/"
  register: lint_result
"""

RETURN = r"""
rc:
  description:
    - Return code from the `ansible-lint` command. Zero indicates no issues detected.
  returned: always
  type: int
stdout:
  description:
    - Captured standard output from `ansible-lint`.
  returned: always
  type: str
stderr:
  description:
    - Captured standard error from `ansible-lint` (including lint violations).
  returned: always
  type: str
msg:
  description:
    - Human-readable error message if the module fails to invoke `ansible-lint` itself.
  returned: on failure
  type: str
"""

def run_subprocess(cmd, module):
    """
    Wrapper to invoke subprocess, capture stdout/stderr, return (rc, stdout, stderr).
    If binary not found or OSError occurs, fail via module.fail_json.
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
        path=dict(type="path", required=True),
        extra_args=dict(type="list", elements="str", required=False, default=[]),
        exclude=dict(type="list", elements="str", required=False, default=[]),
        force=dict(type="bool", default=False),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    path = module.params["path"]
    extra_args = module.params["extra_args"]
    exclude = module.params["exclude"]
    force = module.params["force"]

    if not os.path.exists(path):
        module.fail_json(msg=f"Specified path not found: {path}")

    # Build ansible-lint command
    cmd = ["ansible-lint", path]
    for pattern in exclude:
        cmd.extend(["-x", pattern])
    if extra_args:
        cmd.extend(extra_args)

    rc, stdout, stderr = run_subprocess(cmd, module)

    result = dict(rc=rc, stdout=stdout, stderr=stderr)

    # If force is False, fail on non-zero rc; else return rc and let caller decide
    if rc != 0 and not force:
        module.fail_json(msg=f"ansible-lint detected issues (rc={rc})", **result)

    module.exit_json(changed=False, **result)

if __name__ == "__main__":
    main()

