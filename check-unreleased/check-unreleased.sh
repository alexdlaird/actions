#!/usr/bin/env bash
# Fails if a version is already released: tagged X.Y.Z, or X.Y.Z+N by a release that also stamped a build number.
# Inputs (environment): VERSION.
set -eo pipefail

RELEASED=$(git tag --list "${VERSION}" "${VERSION}+*")
if [ -n "$RELEASED" ]; then
  echo "::error::${VERSION} is already released (${RELEASED}), so bump the version before releasing."
  exit 1
fi
echo "${VERSION} is unreleased"
