# plugins/module_utils/semaphore_api.py

import ssl
import urllib.request
import urllib.error
import json

__all__ = [
    "semaphore_get",
    "semaphore_post",
    "semaphore_put",
    "semaphore_delete",
    "semaphore_request",
    "semaphore_request_allow_status",
    "semaphore_get_json",
    "get_auth_headers",
    "exit_check_mode",
    "sanitize_check_mode_value",
]


def semaphore_get(url, validate_certs=True, headers=None):
    return semaphore_request("GET", url, headers=headers, validate_certs=validate_certs)[0:3]


def semaphore_post(url, body=None, headers=None, validate_certs=True):
    return semaphore_request("POST", url, body=body, headers=headers, validate_certs=validate_certs)[0:3]


def semaphore_delete(url, headers=None, validate_certs=True):
    return semaphore_request("DELETE", url, headers=headers, validate_certs=validate_certs)[0:3]

def semaphore_put(url, body=None, headers=None, validate_certs=True):
    return semaphore_request("PUT", url, body=body, headers=headers, validate_certs=validate_certs)[0:3]

def semaphore_request(method, url, body=None, headers=None, validate_certs=True):
    """
    Generic HTTP request for interacting with Semaphore API.
    Returns (response_body_str, status_code, set_cookie_header)
    """
    context = None
    if url.startswith("https") and not validate_certs:
        context = ssl._create_unverified_context()

    if body is not None and isinstance(body, dict):
        body = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)

    try:
        with urllib.request.urlopen(req, context=context) if context else urllib.request.urlopen(req) as response:
            return (
                response.read().decode().strip(),
                response.getcode(),
                response.getheader("Set-Cookie")
            )
    except urllib.error.HTTPError as e:
        raise ConnectionError(f"{method} failed with status {e.code}: {e.read().decode()}")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Failed to connect to {url}: {e}")


def semaphore_request_allow_status(method, url, body=None, headers=None, validate_certs=True):
    """
    HTTP request helper that preserves HTTP status codes instead of raising on
    HTTPError. Returns (response_body_str, status_code, set_cookie_header).
    """
    context = None
    if url.startswith("https") and not validate_certs:
        context = ssl._create_unverified_context()

    if body is not None and isinstance(body, dict):
        body = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)

    try:
        with urllib.request.urlopen(req, context=context) if context else urllib.request.urlopen(req) as response:
            return (
                response.read().decode().strip(),
                response.getcode(),
                response.getheader("Set-Cookie")
            )
    except urllib.error.HTTPError as e:
        return (
            e.read().decode(),
            e.code,
            e.headers.get("Set-Cookie"),
        )
    except urllib.error.URLError as e:
        raise ConnectionError(f"Failed to connect to {url}: {e}")


_CHECK_MODE_REDACT_KEYS = {
    "api_token",
    "auth_secret",
    "auth_secret_id",
    "cookie",
    "login_password",
    "passphrase",
    "password",
    "private_key",
    "secret",
    "session_cookie",
    "ssh",
    "token",
    "vault_password",
}


def get_auth_headers(session_cookie=None, api_token=None):
    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    elif session_cookie:
        headers["Cookie"] = session_cookie
    else:
        raise ValueError("Either session_cookie or api_token must be provided.")
    headers["Content-Type"] = "application/json"
    return headers


def sanitize_check_mode_value(value, key=None):
    if key and key.lower() in _CHECK_MODE_REDACT_KEYS:
        return "<redacted>"

    if isinstance(value, dict):
        return {
            item_key: sanitize_check_mode_value(item_value, item_key)
            for item_key, item_value in value.items()
        }

    if isinstance(value, list):
        return [sanitize_check_mode_value(item) for item in value]

    if isinstance(value, tuple):
        return tuple(sanitize_check_mode_value(item) for item in value)

    return value


def semaphore_get_json(url, headers=None, validate_certs=True):
    body, status, cookie = semaphore_request_allow_status(
        "GET",
        url,
        headers=headers,
        validate_certs=validate_certs,
    )

    parsed = None
    if isinstance(body, str) and body:
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = None
    elif body not in ("", None):
        parsed = body

    return parsed, body, status, cookie


def exit_check_mode(module, action=None, planned=None, changed=True):
    module_name = getattr(module, "_name", None)
    planned_action = action or module_name or "write_operation"
    planned_payload = planned if planned is not None else module.params

    module.exit_json(
        changed=changed,
        check_mode=True,
        skipped_execution=True,
        planned_action=planned_action,
        planned=sanitize_check_mode_value(planned_payload),
    )
