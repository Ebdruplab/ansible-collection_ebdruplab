# ebdruplab.automation

Ansible automation utilities and callback plugins.

## Included Plugins

| Plugin       | Type     | Description                                                           |
| ------------ | -------- | --------------------------------------------------------------------- |
| `http_event` | callback | Send HTTP webhook events based on Ansible playbook results            |
| `smtp_event` | callback | Send one SMTP email report based on the final Ansible playbook result |

# http_event Callback Plugin

The `http_event` callback plugin enhances the ability to trigger external automation workflows when an Ansible playbook completes.

The plugin can send HTTP requests based on the final playbook result:

* success
* failure
* unreachable

It was initially created to enhance Semaphore UI workflows, but it is designed to work with any automation platform, orchestration system, monitoring solution, CI/CD platform, or webhook-based integration.

Any system capable of receiving an HTTP webhook can consume events from this plugin.

Examples:

* Semaphore UI
* Rundeck
* AWX / Ansible Automation Platform
* GitLab CI
* Jenkins
* Argo Workflows
* Home Assistant
* Slack webhook integrations
* Discord webhook integrations
* Custom internal APIs

## http_event Features

* Separate webhook URLs for:

  * success
  * failure
  * unreachable

* Token authentication support

* Custom authentication headers

* Configurable HTTP methods

* Configurable status header

* Additional static headers

* Optional affected-host header

* JSON payload support

* TLS certificate validation control

* Environment variable support

* `ansible.cfg` configuration support

* Non-blocking behavior:

  * webhook failures do not fail the Ansible playbook

# smtp_event Callback Plugin

The `smtp_event` callback plugin sends a single email report when an Ansible playbook finishes.

The plugin is designed to produce a simple final report that explains whether the playbook completed successfully, failed, or had unreachable hosts.

The plugin gathers playbook context while Ansible runs and sends only one email at the end of the playbook.

The final email can report:

* success
* failure
* unreachable

The email report includes:

* final result
* playbook name
* play name
* all play names seen during the run
* targets in play
* affected hosts
* failed hosts
* unreachable hosts
* last task
* what went wrong
* Ansible recap

For failures and unreachable hosts, the report includes the relevant host, play, task, module, message, stderr, and source path when available.

## smtp_event Features

* Sends one final email report per playbook run
* Supports success, failure, and unreachable result reporting
* Includes play name in the email subject
* Supports configurable subject prefixes such as `[Ansible Ebdruplab]`
* Includes affected hosts and error details
* Includes the last task Ansible reached
* Supports SMTP authentication
* Supports STARTTLS
* Supports SMTP-over-SSL
* Supports CC and BCC recipients
* Supports TLS certificate validation control
* Supports optional captured event dump
* Environment variable support
* `ansible.cfg` configuration support
* Non-blocking behavior:

  * email delivery failures do not fail the Ansible playbook

# Installation

## Install from source

Run:

`ansible-galaxy collection install ebdruplab.automation`

## Local development install

Run:

`ansible-galaxy collection build`

Then install the generated archive:

`ansible-galaxy collection install ebdruplab-automation-*.tar.gz`

# Enable Callback Plugins

Add the callback plugin to `ansible.cfg`.

To enable `http_event`:

`callbacks_enabled = ebdruplab.automation.http_event`

To enable `smtp_event`:

`callbacks_enabled = ebdruplab.automation.smtp_event`

To enable both:

`callbacks_enabled = ebdruplab.automation.http_event, ebdruplab.automation.smtp_event`

# Configuration

The plugins support configuration from:

* `ansible.cfg`
* environment variables

Environment variables override values from `ansible.cfg`.

# http_event Configuration

## ansible.cfg Example

In `ansible.cfg`:

[defaults]

callbacks_enabled = ebdruplab.automation.http_event

[callback_http_event]

enabled = true

success_url = [https://automation.example.com/api/success](https://automation.example.com/api/success)

failure_url = [https://automation.example.com/api/failure](https://automation.example.com/api/failure)

unreachable_url = [https://automation.example.com/api/unreachable](https://automation.example.com/api/unreachable)

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

## Environment Variable Example

Set:

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_ENABLED=true`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_SUCCESS_URL=https://automation.example.com/api/success`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_FAILURE_URL=https://automation.example.com/api/failure`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_UNREACHABLE_URL=https://automation.example.com/api/unreachable`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_AUTH_TOKEN=super-secret-token`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_AUTH_HEADER=Authorization`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_AUTH_SCHEME=Bearer`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_STATUS_HEADER=X-Ansible-Job-Status`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_EXTRA_HEADERS=X-Environment=production,X-Source=ansible`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_HOST_HEADER=X-Ansible-Hosts`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_TIMEOUT=10`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_VALIDATE_CERTS=true`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_METHOD=POST`

`EBDRUPLAB_AUTOMATION_HTTP_EVENT_SEND_BODY=true`

# smtp_event Configuration

## ansible.cfg Example

In `ansible.cfg`:

[defaults]

callbacks_enabled = ebdruplab.automation.smtp_event

[callback_smtp_event]

enabled = true

success = true

failure = true

unreachable = true

subject_prefix = [Ansible Ebdruplab]

smtp_host = smtp.example.com

smtp_port = 587

sender = Ansible [ansible@example.com](mailto:ansible@example.com)

to = [kristian@ebdruplab.dk](mailto:kristian@ebdruplab.dk)

cc =

bcc =

username = [ansible@example.com](mailto:ansible@example.com)

password = super-secret-password

starttls = true

use_ssl = false

validate_certs = true

timeout = 30

send_event_dump = false

## SMTP-over-SSL Example

Use port `465` with `use_ssl = true`.

[callback_smtp_event]

enabled = true

smtp_host = smtp.example.com

smtp_port = 465

sender = Ansible [ansible@example.com](mailto:ansible@example.com)

to = [kristian@ebdruplab.dk](mailto:kristian@ebdruplab.dk)

username = [ansible@example.com](mailto:ansible@example.com)

password = super-secret-password

starttls = false

use_ssl = true

validate_certs = true

## Environment Variable Example

Set:

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_ENABLED=true`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_SUCCESS=true`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_FAILURE=true`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_UNREACHABLE=true`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_SUBJECT_PREFIX=[Ansible Ebdruplab]`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_SMTP_HOST=smtp.example.com`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_SMTP_PORT=587`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_SENDER=Ansible <ansible@example.com>`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_TO=kristian@ebdruplab.dk`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_CC=`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_BCC=`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_USERNAME=ansible@example.com`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_PASSWORD=super-secret-password`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_STARTTLS=true`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_USE_SSL=false`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_VALIDATE_CERTS=true`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_TIMEOUT=30`

`EBDRUPLAB_AUTOMATION_SMTP_EVENT_SEND_EVENT_DUMP=false`

# Callback Behavior

Both callback plugins determine the final playbook result using this precedence order:

`failure > unreachable > success`

## Success

When all hosts complete successfully:

* `http_event` calls `success_url`
* `smtp_event` sends a success report email when `success = true`

## Failure

When one or more hosts fail:

* `http_event` calls `failure_url`
* `smtp_event` sends a failure report email when `failure = true`

The SMTP report explains which hosts failed and includes captured task and error details.

## Unreachable

When one or more hosts are unreachable:

* `http_event` calls `unreachable_url`
* `smtp_event` sends an unreachable report email when `unreachable = true`

The SMTP report explains which hosts were unreachable and includes captured unreachable event details.

# smtp_event Email Subject

The `smtp_event` subject format is:

`[prefix] STATUS - play name - playbook name - affected hosts`

Example:

`[Ansible Ebdruplab] FAILURE - Configure servers - site.yml - web01,web02`

The prefix is configured with:

`subject_prefix = [Ansible Ebdruplab]`

To disable the prefix, set `subject_prefix` to an empty value.

# smtp_event Example Email Report

Example failure report:

Ansible report

Result: failure

Summary: Failure on web01 at task 'Install package': No package matching 'example-package' is available

Context

Playbook: site.yml

Play: Configure servers

All plays: Configure servers

Targets in play: web01, web02

Last task: Install package (ansible.builtin.apt) in roles/common/tasks/main.yml:24

Hosts

All hosts: web01, web02

Affected hosts: web01

Failed hosts: web01

Unreachable hosts: none

What happened

* Host: web01
  Event: failure
  Play: Configure servers
  Task: Install package
  Module: ansible.builtin.apt
  Path: roles/common/tasks/main.yml
  Line: 24
  Message: No package matching 'example-package' is available

Recap

web01: ok=5 changed=1 unreachable=0 failures=1 skipped=0 rescued=0 ignored=0

web02: ok=6 changed=0 unreachable=0 failures=0 skipped=1 rescued=0 ignored=0

# http_event Example Headers

Example HTTP headers:

`Authorization: Bearer super-secret-token`

`X-Ansible-Job-Status: failure`

`X-Ansible-Hosts: web01,web02`

`X-Environment: production`

`X-Source: ansible`

# http_event Example JSON Payload

Example JSON payload:

Status: `failure`

Hosts: `web01`, `web02`

Failed hosts: `web01`

Unreachable hosts: none

OK hosts: `web02`

Changed hosts: `web01`

# Example Use Cases

## Trigger a Semaphore UI template

Ansible playbook fails.

`http_event` sends a webhook.

Semaphore UI receives the webhook.

Semaphore starts a remediation job.

## Trigger Slack notifications

Ansible detects an unreachable host.

`http_event` sends a webhook to a Slack integration.

The operations team is notified.

## Send an SMTP report to operations

Ansible playbook finishes.

`smtp_event` sends one email report.

The email explains whether the playbook succeeded, failed, or had unreachable hosts.

The email includes the play name, affected hosts, last task, and error details.

## Trigger automated remediation

Host failure detected.

`http_event` triggers an external API.

An automation platform starts a recovery workflow.

# Security Notes

Recommended best practices:

* use environment variables for secrets
* avoid storing tokens or SMTP passwords in plaintext
* use Ansible Vault when possible
* restrict permissions on configuration files
* use HTTPS endpoints for webhooks
* use STARTTLS or SMTP-over-SSL for email delivery
* keep certificate validation enabled
* avoid disabling `validate_certs` except for controlled local testing

# Failure Handling

The callback plugins never change the final Ansible playbook result.

If a webhook request fails:

* a warning is logged
* the playbook continues normally
* no additional failure state is introduced

If an SMTP email fails:

* a warning is logged
* the playbook continues normally
* no additional failure state is introduced

This prevents webhook outages, SMTP outages, or notification failures from breaking Ansible execution.

# Collection Structure

ansible_collections/

└── ebdruplab/

    └── automation/

        ├── plugins/

        │   └── callback/

        │       ├── http_event.py

        │       └── smtp_event.py

        ├── docs/

        ├── README.md

        ├── CHANGELOG.md

        └── galaxy.yml

# Compatibility

| Component    | Supported |
| ------------ | --------- |
| ansible-core | 2.14+     |
| Python       | 3.9+      |

# License

MIT

# Author

ebdruplab
