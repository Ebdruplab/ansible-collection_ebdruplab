# Ansible Collection - `ebdruplab.semaphoreui`

This Ansible collection provides modules for automating the management of [Semaphore UI](https://semaphoreui.com), a modern web interface for Ansible. It allows users to manage projects, templates, inventories, environments, keys, tasks, schedules, users, views, and more directly from Ansible playbooks.

---

## Features

- **Login/logout** support with session cookies or API tokens
- Full **project** lifecycle (create, update, delete, list, get)
- Manage **templates** and **schedules**
- CRUD operations for **inventories**, **repositories**, and **SSH/API keys**
- Manage **tasks** (start, cancel, retrieve logs/output)
- Create and control **environments** and **template variables**
- Support for **user**, **project user** and **token** management
- Role and view administration
- Seamless integration with Semaphore’s REST API (v2+)

---

## Requirements

- Ansible 2.10+
- tested on semaphore UI version 2.14

---

## Included Modules

| Area | Modules |
|------|---------|
| **Auth** | `login`, `logout`, `ping` |
| **Project** | `project_create`, `project_delete`, `project_update`, `project_get`, `project_list`, `project_backup`, `project_restore`, `project_events` |
| **Template** | `project_template_create`, `project_template_update`, `project_template_list`, `project_template_delete` |
| **Schedule** | `project_schedule_create`, `project_schedule_update`, `project_schedule_get`, `project_schedule_list`, `project_schedule_delete` |
| **Task** | `project_task_start`, `project_task_get`, `project_task_list`, `project_task_output_get`, `project_task_logs`, `project_task_raw_output`, `project_task_cancel`, `project_task_delete` |
| **Inventory** | `project_inventory_create`, `project_inventory_update`, `project_inventory_get`, `project_inventory_list`, `project_inventory_delete` |
| **Repository** | `project_repository_create`, `project_repository_update`, `project_repository_get`, `project_repository_list`, `project_repository_delete` |
| **Key** | `project_key_create`, `project_key_get`, `project_key_list`, `project_key_delete` |
| **Environment** | `project_environment_create`, `project_environment_update`, `project_environment_get`, `project_environment_list`, `project_environment_delete` |
| **Template Variables** | `project_template_variable_create`, `project_template_variable_update`, `project_template_variable_get`, `project_template_variable_list`, `project_template_variable_delete` |
| **User Management** | `user_create`, `user_delete`, `user_get`, `user_list`, `user_update`, `user_password_update` |
| **Project User Management** | `porject_user_create`, `porject_user_delete`, `porject_user_update`, `porject_user_list` |
| **Tokens** | `user_token_create`, `user_token_delete`, `user_token_get` |
| **Views & Roles** | `project_view_create`, `project_view_get`, `project_view_list`, `project_view_delete`, `project_role` |
| **WebSocket Status** | `websocket_status` |

---

## Usage

Example for how to use this.


### Example Playbook – Logging in, Creating a Project, and Uploading a Key

This example shows how to authenticate with Semaphore UI, create a project, and upload an SSH key. It uses a session-based login flow and demonstrates secure credential handling using **Ansible Vault**.

```yaml
---
- name: "Provision Semaphore UI project with key"
  hosts: localhost
  gather_facts: false

  vars:
    semaphore_host: "http://semaphore.local"
    semaphore_port: 3000

    # It's highly recommended to store sensitive variables in Ansible Vault
    semaphore_username: "{{ vault_semaphore_username }}"
    semaphore_password: "{{ vault_semaphore_password }}"
    ssh_key_private: "{{ vault_ssh_key_private }}"
    ssh_key_name: "Ansible Deploy Key"

  tasks:
    - name: "Log in to Semaphore"
      ebdruplab.semaphoreui.login:
        host: "{{ semaphore_host }}"
        port: "{{ semaphore_port }}"
        username: "{{ semaphore_username }}"
        password: "{{ semaphore_password }}"
      register: login_result

    - name: "Create a project"
      ebdruplab.semaphoreui.project_create:
        host: "{{ semaphore_host }}"
        port: "{{ semaphore_port }}"
        session_cookie: "{{ login_result.session_cookie }}"
        name: "Automated Project"
        alert: false
        alert_chat: "OpsRoom"
        max_parallel_tasks: 3
        demo: false
      register: project_result

    - name: "Upload SSH key to the project"
      ebdruplab.semaphoreui.project_key_create:
        host: "{{ semaphore_host }}"
        port: "{{ semaphore_port }}"
        session_cookie: "{{ login_result.session_cookie }}"
        project_id: "{{ project_result.project.id }}"
        name: "{{ ssh_key_name }}"
        type: "ssh"
        ssh:
          login: "git"
          private_key: "{{ ssh_key_private }}"
---
- name: "Provision Semaphore UI project with repo and template - ebdruplab_example"
  hosts: localhost
  gather_facts: false

  vars:
    semaphore_host: "http://localhost"
    semaphore_port: 3000
    # Use Ansible Vault for these
    semaphore_username: "{{ vault_semaphore_username }}"
    semaphore_password: "{{ vault_semaphore_password }}"
    ssh_private_key: "{{ vault_ssh_private_key }}"
    project_name: "ebdruplab_example_project"
    repo_name: "ebdruplab_example_repo"
    template_name: "ebdruplab_example_template"

  tasks:
    - name: "Login to Semaphore"
      ebdruplab.semaphoreui.login:
        host: "{{ semaphore_host }}"
        port: "{{ semaphore_port }}"
        username: "{{ semaphore_username }}"
        password: "{{ semaphore_password }}"
      register: login_result

    - name: "Create project"
      ebdruplab.semaphoreui.project_create:
        host: "{{ semaphore_host }}"
        port: "{{ semaphore_port }}"
        session_cookie: "{{ login_result.session_cookie }}"
        name: "{{ project_name }}"
        alert: false
        alert_chat: "ebdruplab"
        max_parallel_tasks: 1
        demo: false
      register: created_project

    - name: "Create SSH key"
      ebdruplab.semaphoreui.project_key_create:
        host: "{{ semaphore_host }}"
        port: "{{ semaphore_port }}"
        session_cookie: "{{ login_result.session_cookie }}"
        project_id: "{{ created_project.project.id }}"
        name: "ebdruplab_example_key"
        type: "ssh"
        ssh:
          login: "git"
          private_key: "{{ ssh_private_key }}"
      register: created_key

    - name: "Create repository"
      ebdruplab.semaphoreui.project_repository_create:
        host: "{{ semaphore_host }}"
        port: "{{ semaphore_port }}"
        session_cookie: "{{ login_result.session_cookie }}"
        project_id: "{{ created_project.project.id }}"
        repository:
          name: "{{ repo_name }}"
          git_url: "git@github.com/Ebdruplab/ansible-semaphore_ebdruplab_examples.git"
          git_branch: "main"
          ssh_key_id: "{{ created_key.key.id }}"
      register: created_repo

    - name: "Create static inventory"
      ebdruplab.semaphoreui.project_inventory_create:
        host: "{{ semaphore_host }}"
        port: "{{ semaphore_port }}"
        session_cookie: "{{ login_result.session_cookie }}"
        project_id: "{{ created_project.project.id }}"
        inventory:
          name: "ebdruplab_example_inventory"
          type: "static"
          inventory: "localhost ansible_connection=local"
      register: created_inventory

    - name: "Create template"
      ebdruplab.semaphoreui.project_template_create:
        host: "{{ semaphore_host }}"
        port: "{{ semaphore_port }}"
        session_cookie: "{{ login_result.session_cookie }}"
        project_id: "{{ created_project.project.id }}"
        template:
          name: "{{ template_name }}"
          app: "ansible"
          playbook: "playbooks/pb-semaphore-example.yml"
          inventory_id: "{{ created_inventory.inventory.id }}"
          repository_id: "{{ created_repo.repository.id }}"
          environment_id: null
          type: "job"
          allow_override_args_in_task: false
          survey_vars: []

    - name: "Logout of Semaphore"
      ebdruplab.semaphoreui.logout:
        host: "{{ semaphore_host }}"
        port: "{{ semaphore_port }}"
        session_cookie: "{{ login_result.session_cookie }}"
```

### Protect Your Credentials

I **strongly recommend** using [Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html) to encrypt your sensitive variables such as:

* Semaphore `username` and `password`
* SSH private keys
* API tokens

#### Encrypt your secrets with:

```bash
ansible-vault encrypt_string 'changeme' --name 'vault_semaphore_password'
```

Or store them in a `vault.yml` file:

```yaml
vault_semaphore_username: admin
vault_semaphore_password: changeme
vault_ssh_key_private: |
  -----BEGIN OPENSSH PRIVATE KEY-----
  ...
```

And then load them into your playbook:

```yaml
vars_files:
  - vault.yml
```

