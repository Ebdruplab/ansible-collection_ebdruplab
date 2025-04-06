#!/bin/bash
#
# This script sets environment variables for Ansible integration tests against Semaphore.
# It MUST be sourced (not just run), so the variables remain in your shell session:
#     source ./set_env_for_integration.sh
#
# It sets:
#   - ebdruplab_integration_test_USER  (default: admin)
#   - ebdruplab_integration_test_PW    (default: test123)
#
# These are used in the Ansible playbook to log in to Semaphore and fetch project data.

echo "Enter Semaphore Username (default: admin): "
read -r username
username=${username:-admin}

echo "Enter Semaphore Password (default: test123): "
read -rs password
password=${password:-test123}
echo ""

export ebdruplab_integration_test_USER="$username"
export ebdruplab_integration_test_PW="$password"

echo "✅ Environment variables set:"
echo " - ebdruplab_integration_test_USER=$ebdruplab_integration_test_USER"
echo " - ebdruplab_integration_test_PW=[HIDDEN]"

echo "Run your playbook with:"
echo "ansible-playbook tests/integration/test_project_list.yml -i localhost, -c local"
