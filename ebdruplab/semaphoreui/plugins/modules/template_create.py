from ansible.module_utils.basic import AnsibleModule
from ..module_utils.semaphore_api import semaphore_post, get_auth_headers
import json

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            project_id=dict(type='int', required=True),
            template=dict(type='dict', required=True),
            session_cookie=dict(type='str', required=False, no_log=True),
            api_token=dict(type='str', required=False, no_log=True),
            validate_certs=dict(type='bool', default=True),
        ),
        required_one_of=[["session_cookie", "api_token"]],
        supports_check_mode=False
    )

    url = f"{module.params['host']}:{module.params['port']}/api/project/{module.params['project_id']}/templates"

    headers = get_auth_headers(module.params["session_cookie"], module.params["api_token"])
    headers["Content-Type"] = "application/json"
    body = json.dumps(module.params["template"]).encode("utf-8")

    response_body, status, _ = semaphore_post(url, body=body, headers=headers, validate_certs=module.params["validate_certs"])
    if status not in (200, 201):
        module.fail_json(msg=f"POST failed with status {status}: {response_body}")

    module.exit_json(changed=True, template=json.loads(response_body))

if __name__ == '__main__':
    main()
