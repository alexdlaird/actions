#!/usr/bin/env bash
# Creates a Sentry release for a version, associates the commits it adds (from the local checkout's history), and
# finalizes it.
# Inputs (environment): VERSION, SENTRY_PROPERTIES, SENTRY_AUTH_TOKEN, SENTRY_CLI_VERSION; sentry-cli reads the
# SENTRY_* ones itself.
set -euo pipefail

if [ ! -f "$SENTRY_PROPERTIES" ]; then
  echo "::error::${SENTRY_PROPERTIES} not found, so there's no Sentry project to release ${VERSION} in."
  exit 1
fi

pip install --quiet "sentry-cli==${SENTRY_CLI_VERSION}"

sentry-cli releases new "$VERSION"
sentry-cli releases set-commits --auto "$VERSION"
sentry-cli releases finalize "$VERSION"
echo "Created and finalized Sentry release ${VERSION}"
