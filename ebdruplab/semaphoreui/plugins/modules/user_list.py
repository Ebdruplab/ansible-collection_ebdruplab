from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_get, get_auth_headers
import json

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True)
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    url = f"{module.params['host']}:{module.params['port']}/api/users"
    headers = get_auth_headers(module.params['session_cookie'], module.params['api_token'])

    try:
        body, status, _ = semaphore_get(url, headers=headers, validate_certs=module.params["validate_certs"])
        if status != 200:
            module.fail_json(msg=f"Failed to list users: HTTP {status}")
        users = json.loads(body)
        module.exit_json(changed=False, users=users)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()