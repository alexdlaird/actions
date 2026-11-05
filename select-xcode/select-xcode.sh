#!/usr/bin/env bash
set -eo pipefail

LATEST_XCODE=$(find /Applications -maxdepth 1 -name 'Xcode*.app' -print0 | xargs -0 -n1 basename \
  | grep -v -E '(beta|Release_Candidate)' | sort -V | tail -n 1)
if [ -z "$LATEST_XCODE" ]; then
  echo "::error::No stable Xcode found in /Applications"
  exit 1
fi
sudo xcode-select -s "/Applications/${LATEST_XCODE}/Contents/Developer"
xcodebuild -version
