#!/usr/bin/env bash
# Compares the working tree (untracked files included) when COMMIT is empty, otherwise COMMIT (fetched when missing).
# In changelog mode CHANGELOG.md, which the release rewrites, may differ.
set -eo pipefail

EXCLUDE=()
if [ "$CHANGELOG" = "true" ]; then
  EXCLUDE=(':(exclude)CHANGELOG.md')
fi
if [ -z "$COMMIT" ]; then
  if ! git diff --quiet "$TESTED_SHA" -- . "${EXCLUDE[@]}" \
      || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    echo "::error::The code about to ship differs from the tested commit ${TESTED_SHA:0:7}:"
    git diff --stat "$TESTED_SHA" -- . "${EXCLUDE[@]}"
    git ls-files --others --exclude-standard
    exit 1
  fi
else
  git cat-file -e "${COMMIT}^{commit}" 2>/dev/null || git fetch -q origin "$COMMIT"
  if ! git diff --quiet "$TESTED_SHA" "$COMMIT" -- . "${EXCLUDE[@]}"; then
    echo "::error::${COMMIT:0:7} is not the tested commit ${TESTED_SHA:0:7}'s code; stopping before anything ships."
    exit 1
  fi
fi
