Changelog
=========

Version 2.0.1
-------------

**Fetures**

- Adding new feature to the ``project_deploy`` role.
  - Added and reworked the role to be able to handle ``project_deploy_force_project_update``.
  - It will then update ``projects``, ``templates``, ``keys``, ``schedules``, ``integrations``, ``users_access``, ``inventories``, ``views``, ``environments`` and ``repositories``.

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

Version 2.0.1
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

Version 1.0.0
-------------

Initial release; no further info.
