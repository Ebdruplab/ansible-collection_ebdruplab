# Ansible Role — `ebdruplab.semaphoreui.project_deploy`

Deploy a complete Semaphore project from one declarative variable tree. The role logs in (or uses an API token), validates your config, optionally deletes an existing project, then creates/links **keys, repositories, views, inventories, environments, templates, schedules,** and **integrations** — idempotently.

You can see a working example under the repository’s **`tests/`** directory.

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
project_deploy_debug: false                       # Extra debug logs
project_deploy_sensitive_data_no_log: true        # Hide sensitive values in task logs
project_deploy_force_project_creation: false      # Always create a new project (even if same name exists)
project_deploy_force_project_update:   false      # Reuse first matching project and sync resources
project_deploy_force_project_delete:   false      # Delete matching project(s) before creating fresh
project_deploy_force_project_delete_timer: 5      # Seconds to pause before delete

# Pruning (delete items not present in your YAML)
project_deploy_variable_delete: false

# Declarative config (preferred shapes shown below)
project_deploy_config:
  project: {}
  users_access: []          # list
  keys: {}                  # map (handle -> key spec)
  repositories: []          # list
  views: {}                 # map (handle -> {title, position})
  inventories: {}           # map
  environments: {}          # map
  templates: {}             # map
  schedules: {}             # map
  integrations: {}          # map
```

> If you previously used empty lists (`[]`) for maps, switch to `{}` to match the role’s expectations (most task files iterate with `dict2items`).

---

## What the role does

1. **Auth** via API token *or* username/password.

2. **Preflight** validation of your `project_deploy_config`.

3. **Existing projects**

   * None → **create** a new one
   * Found → behavior depends on flags

     * `project_deploy_force_project_delete: true` → pause → **delete** → **create fresh**
     * `project_deploy_force_project_creation: true` → **create another** project with same name
     * `project_deploy_force_project_update: true` → **reuse** first match and **sync** resources
     * Otherwise → **fail safely**

4. **Create/link resources in order**
   keys → repositories → views → inventories → environments → templates → schedules → integrations

5. **Expose lookups** so later steps can resolve IDs by name/title:
   `created_keys_by_name`, `created_repos_by_name`, `created_project_view_by_title`, `created_inventory_by_name`, `created_environments_by_name`, `created_templates_by_name`, `created_schedules_by_name`, `created_integrations_by_name`.

6. **Pruning** (when `project_deploy_variable_delete: true`)

   * Removes **schedules**, **integrations**, **templates** (and other supported resources) that exist in Semaphore but are **not** present in your YAML.

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

  users_access:                      # list (users must already exist in Semaphore)
    - username: "admin"
      role: "Owner"                  # Owner | Manager | Task Runner | Guest (case/space-insensitive)

  keys:                              # map
    key_handle:
      name: "Human Name"
      type: ssh | login_password
      ssh:
        login: "ansibleuser"
        passphrase: "{{ vault_passphrase }}"
        private_key: "{{ vault_private_key_multiline }}"
      login_password:
        login: "Git User"
        password: "{{ vault_git_password }}"

  repositories:                      # list
    - name: "Repo Name"
      git_url: "https://github.com/org/repo.git"
      git_branch: "main"
      key_name: "Human Name of a key"      # or ssh_key_id

  views:                             # map
    my_view:
      title: "Board Column"
      position: 0

  inventories:                       # map
    inv1:
      name: "Static YAML"
      type: static-yaml | static | file
      inventory: |                   # for static/static-yaml
        all:
          hosts:
            localhost:
              ansible_connection: local
      repository_name: "Repo Name"   # for type=file (or repository_id)
      inventory_file: "path/in/repo.ini"
      ssh_key_name: "SSH key name"   # required
      become_key_name: "SSH key name (become)"   # optional

  environments:                      # map
    env1:
      name: "Env Name"
      password: "{{ vault_env_password | default('', true) }}"
      env: { KEY: "value" }          # environment variables (non-secret)
      json: { foo: "bar" }           # extra variables (non-secret) – alias: extra_variables
      secrets:                       # always created/ensured
        - name: "DB_PASSWORD"
          secret: "{{ vault_db_password }}"
          type: env                  # env | json

  templates:                         # map
    job1:
      name: "Run Example"
      app: "ansible"                 # default if omitted
      type: "job"
      repository_name: "Repo Name"   # or repository_id
      inventory_name: "Inventory Name" # or inventory_id
      environment_name: "Env Name"   # or environment_id (optional)
      view_title: "Board Column"     # or view_id (optional)
      playbook: "playbooks/site.yml"
      description: "Runs site"
      arguments: []                  # list/dict OK; role serializes to JSON string
      vaults: []                     # optional list of {id, type}
      tags:                          # the API expects newline-separated string; give list and role joins with '\n'
        - web
        - prod

  schedules:                         # map
    nightly_example:
      name: "Nightly – Run Example"
      cron_format: "0 3 * * *"
      template_name: "Run Example"   # or template_id
      active: false
      arguments: []                  # optional (role serializes when needed)

  integrations:                      # map
    webhook_hmac:
      name: "Deploy via HMAC"
      template_name: "Run Example"   # or template_id
      auth_method: "HMAC"            # None | GitHub Webhooks | Bitbucket Webhooks | Token | HMAC | BasicAuth
      auth_header: "token"           # only for Token/HMAC; defaults to "token"
      auth_secret_name: "hmac-secret"  # or auth_secret_id
      task_params:
        diff: false
        dry_run: false
```

### Notes on fields and conversions

* **Templates**

  * The `project_template_create` module requires: `name`, `app`, `playbook`, `inventory_id`, `repository_id`. The role resolves `*_name` → IDs for you when possible.
  * `arguments`: Provide a string **or** list/dict. Lists/dicts are serialized to a JSON string (e.g., `[]`).
  * `tags`: Provide a **list** in YAML; the role will join it with `'\n'` to match the API’s newline-separated string.
  * When **updating** templates, the role only sends supported fields (does **not** include `template.id` or `template.project_id` in the payload).

* **Schedules**

  * `template_id` is required by the API. The role will resolve `template_name` → `template_id` using existing/created templates.

* **Integrations**

  * `auth_method` uses UI-friendly values; the module converts to API codes.
  * `auth_header` only applies to **Token**/**HMAC** and defaults to `"token"` when omitted.
  * `task_params.debug_level` is pinned to `4` by the module; you can set only `diff` and `dry_run`.

* **Pruning**

  * When `project_deploy_variable_delete: true`, the role removes existing **schedules**, **integrations**, and **templates** not present in `project_deploy_config`.

---

## Example play

```yaml
- hosts: localhost
  vars_files:
    - vars/project.yml
  roles:
    - role: ebdruplab.semaphoreui.project_deploy
```

### `vars/project.yml` (minimal but complete)

```yaml
project_deploy_semaphore_host: "http://localhost"
project_deploy_semaphore_port: 3000
project_deploy_semaphore_username: "admin"
project_deploy_semaphore_password: "changeme"

project_deploy_debug: false
project_deploy_sensitive_data_no_log: false
project_deploy_force_project_update: true
project_deploy_variable_delete: true

project_deploy_config:
  project:
    name: "Ebdruplab Example Project"
    alert: false
    alert_chat: ""
    max_parallel_tasks: 0
    demo: false

  users_access:
    - username: "ServiceDeskRunner"
      role: task_runner

  keys:
    project_ssh:
      name: "Ebdruplab example ssh key"
      type: ssh
      ssh:
        login: "ansibleuser"
        passphrase: "{{ vaulted_pk_passphrase }}"
        private_key: "{{ vaulted_pk_private_key }}"
    git_user:
      name: "Ebdruplab Example User"
      type: login_password
      login_password:
        login: "Fake Git User"
        password: "{{ vaulted_git_password }}"

  repositories:
    - name: "Repositorie Ebdruplab Demo"
      git_url: "https://github.com/Ebdruplab/ansible-semaphore_ebdruplab_examples.git"
      git_branch: "main"
      key_name: "Ebdruplab Example User"

  views:
    examples:
      title: "Examples"
      position: 0

  inventories:
    inv_repo:
      name: "A repository Inventory"
      type: "file"
      repository_name: "Repositorie Ebdruplab Demo"
      inventory_file: "inventories/example/example.ini"
      ssh_key_name: "Ebdruplab example ssh key"
      become_key_name: "Ebdruplab example ssh key"

  environments:
    env1:
      name: "Test Environment"
      env:
        KEY: "value"
      json:
        foo: "bar"
      secrets:
        - name: "DB_PASSWORD"
          secret: "{{ vaulted_db_password }}"
          type: env
        - name: "api_token"
          secret: "{{ vaulted_api_token }}"
          type: json

  templates:
    run_example:
      name: "Run Example Playbook"
      app: "ansible"
      type: "job"
      repository_name: "Repositorie Ebdruplab Demo"
      inventory_name: "A repository Inventory"
      environment_name: "Test Environment"
      view_title: "Examples"
      playbook: "playbooks/pb-semaphore-example.yml"
      description: "Runs the example Ansible playbook"
      arguments: []
      tags:
        - demo
        - example

  schedules:
    nightly_example:
      name: "Nightly – Run Example Playbook"
      cron_format: "0 3 * * *"
      template_name: "Run Example Playbook"
      active: false

  integrations:
    webhook_hmac:
      name: "Deploy via HMAC"
      template_name: "Run Example Playbook"
      auth_method: "HMAC"
      auth_header: "token"
      auth_secret_name: "hmac-secret"
      task_params:
        diff: false
        dry_run: false
```

---

## Tips

* **Names → IDs** are resolved automatically where possible. If you specify both, IDs win.
* **Arguments/Vaults** can be given as strings or list/dict; lists/dicts are serialized to API-friendly strings.
* **Template tags** should be authored as a **YAML list**; the role converts to a newline-separated string that the API expects.
* **Debugging**: set `project_deploy_debug: true` to see helpful interim maps (e.g., desired vs. existing resources).

---

## License

MIT

## Author

Kristian Ebdrup — [kristian@ebdruplab.dk](mailto:kristian@ebdruplab.dk)
GitHub: [https://github.com/kris9854](https://github.com/kris9854)

> Want to see this role in action? Check the **`tests/`** folder for a runnable example.
