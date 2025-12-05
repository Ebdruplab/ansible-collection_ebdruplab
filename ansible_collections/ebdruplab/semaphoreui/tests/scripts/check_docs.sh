#!/usr/bin/env bash

# ------------------------------------------------------------
# Script: check_ansible_docs.sh
# Description:
#   Checks whether all Ansible module docs for the given
#   collection prefix are valid. Prints OK in green and ERROR in red.
# ------------------------------------------------------------

MODULE_PREFIX="ebdruplab.semaphoreui"

for m in $(ansible-doc -l | awk -v p="$MODULE_PREFIX" '$1 ~ p {print $1}'); do
  if ansible-doc "$m" >/dev/null 2>&1; then
    echo -e "\e[32m✔ $m OK\e[0m"
  else
    echo -e "\e[31m✘ $m ERROR\e[0m"
  fi
done

