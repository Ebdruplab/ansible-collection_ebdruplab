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

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

COLLECTION_BUILD_DIR="../../"
TESTS_DIR="../integration"
RUN_SEMAPHORE=false
SEMAPHORE_CONTAINER_NAME="semaphore"

function info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

function success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

function error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

function build_and_install_collection() {
    info "Building Ansible collection in: $COLLECTION_BUILD_DIR"
    cd "$COLLECTION_BUILD_DIR"

    ansible-galaxy collection build --force

    archive_name=$(ls *.tar.gz | head -n 1)
    if [ -z "$archive_name" ]; then
        error "Collection archive was not created."
        exit 1
    fi

    info "Installing collection: $archive_name"
    ansible-galaxy collection install --force "$archive_name"

    info "Removing archive: $archive_name"
    rm -f "$archive_name"

    cd - >/dev/null
}

function start_semaphore_container() {
    info "Starting Semaphore container..."
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
    info "Stopping and removing Semaphore container..."
    sudo docker stop "$SEMAPHORE_CONTAINER_NAME"
    sudo docker rm "$SEMAPHORE_CONTAINER_NAME"
}

function run_tests() {
    info "Running Ansible integration tests locally..."
    find "$TESTS_DIR" -type f -path "*/tasks/*.yml" ! -name "backup_single_project.yml" | sort | while read -r playbook; do
        echo -e "${CYAN}------------------------------------------------------------"
        echo "Running test playbook: $playbook"
        echo -e "------------------------------------------------------------${NC}"
        ansible-playbook -i 'localhost,' --connection=local "$playbook"
        if [ $? -ne 0 ]; then
            error "Playbook failed: $playbook"
            [ "$RUN_SEMAPHORE" = true ] && stop_semaphore_container
            exit 1
        fi
        echo ""
    done
    success "All tests completed successfully."
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
        error "Unknown option: $1"
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
