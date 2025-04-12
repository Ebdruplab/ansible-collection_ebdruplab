from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            user_id=dict(type='int', required=True),
            name=dict(type='str', required=True),
            username=dict(type='str', required=True),
            email=dict(type='str', required=True),
            alert=dict(type='bool', default=False),
            admin=dict(type='bool', default=False),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
    )

    url = f"{module.params['host']}:{module.params['port']}/api/users/{module.params['user_id']}"
    headers = get_auth_headers(module.params["session_cookie"], module.params["api_token"])
    headers["Content-Type"] = "application/json"

    payload = {
        "name": module.params["name"],
        "username": module.params["username"],
        "email": module.params["email"],
        "alert": module.params["alert"],
        "admin": module.params["admin"],
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        _, status, _ = semaphore_put(url, body=body, headers=headers, validate_certs=module.params["validate_certs"])
        if status != 204:
            module.fail_json(msg=f"PUT failed with status {status}")
        module.exit_json(changed=True, updated=True)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
