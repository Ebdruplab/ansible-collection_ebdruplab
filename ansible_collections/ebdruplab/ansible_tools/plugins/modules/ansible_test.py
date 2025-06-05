#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 ebdruplab
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
import subprocess
import os

DOCUMENTATION = r"""
---
module: ansible_test
short_description: Run ansible-test on a collection or role
version_added: "1.0.0"
description:
  - Invoke `ansible-test` for a specific test suite (sanity, unit, or integration) against a collection or role.
  - Useful in CI pipelines to validate module code, style, and functionality.
options:
  path:
    description:
      - Path to the root of the collection or role you wish to test.
      - For collections, should point to the collection directory containing galaxy.yml.
      - For roles, point to the role directory containing meta/main.yml.
    type: path
    required: true
  suite:
    description:
      - Which ansible-test suite to run.
      - `sanity`: Checks coding style, imports, and basic structure.
      - `unit`: Runs unit tests for Python modules (if present).
      - `integration`: Runs integration tests against an environment.
    type: str
    required: true
    choices: ['sanity', 'unit', 'integration']
  extra_args:
    description:
      - Additional arguments to pass directly to `ansible-test`.
      - For example, `--test-id` filters or verbosity flags.
    type: list
    elements: str
    required: false
    default: []

author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
# 1) Run sanity checks on a collection
- name: Run ansible-test sanity on my_collection
  ebdruplab.ansible_tools.ansible_test:
    path: "./collections/ansible_collections/ebdruplab/my_collection"
    suite: "sanity"
  register: test_result

- name: Fail if sanity errors
  ansible.builtin.fail:
    msg: "Sanity checks failed (rc={{ test_result.rc }})"
  when: test_result.rc != 0

# 2) Run unit tests on a role
- name: Run ansible-test unit on my_role
  ebdruplab.ansible_tools.ansible_test:
    path: "./roles/my_role"
    suite: "unit"
    extra_args:
      - "--test-id"
      - "ansible_test_units"
  register: test_result

# 3) Run integration tests on a collection
- name: Run ansible-test integration on my_collection
  ebdruplab.ansible_tools.ansible_test:
    path: "./collections/ansible_collections/ebdruplab/my_collection"
    suite: "integration"
    extra_args:
      - "--docker"
  register: test_result
"""

RETURN = r"""
rc:
  description:
    - Return code from the `ansible-test` command. Zero indicates success.
  returned: always
  type: int
stdout:
  description:
    - Captured standard output from `ansible-test`.
  returned: always
  type: str
stderr:
  description:
    - Captured standard error from `ansible-test`.
  returned: always
  type: str
msg:
  description:
    - Human-readable error message if the module fails to invoke `ansible-test` itself.
  returned: on failure
  type: str
"""

def run_subprocess(cmd, module):
    """
    Wrapper to invoke subprocess, capture stdout/stderr, return (rc, stdout, stderr).
    If ansible-test is not found or errors, fail via module.fail_json.
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
        suite=dict(type="str", required=True, choices=['sanity', 'unit', 'integration']),
        extra_args=dict(type="list", elements="str", required=False, default=[]),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    path = module.params["path"]
    suite = module.params["suite"]
    extra_args = module.params["extra_args"]

    if not os.path.exists(path):
        module.fail_json(msg=f"Specified path not found: {path}")

    # Build ansible-test command
    cmd = ["ansible-test", suite, path]
    if extra_args:
        cmd.extend(extra_args)

    rc, stdout, stderr = run_subprocess(cmd, module)

    result = dict(rc=rc, stdout=stdout, stderr=stderr)

    if rc != 0:
        module.fail_json(msg=f"ansible-test {suite} failed (rc={rc})", **result)

    module.exit_json(changed=False, **result)

if __name__ == "__main__":
    main()

