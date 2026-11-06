#!/usr/bin/env bash
# sentry-cli reads the SENTRY_* inputs from the environment itself.
set -euo pipefail

if [ ! -f "$SENTRY_PROPERTIES" ]; then
  echo "::error::${SENTRY_PROPERTIES} not found, so there's no Sentry project to release ${VERSION} in"
  exit 1
fi

pip install --quiet "sentry-cli==${SENTRY_CLI_VERSION}"

sentry-cli releases new "$VERSION"
sentry-cli releases set-commits --auto "$VERSION"
sentry-cli releases finalize "$VERSION"
echo "Created and finalized Sentry release ${VERSION}"
