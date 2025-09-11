# deploy_semaphore_mcp

Installs and configures the [`semaphore-mcp`](https://github.com/cloin/semaphore-mcp) MCP server **locally** so Claude Desktop (or another MCP client) can talk to your SemaphoreUI instance. Some user interaction is required (e.g., generating an API token).

> **OS support:** Ubuntu/Debian/Fedora and macOS (Darwin).
> **Windows is not supported** for this installation.



## Requirements

1. **Claude Desktop** installed (or another MCP-capable client).
2. A running **SemaphoreUI** instance you can reach.
3. **Python 3.10+** on the target host.
4. (Recommended) `pipx` if you want isolated CLI install via pipx.
5. Ansible collections:

   * `community.general` (for the `pipx` module)

Install the collection:

```bash
ansible-galaxy collection install community.general
# or via a file:
# echo -e "collections:\n  - community.general" > collections/requirements.yml
# ansible-galaxy collection install -r collections/requirements.yml
```



## Role Variables

Below are the primary variables (defaults shown). Override as needed (e.g., in `group_vars`, `host_vars`, or at the play level).

```yaml
# sensitive data
semaphore_mcp_no_log: true

# Installation options
semaphore_mcp_install_method: "pipx"          # "pipx" or "pip"
semaphore_mcp_version: ""                     # e.g. "0.1.9" or empty for latest
semaphore_mcp_python: "python3"               # used by runtime fallback
semaphore_mcp_pip_executable: "pip3"
semaphore_mcp_pipx_executable: "pipx"

# (Optional) manage wrapper/env file – usually disabled when configuring Claude directly
semaphore_mcp_manage_wrapper: false
semaphore_mcp_env_file: "/etc/semaphore-mcp.env"
semaphore_mcp_wrapper_path: "/usr/local/bin/semaphore-mcp-run"

# Claude Desktop command settings (used if writing the Claude config)
semaphore_mcp_command: "semaphore-mcp"
semaphore_mcp_command_args: []

# Runtime env for the MCP server
semaphore_mcp_url: "http://localhost:3000"
semaphore_mcp_api_token: ""                   # REQUIRED – set via vars or Ansible Vault (see tests for example creation)
semaphore_mcp_log_level: ""                   # e.g. DEBUG | INFO | WARN | ERROR

# Validate after install
semaphore_mcp_validate: true

# Supported Systems (preflight gate)
semaphore_mcp_supported_distributions:
  - Ubuntu
  - Debian
  - Fedora
semaphore_mcp_supported_systems:
  - Darwin

# Claude Desktop config paths
semaphore_mcp_claude_config_mac: "~/Library/Application Support/Claude/claude_desktop_config.json"
semaphore_mcp_claude_config_linux: "~/.config/claude-desktop/claude_desktop_config.json"

# Whether the role should modify Claude Desktop config on the target
semaphore_mcp_config_claude: false
```

### Notes

* **API Token is required.** The role fails early if `semaphore_mcp_api_token` is empty. Store it with **Ansible Vault**.
* If `semaphore_mcp_config_claude: true`, the role **adds only missing** keys under `mcpServers.semaphore` in Claude’s config:

  * Adds `SEMAPHORE_URL` and `SEMAPHORE_API_TOKEN` if missing.
  * Adds `command`/`args` if missing.
  * **Does not overwrite** an existing `command`; a warning is shown instead.
* By default we **do not** create a wrapper script or env file. You can enable them by setting `semaphore_mcp_manage_wrapper: true`.



## What the Role Does

* Installs `semaphore-mcp` via **pipx** (default) or **pip**.
* Verifies the CLI is available.
* Optionally updates **Claude Desktop** config with the minimal MCP server block (without disturbing other settings).
* Enforces OS support in **preflight** and fails if unsupported.

**Tags you can use:**

* `install` – installation steps
* `configure` – configuration steps (Claude config, etc.)
* `validate` – verification steps
* `semaphore`, `mcp` – logical grouping
* `secrets` – tasks touching sensitive values

Example:

```bash
ansible-playbook test.yml -K --diff -e semaphore_mcp_config_claude=true
```



## Example Playbook

### Minimal (install only, bring your own Claude config)

```yaml
- hosts: localhost
  gather_facts: false
  roles:
    - role: ebdruplab.semaphoreui.deploy_semaphore_mcp
      vars:
        semaphore_mcp_install_method: pipx
        semaphore_mcp_url: "http://localhost:3000"
        semaphore_mcp_api_token: "{{ vault_semaphore_mcp_token }}"
```

### Install + configure Claude Desktop (adds missing env/command)

```yaml
---
- name: "Example Use"
  hosts: localhost
  gather_facts: true
  vars_files:
    - "vars/example_vars.yml"

  pre_tasks:
    - name: "Pre | Login"
      ebdruplab.semaphoreui.login:
        host: "{{ project_deploy_semaphore_host }}"
        port: "{{ project_deploy_semaphore_port }}"
        username: "{{ project_deploy_semaphore_username | default('admin') }}"
        password: "{{ project_deploy_semaphore_password | default('changeme') }}"
      register: login_result
      tags:
        - token
        - create
        - auth
        - login

    - name: "Generate API token and fact for role"
      block:
        - name: "Create API KEY"
          ebdruplab.semaphoreui.user_token_create:
            host: "{{ project_deploy_semaphore_host }}"
            port: "{{ project_deploy_semaphore_port }}"
            session_cookie: "{{ login_result.session_cookie }}"
          register: _api_key
          tags:
            - token
            - create
      always:
        - name: "Pre | Logout"
          ebdruplab.semaphoreui.logout:
            host: "{{ project_deploy_semaphore_host }}"
            port: "{{ project_deploy_semaphore_port }}"
            session_cookie: "{{ login_result.session_cookie }}"
          tags:
            - token
            - create
            - auth
            - logout

  roles:
    - name: "Import role: deploy_semaphore_mcp"
      role: ebdruplab.semaphoreui.deploy_semaphore_mcp
      vars:
        semaphore_mcp_api_token: "{{ _api_key.token.id }}"


  post_tasks:
    - name: "Post | Login"
      ebdruplab.semaphoreui.login:
        host: "{{ project_deploy_semaphore_host }}"
        port: "{{ project_deploy_semaphore_port }}"
        username: "{{ project_deploy_semaphore_username | default('admin') }}"
        password: "{{ project_deploy_semaphore_password | default('changeme') }}"
      register: login_result
      tags:
        - users
        - auth
        - login

    - name: "Reconcile Service Desk User"
      block:
        - name: "Delete API KEY"
          ebdruplab.semaphoreui.user_token_delete:
            host: "{{ project_deploy_semaphore_host }}"
            port: "{{ project_deploy_semaphore_port }}"
            session_cookie: "{{ login_result.session_cookie }}"
            api_token_id: "{{ _api_key.token.id }}"
          when: semaphore_mcp_cleanup_api_key
          tags:
            - token
            - delete

      always:
        - name: "Post | Logout"
          ebdruplab.semaphoreui.logout:
            host: "{{ project_deploy_semaphore_host }}"
            port: "{{ project_deploy_semaphore_port }}"
            session_cookie: "{{ login_result.session_cookie }}"
          tags:
            - token
            - delete
            - auth
            - logout

```

> Tip: If `semaphore-mcp` isn’t on PATH (common with `pip --user`), set a full path in `semaphore_mcp_command`.



## Post-Install Check

On the target:

```bash
semaphore-mcp --help
```

If configuring Claude Desktop, your file will contain a `"mcpServers": { "semaphore": { ... } }` block with your URL/token. Restart Claude Desktop and test:

```
List all projects in SemaphoreUI
```



## Dependencies

* Ansible collection: `community.general` (for `community.general.pipx`)
* No role dependencies.



## License

MIT



## Author Information

Kristian Ebdrup — [kristian@ebdruplab.dk](mailto:kristian@ebdruplab.dk)

