# Ansible Role — `ebdruplab.semaphoreui.project_deploy`

Deploy a complete Semaphore project from one declarative variable tree.
The role authenticates (API token or username/password), validates your configuration, optionally deletes an existing project, and then creates or synchronizes **keys, repositories, views, inventories, environments, templates, schedules, and integrations** — idempotently.

From **v2.0.6**, integrations can also define **extraction values**, allowing request data (for example HTTP headers) to be mapped to environment variables for integration-triggered tasks.

A working example can be found in the repository’s **`tests/`** directory.

---

## Requirements

* Ansible 2.10+
* Collection: `ebdruplab.semaphoreui` (this role lives inside it)
* A reachable Semaphore instance

---

## Defaults (quick view)

```yaml
# Connection
project_deploy_semaphore_host: "http://localhost"
project_deploy_semaphore_port: 3000
project_deploy_semaphore_username: "admin"
project_deploy_semaphore_password: "changeme"
# project_deploy_semaphore_api_token: "KEY"

# Safety
project_deploy_debug: false
project_deploy_sensitive_data_no_log: true
project_deploy_force_project_creation: false
project_deploy_force_project_update: false
project_deploy_force_project_delete: false
project_deploy_force_project_delete_timer: 5

# Pruning (delete items not present in your YAML)
project_deploy_variable_delete: false

# Declarative config
project_deploy_config:
  project: {}
  users_access: []
  keys: {}
  repositories: []
  views: {}
  inventories: {}
  environments: {}
  templates: {}
  schedules: {}
  integrations: {}
```

> If you previously used empty lists (`[]`) for map-based sections, switch to `{}`.
> Most task files iterate using `dict2items`.

---

## What the role does

1. **Authenticate**

   * API token **or**
   * Username/password

2. **Preflight validation** of `project_deploy_config`

3. **Project handling**

   * No project found → **create**
   * Project found → behavior controlled by flags:

     * `project_deploy_force_project_delete` → delete → create fresh
     * `project_deploy_force_project_creation` → create another project with same name
     * `project_deploy_force_project_update` → reuse and sync resources
     * Otherwise → fail safely

4. **Create / sync resources in order**

   ```
   keys → repositories → views → inventories → environments
        → templates → schedules → integrations → integration extraction values
   ```

5. **Expose lookup maps** for resolving IDs by name:

   * `created_keys_by_name`
   * `created_repos_by_name`
   * `created_project_view_by_title`
   * `created_inventory_by_name`
   * `created_environments_by_name`
   * `created_templates_by_name`
   * `created_schedules_by_name`
   * `created_integrations_by_name`

6. **Pruning** (when enabled)

   * Removes existing resources in Semaphore that are **not** present in your YAML

---

## Variable schema (overview)

```yaml
project_deploy_config:
  project:
    name: "Your Project"
    alert: false
    alert_chat: ""
    max_parallel_tasks: 0
    demo: false

  users_access:
    - username: "admin"
      role: "Owner"

  keys:
    key_handle:
      name: "Human Name"
      type: ssh | login_password
      ssh:
        login: "ansibleuser"
        passphrase: "{{ vault_passphrase }}"
        private_key: "{{ vault_private_key }}"
      login_password:
        login: "Git User"
        password: "{{ vault_git_password }}"

  repositories:
    - name: "Repo Name"
      git_url: "https://github.com/org/repo.git"
      git_branch: "main"
      key_name: "Human Name of a key"

  views:
    my_view:
      title: "Board Column"
      position: 0

  inventories:
    inv1:
      name: "Static YAML"
      type: static-yaml | static | file
      inventory: {}
      repository_name: "Repo Name"
      inventory_file: "path/in/repo.ini"
      ssh_key_name: "SSH key name"
      become_key_name: "SSH key name (become)"

  environments:
    env1:
      name: "Env Name"
      env: { KEY: "value" }
      json: { foo: "bar" }
      secrets:
        - name: "DB_PASSWORD"
          secret: "{{ vault_db_password }}"
          type: env

  templates:
    job1:
      name: "Run Example"
      app: "ansible"
      type: "job"
      repository_name: "Repo Name"
      inventory_name: "Inventory Name"
      environment_name: "Env Name"
      view_title: "Board Column"
      playbook: "playbooks/site.yml"
      arguments: []
      tags:
        - web
        - prod

  schedules:
    nightly_example:
      name: "Nightly – Run Example"
      cron_format: "0 3 * * *"
      template_name: "Run Example"
      active: false

  integrations:
    webhook_hmac:
      name: "Deploy via HMAC"
      template_name: "Run Example"
      auth_method: "HMAC"
      auth_header: "token"
      auth_secret_name: "hmac-secret"
      task_params:
        diff: false
        dry_run: false

      # OPTIONAL (v2.0.6+)
      extraction_values:
        - name: "Extract Environment"
          key: "X-Env"
          value_source: "header"
          variable_type: "environment"
          variable: "DEPLOY_ENV"

        - name: "Extract Service"
          key: "X-Service"
          value_source: "header"
          variable_type: "environment"
          variable: "SERVICE_NAME"
```

---

## Notes on fields and behavior

### Templates

* `*_name` fields are automatically resolved to IDs.
* `arguments` may be string, list, or dict; lists/dicts are serialized to JSON.
* `tags` are authored as a list and converted to newline-separated strings.

### Schedules

* The API requires `template_id`; `template_name` is resolved automatically.

### Integrations

* `auth_method` uses UI-friendly values; the module converts internally.
* `auth_header` applies only to Token/HMAC and defaults to `"token"`.
* Only `diff` and `dry_run` are configurable in `task_params`.

### Integration Extraction Values (v2.0.6+)

* Optional and **fully backwards compatible**
* Created only when `extraction_values` is defined
* Map incoming request data (headers, payload, query) to task variables
* Existing integrations without extraction values are unaffected

### Pruning

* When `project_deploy_variable_delete: true`, resources not present in YAML are removed.

---

## Example play

```yaml
- hosts: localhost
  vars_files:
    - vars/project.yml
  roles:
    - role: ebdruplab.semaphoreui.project_deploy
```

---

## Tips

* Name-based references are preferred; IDs override names if both are set.
* Enable `project_deploy_debug: true` to inspect intermediate resolution maps.
* Extraction values are additive and safe to introduce incrementally.

---

## License

MIT

## Author

Kristian Ebdrup — [kristian@ebdruplab.dk](mailto:kristian@ebdruplab.dk)
GitHub: [https://github.com/kris9854](https://github.com/kris9854)

> See the **`tests/`** directory for a runnable end-to-end example.

