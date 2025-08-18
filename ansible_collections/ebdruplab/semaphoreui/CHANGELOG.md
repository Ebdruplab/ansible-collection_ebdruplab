# Changelog

## Version 2.0.0

### Added

#### Module Added
- **project_integration_create**  
  Added so we are able to create integrations through ansible on the semaphore ui platform

#### Module changes
- **project_inventory_create**  
  Added support for `ssh_key_id` (required) and `become_key_id` (optional) parameters.
- **project_inventory_update**  
  Added support for `ssh_key_id` and `become_key_id` parameters.

#### Roles added
- **project_deploy**  
  Added to support a high level yaml vars file to populate with project, inventory keys and more.

---
