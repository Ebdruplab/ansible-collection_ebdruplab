# Ansible Role: ebdruplab.semaphoreui.project_deploy

This role deploys a complete Semaphore project from a set of structured, namespaced variables. It handles the creation and linking of all associated resources like keys, repositories, inventories, environments, views, and templates. The role is idempotent, meaning it can be run multiple times without causing errors.

## Features

- **Idempotent Project Creation:** Checks if a project with the same name exists before creating it.
- **Declarative Configuration:** Define your entire project, including all resources, in a single YAML structure.
- **Dependency Validation:** Performs pre-flight checks to ensure all resource references (e.g., keys for repositories, inventories for templates) are valid before attempting deployment.
- **Automated Login/Logout:** Handles session management securely.

## Requirements

- Ansible 2.10+
- `ebdruplab.semaphoreui` collection installed.

## Role Variables

The role is configured using a set of `project_deploy_` prefixed variables.

### Connection & Authentication
- `project_deploy_semaphore_host`: URL of the Semaphore server. (Default: `http://localhost`)
- `project_deploy_semaphore_port`: Port of the Semaphore server. (Default: `3000`)
- `project_deploy_semaphore_username`: Username for authentication. (Default: `admin`)
- `project_deploy_semaphore_password`: Password for authentication. (Default: `changeme`)

### Project & Resource Definitions
- `project_deploy_config`: A dictionary containing all resource definitions for the project.
  - `project`: A dictionary defining the project to be created.
  - `keys`: A list of access keys to create.
  - `repositories`: A list of repositories to create.
  - `inventories`: A list of inventories to create.
  - `environments`: A list of environments to create.
  - `views`: A list of views to create.
  - `templates`: A list of templates to create.

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: ebdruplab.semaphoreui.project_deploy
      vars:
        project_deploy_semaphore_host: "http://semaphore.example.com"
        project_deploy_semaphore_port: 3000
        project_deploy_semaphore_username: "admin"
        project_deploy_semaphore_password: "changeme"

        project_deploy_config:
          project:
            name: "My Awesome Project"
            alert: true
            alert_chat: "ops-channel"

          keys:
            - name: "deploy-key"
              type: "ssh"
              ssh:
                login: "git"
                private_key: "{{ lookup('file', '~/.ssh/id_rsa') }}"

          repositories:
            - name: "my-app-repo"
              git_url: "git@github.com:example/my-app.git"
              git_branch: "main"
              key_name: "deploy-key"

          inventories:
            - name: "static-inventory"
              type: "static"
              inventory: "localhost ansible_connection=local"

          environments:
            - name: "production"
              json: '{"foo": "bar"}'

          views:
            - title: "Dashboard"
              position: 1

          templates:
            - name: "Deploy App"
              playbook: "deploy.yml"
              inventory_name: "static-inventory"
              repository_name: "my-app-repo"
              environment_name: "production"
```

## License

MIT

## Author Information

Kristian Ebdrup