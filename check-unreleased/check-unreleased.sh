#!/usr/bin/env bash
set -eo pipefail

RELEASED=$(git tag --list "${VERSION}" "${VERSION}+*")
if [ -n "$RELEASED" ]; then
  echo "::error::${VERSION} is already released (${RELEASED}), so bump the version before releasing."
  exit 1
fi
echo "${VERSION} is unreleased"
