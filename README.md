
# Ebdruplab — Ansible Collections

This repository hosts Ansible collections maintained by Ebdruplab.

## Collections

* **`ebdruplab.semaphoreui`** — Modules and a role for managing Semaphore via its HTTP API.
  📚 Docs: [https://github.com/Ebdruplab/ansible-collection\_ebdruplab/blob/main/ansible\_collections/ebdruplab/semaphoreui/README.md](https://github.com/Ebdruplab/ansible-collection_ebdruplab/blob/main/ansible_collections/ebdruplab/semaphoreui/README.md)

> For any additional collections, see each collection’s `README.md` inside its folder under `ansible_collections/ebdruplab/<collection_name>/`.

## Install (from Galaxy)

```bash
ansible-galaxy collection install ebdruplab.<COLLECTION_NAME>
```

## Install (from source)

```bash
# From repo root
ansible-galaxy collection build ansible_collections/ebdruplab/<COLLECTION_NAME>
ansible-galaxy collection install ./ebdruplab-semaphoreui-*.tar.gz --force
```

## Contributing

* Open issues and PRs against this repo.
* Keep module docs (`DOCUMENTATION`, `EXAMPLES`, `RETURN`) valid so `ansible-doc` works.
  * An example of a script to check this `ansible-doc -t module $(ansible-doc -t module -l | awk '/^ebdruplab\.<COLLECTION_NAME>\./{print $1}')`

## License

MIT — see `LICENSE`.
