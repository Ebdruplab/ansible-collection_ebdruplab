#!/usr/bin/env bash

# ------------------------------------------------------------
# Script: check_ansible_docs.sh
# Description:
#   Checks whether all Ansible module docs for the given
#   collection prefix are valid. Prints OK in green and ERROR in red.
# ------------------------------------------------------------

MODULE_PREFIX="ebdruplab.semaphoreui"

COLL_VERSION=$(
  ansible-galaxy collection list 2>/dev/null \
  | awk -v c="$MODULE_PREFIX" '$1==c {print $2; exit}'
)
[ -z "$COLL_VERSION" ] && COLL_VERSION="unknown"

echo -e "\e[36m=== Testing $MODULE_PREFIX (version: $COLL_VERSION) ===\e[0m"
echo

for m in $(ansible-doc -l | awk -v p="$MODULE_PREFIX" '$1 ~ p {print $1}'); do
  OUTPUT=$(ansible-doc "$m" 2>&1)
  STATUS=$?

  if [ $STATUS -eq 0 ]; then
    echo -e "\e[32m✔ $m OK\e[0m"
  else
    ERROR_LINE=$(echo "$OUTPUT" | grep -m1 -E 'ERROR!|Expected|Unable|failed|Traceback')
    [ -z "$ERROR_LINE" ] && ERROR_LINE="Documentation parsing failed"

    echo -e "\e[31m✘ $m ERROR\e[0m"
    echo -e "  \e[31m↳ $ERROR_LINE\e[0m"
  fi
done
