Changelog
=========

Version 2.0.3
-------------

Role
----
- **Initial public release** of the role `ebdruplab.semaphoreui.deploy_semaphore_mcp`.
  - Installs `semaphore-mcp` locally via **pipx** (default) or **pip**.
  - **Preflight checks**:
    - Enforce supported OS: Ubuntu/Debian/Fedora and macOS (Darwin).
    - Fail fast if required variable `semaphore_mcp_api_token` is missing.
  - **Claude Desktop integration (optional)** when `semaphore_mcp_config_claude: true`:
    - Safely merges only missing keys under `mcpServers.semaphore` (does not overwrite existing values).
    - Adds `SEMAPHORE_URL` and `SEMAPHORE_API_TOKEN` if absent.
    - Adds `command`/`args` if absent and **warns** if an existing `command` differs.
    - OS-aware config paths for macOS/Linux and automatic file backups.
  - **Idempotent install & configure** tasks; organized tags: `install`, `configure`, `validate`, `semaphore`, `mcp`, `secrets`.
  - **Secret-safe logging** with `semaphore_mcp_no_log: true`.
  - Optional `MCP_LOG_LEVEL` via `semaphore_mcp_log_level`.
  - Wrapper/env management is **disabled by default** (`semaphore_mcp_manage_wrapper: false`) but available if needed.


Version 2.0.2
-------------
Minor bug fixes

Version 2.0.1
-------------

**Fetures, fixes and documentation**

- Adding new feature to the ``project_deploy`` role.
  - Added and reworked the role to be able to handle ``project_deploy_force_project_update``.
  - It will then update ``projects``, ``templates``, ``keys``, ``schedules``, ``integrations``, ``users_access``, ``inventories``, ``views``, ``environments`` and ``repositories``.

- **plugins/modules/project_integration_update.py**
  - Accepts both UI labels and slugs for auth_method (e.g., Token and token, HMAC and hmac).
  - Normalizes to API slugs and applies smart defaults for auth_header:
    - token → token
    - hmac → X-Hub-Signature-256
  - Resolves the error: “value of auth_method must be one of … got: token” when playbooks pass the slug.

- **plugins/modules/project_integration_create.py**
  - Documentation/examples clarified that labels and slugs are accepted.
  - Default header logic documented; task_params.environment is JSON-encoded when a dict/list is provided.

- **plugins/modules/project_template_update.py**
  - Rewrote DOCUMENTATION to satisfy ansible-doc (no nested mappings in a description list item; every (sub-)option has a description).
  - Added complete EXAMPLES.
  - Normalizes tags / skip_tags (list or string → newline-separated string).
  - Accepts task_params.tags, task_params.skip_tags, task_params.limit as string or list.
  - Maps common aliases (camelCase & legacy) to canonical fields.
  - Drops task_params and survey_vars for job templates (API quirk) to avoid 400s.

- **plugins/modules/semaphore_template_create.py**
  - Documentation aligned with the original example style while fixing invalid/missing bits to pass ansible-doc.
  - Fix: tags / skip_tags normalization; applies prompt_* via follow-up PUT (includes app and type to avoid “Invalid app id”).
  - Create fallbacks for job templates that reject task_params.allow_debug.

- **plugins/modules/project_repository_update.py**
  - Added missing description on all options/suboptions/returns to resolve:
    - “All (sub-)options and return values must have a 'description' field.”

Module Added
~~~~~~~~~~~~

- **user_password_update.py**  
  Added so we are able to update user's password using Ansible.

- **project_key_update.py**  
  Added so we are able to update keys using Ansible.

- **project_view_update.py**  
  Added a way to update views using Ansible.

Module update
~~~~~~~~~~~~~
- **plugins/modules/project_integration_update.py**  
  Fixed the documentation and fixed problems with updating integrations as there where a missing key.

- **project_backup.py**
  - ``plugins/modules/project_backup.py``: Hardened response handling
    - Now accepts ``bytes``, ``str``, or already-decoded ``dict`` from ``semaphore_get`` and normalizes to a Python ``dict``.
  - ``plugins/modules/project_backup.py``: Improved error messages
    - On non-200 responses, includes HTTP status **and** a readable response body (decodes bytes / dumps dicts) to aid debugging.
  - ``plugins/modules/project_backup.py``: Return metadata
    - Explicitly returns ``changed: false`` (read-only GET) and ``status`` (HTTP status code).
  - ``plugins/modules/project_backup.py``: Header cleanup
    - Removed unnecessary ``Content-Type: application/json`` header on GET requests.
  - ``plugins/modules/project_backup.py``: Robust URL construction
    - Uses ``host.rstrip("/")`` and passes named parameters (``url``, ``headers``, ``validate_certs``) to ``semaphore_get``.
  - ``plugins/modules/project_backup.py``: Documentation polish
    - Clarified endpoint path (``GET /api/project/{project_id}/backup``), examples include schedules discovery, and documented new return fields.

Role
----
- **roles/project_deploy**
  - Integration tasks now tolerate label/slug inputs and resolve template_id from either explicit template_id, template_name, or newly created templates.
  - Additional facts/maps and optional debug output to make schedule/integration resolution visible.
  - (Docs) Provided schedule management snippets clarifying create/update/prune flow.

Bug fixes
-------------

**Bug fix:**

- `ebdruplab.semaphoreui.project_user_update <https://github.com/Ebdruplab/Ansible-collection_ebdruplab/issues/4>`_

Version 2.0.0
-------------

Added
~~~~~

Module Added
^^^^^^^^^^^^

- **project_integration_create** — Added so we are able to create integrations through Ansible on the Semaphore UI platform.

Module changes
^^^^^^^^^^^^^^

- **project_inventory_create** — Added support for ``ssh_key_id`` (required) and ``become_key_id`` (optional) parameters.
- **project_inventory_update** — Added support for ``ssh_key_id`` and ``become_key_id`` parameters.

Roles added
^^^^^^^^^^^

- **project_deploy** — Added to support a high level YAML vars file to populate with project, inventory keys and more.

Version 2.0.4
-------------
Fixed bug: https://github.com/Ebdruplab/ansible-collection_ebdruplab/issues/11


Initial release; no further info.
