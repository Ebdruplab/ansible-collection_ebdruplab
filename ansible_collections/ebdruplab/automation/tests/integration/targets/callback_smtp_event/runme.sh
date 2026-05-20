#!/usr/bin/env bash

set -euo pipefail

target_dir="$(cd "$(dirname "$0")" && pwd)"
collection_root="$(cd "${target_dir}/../../../.." && pwd)"
collections_root="$(cd "${collection_root}/../../.." && pwd)"
collections_path="${ANSIBLE_COLLECTIONS_PATH:-${collections_root}}"
work_dir="$(mktemp -d)"

cleanup() {
    if [[ -n "${server_pid:-}" ]] && kill -0 "${server_pid}" 2>/dev/null; then
        kill "${server_pid}" 2>/dev/null || true
        wait "${server_pid}" 2>/dev/null || true
    fi
    rm -rf "${work_dir}"
}

trap cleanup EXIT

start_smtp_server() {
    local scenario="$1"
    server_output_dir="${work_dir}/${scenario}-smtp"
    port_file="${work_dir}/${scenario}-smtp-port"
    server_log="${work_dir}/${scenario}-smtp-server.log"

    python3 "${target_dir}/files/fake_smtp_server.py" \
        --output-dir "${server_output_dir}" \
        --port-file "${port_file}" \
        >"${server_log}" 2>&1 &
    server_pid=$!

    for _ in $(seq 1 100); do
        if [[ -s "${port_file}" ]]; then
            return 0
        fi
        sleep 0.1
    done

    cat "${server_log}"
    echo "SMTP test server failed to start for scenario '${scenario}'" >&2
    exit 1
}

inventory_file="${work_dir}/inventory.ini"

cat > "${inventory_file}" <<'EOF'
smtp_host1 ansible_connection=local
smtp_host2 ansible_connection=local
EOF

run_playbook() {
    local playbook_path="$1"
    local expect_success="$2"

    set +e
    ANSIBLE_NOCOLOR=1 \
    ANSIBLE_STDOUT_CALLBACK=default \
    ANSIBLE_COLLECTIONS_PATH="${collections_path}" \
    ANSIBLE_CALLBACKS_ENABLED=ebdruplab.automation.smtp_event \
    EBDRUPLAB_AUTOMATION_SMTP_EVENT_ENABLED=true \
    EBDRUPLAB_AUTOMATION_SMTP_EVENT_FAILURE=true \
    EBDRUPLAB_AUTOMATION_SMTP_EVENT_SUCCESS=true \
    EBDRUPLAB_AUTOMATION_SMTP_EVENT_UNREACHABLE=false \
    EBDRUPLAB_AUTOMATION_SMTP_EVENT_SMTP_HOST=127.0.0.1 \
    EBDRUPLAB_AUTOMATION_SMTP_EVENT_SMTP_PORT="${smtp_port}" \
    EBDRUPLAB_AUTOMATION_SMTP_EVENT_SENDER='Ansible Bot <ansible@example.com>' \
    EBDRUPLAB_AUTOMATION_SMTP_EVENT_TO='Ops Team <ops@example.com>' \
    EBDRUPLAB_AUTOMATION_SMTP_EVENT_CC='Audit Team <audit@example.com>' \
    EBDRUPLAB_AUTOMATION_SMTP_EVENT_BCC='Hidden Team <hidden@example.com>' \
    EBDRUPLAB_AUTOMATION_SMTP_EVENT_SUBJECT_PREFIX='[SMTP Integration]' \
    EBDRUPLAB_AUTOMATION_SMTP_EVENT_SEND_EVENT_DUMP=true \
    ansible-playbook -i "${inventory_file}" "${playbook_path}"
    playbook_status=$?
    set -e

    if [[ "${expect_success}" == "true" && "${playbook_status}" -ne 0 ]]; then
        echo "Expected playbook '${playbook_path}' to succeed" >&2
        exit 1
    fi

    if [[ "${expect_success}" == "false" && "${playbook_status}" -eq 0 ]]; then
        echo "Expected playbook '${playbook_path}' to fail" >&2
        exit 1
    fi
}

validate_and_print_capture() {
    local scenario="$1"
    local capture_file="${server_output_dir}/capture.json"

    if [[ ! -f "${capture_file}" ]]; then
        cat "${server_log}"
        echo "SMTP test server did not capture a message for scenario '${scenario}'" >&2
        exit 1
    fi

    python3 - "${capture_file}" "${scenario}" <<'PY'
import json
import sys
from email import policy
from email.parser import Parser

capture_path = sys.argv[1]
scenario = sys.argv[2]
with open(capture_path, encoding="utf-8") as handle:
    capture = json.load(handle)

message = Parser(policy=policy.default).parsestr(capture["message"])
body_part = message.get_body(preferencelist=("plain",))
body = body_part.get_content() if body_part else message.get_content()

assert capture["mail_from"] == "ansible@example.com", capture
assert sorted(capture["rcpt_tos"]) == [
    "audit@example.com",
    "hidden@example.com",
    "ops@example.com",
], capture

assert message["From"] == "Ansible Bot <ansible@example.com>", message.items()
assert message["To"] == "Ops Team <ops@example.com>", message.items()
assert message["Cc"] == "Audit Team <audit@example.com>", message.items()
assert message["Bcc"] is None, message.items()

if scenario == "failure":
    assert (
        str(message["Subject"]).strip()
        == "[SMTP Integration] FAILURE - SMTP failure integration play - playbook_failure.yml - smtp_host2"
    ), message["Subject"]
    assert "Result: failure" in body, body
    assert (
        "Failure on smtp_host2 at task 'Trigger failure on secondary host': callback_smtp_event integration failure"
        in body
    ), body
    assert "Playbook: playbook_failure.yml" in body, body
    assert "Play: SMTP failure integration play" in body, body
    assert "Targets in play: all, smtp_host1, smtp_host2" in body, body
    assert "All hosts: smtp_host1, smtp_host2" in body, body
    assert "Affected hosts: smtp_host2" in body, body
    assert "Failed hosts: smtp_host2" in body, body
    assert "Unreachable hosts: none" in body, body
    assert "smtp_host1: ok=1 changed=0 unreachable=0 failures=0" in body, body
    assert "smtp_host2: ok=1 changed=0 unreachable=0 failures=1" in body, body
    assert "Captured event dump" in body, body
elif scenario == "success":
    assert (
        str(message["Subject"]).strip()
        == "[SMTP Integration] SUCCESS - SMTP success integration play - playbook_success.yml - smtp_host1,smtp_host2"
    ), message["Subject"]
    assert "Result: success" in body, body
    assert "Playbook completed successfully on smtp_host1, smtp_host2." in body, body
    assert "Playbook: playbook_success.yml" in body, body
    assert "Play: SMTP success integration play" in body, body
    assert "Targets in play: all, smtp_host1, smtp_host2" in body, body
    assert "All hosts: smtp_host1, smtp_host2" in body, body
    assert "Affected hosts: smtp_host1, smtp_host2" in body, body
    assert "Failed hosts: none" in body, body
    assert "Unreachable hosts: none" in body, body
    assert "No failures or unreachable hosts were recorded." in body, body
    assert "smtp_host1: ok=1 changed=0 unreachable=0 failures=0" in body, body
    assert "smtp_host2: ok=1 changed=0 unreachable=0 failures=0" in body, body
else:
    raise AssertionError(f"Unknown scenario: {scenario}")

print(f"Captured SMTP message for {scenario}:")
for header in ["Date", "From", "To", "Cc", "Message-ID", "Subject"]:
    value = message.get(header)
    if value is not None:
        print(f"{header}: {str(value).strip()}")

print()
print(body.rstrip())
PY
}

run_scenario() {
    local scenario="$1"
    local playbook_name="$2"
    local expect_success="$3"

    start_smtp_server "${scenario}"
    smtp_port="$(cat "${port_file}")"
    run_playbook "${target_dir}/${playbook_name}" "${expect_success}"
    wait "${server_pid}"
    server_pid=""
    validate_and_print_capture "${scenario}"
}

run_scenario failure playbook_failure.yml false
run_scenario success playbook_success.yml true
