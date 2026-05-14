# Changelog

All notable changes to this collection will be documented in this file.

The format is based on Keep a Changelog.

---

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