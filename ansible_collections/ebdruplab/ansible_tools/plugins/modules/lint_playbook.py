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
  fix:
    description:
      - If true, run ansible-lint in autofix mode (pass `--fix`).
    type: bool
    default: false
  fix_list:
    description:
      - List of specific rule IDs or tags to auto-fix.
      - If omitted (and `fix` is true), the module will default to fixing *all* available issues.
      - When provided, this list is joined with commas and passed as `--fix=<comma-separated>`.
    type: list
    elements: str
    required: false
    default: []

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

# 4) Lint and autofix all issues
- name: Auto-fix all lint issues
  lint_playbook:
    path: "./playbooks/"
    fix: true
  register: lint_result

# 5) Lint and autofix only YAML and Jinja rules
- name: Auto-fix specific rules
  lint_playbook:
    path: "./playbooks/"
    fix: true
    fix_list:
      - yaml
      - jinja
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
    # Define module arguments
    module_args = dict(
        path=dict(type="path", required=True),
        extra_args=dict(type="list", elements="str", required=False, default=[]),
        exclude=dict(type="list", elements="str", required=False, default=[]),
        force=dict(type="bool", default=False),
        fix=dict(type="bool", default=False),
        fix_list=dict(type="list", elements="str", required=False, default=[]),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    path = module.params["path"]
    extra_args = module.params["extra_args"]
    exclude = module.params["exclude"]
    force = module.params["force"]
    fix = module.params["fix"]
    fix_list = module.params["fix_list"]

    # Ensure the specified path exists
    if not os.path.exists(path):
        module.fail_json(msg=f"Specified path not found: {path}")

    # Build the ansible-lint command
    cmd = ["ansible-lint", path]

    # Exclude patterns
    for pattern in exclude:
        cmd.extend(["-x", pattern])

    # Extra user-provided args
    if extra_args:
        cmd.extend(extra_args)

    # Autofix support: if fix is true, append --fix
    # If fix_list is non-empty, use --fix=<comma-separated list>
    if fix:
        if fix_list:
            # Join the list of rules/tags to fix
            joined = ",".join(fix_list)
            cmd.append(f"--fix={joined}")
        else:
            # No specific list provided: fix all issues
            cmd.append("--fix")

    # Run ansible-lint
    rc, stdout, stderr = run_subprocess(cmd, module)

    # Prepare result dictionary
    result = dict(rc=rc, stdout=stdout, stderr=stderr)

    # If not forcing, fail on any lint errors (rc != 0)
    if rc != 0 and not force:
        module.fail_json(msg=f"ansible-lint detected issues (rc={rc})", **result)

    # Exit normally; caller can inspect rc
    module.exit_json(changed=False, **result)


if __name__ == "__main__":
    main()

