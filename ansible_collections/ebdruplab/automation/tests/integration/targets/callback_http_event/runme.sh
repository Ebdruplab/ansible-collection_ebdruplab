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

start_http_server() {
    local scenario="$1"
    server_output_dir="${work_dir}/${scenario}-http"
    port_file="${work_dir}/${scenario}-http-port"
    server_log="${work_dir}/${scenario}-http-server.log"

    python3 "${target_dir}/files/fake_http_server.py" \
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
    echo "HTTP test server failed to start for scenario '${scenario}'" >&2
    exit 1
}

inventory_file="${work_dir}/inventory.ini"

cat > "${inventory_file}" <<'EOF'
http_host1 ansible_connection=local
http_host2 ansible_connection=local
EOF

run_playbook() {
    local playbook_path="$1"
    local expect_success="$2"
    local method="$3"

    set +e
    ANSIBLE_NOCOLOR=1 \
    ANSIBLE_STDOUT_CALLBACK=default \
    ANSIBLE_COLLECTIONS_PATH="${collections_path}" \
    ANSIBLE_CALLBACKS_ENABLED=ebdruplab.automation.http_event \
    EBDRUPLAB_AUTOMATION_HTTP_EVENT_ENABLED=true \
    EBDRUPLAB_AUTOMATION_HTTP_EVENT_SUCCESS_URL="http://127.0.0.1:${http_port}/success" \
    EBDRUPLAB_AUTOMATION_HTTP_EVENT_FAILURE_URL="http://127.0.0.1:${http_port}/failure" \
    EBDRUPLAB_AUTOMATION_HTTP_EVENT_UNREACHABLE_URL="http://127.0.0.1:${http_port}/unreachable" \
    EBDRUPLAB_AUTOMATION_HTTP_EVENT_AUTH_TOKEN='secret-token' \
    EBDRUPLAB_AUTOMATION_HTTP_EVENT_AUTH_HEADER='X-Auth-Token' \
    EBDRUPLAB_AUTOMATION_HTTP_EVENT_AUTH_SCHEME='Token' \
    EBDRUPLAB_AUTOMATION_HTTP_EVENT_STATUS_HEADER='X-Job-Status' \
    EBDRUPLAB_AUTOMATION_HTTP_EVENT_HOST_HEADER='X-Affected-Hosts' \
    EBDRUPLAB_AUTOMATION_HTTP_EVENT_EXTRA_HEADERS='X-Source=ansible,X-Environment=test' \
    EBDRUPLAB_AUTOMATION_HTTP_EVENT_METHOD="${method}" \
    EBDRUPLAB_AUTOMATION_HTTP_EVENT_SEND_BODY=true \
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
    local expected_method="$2"
    local capture_file="${server_output_dir}/capture.json"

    if [[ ! -f "${capture_file}" ]]; then
        cat "${server_log}"
        echo "HTTP test server did not capture a request for scenario '${scenario}'" >&2
        exit 1
    fi

    python3 - "${capture_file}" "${scenario}" "${expected_method}" <<'PY'
import json
import sys

capture_path = sys.argv[1]
scenario = sys.argv[2]
expected_method = sys.argv[3]

with open(capture_path, encoding="utf-8") as handle:
    capture = json.load(handle)

headers = capture["headers"]
body = json.loads(capture["body"])

assert capture["method"] == expected_method, capture
assert headers["X-Auth-Token"] == "Token secret-token", headers
assert headers["X-Source"] == "ansible", headers
assert headers["X-Environment"] == "test", headers
assert headers["Content-Type"] == "application/json", headers
assert headers["User-Agent"] == "ebdruplab.automation.http_event", headers

if scenario == "failure":
    assert capture["path"] == "/failure", capture
    assert headers["X-Job-Status"] == "failure", headers
    assert headers["X-Affected-Hosts"] == "http_host2", headers
    assert body["status"] == "failure", body
    assert body["hosts"] == ["http_host2"], body
    assert body["failed_hosts"] == ["http_host2"], body
    assert body["unreachable_hosts"] == [], body
    assert body["ok_hosts"] == ["http_host1", "http_host2"], body
    assert body["changed_hosts"] == [], body
elif scenario == "success":
    assert capture["path"] == "/success", capture
    assert headers["X-Job-Status"] == "success", headers
    assert headers["X-Affected-Hosts"] == "http_host1,http_host2", headers
    assert body["status"] == "success", body
    assert body["hosts"] == ["http_host1", "http_host2"], body
    assert body["failed_hosts"] == [], body
    assert body["unreachable_hosts"] == [], body
    assert body["ok_hosts"] == ["http_host1", "http_host2"], body
    assert body["changed_hosts"] == [], body
else:
    raise AssertionError(f"Unknown scenario: {scenario}")

print(f"Captured HTTP request for {scenario}:")
print(f"{capture['method']} {capture['path']}")
for header in [
    "X-Auth-Token",
    "X-Job-Status",
    "X-Affected-Hosts",
    "X-Source",
    "X-Environment",
    "Content-Type",
    "User-Agent",
]:
    print(f"{header}: {headers[header]}")

print()
print(json.dumps(body, indent=2, sort_keys=True))
PY
}

run_scenario() {
    local scenario="$1"
    local playbook_name="$2"
    local expect_success="$3"
    local method="$4"

    start_http_server "${scenario}"
    http_port="$(cat "${port_file}")"
    run_playbook "${target_dir}/${playbook_name}" "${expect_success}" "${method}"
    wait "${server_pid}"
    server_pid=""
    validate_and_print_capture "${scenario}" "${method}"
}

run_scenario failure playbook_failure.yml false PATCH
run_scenario success playbook_success.yml true PUT
