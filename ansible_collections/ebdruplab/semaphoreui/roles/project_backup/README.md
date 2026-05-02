# Ansible Role: `ebdruplab.semaphoreui.project_backup`

This role reads an existing Semaphore project and writes it to a YAML file.

The generated file is made for the `ebdruplab.semaphoreui.project_deploy` role, so you can:

- back up a project
- save it in Git
- redeploy it later
- move it to another Semaphore instance

## Requirements

- Ansible 2.10+
- A reachable Semaphore instance
- The `ebdruplab.semaphoreui` collection
- Login credentials or an API token

## Main Variables

### General

```yaml
project_backup_debug: false
project_backup_sensitive_data_no_log: true
```

### Connection and authentication

```yaml
project_backup_semaphore_host: "http://localhost"
project_backup_semaphore_port: 3000
project_backup_semaphore_username: "admin"
project_backup_semaphore_password: "changeme"
# project_backup_semaphore_api_token: "KEY"
```

You can also use the shared connection variables instead of the role-specific ones:

```yaml
ebdruplab_semaphore_host: "http://localhost"
ebdruplab_semaphore_port: 3000
ebdruplab_semaphore_username: "admin"
ebdruplab_semaphore_password: "changeme"
# ebdruplab_semaphore_api_token: "KEY"
```

You can use either:

- username and password
- API token

### Target project

Use one of these:

```yaml
project_backup_project_name: ""
project_backup_project_id: 0
```

If both are set, the project name is preferred.

### Output

```yaml
project_backup_output_dir: "{{ playbook_dir }}/.backup/generated_vars"
project_backup_output_filename: "generated.project_deploy.yml"
```

This is where the generated YAML file will be written.

### Generated file structure

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

Sensitive values are replaced with vault variable placeholders.

Example:

```yaml
password: "{{ ansible_vault_PROJECT_VAULT_PASSWORD_PASSWORD }}"
```

The variable names are also listed under `project_backup_vault_variables` so you can add them to an encrypted vars file.

## What the role does

The role will:

1. connect to Semaphore
2. find the project by name or ID
3. read project data
4. convert it into `project_deploy` format
5. replace secret values with vault placeholders
6. write the result to one YAML file

The backup includes project data such as:

- project settings
- users
- keys
- repositories
- views
- inventories
- environments
- templates
- schedules
- integrations
- integration extraction values

## Examples

Simple example files are included in:

- `examples/basic.yml`
- `examples/vars.yml`

Run it like this:

```bash
ansible-playbook examples/basic.yml
```

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

## Use the Output with `project_deploy`

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

## Recommended Workflow

1. Run `project_backup` and generate `generated.project_deploy.yml`.
2. Open the generated file and review all generated key login values before using it.
3. Pay special attention to:
   - `project_deploy_config.keys.<name>.login_password.login`
   - `project_deploy_config.keys.<name>.ssh.login`
4. If you see placeholder values such as `CHANGE_ME_LOGIN` or `CHANGE_ME_SSH_LOGIN`, replace them with the real values.
5. Open the generated file and look at `project_backup_vault_variables`.
6. Create a vaulted vars file and define each listed variable.
7. Use both files together with `ebdruplab.semaphoreui.project_deploy`.

Example:

```yaml
- hosts: localhost
  gather_facts: false
  vars_files:
    - .backup/generated_vars/generated.project_deploy.yml
    - vaulted.project_backup.secrets.yml
  roles:
    - role: ebdruplab.semaphoreui.project_deploy
```

This means `project_backup` can be used to generate the YAML, and `project_deploy` can later deploy that same YAML again.

## Notes

- This role is meant to work together with `ebdruplab.semaphoreui.project_deploy`.
- The generated file is ready for Git, but you still need to define the vault variables for secret values.
- Semaphore does not return raw key secret material, so some key-related secrets will be written as placeholders that you must fill in yourself.
- Semaphore may also fail to return some key login fields through the API, so always review generated key login values before restoring or redeploying a backup.

## Dependencies

None.

## License

MIT-0

## Author Information

Kristian Ebdrup  
Email: [kristian@ebdruplab.dk](mailto:kristian@ebdruplab.dk)  
GitHub: [https://github.com/kris9854](https://github.com/kris9854)
