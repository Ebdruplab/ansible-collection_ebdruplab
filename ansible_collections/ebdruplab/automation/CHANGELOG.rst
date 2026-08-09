# Changelog

All notable changes to this collection will be documented in this file.

The format is based on Keep a Changelog.

---

# [2.0.0] - 2026-05-26

## Added

- Added `smtp_event` callback plugin
- Added support for SMTP email reports on:
  - success
  - failure
  - unreachable
- Added configurable SMTP authentication
- Added STARTTLS support
- Added SMTP-over-SSL support
- Added CC and BCC recipient support
- Added configurable subject prefixes
- Added affected host and error detail reporting
- Added final playbook recap in email reports
- Added TLS certificate validation control
- Added optional captured event dump support
- Added environment variable configuration support
- Added `ansible.cfg` configuration support
- Added non-blocking email delivery behavior

## Notes

This release introduces SMTP-based final playbook reporting alongside the existing webhook integration.

# [1.0.0] - 2026-05-14

## Added

- Initial release of `ebdruplab.automation`
- Added `http_event` callback plugin
- Added support for:
  - success webhook URLs
  - failure webhook URLs
  - unreachable webhook URLs
- Added configurable HTTP authentication
- Added configurable authentication headers
- Added configurable authentication schemes
- Added configurable status headers
- Added configurable custom headers
- Added configurable host headers
- Added JSON request payload support
- Added configurable HTTP methods
- Added configurable request timeout support
- Added TLS certificate validation control
- Added environment variable configuration support
- Added `ansible.cfg` configuration support
- Added structured webhook payloads
- Added non-blocking webhook behavior
- Added logging for webhook failures
- Added Semaphore UI integration support
- Added generic webhook integration support for external automation systems

## Notes

Initial version focused on enhancing external automation workflows triggered from Ansible playbook results.
````
