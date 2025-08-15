# Ansible Role — `ebdruplab.semaphoreui.project_deploy`

Deploy a complete Semaphore project from one declarative variable tree. The role logs in (or uses an API token), validates your config, optionally deletes an existing project, then creates/links **keys, repositories, views, inventories, environments,** and **templates** — idempotently.



## Requirements
- Ansible 2.10+
- Collection: `ebdruplab.semaphoreui` (this role lives inside it)
- A reachable Semaphore instance

## Defaults (quick view)

```yaml
# Connection
project_deploy_semaphore_host: "http://localhost"
project_deploy_semaphore_port: 3000
project_deploy_semaphore_username: "admin"
project_deploy_semaphore_password: "changeme"
# project_deploy_semaphore_api_token: "KEY"

# Safety
project_deploy_sensitive_data_no_log: true        # if sensitive data should be logged or not
project_deploy_force_project_creation: false      # create a new project even if same name exists
project_deploy_force_project_update:   false      # update the first matching project
project_deploy_force_project_delete:   false      # delete all matching projects, then create
project_deploy_force_project_delete_timer: 5      # seconds to pause before delete

# Declarative config (fill these)
project_deploy_config:
  project: []
  keys: []
  repositories: []
  views: []
  inventories: []
  environments: []
  templates: []
````

## What the role does

1. **Auth** via API token *or* username/password.
2. **Preflight** validation of your `project_deploy_config`.
3. **Existing projects**:  
  
   * If none: create a new one.  
   * If some:  
  
     * `project_deploy_force_project_delete: true` → warn + pause → delete → create fresh.  
     * `project_deploy_force_project_creation: true` → create **another** project with same name.  
     * `project_deploy_force_project_update: true` → reuse the first match and update resources.  
     * Otherwise → fail safely.  
4. **Create/link resources** in a sensible order:  
  
   * keys → repositories → views → inventories → environments → templates  
5. **Expose lookups** like `created_*_by_name` so later steps can reference IDs by name.  

## Variable schema (overview)

> Shapes shown are the recommended ones this role expects.

```yaml
project_deploy_config:
  project:
    name: "Your Project"
    alert: false
    alert_chat: ""
    max_parallel_tasks: 0
    demo: false

  keys:                       # map of keys
    key_handle:
      name: "Human Name"
      type: ssh | login_password
      ssh:
        login: "user"
        passphrase: "vault:..."
        private_key: "vault:..."         # multiline OK
      login_password:
        login: "Git User"
        password: "vault:..."

  repositories:               # list
    - name: "Repo Name"
      git_url: "https://..."
      git_branch: "main"
      key_name: "Human Name of a key"    # or key_id

  views:                      # map
    my_view:
      title: "Board Column"
      position: 0

  inventories:                # map
    inv1:
      name: "Static YAML"
      type: static-yaml | static | file
      inventory: |            # for static/static-yaml
        ...
      repository_name: "Repo Name"   # for type=file (or repository_id)
      inventory_file: "path/in/repo.ini"
      ssh_key_name: "SSH key name"    # required
      become_key_name: "Sudo key"     # optional

  environments:               # map
    env1:
      name: "Env Name"
      password: "vault:..."           # optional
      env: { KEY: "value" }           # environment vars
      json: { foo: "bar" }            # extra vars (alias: extra_variables)
      secrets:                         # always create
        - name: "DB_PASSWORD"
          secret: "vault:..."
          type: env                    # or json / extra_variables

  templates:                  # map
    job1:
      name: "Run Example"
      type: "job"
      repository_name: "Repo Name"
      inventory_name: "Inventory Name"
      environment_name: "Env Name"
      view_title: "Board Column"
      playbook: "playbooks/site.yml"
      description: "Runs site"
      arguments: []                   # list (role converts to JSON string)
      vaults: []                      # optional

  schedules:
    nightly_example:
      name: "Nightly – Run Example"
      cron_format: "0 3 * * *"
      template_name: "Run Example"
      active: false # true | false
```

## Example play

```yaml
- hosts: localhost
  vars_files:
    - vars/project.yml
  roles:
    - role: ebdruplab.semaphoreui.project_deploy
```

**`vars/project.yml` (minimal but complete):**

```yaml
project_deploy_semaphore_host: "http://localhost"
project_deploy_semaphore_port: 3000
project_deploy_semaphore_username: "admin"
project_deploy_semaphore_password: "changeme"

project_deploy_force_project_delete: false
project_deploy_force_project_delete_timer: 2

project_deploy_config:
  project:
    name: "Ebdruplab Example Project"
    alert: false
    alert_chat: ""
    max_parallel_tasks: 0
    demo: false

  keys:
    project_ssh:
      name: "Ebdruplab example ssh key"
      type: ssh
      ssh:
        login: "ansibleuser"
        passphrase: "vault:ssh_passphrase"
        private_key: "vault:ssh_private_key"
    git_user:
      name: "Ebdruplab Example User"
      type: login_password
      login_password:
        login: "Fake Git User"
        password: "vault:git_password"

  repositories:
    - name: "Repositorie Ebdruplab Demo"
      git_url: "https://github.com/Ebdruplab/ansible-semaphore_ebdruplab_examples.git"
      git_branch: "main"
      key_name: "Ebdruplab Example User"

  views:
    main:
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
          secret: "vault:db_password"
          type: env
        - name: "api_token"
          secret: "vault:api_token"
          type: json

  templates:
    run_example:
      name: "Run Example Playbook"
      type: "job"
      repository_name: "Repositorie Ebdruplab Demo"
      inventory_name: "A repository Inventory"
      environment_name: "Test Environment"
      view_title: "Examples"
      playbook: "playbooks/pb-semaphore-example.yml"
      arguments: []    # will be serialized to "[]"
      description: "Runs the example Ansible playbook"

  schedules:
    nightly_example:
      name: "Nightly – Run Example Playbook"
      cron_format: "0 3 * * *"
      template_name: "Run Example Playbook"
      active: false
```

## Tips

* **Names → IDs**: The role resolves `*_name` references to IDs and stores maps like `created_repos_by_name`, `created_inventory_by_name`, `created_environments_by_name`, `created_project_view_by_title`, etc., for later steps.
* **Template arguments**: Provide `arguments`/`vaults` as YAML lists or dicts — the role serializes them to JSON strings the API expects.
* **Secrets in environments**: Use `type: env` (environment vars) or `type: json` (extra vars). Aliases `extra_variables`/`extra_vars` are accepted.

## License

MIT

## Author

Kristian Ebdrup <kristian@ebdruplab.dk>
Github: https://github.com/kris9854

