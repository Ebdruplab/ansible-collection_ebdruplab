Role Name
=========

A brief description of the role goes here.

Requirements
------------

Any pre-requisites that may not be covered by Ansible itself or the role should be mentioned here. For instance, if the role uses the EC2 module, it may be a good idea to mention in this section that the boto package is required.

Role Variables
--------------

A description of the settable variables for this role should go here, including any variables that are in defaults/main.yml, vars/main.yml, and any variables that can/should be set via parameters to the role. Any variables that are read from other roles and/or the global scope (ie. hostvars, group vars, etc.) should be mentioned here as well.

Dependencies
------------

A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: username.rolename, x: 42 }
```yaml
project_deploy_vars:
  - host: semaphore.example.com
    port: 3000
    username: admin
    password: changeme

    project:
      name: MyProject
      description: This is a demo project
      key_id: 1
      repository_id: 1

    repositories:
      - name: main-repo
        url: git@github.com:myorg/main.git
        ssh_key_id: 1
        branch: main

    environments:
      - name: dev
        variables:
          - key: ENV
            value: development

      - name: prod
        variables:
          - key: ENV
            value: production

    inventories:
      - name: staging
        type: static
        inventory: |
          [web]
          web1.example.com

      - name: prod
        type: static
        inventory: |
          [db]
          db1.example.com

    templates:
      - name: Build App
        playbook: build.yml
        inventory: staging
        environment: dev
        arguments: "--tags build"

      - name: Deploy App
        playbook: deploy.yml
        inventory: prod
        environment: prod
        arguments: "--limit prod"

```


License
-------

BSD

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
