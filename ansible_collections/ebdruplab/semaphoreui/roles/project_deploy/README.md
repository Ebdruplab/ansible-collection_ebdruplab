# Ansible Role: `ebdruplab.semaphoreui.project_deploy`

This role deploys a full Semaphore project from one YAML configuration.

It can create or update:

- the project itself
- project users
- keys
- repositories
- views
- inventories
- environments
- templates
- schedules
- integrations
- integration extraction values

The goal is simple: describe your project once in YAML and let the role build it in Semaphore.

## Requirements

- Ansible 2.16+
- The `ebdruplab.semaphoreui` collection
- A working Semaphore instance
- Login credentials or an API token

## Main Variables

### Connection

```yaml
project_deploy_semaphore_host: "http://localhost"
project_deploy_semaphore_port: 3000
project_deploy_semaphore_username: "admin"
project_deploy_semaphore_password: "changeme"
# project_deploy_semaphore_api_token: "KEY"
```

You can use either:

- username and password
- API token

### Safety Flags

```yaml
project_deploy_debug: false
project_deploy_sensitive_data_no_log: true
project_deploy_force_project_creation: false
project_deploy_force_project_update: false
project_deploy_force_project_delete: false
project_deploy_force_project_delete_timer: 5
project_deploy_variable_delete: false
```

What they do:

- `project_deploy_force_project_update`: update an existing project with the same name
- `project_deploy_force_project_delete`: delete and recreate the project
- `project_deploy_force_project_creation`: create a new project even if one with the same name already exists
- `project_deploy_variable_delete`: remove items in Semaphore that are not present in your YAML

## Basic Configuration

```yaml
project_deploy_config:
  project:
    name: "My Project"
    alert: false
    alert_chat: ""
    max_parallel_tasks: 0
    demo: false

  users_access:
    - username: "admin"
      role: "Owner"

  keys: {}
  repositories: []
  views: {}
  inventories: {}
  environments: {}
  templates: {}
  schedules: {}
  integrations: {}
```

Use `{}` for map-based sections like `keys`, `views`, `inventories`, `environments`, `templates`, `schedules`, and `integrations`.

## Simple Example

```yaml
project_deploy_config:
  project:
    name: "Demo Project"

  users_access:
    - username: "admin"
      role: "Owner"

  keys:
    repo_key:
      name: "Git Login"
      type: login_password
      login_password:
        login: "git-user"
        password: "{{ vault_git_password }}"

  repositories:
    - name: "Example Repo"
      git_url: "https://github.com/example/repo.git"
      git_branch: "main"
      key_name: "Git Login"

  views:
    main:
      title: "Main"
      position: 0

  inventories:
    local_inventory:
      name: "Local Inventory"
      type: static
      inventory: "localhost ansible_connection=local"

  environments:
    default_env:
      name: "Default Environment"
      env:
        APP_ENV: "prod"

  templates:
    deploy_job:
      name: "Deploy"
      type: job
      repository_name: "Example Repo"
      inventory_name: "Local Inventory"
      environment_name: "Default Environment"
      view_title: "Main"
      playbook: "playbooks/site.yml"
```

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
  vars_files:
    - vars/project.yml
  roles:
    - role: ebdruplab.semaphoreui.project_deploy
```

## How It Works

The role will:

1. authenticate to Semaphore
2. validate your config
3. create the project if it does not exist
4. update the project if `project_deploy_force_project_update` is enabled
5. create or sync the project resources in the correct order

If a project already exists and no force flag is enabled, the role fails safely instead of changing it by accident.

## Notes

- Name-based references such as `repository_name`, `inventory_name`, `environment_name`, and `template_name` are resolved automatically.
- Integrations can include `extraction_values` if you want to map headers, payload values, or query values into variables.
- Set `project_deploy_debug: true` if you want extra debug output while testing.
- A full working example is available in the role `tests/` folder.

## License

MIT

## Author Information

Kristian Ebdrup  
Email: [kristian@ebdruplab.dk](mailto:kristian@ebdruplab.dk)  
GitHub: [https://github.com/kris9854](https://github.com/kris9854)
