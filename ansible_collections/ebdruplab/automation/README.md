# ebdruplab.automation

Ansible automation utilities and callback plugins.

## Included Plugins

| Plugin | Type | Description |
|---|---|---|
| `http_event` | callback | Send HTTP webhook events based on Ansible playbook results |

# http_event Callback Plugin

The `http_event` callback plugin is created to enhance the ability to trigger external automation workflows when an Ansible playbook completes.

The plugin can send HTTP requests based on the final playbook result:

- success
- failure
- unreachable

It was initially created to enhance Semaphore UI workflows, but it is designed to work with any automation platform, orchestration system, monitoring solution, CI/CD platform, or webhook-based integration.

Any system capable of receiving an HTTP webhook can consume events from this plugin.

Examples:

- Semaphore UI
- Rundeck
- AWX / Ansible Automation Platform
- GitLab CI
- Jenkins
- Argo Workflows
- Home Assistant
- Slack webhook integrations
- Discord webhook integrations
- Custom internal APIs

# Features

- Separate webhook URLs for:
  - success
  - failure
  - unreachable

- Token authentication support

- Custom authentication headers

- Configurable HTTP methods

- Configurable status header

- Additional static headers

- Optional affected-host header

- JSON payload support

- TLS certificate validation control

- Environment variable support

- `ansible.cfg` configuration support

- Non-blocking behavior
  - webhook failures do not fail the Ansible playbook

# Installation

## Install from source

```bash
ansible-galaxy collection install ebdruplab.automation
````

## Local development install

```bash
ansible-galaxy collection build
ansible-galaxy collection install ebdruplab-automation-*.tar.gz
```

# Enable the Callback Plugin

Add the callback plugin to `ansible.cfg`.

```ini
[defaults]
callbacks_enabled = ebdruplab.automation.http_event
```

# Configuration

The plugin supports configuration from:

* `ansible.cfg`
* environment variables

Environment variables override values from `ansible.cfg`.

# ansible.cfg Example

```ini
[defaults]
callbacks_enabled = ebdruplab.automation.http_event

[callback_http_event]
enabled = true

success_url = https://automation.example.com/api/success
failure_url = https://automation.example.com/api/failure
unreachable_url = https://automation.example.com/api/unreachable

auth_token = super-secret-token
auth_header = Authorization
auth_scheme = Bearer

status_header = X-Ansible-Job-Status

extra_headers = X-Environment=production,X-Source=ansible

host_header = X-Ansible-Hosts

timeout = 10
validate_certs = true

method = POST
send_body = true
```

# Environment Variable Example

```bash
export EBDRUPLAB_AUTOMATION_HTTP_EVENT_ENABLED="true"

export EBDRUPLAB_AUTOMATION_HTTP_EVENT_SUCCESS_URL="https://automation.example.com/api/success"
export EBDRUPLAB_AUTOMATION_HTTP_EVENT_FAILURE_URL="https://automation.example.com/api/failure"
export EBDRUPLAB_AUTOMATION_HTTP_EVENT_UNREACHABLE_URL="https://automation.example.com/api/unreachable"

export EBDRUPLAB_AUTOMATION_HTTP_EVENT_AUTH_TOKEN="super-secret-token"
export EBDRUPLAB_AUTOMATION_HTTP_EVENT_AUTH_HEADER="Authorization"
export EBDRUPLAB_AUTOMATION_HTTP_EVENT_AUTH_SCHEME="Bearer"

export EBDRUPLAB_AUTOMATION_HTTP_EVENT_STATUS_HEADER="X-Ansible-Job-Status"

export EBDRUPLAB_AUTOMATION_HTTP_EVENT_EXTRA_HEADERS="X-Environment=production,X-Source=ansible"

export EBDRUPLAB_AUTOMATION_HTTP_EVENT_HOST_HEADER="X-Ansible-Hosts"

export EBDRUPLAB_AUTOMATION_HTTP_EVENT_TIMEOUT="10"
export EBDRUPLAB_AUTOMATION_HTTP_EVENT_VALIDATE_CERTS="true"

export EBDRUPLAB_AUTOMATION_HTTP_EVENT_METHOD="POST"
export EBDRUPLAB_AUTOMATION_HTTP_EVENT_SEND_BODY="true"
```


# Callback Behavior

The plugin determines the final playbook result using this precedence order:

```text
failure > unreachable > success
```

## Success

When all hosts complete successfully:

```text
success_url
```

is called.

## Failure

When one or more hosts fail:

```text
failure_url
```

is called.

## Unreachable

When one or more hosts are unreachable:

```text
unreachable_url
```

is called.

---

# Example Headers

```http
Authorization: Bearer super-secret-token
X-Ansible-Job-Status: failure
X-Ansible-Hosts: web01,web02
X-Environment: production
X-Source: ansible
```

# Example JSON Payload

```json
{
  "status": "failure",
  "hosts": [
    "web01",
    "web02"
  ],
  "failed_hosts": [
    "web01"
  ],
  "unreachable_hosts": [],
  "ok_hosts": [
    "web02"
  ],
  "changed_hosts": [
    "web01"
  ]
}
```

# Example Use Cases

## Trigger a Semaphore UI template

```text
Ansible playbook fails
        |
        v
http_event sends webhook
        |
        v
Semaphore UI receives webhook
        |
        v
Semaphore starts remediation job
```

## Trigger Slack notifications

```text
Ansible unreachable host
        |
        v
Webhook sent to Slack integration
        |
        v
Operations team notified
```

## Trigger automated remediation

```text
Host failure detected
        |
        v
Webhook triggers external API
        |
        v
Automation platform starts recovery workflow
```

# Security Notes

Recommended best practices:

* use environment variables for secrets
* avoid storing tokens in plaintext
* use Ansible Vault when possible
* restrict permissions on configuration files
* use HTTPS endpoints
* keep certificate validation enabled



# Failure Handling

The callback plugin never changes the final Ansible playbook result.

If the webhook request fails:

* a warning is logged
* the playbook continues normally
* no additional failure state is introduced

This prevents automation loops or webhook outages from breaking Ansible execution.


# Collection Structure

```text
ansible_collections/
└── ebdruplab/
    └── automation/
        ├── plugins/
        │   └── callback/
        │       └── http_event.py
        ├── docs/
        ├── README.md
        ├── CHANGELOG.md
        └── galaxy.yml
```


# Compatibility

| Component    | Supported |
| ------------ | --------- |
| ansible-core | 2.14+     |
| Python       | 3.9+      |


# License

MIT



# Author

ebdruplab

