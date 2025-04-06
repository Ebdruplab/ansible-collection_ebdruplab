#!/bin/bash

################################################################################
# run_all_tests.sh
#
# Description:
#   Builds and installs the Ansible collection, then runs all test playbooks.
#   Supports optional Semaphore container for testing API interactions.
#
# How to Run:
#   ./run_all_tests.sh                       # Build collection, run all tests locally
#   ./run_all_tests.sh --with-semaphore     # Start Semaphore container before tests
#
# Flags:
#   --with-semaphore  Start and stop the Semaphore UI Docker container before/after tests.
################################################################################

set -e

COLLECTION_BUILD_DIR="../../"
TESTS_DIR="../integration"
RUN_SEMAPHORE=false
SEMAPHORE_CONTAINER_NAME="semaphore"

function build_and_install_collection() {
    echo "[INFO] Building Ansible collection in: $COLLECTION_BUILD_DIR"
    cd "$COLLECTION_BUILD_DIR"

    ansible-galaxy collection build --force

    archive_name=$(ls *.tar.gz | head -n 1)
    if [ -z "$archive_name" ]; then
        echo "[ERROR] Collection archive was not created."
        exit 1
    fi

    echo "[INFO] Installing collection: $archive_name"
    ansible-galaxy collection install --force "$archive_name"

    echo "[INFO] Removing archive: $archive_name"
    rm -f "$archive_name"

    cd - >/dev/null
}

function start_semaphore_container() {
    echo "[INFO] Starting Semaphore container..."
    sudo docker run --name "$SEMAPHORE_CONTAINER_NAME" \
        -p 3000:3000 \
        -e SEMAPHORE_DB_DIALECT=bolt \
        -e SEMAPHORE_ADMIN=admin \
        -e SEMAPHORE_ADMIN_PASSWORD=changeme \
        -e SEMAPHORE_ADMIN_NAME="Admin" \
        -e SEMAPHORE_ADMIN_EMAIL=admin@localhost \
        -d semaphoreui/semaphore:v2.13.5
}

function stop_semaphore_container() {
    echo "[INFO] Stopping and removing Semaphore container..."
    sudo docker stop "$SEMAPHORE_CONTAINER_NAME"
    sudo docker rm "$SEMAPHORE_CONTAINER_NAME"
}

function run_tests() {
    echo "[INFO] Running Ansible integration tests locally..."
    find "$TESTS_DIR" -type f -path "*/tasks/*.yml" | sort | while read -r playbook; do
        echo "------------------------------------------------------------"
        echo "Running test playbook: $playbook"
        echo "------------------------------------------------------------"
        ansible-playbook -i 'localhost,' --connection=local "$playbook"
        if [ $? -ne 0 ]; then
            echo "[ERROR] Playbook failed: $playbook"
            [ "$RUN_SEMAPHORE" = true ] && stop_semaphore_container
            exit 1
        fi
        echo ""
    done
    echo "[INFO] All tests completed successfully."
}

function show_help() {
    echo "Usage: $0 [--with-semaphore]"
    echo ""
    echo "  --with-semaphore  Start and stop the Semaphore UI Docker container."
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
    --with-semaphore)
        RUN_SEMAPHORE=true
        shift
        ;;
    -h | --help)
        show_help
        exit 0
        ;;
    *)
        echo "[ERROR] Unknown option: $1"
        show_help
        exit 1
        ;;
    esac
done

build_and_install_collection

if [ "$RUN_SEMAPHORE" = true ]; then
    start_semaphore_container
fi

run_tests

if [ "$RUN_SEMAPHORE" = true ]; then
    stop_semaphore_container
fi
