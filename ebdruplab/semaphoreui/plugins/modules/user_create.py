from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            name=dict(type='str', required=True),
            username=dict(type='str', required=True),
            email=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            alert=dict(type='bool', default=False),
            admin=dict(type='bool', default=False),
            external=dict(type='bool', default=False),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
    )

    url = f"{module.params['host']}:{module.params['port']}/api/users"
    headers = get_auth_headers(module.params["session_cookie"], module.params["api_token"])
    headers["Content-Type"] = "application/json"

    payload = {
        "name": module.params["name"],
        "username": module.params["username"],
        "email": module.params["email"],
        "password": module.params["password"],
        "alert": module.params["alert"],
        "admin": module.params["admin"],
        "external": module.params["external"],
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        response_body, status, _ = semaphore_post(url, body=body, headers=headers, validate_certs=module.params["validate_certs"])
        if status != 201:
            module.fail_json(msg=f"POST failed with status {status}: {response_body}")
        module.exit_json(changed=True, user=json.loads(response_body))
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
