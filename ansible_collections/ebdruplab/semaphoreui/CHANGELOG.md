# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] – 2025-05-26

### Added
- **Ansible Collection "ebdruplab.semaphoreui" initial release**  
  - Collection metadata (`galaxy.yml`) with author, description, license, and version fields.
  - Directory layout:
    ```
    semaphoreui/
    ├── galaxy.yml
    ├── docs/
    ├── plugins/
    │   ├── module_utils/
    │   │   └── semaphore_api.py
    │   └── modules/
    │       ├── apps_list.py
    │       ├── events.py
    │       ├── events_last.py
    │       ├── info.py
    │       ├── login.py
    │       ├── logout.py
    │       ├── ping.py
    │       ├── project_backup.py
    │       ├── project_create.py
    │       ├── project_delete.py
    │       ├── project_environment_create.py
    │       ├── project_environment_delete.py
    │       ├── project_environment_get.py
    │       ├── project_environment_list.py
    │       ├── project_environment_update.py
    │       ├── project_events.py
    │       ├── project_get.py
    │       ├── project_inventory_create.py
    │       ├── project_inventory_delete.py
    │       ├── project_inventory_get.py
    │       ├── project_inventory_list.py
    │       ├── project_inventory_update.py
    │       ├── project_key_create.py
    │       ├── project_key_delete.py
    │       ├── project_key_get.py
    │       ├── project_key_list.py
    │       ├── project_list.py
    │       ├── project_repository_create.py
    │       ├── project_repository_delete.py
    │       ├── project_repository_get.py
    │       ├── project_repository_list.py
    │       ├── project_repository_update.py
    │       ├── project_restore.py
    │       ├── project_role.py
    │       ├── project_schedule_create.py
    │       ├── project_schedule_delete.py
    │       ├── project_schedule_get.py
    │       ├── project_schedule_list.py
    │       ├── project_schedule_update.py
    │       ├── project_task_cancel.py
    │       ├── project_task_delete.py
    │       ├── project_task_get.py
    │       ├── project_task_list.py
    │       ├── project_task_logs.py
    │       ├── project_task_output_get.py
    │       ├── project_task_raw_output.py
    │       ├── project_task_start.py
    │       ├── project_tasks_list.py
    │       ├── project_template_create.py
    │       ├── project_template_delete.py
    │       ├── project_template_list.py
    │       ├── project_template_update.py
    │       ├── project_update.py
    │       ├── project_view_create.py
    │       ├── project_view_delete.py
    │       ├── project_view_get.py
    │       ├── project_view_list.py
    │       ├── user_create.py
    │       ├── user_delete.py
    │       ├── user_get.py
    │       ├── user_list.py
    │       ├── user_password_update.py
    │       ├── user_token_create.py
    │       ├── user_token_delete.py
    │       ├── user_token_get.py
    │       ├── user_update.py
    │       ├── websocket_status.py
    │       └── (all modules include full `DOCUMENTATION`, `EXAMPLES`, and `RETURN` stanzas)
    ├── tests/
    │   ├── integration/
    │   │   ├── apps_list/
    │   │   ├── events/
    │   │   ├── info/
    │   │   ├── login_logout/
    │   │   ├── project_backup/
    │   │   ├── project_create_delete/
    │   │   ├── project_environments/
    │   │   ├── project_events/
    │   │   ├── project_get/
    │   │   ├── project_inventory/
    │   │   ├── project_key/
    │   │   ├── project_list/
    │   │   ├── project_repository/
    │   │   ├── project_restore/
    │   │   ├── project_role/
    │   │   ├── project_schedule/
    │   │   ├── project_tasks/
    │   │   ├── project_template/
    │   │   ├── project_update/
    │   │   ├── project_view/
    │   │   ├── user_crud/
    │   │   └── websocket_status/
    │   └── scripts/
    │       ├── run_all_tests.sh
    │       └── set_env_for_integration.sh
    └── CHANGELOG.md
    ```
- **New "module_utils/semaphore_api.py"**  
  - Provides a reusable Python client for the Semaphore API.  
  - Implements authentication, CRUD operations, and error handling.  
  - Replaces raw `urlopen()` calls with `open_url()` for full Ansible compatibility.

- **Modules Added** (complete list):  
  - **Authentication & Basic Info**  
    - `login.py`: Log in to Semaphore, obtain session cookie or token.  
    - `logout.py`: Terminate a Semaphore session.  
    - `ping.py`: Health check—ensure API endpoint is reachable.  
    - `info.py`: Gather general Semaphore account info (user limits, quotas, etc.).  

  - **Listing Resources**  
    - `apps_list.py`: List available Semaphore applications.  
    - `events.py`: List all events for a given project or globally.  
    - `events_last.py`: Retrieve the most recent event.  
    - `user_list.py`: List all users associated with the Semaphore account.  
    - `project_list.py`: List all projects.  
    - `project_inventory_list.py`: List all inventories for a project.  
    - `project_key_list.py`: List all SSH keys in a project.  
    - `project_repository_list.py`: List all repositories in a project.  
    - `project_role.py`: List or assign roles in a project.  
    - `project_schedule_list.py`: List all schedules attached to a project.  
    - `project_tasks_list.py`: List all tasks for a project.  
    - `project_template_list.py`: List all job templates in a project.  
    - `project_view_list.py`: List all views in a project.  
    - `websocket_status.py`: Check the status of any WebSocket connections.  

  - **Create Operations**  
    - `project_create.py`: Create a new Semaphore project.  
    - `project_environment_create.py`: Create a new environment for an existing project.  
    - `project_inventory_create.py`: Create a new inventory for a project.  
    - `project_key_create.py`: Upload or create a new SSH key.  
    - `project_repository_create.py`: Add a new repository to a project (with Git URL, branch, SSH key).  
    - `project_schedule_create.py`: Create a scheduled job.  
    - `project_task_start.py`: Manually start a project task/job.  
    - `project_template_create.py`: Create a new job template.  
    - `project_view_create.py`: Create a new view in the project.  
    - `user_create.py`: Add a new user to the Semaphore account.  
    - `user_token_create.py`: Generate an API token for a user.  

  - **Read / Get Operations**  
    - `project_get.py`: Retrieve details (metadata, settings) about a specific project.  
    - `project_environment_get.py`: Fetch details of an environment within a project.  
    - `project_inventory_get.py`: Fetch details of a specific inventory.  
    - `project_key_get.py`: Retrieve details of a specific SSH key.  
    - `project_repository_get.py`: Retrieve details of a specific repository.  
    - `project_schedule_get.py`: Retrieve details of a specific schedule.  
    - `project_task_get.py`: Fetch details of a specific task.  
    - `project_task_logs.py`: Retrieve logs for a given project task.  
    - `project_task_output_get.py`: Retrieve raw or formatted output of a project task.  
    - `project_template_get.py`: Retrieve details of a specific job template.  
    - `project_view_get.py`: Retrieve details of a specific view.  
    - `user_get.py`: Fetch a user’s details by user ID.  
    - `user_token_get.py`: Retrieve details of a specific user token.  

  - **Update Operations**  
    - `project_environment_update.py`: Modify an existing environment’s settings.  
    - `project_inventory_update.py`: Rename or alter properties of an inventory.  
    - `project_key_update.py`: (Not included in v1.0.0 — deferred to next minor release.)  
    - `project_repository_update.py`: Change repository URL, branch, or SSH key association.  
    - `project_schedule_update.py`: Modify schedule metadata (cron expression, next run date).  
    - `project_task_raw_output.py`: Adjust output formatting settings for raw logs.  
    - `project_template_update.py`: Update an existing job template’s configuration.  
    - `project_update.py`: Update project settings (name, description, tags).  
    - `project_view_update.py`: Modify an existing view’s filter or columns.  
    - `user_update.py`: Update user fields (email, role, status).  

  - **Delete Operations**  
    - `project_delete.py`: Remove a project and all associated resources.  
    - `project_environment_delete.py`: Delete an environment from a project.  
    - `project_inventory_delete.py`: Delete an inventory from a project.  
    - `project_key_delete.py`: Remove an SSH key from a project.  
    - `project_repository_delete.py`: Remove a repository from a project.  
    - `project_schedule_delete.py`: Delete a scheduled job.  
    - `project_task_cancel.py`: Cancel a running task/job.  
    - `project_task_delete.py`: Remove task records from a project.  
    - `project_template_delete.py`: Delete a job template.  
    - `project_view_delete.py`: Remove a view.  
    - `user_delete.py`: Delete a user from the Semaphore account.  
    - `user_token_delete.py`: Revoke a specific user token.  
    - `project_restore.py`: Restore a previously deleted resource (projects only; placeholder for future).  

- **Integration Tests** (under `tests/integration/`):  
  - “Smoke test” playbooks for each major module category:  
    - `apps_list: test_apps_list.yml`  
    - `events: test_events.yml`  
    - `info: test_info.yml`  
    - `login_logout: test_login_logout.yml`  
    - `ping: test_ping.yml`  
    - **Project CRUD:**  
      - `project_create_delete: test_project_create.yml`, `test_project_delete.yml`  
      - `project_environments: test_project_environment_create.yml`, `test_project_environment_delete.yml`  
      - `project_inventory: test_project_inventory_create.yml`, `test_project_inventory_delete.yml`  
      - `project_key: test_project_key_create.yml`, `test_project_key_delete.yml`  
      - `project_repository: test_project_repository_create.yml`, `test_project_repository_delete.yml`  
      - `project_restore: test_project_restore.yml`  
      - `project_role: test_project_role.yml`  
      - `project_schedule: test_project_schedule_create.yml`, `test_project_schedule_delete.yml`  
      - `project_tasks: test_project_task_start.yml`, `test_project_task_cancel.yml`  
      - `project_template: test_project_template_create.yml`, `test_project_template_delete.yml`  
      - `project_update: test_project_update.yml`  
      - `project_view: test_project_view_create.yml`, `test_project_view_delete.yml`  
      - `project_event: test_project_events.yml`  
    - **User CRUD:**  
      - `user_crud: test_user_create.yml`, `test_user_delete.yml`, `test_user_update.yml`  
      - `user_token: test_user_token_create.yml`, `test_user_token_delete.yml`  
    - **WebSocket Status:**  
      - `websocket_status: test_websocket_status.yml`  

- **Continuous Integration / Linting Configuration**  
  - Included `.github/workflows/ci.yml` (or equivalent) for:  
    - Running `ansible-test sanity ansible_tools` on all modules and test playbooks.  
    - Python versions tested: 3.13 (with warnings for 3.8–3.12 skipped).  
    - `yamllint` checks against each test playbook.  
    - `shellcheck` (skipped if not installed).  
  - Pre-commit hooks (suggested) for:  
    - Enforcing PEP 8 (via `autopep8` or `flake8`).  
    - Stripping trailing whitespace.  
    - Ensuring two blank lines before top-level definitions.  

- **Documentation / Examples**  
  - `README.md` updated with:  
    - Installation instructions (`ansible-galaxy collection install ebdruplab`).  
    - Basic usage examples for each high-level module (e.g., how to create a project, list repositories, etc.).  
    - Role of `semaphore_api.py` in module utilities.  
    - Supported Ansible versions (e.g., Ansible Core 2.18+).  
  - Added license references in every module’s header (GPLv3).  
  - `docs/` directory stub created (to be populated in 1.1.0 with detailed module docs).  

- **Licensing**  
  - All modules and collection files now include a GPLv3 license header in the first 20 lines.  
  - Switched all smart quotes to ASCII quotes (`'`, `"`).  

- **Packaging**  
  - Added `MANIFEST.in` to include all Python modules, test playbooks, docs, and `CHANGELOG.md`.  
  - Ensured `plugins/modules/` and `plugins/module_utils/` are included when building the collection.  

### Changed
- Not applicable for the initial release (everything is new).

### Fixed
- Not applicable for the initial release (no prior bugs to fix).

### Deprecated
- None in this version.

### Removed
- None in this version.

### Security
- None in this version.

## [1.0.1] – 2025-06-05

### Changed
- Added changelog.md

### Fixed
- ran `ansible-test sanity`, and ran throug fixing items
