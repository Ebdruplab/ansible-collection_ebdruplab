import ssl
import urllib.request
import urllib.error
import json

def semaphore_get(url, validate_certs=True, headers=None):
    return semaphore_request("GET", url, headers=headers, validate_certs=validate_certs)[0:3]

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

def get_auth_headers(session_cookie=None, api_token=None):
    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    elif session_cookie:
        headers["Cookie"] = session_cookie
    else:
        raise ValueError("Either session_cookie or api_token must be provided.")
    return headers
