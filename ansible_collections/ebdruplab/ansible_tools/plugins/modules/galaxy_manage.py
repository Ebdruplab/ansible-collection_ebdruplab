#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2025 ebdruplab
# MIT License (see LICENSE file or https://opensource.org/licenses/MIT)

from ansible.module_utils.basic import AnsibleModule
import subprocess
import os
import json

DOCUMENTATION = r"""
---
module: galaxy_manage
short_description: Manage Ansible Galaxy operations (install, build, publish, install from local artifact) with support for alternative servers
version_added: "1.0.0"
description:
  - Manage roles and collections by invoking the ansible-galaxy CLI.
  - Supports installing from a requirements file, building roles or collections, publishing to Galaxy or an alternative Ansible Automation Hub server, importing (publishing) a role by namespace and name, and installing a built role or collection tarball locally.
options:
  action:
    description:
      - Which ansible-galaxy subcommand to run.
      - `install`: Install roles/collections from a requirements file.
      - `build_collection`: Build a collection tarball from a local collection directory.
      - `build_role`: Build a role tarball from a local role directory.
      - `publish_collection`: Publish a built collection tarball to Galaxy or alternative server.
      - `publish_role`: Publish (import) a role by namespace and name to Galaxy or alternative server.
      - `install_artifact`: Install a built role or collection tarball locally.
    type: str
    required: true
    choices: ['install', 'build_collection', 'build_role', 'publish_collection', 'publish_role', 'install_artifact']

  # Parameters for 'install'
  requirements_file:
    description:
      - Path to a YAML file listing roles/collections in the standard requirements format.
      - Only used when `action: install`.
    type: path
    required: false
  dest:
    description:
      - Destination directory where `ansible-galaxy install` will place roles/collections.
      - Only used when `action: install`.
    type: path
    required: false
  force:
    description:
      - For `install`, pass `--force` to re-install even if already present.
      - For `build_collection` or `build_role`, pass `--force` to overwrite existing artifact.
      - For `install_artifact`, pass `--force` to overwrite existing installation.
      - Only used when action is `install`, `build_collection`, `build_role`, or `install_artifact`.
    type: bool
    default: false

  # Parameters for 'build_collection'
  source_dir:
    description:
      - Path to the root of the collection to build (must contain galaxy.yml).
      - Only used when `action: build_collection`.
    type: path
    required: false
  output_path:
    description:
      - Directory in which to place the built collection tarball.
      - If omitted, the tarball is created in the current working directory.
      - Only used when `action: build_collection`.
    type: path
    required: false

  # Parameters for 'build_role'
  role_dir:
    description:
      - Path to the root of the role to build (must contain meta/main.yml).
      - Only used when `action: build_role`.
    type: path
    required: false
  role_output_path:
    description:
      - Directory in which to place the built role tarball.
      - If omitted, the tarball is created in the current working directory.
      - Only used when `action: build_role`.
    type: path
    required: false

  # Parameters for 'publish_collection'
  collection_archive:
    description:
      - Path to a built collection `.tar.gz` file (produced by `build_collection`).
      - Only used when `action: publish_collection`.
    type: path
    required: false
  server:
    description:
      - The Galaxy or Automation Hub server to target (e.g., `https://galaxy.ansible.com` or custom hub URL).
      - If omitted, defaults to the community Galaxy server.
      - Used when action is `publish_collection` or `publish_role`.
    type: str
    required: false
  api_token:
    description:
      - Ansible Galaxy API token (or an environment variable name containing it).
      - If provided, this module will set the `ANSIBLE_GALAXY_TOKEN` env var for the subprocess.
      - Only used when action is `publish_collection` or `publish_role`.
    type: str
    required: false
    no_log: true

  # Parameters for 'publish_role'
  namespace:
    description:
      - The namespace/owner under which to publish the role (e.g. `my_username`).
      - Only used when `action: publish_role`.
    type: str
    required: false
  role_name:
    description:
      - The name of the role to publish (e.g. `my_role`).
      - Only used when `action: publish_role`.
    type: str
    required: false

  # Parameters for 'install_artifact'
  artifact_path:
    description:
      - Path to a built role or collection `.tar.gz` file.
      - Only used when `action: install_artifact`.
    type: path
    required: false
  artifact_type:
    description:
      - Type of artifact to install. Choices: `role` or `collection`.
      - Only used when action is `install_artifact`.
    type: str
    required: false
    choices: ['role', 'collection']

author:
  - "Kristian Ebdrup (@kris9854)"
"""

EXAMPLES = r"""
# 1) Install using a requirements.yml:
- name: Install roles/collections via ansible-galaxy
  ebdruplab.ansible_tools.galaxy_manage:
    action: install
    requirements_file: "ci/requirements.yml"
    dest: ".cache/ansible_deps"
    force: false

# 2) Build a collection tarball from source:
- name: Build collection from local source
  ebdruplab.ansible_tools.galaxy_manage:
    action: build_collection
    source_dir: "./collections/ansible_collections/ebdruplab/ansible_tools"
    output_path: "./dist"
    force: true

# 3) Build a role tarball from a local role directory:
- name: Build role from local source
  ebdruplab.ansible_tools.galaxy_manage:
    action: build_role
    role_dir: "./roles/my_role"
    role_output_path: "./dist"
    force: false

# 4) Publish a built collection to Galaxy (default server) using an API token:
- name: Publish ebdruplab-ansible_tools-1.0.0.tar.gz to Galaxy
  ebdruplab.ansible_tools.galaxy_manage:
    action: publish_collection
    collection_archive: "dist/ebdruplab-ansible_tools-1.0.0.tar.gz"
    api_token: "{{ lookup('env', 'ANSIBLE_GALAXY_TOKEN') }}"

# 5) Publish a collection to a custom hub with explicit server and token:
- name: Publish to private Automation Hub
  ebdruplab.ansible_tools.galaxy_manage:
    action: publish_collection
    collection_archive: "dist/private_namespace-private_collection-1.0.0.tar.gz"
    server: "https://automationhub.example.com"
    api_token: "{{ lookup('env', 'AH_TOKEN') }}"

# 6) Publish a role under namespace 'ebdruplab' on the default Galaxy:
- name: Publish role 'my_role' under namespace 'ebdruplab'
  ebdruplab.ansible_tools.galaxy_manage:
    action: publish_role
    namespace: "ebdruplab"
    role_name: "my_role"
    api_token: "{{ lookup('env', 'ANSIBLE_GALAXY_TOKEN') }}"

# 7) Publish a role into a private Automation Hub:
- name: Publish role into private Automation Hub
  ebdruplab.ansible_tools.galaxy_manage:
    action: publish_role
    namespace: "ebdruplab"
    role_name: "my_private_role"
    server: "https://automationhub.example.com"
    api_token: "{{ lookup('env', 'AH_TOKEN') }}"

# 8) Install a built collection tarball locally:
- name: Install a local collection tarball
  ebdruplab.ansible_tools.galaxy_manage:
    action: install_artifact
    artifact_path: "dist/ebdruplab-ansible_tools-1.0.0.tar.gz"
    artifact_type: "collection"
    force: true

# 9) Install a built role tarball locally:
- name: Install a local role tarball
  ebdruplab.ansible_tools.galaxy_manage:
    action: install_artifact
    artifact_path: "dist/my_role-1.0.0.tar.gz"
    artifact_type: "role"
    force: false
"""

RETURN = r"""
installed:
  description:
    - List of roles/collections parsed from requirements.yml (only if `action: install`).
  returned: when action == 'install'
  type: list
  sample: ["geerlingguy.mysql", "community.general"]

artifact_path:
  description:
    - The path to the built tarball (only if `action: build_collection` or `action: build_role` succeeded).
  returned: when action in ['build_collection', 'build_role']
  type: str
  sample: "dist/ebdruplab-ansible_tools-1.0.0.tar.gz"

rc:
  description:
    - Return code from the invoked `ansible-galaxy` CLI.
  returned: always
  type: int

stdout:
  description:
    - Captured standard output from the `ansible-galaxy` CLI command.
  returned: always
  type: str

stderr:
  description:
    - Captured standard error from the `ansible-galaxy` CLI command.
  returned: always
  type: str

msg:
  description:
    - Human-readable error message when `failed` is true.
  returned: on failure
  type: str
"""

def run_subprocess(cmd, env_vars=None, module=None):
    """
    Wrapper around subprocess.Popen to run an external command, capture stdout/stderr, and return the rc.
    If env_vars is provided, it updates os.environ copy for the subprocess.
    """
    chosen_env = os.environ.copy()
    if env_vars:
        chosen_env.update(env_vars)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=chosen_env
        )
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout, stderr
    except OSError as e:
        if module:
            module.fail_json(msg=f"Failed to execute {cmd[0]}: {e}")
        else:
            return 1, "", str(e)

def action_install(module, params):
    """
    Handle: ansible-galaxy install -r <requirements_file> -p <dest> [--force]
    """
    requirements_file = params.get('requirements_file')
    dest = params.get('dest')
    force = params.get('force')

    if not requirements_file:
        module.fail_json(msg="`requirements_file` is required when action=='install'")
    if not dest:
        module.fail_json(msg="`dest` is required when action=='install'")

    try:
        import yaml
        with open(requirements_file, 'r') as f:
            content = yaml.safe_load(f)
    except Exception as e:
        module.fail_json(msg=f"Failed to parse requirements file {requirements_file}: {e}")

    installed_items = []
    if isinstance(content, dict):
        for section in ('collections', 'roles'):
            if section in content and isinstance(content[section], list):
                for entry in content[section]:
                    if isinstance(entry, dict) and entry.get('name'):
                        installed_items.append(entry['name'])
                    elif isinstance(entry, str):
                        installed_items.append(entry)

    try:
        os.makedirs(dest, exist_ok=True)
    except Exception as e:
        module.fail_json(msg=f"Failed to create destination directory {dest}: {e}")

    cmd = ["ansible-galaxy", "install", "-r", requirements_file, "-p", dest]
    if force:
        cmd.append("--force")

    rc, stdout, stderr = run_subprocess(cmd, module=module)

    result = {
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
        'installed': installed_items,
    }

    if rc != 0:
        module.fail_json(msg=f"ansible-galaxy install failed with code {rc}", **result)

    module.exit_json(changed=True, **result)

def action_build_collection(module, params):
    """
    Handle: ansible-galaxy collection build <source_dir> [--output-path <output_path>] [--force]
    """
    source_dir = params.get('source_dir')
    output_path = params.get('output_path')
    force = params.get('force')

    if not source_dir:
        module.fail_json(msg="`source_dir` is required when action=='build_collection'")
    if not os.path.isdir(source_dir):
        module.fail_json(msg=f"Collection source directory not found: {source_dir}")

    cmd = ["ansible-galaxy", "collection", "build", source_dir]
    if output_path:
        try:
            os.makedirs(output_path, exist_ok=True)
        except Exception as e:
            module.fail_json(msg=f"Failed to create output directory {output_path}: {e}")
        cmd.extend(["--output-path", output_path])
    if force:
        cmd.append("--force")

    rc, stdout, stderr = run_subprocess(cmd, module=module)

    result = {
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
    }

    artifact_path = None
    for line in stdout.splitlines():
        if "Created collection at" in line:
            artifact_path = line.split("Created collection at", 1)[1].strip()
            break

    if artifact_path:
        result['artifact_path'] = artifact_path

    if rc != 0:
        module.fail_json(msg=f"ansible-galaxy collection build failed with code {rc}", **result)

    module.exit_json(changed=True, **result)

def action_build_role(module, params):
    """
    Handle: ansible-galaxy role build <role_dir> [--output-path <role_output_path>] [--force]
    """
    role_dir = params.get('role_dir')
    role_output_path = params.get('role_output_path')
    force = params.get('force')

    if not role_dir:
        module.fail_json(msg="`role_dir` is required when action=='build_role'")
    if not os.path.isdir(role_dir):
        module.fail_json(msg=f"Role directory not found: {role_dir}")

    cmd = ["ansible-galaxy", "role", "build", role_dir]
    if role_output_path:
        try:
            os.makedirs(role_output_path, exist_ok=True)
        except Exception as e:
            module.fail_json(msg=f"Failed to create output directory {role_output_path}: {e}")
        cmd.extend(["--output-path", role_output_path])
    if force:
        cmd.append("--force")

    rc, stdout, stderr = run_subprocess(cmd, module=module)

    result = {
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
    }

    artifact_path = None
    for line in stdout.splitlines():
        if "Created role at" in line:
            artifact_path = line.split("Created role at", 1)[1].strip()
            break

    if artifact_path:
        result['artifact_path'] = artifact_path

    if rc != 0:
        module.fail_json(msg=f"ansible-galaxy role build failed with code {rc}", **result)

    module.exit_json(changed=True, **result)

def action_publish_collection(module, params):
    """
    Handle: ansible-galaxy collection publish <collection_archive> [--server <server>]
    Uses api_token (or env var) to set ANSIBLE_GALAXY_TOKEN in subprocess.
    """
    collection_archive = params.get('collection_archive')
    server = params.get('server')
    api_token = params.get('api_token')

    if not collection_archive:
        module.fail_json(msg="`collection_archive` is required when action=='publish_collection'")
    if not os.path.exists(collection_archive):
        module.fail_json(msg=f"Collection archive not found: {collection_archive}")

    cmd = ["ansible-galaxy", "collection", "publish", collection_archive]
    if server:
        cmd.extend(["--server", server])

    env_vars = {}
    if api_token:
        if api_token in os.environ:
            env_vars['ANSIBLE_GALAXY_TOKEN'] = os.environ.get(api_token)
        else:
            env_vars['ANSIBLE_GALAXY_TOKEN'] = api_token

    rc, stdout, stderr = run_subprocess(cmd, env_vars=env_vars, module=module)

    result = {
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
    }

    if rc != 0:
        module.fail_json(msg=f"ansible-galaxy collection publish failed with code {rc}", **result)

    module.exit_json(changed=True, **result)

def action_publish_role(module, params):
    """
    Handle: ansible-galaxy role import <namespace> <role_name> [--server <server>]
    Uses api_token (or env var) to set ANSIBLE_GALAXY_TOKEN in subprocess.
    """
    namespace = params.get('namespace')
    role_name = params.get('role_name')
    server = params.get('server')
    api_token = params.get('api_token')

    if not namespace:
        module.fail_json(msg="`namespace` is required when action=='publish_role'")
    if not role_name:
        module.fail_json(msg="`role_name` is required when action=='publish_role'")

    cmd = ["ansible-galaxy", "role", "import", namespace, role_name]
    if server:
        cmd.extend(["--server", server])

    env_vars = {}
    if api_token:
        if api_token in os.environ:
            env_vars['ANSIBLE_GALAXY_TOKEN'] = os.environ.get(api_token)
        else:
            env_vars['ANSIBLE_GALAXY_TOKEN'] = api_token

    rc, stdout, stderr = run_subprocess(cmd, env_vars=env_vars, module=module)

    result = {
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
    }

    if rc != 0:
        module.fail_json(msg=f"ansible-galaxy role import failed with code {rc}", **result)

    module.exit_json(changed=True, **result)

def action_install_artifact(module, params):
    """
    Handle: ansible-galaxy <role|collection> install <artifact_path> [--force]
    """
    artifact_path = params.get('artifact_path')
    artifact_type = params.get('artifact_type')
    force = params.get('force')

    if not artifact_path:
        module.fail_json(msg="`artifact_path` is required when action=='install_artifact'")
    if not artifact_type:
        module.fail_json(msg="`artifact_type` is required when action=='install_artifact'")
    if artifact_type not in ['role', 'collection']:
        module.fail_json(msg="`artifact_type` must be either 'role' or 'collection'")
    if not os.path.exists(artifact_path):
        module.fail_json(msg=f"Artifact not found: {artifact_path}")

    if artifact_type == 'collection':
        cmd = ["ansible-galaxy", "collection", "install", artifact_path]
    else:
        cmd = ["ansible-galaxy", "role", "install", artifact_path]

    if force:
        cmd.append("--force")

    rc, stdout, stderr = run_subprocess(cmd, module=module)

    result = {
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
    }

    if rc != 0:
        module.fail_json(msg=f"ansible-galaxy {artifact_type} install failed with code {rc}", **result)

    module.exit_json(changed=True, **result)

def main():
    module_args = dict(
        action=dict(type="str", required=True,
                    choices=['install', 'build_collection', 'build_role', 'publish_collection', 'publish_role', 'install_artifact']),
        requirements_file=dict(type="path", required=False),
        dest=dict(type="path", required=False),
        force=dict(type="bool", default=False),
        source_dir=dict(type="path", required=False),
        output_path=dict(type="path", required=False),
        role_dir=dict(type="path", required=False),
        role_output_path=dict(type="path", required=False),
        collection_archive=dict(type="path", required=False),
        server=dict(type="str", required=False),
        api_token=dict(type="str", required=False, no_log=True),
        namespace=dict(type="str", required=False),
        role_name=dict(type="str", required=False),
        artifact_path=dict(type="path", required=False),
        artifact_type=dict(type="str", required=False, choices=['role', 'collection']),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    params = module.params
    action = params.get('action')

    if action == 'install':
        action_install(module, params)
    elif action == 'build_collection':
        action_build_collection(module, params)
    elif action == 'build_role':
        action_build_role(module, params)
    elif action == 'publish_collection':
        action_publish_collection(module, params)
    elif action == 'publish_role':
        action_publish_role(module, params)
    elif action == 'install_artifact':
        action_install_artifact(module, params)
    else:
        module.fail_json(msg=f"Unsupported action: {action}")

if __name__ == "__main__":
    main()

