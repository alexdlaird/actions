#!/usr/bin/env bash
set -eo pipefail

APPS_DIR="${XCODE_APPS_DIR:-/Applications}"
LATEST_XCODE=$(find "$APPS_DIR" -maxdepth 1 -name 'Xcode*.app' -print0 | xargs -0 -n1 basename \
  | grep -v -E '(beta|Release_Candidate)' | sort -V | tail -n 1 || true)
if [ -z "$LATEST_XCODE" ]; then
  echo "::error::No stable Xcode found in ${APPS_DIR}"
  exit 1
fi
# For this job only, so a self-hosted runner needs no root and jobs on the same Mac never switch it for each other
export DEVELOPER_DIR="${APPS_DIR}/${LATEST_XCODE}/Contents/Developer"
echo "DEVELOPER_DIR=${DEVELOPER_DIR}" >> "$GITHUB_ENV"
xcodebuild -version
