# Ansible Role: `ebdruplab.semaphoreui.project_backup`

Generate a **`project_deploy_config`** structure from an existing Semaphore UI project and write it as **Ansible vars YAML**.
The generated file can be committed to Git and later consumed directly by the
`ebdruplab.semaphoreui.project_deploy` role to recreate the project.

This role **reads live project state** from Semaphore (projects, keys, repos, inventories, templates, schedules, integrations, etc.) and converts it into the declarative format expected by `project_deploy`.

## Requirements

* Ansible **2.10+**
* A reachable Semaphore UI instance
* Ansible collection: `ebdruplab.semaphoreui`
* Valid authentication:

  * Username/password **or**
  * API token

## Role Variables

### General

```yaml
project_backup_debug: false
project_backup_sensitive_data_no_log: true
```

* `project_backup_debug`
  Enable additional debug output.

* `project_backup_sensitive_data_no_log`
  Prevents sensitive values from appearing in Ansible logs.

### Connection and authentication

```yaml
project_backup_semaphore_host: "http://localhost"
project_backup_semaphore_port: 3000
project_backup_semaphore_username: "admin"
project_backup_semaphore_password: "changeme"
# project_backup_semaphore_api_token: "KEY"
```

Authentication is handled internally by the role using `login.yml` and `logout.yml`.

### Target project selection

You must select **exactly one project**.

Project **name is preferred**.
If a name is provided, it is always used even if an ID is set.

```yaml
project_backup_project_name: ""
project_backup_project_id: 0
```

Resolution logic:

1. If `project_backup_project_name` is set → resolve project ID by name
2. Otherwise → use `project_backup_project_id`
3. Fail if neither resolves to a valid project

### Output

```yaml
project_backup_output_dir: "{{ playbook_dir }}/.backup/generated_vars"
project_backup_output_filename: "generated.project_deploy.yml"
```

The role writes a single YAML file containing the generated configuration.

### Vars structure

```yaml
project_backup_root_key: "project_deploy_config"
project_backup_vault_variables_root_key: "project_backup_vault_variables"
project_backup_vault_variable_prefix: "ansible_vault"
```

The output file will look like:

```yaml
project_deploy_config:
  project:
    name: My Project
    ...
  inventories: {}
  templates: {}
  schedules: {}
project_backup_vault_variables:
  - ansible_vault_MY_KEY_PASSWORD
  - ansible_vault_MY_ENVIRONMENT_DB_PASSWORD_SECRET
```

This format is **shaped for direct use by** `project_deploy`.
Sensitive password-like values are replaced with Jinja expressions such as
`{{ ansible_vault_PROJECT_VAULT_PASSWORD_PASSWORD }}` and the generated variable
names are listed under `project_backup_vault_variables` so you can define them
later in an encrypted vars file.
Semaphore does not return raw key secret material through the API, so key-related
vault variables are generated as placeholders that you must populate yourself.

## What the role does

1. Resolves global or role-specific Semaphore connection variables
2. Logs in to Semaphore
3. Resolves the target project
4. Collects:

   * Project metadata
   * Users access
   * Keys
   * Repositories
   * Views
   * Inventories
   * Environments
   * Templates
   * Schedules
   * Integrations
   * Integration extraction values
5. Normalizes all resources into `project_deploy`-compatible form
6. Replaces password-like secrets with vault variable placeholders
7. Writes a single vars YAML file
8. Logs out of Semaphore

## Example Playbook

```yaml
- hosts: localhost
  gather_facts: false
  roles:
    - role: ebdruplab.semaphoreui.project_backup
      vars:
        project_backup_semaphore_host: "https://semaphore.example.com"
        project_backup_semaphore_api_token: "{{ lookup('env', 'SEMAPHORE_TOKEN') }}"
        project_backup_project_name: "My Project"
```

## Using the output with `project_deploy`

```yaml
vars_files:
  - .backup/generated_vars/generated.project_deploy.yml
  - vaulted.project_backup.secrets.yml
```

```yaml
- hosts: localhost
  gather_facts: false
  roles:
    - role: ebdruplab.semaphoreui.project_deploy
```

Example vaulted vars file:

```yaml
ansible_vault_PROJECT_VAULT_PASSWORD_PASSWORD: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  ...
ansible_vault_TEST_ENVIRONMENT_DB_PASSWORD_SECRET: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  ...
```

## Dependencies

None.

Designed to work together with:

* `ebdruplab.semaphoreui.project_deploy`

## License

MIT-0

## Author Information

**Kristian Ebdrup**
GitHub: [https://github.com/kris9854](https://github.com/kris9854)
