ebdruplab.semaphoreui.project_backup
=========
Back up a Semaphore UI project using the built-in Semaphore backup API and optionally export the result as **Ansible-friendly vars YAML**.  
The generated vars can be safely committed to Git and reused with the `project_deploy` role to recreate the project.

Sensitive values (passwords, tokens, keys) are **never exported in plaintext**. They are replaced with Ansible Vault variable references (`{{ vault_* }}`).

Requirements
------------

- Ansible 2.10+
- A reachable Semaphore UI instance
- Collection: `ebdruplab.semaphoreui`
- Valid authentication:
  - API token **or**
  - Username/password (login/logout handled by the role)

Role Variables
--------------
## Global connection variables (recommended)

You can define **global** Semaphore connection/auth variables once and reuse them across the collection’s roles (including `project_deploy` and `project_backup`).  
If any of the `ebdruplab_semaphore_*` variables are set, the role will use them as defaults (role-specific variables still take precedence).

```yaml
# Global Semaphore connection/auth
ebdruplab_semaphore_host: "http://localhost"
ebdruplab_semaphore_port: 3000
ebdruplab_semaphore_username: "admin"
ebdruplab_semaphore_password: "changeme"
# ebdruplab_semaphore_api_token: "KEY"
```


### Connection and authentication variables if global is not used

```yaml
project_backup_semaphore_host: "http://localhost"
project_backup_semaphore_port: 3000
project_backup_semaphore_username: "admin"
project_backup_semaphore_password: "changeme"
# project_backup_semaphore_api_token: "KEY"
````

### Target project (choose one)

```yaml
project_backup_project_id: 0
project_backup_project_name: ""
```

### Output

```yaml
project_backup_output_dir: "./semaphore_backups"
project_backup_output_prefix: "semaphore_project"
project_backup_write_raw_json: true
project_backup_write_vars_yaml: true
```

### Vars export

```yaml
project_backup_vars_layout: "single"   # single | files
project_backup_vars_root_key: "semaphore_project_backup"
project_backup_vars_files_dirname: "vars"
```

### Secret handling

```yaml
project_backup_scrub_secrets: true
project_backup_vault_var_prefix: "vault"
```

Secrets are replaced with Vault references such as:

```yaml
password: "{{ vault_repository_myrepo_password }}"
```

The role **does not read from Ansible Vault**. Users must define these variables themselves.

## Dependencies

None.

This role is designed to integrate with:

* `ebdruplab.semaphoreui.project_deploy` (for restore/recreation)

## Example Playbook

```yaml
- hosts: localhost
  gather_facts: false
  roles:
    - role: ebdruplab.semaphoreui.project_backup
      vars:
        project_backup_semaphore_host: "https://semaphore.example.com"
        project_backup_semaphore_api_token: "{{ lookup('env','SEMAPHORE_TOKEN') }}"
        project_backup_project_name: "My Project"
        project_backup_vars_layout: "single"
```

Using the backup with `project_deploy`:

```yaml
vars_files:
  - semaphore_backups/semaphore_project_12_20260112T120000Z.vars.yml
  - group_vars/all/vault.yml
```

## License

BSD

## Author Information

Kristian Ebdrup — [kristian@ebdruplab.dk](mailto:kristian@ebdruplab.dk)
GitHub: [https://github.com/kris9854](https://github.com/kris9854)

> See the **`ebdruplab/roles/project_deploy/tests/project_generate_restore_and_recreate.yml`** directory for a runnable end-to-end example.

