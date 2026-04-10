#!/bin/bash

################################################################################
# run_all_tests.sh
#
# Description:
#   Builds and installs the Ansible collection, then runs all test playbooks.
#   Supports optional Semaphore container for testing API interactions.
#
# How to Run:
#   ./run_all_tests.sh                          # Build collection, run all tests locally
#   ./run_all_tests.sh --with-semaphore        # Start Semaphore container before tests
#   ./run_all_tests.sh --with-semaphore --copy # Start container and copy path to clipboard before running
#
# Flags:
#   --with-semaphore  Start and stop the Semaphore UI container (Docker or Podman).
#   --copy            Copy each test playbook path to clipboard before running.
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

COLLECTION_BUILD_DIR="../../"
TESTS_DIR="../integration"
RUN_SEMAPHORE=false
COPY_TASKS=false
SEMAPHORE_CONTAINER_NAME="semaphore"
CONTAINER_CMD=""

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

function determine_container_command() {
    if command -v docker &>/dev/null; then
        CONTAINER_CMD="docker"
    elif command -v podman &>/dev/null; then
        CONTAINER_CMD="podman"
    else
        error "Neither Docker nor Podman is installed. Cannot start Semaphore container."
        exit 1
    fi
}

function start_semaphore_container() {
    determine_container_command

    info "Starting Semaphore container with $CONTAINER_CMD..."
    sudo "$CONTAINER_CMD" run --name "$SEMAPHORE_CONTAINER_NAME" \
        -p 3000:3000 \
        -e SEMAPHORE_DB_DIALECT=bolt \
        -e SEMAPHORE_ADMIN=admin \
        -e SEMAPHORE_ADMIN_PASSWORD=changeme \
        -e SEMAPHORE_ADMIN_NAME="Admin" \
        -e SEMAPHORE_ADMIN_EMAIL=admin@localhost \
        -d semaphoreui/semaphore:v2.13.5
}

function stop_semaphore_container() {
    if [ -n "$CONTAINER_CMD" ]; then
        info "Stopping and removing Semaphore container with $CONTAINER_CMD..."
        sudo "$CONTAINER_CMD" stop "$SEMAPHORE_CONTAINER_NAME"
        sudo "$CONTAINER_CMD" rm "$SEMAPHORE_CONTAINER_NAME"
    fi
}

function copy_to_clipboard() {
    local text="$1"
    if command -v xclip &>/dev/null; then
        echo -n "$text" | xclip -selection clipboard
    elif command -v pbcopy &>/dev/null; then
        echo -n "$text" | pbcopy
    elif command -v wl-copy &>/dev/null; then
        echo -n "$text" | wl-copy
    else
        info "Clipboard not supported: no xclip, pbcopy, or wl-copy found."
    fi
}

function run_tests() {
    info "Running Ansible integration tests locally..."

    find "$TESTS_DIR" -type f -path "*/tasks/*.yml" ! -name "backup_single_project.yml" | sort | while read -r playbook; do
        echo -e "${CYAN}------------------------------------------------------------"
        echo "Running test playbook: $playbook"
        echo -e "------------------------------------------------------------${NC}"

        if [ "$COPY_TASKS" = true ]; then
            copy_to_clipboard "$(realpath "$playbook")"
            info "Copied playbook path to clipboard: $playbook"
        fi

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
    echo "Usage: $0 [--with-semaphore] [--copy]"
    echo ""
    echo "  --with-semaphore  Start and stop the Semaphore UI container (Docker or Podman)."
    echo "  --copy            Copy each test playbook path to clipboard before running."
    echo "  -h, --help        Show this help message."
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --with-semaphore)
            RUN_SEMAPHORE=true
            shift
            ;;
        --copy)
            COPY_TASKS=true
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
