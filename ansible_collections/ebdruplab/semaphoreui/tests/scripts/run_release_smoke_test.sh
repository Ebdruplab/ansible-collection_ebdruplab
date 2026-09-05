#!/usr/bin/env bash
# SPDX-License-Identifier: MIT-0
#
# Build the collection and exercise its core deploy/backup workflow against a
# disposable local Semaphore instance.  This is intended as a release gate.

set -euo pipefail

COLLECTION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPOSITORY_DIR="$(cd "${COLLECTION_DIR}/../../.." && pwd)"
CONTAINER_NAME="ebdruplab-semaphore-release-smoke"
WORK_DIR="$(mktemp -d)"
SEMAPHORE_IMAGE="${SEMAPHORE_IMAGE:-semaphoreui/semaphore:v2.18.12}"
SEMAPHORE_DB_DIALECT="${SEMAPHORE_DB_DIALECT:-sqlite}"

cleanup() {
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  rm -rf "${WORK_DIR}"
}
trap cleanup EXIT

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for the release smoke test." >&2
  exit 1
fi

if docker container inspect "${CONTAINER_NAME}" >/dev/null 2>&1; then
  echo "Container ${CONTAINER_NAME} already exists; remove it before running this test." >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required to wait for Semaphore." >&2
  exit 1
fi

echo "Building collection"
ansible-galaxy collection build --force --output-path "${WORK_DIR}" "${COLLECTION_DIR}"

echo "Starting disposable Semaphore instance (${SEMAPHORE_IMAGE}; ${SEMAPHORE_DB_DIALECT})"
docker run --name "${CONTAINER_NAME}" \
  -p 3000:3000 \
  -e "SEMAPHORE_DB_DIALECT=${SEMAPHORE_DB_DIALECT}" \
  -e SEMAPHORE_ADMIN=admin \
  -e SEMAPHORE_ADMIN_PASSWORD=changeme \
  -e SEMAPHORE_ADMIN_NAME=Admin \
  -e SEMAPHORE_ADMIN_EMAIL=admin@localhost \
  -d "${SEMAPHORE_IMAGE}" >/dev/null

for _ in $(seq 1 30); do
  if curl --fail --silent http://localhost:3000/ >/dev/null; then
    break
  fi
  sleep 2
done

if ! curl --fail --silent http://localhost:3000/ >/dev/null; then
  docker logs "${CONTAINER_NAME}" >&2
  echo "Semaphore did not become ready." >&2
  exit 1
fi

export ANSIBLE_COLLECTIONS_PATH="${REPOSITORY_DIR}"

echo "Running backup regression test for templates without a board view"
ansible-playbook -i 'localhost,' --connection=local \
  "${COLLECTION_DIR}/tests/regression/test_template_without_view.yml"

echo "Running backup regression test for empty environments"
ansible-playbook -i 'localhost,' --connection=local \
  "${COLLECTION_DIR}/tests/regression/test_empty_environment.yml"

echo "Running direct environment create, update, rename, and cleanup test"
ansible-playbook -i 'localhost,' --connection=local \
  "${COLLECTION_DIR}/tests/integration/project_environments/tasks/test_project_environments.yml"

echo "Running live project deploy and backup smoke test"
ansible-playbook -i 'localhost,' --connection=local \
  -e "project_backup_output_dir=${WORK_DIR}/backup" \
  "${COLLECTION_DIR}/roles/project_backup/tests/test.yml"

echo "Release smoke test passed."
