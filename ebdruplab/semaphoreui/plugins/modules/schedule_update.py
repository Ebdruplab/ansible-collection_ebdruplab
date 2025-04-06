from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_put, get_auth_headers
import json

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            schedule=dict(type='dict', required=True),
            schedule_id=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=True
    )

    url = f"{module.params['host']}:{module.params['port']}/project/{module.params['project_id']}/schedules/{module.params['schedule_id']}"
    try:
        headers = get_auth_headers(module.params["session_cookie"], module.params["api_token"])
        _, status, _ = semaphore_put(url, body=module.params["schedule"], headers=headers, validate_certs=module.params["validate_certs"])

        if status not in (200, 204):
            module.fail_json(msg=f"Failed to update schedule: HTTP {status}")
        module.exit_json(changed=True, updated=True, status=status)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
