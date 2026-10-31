#!/usr/bin/env bash
# Reads a version from its file with the match part of the sed expression that writes it, so one setting
# describes the file however it's formatted. Two-part versions (X.Y) are written as X.Y.0 and read back as X.Y.
# Inputs (environment): VERSION_FILE, VERSION_PATTERN, VERSION_PARTS (2 or 3), REF (a commit, or empty for the working
# tree). Outputs: version, file_version.
set -euo pipefail

MATCH=$(sed -E 's#^s/(([^/\\]|\\.)*)/.*#\1#' <<< "$VERSION_PATTERN")
if [ -n "$REF" ]; then
  CONTENT=$(git show "${REF}:${VERSION_FILE}")
else
  CONTENT=$(cat "$VERSION_FILE")
fi
FILE_VERSION=$(grep -m1 -e "$MATCH" <<< "$CONTENT" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
if [ -z "$FILE_VERSION" ]; then
  echo "::error::Could not read an X.Y.Z version from ${VERSION_FILE} (line matching: ${MATCH})"
  exit 1
fi
case "$VERSION_PARTS" in
  3) VERSION="$FILE_VERSION" ;;
  2)
    if [ "${FILE_VERSION##*.}" != "0" ]; then
      echo "::error::${VERSION_FILE} has ${FILE_VERSION}, but two-part versions are written as X.Y.0"
      exit 1
    fi
    VERSION="${FILE_VERSION%.*}"
    ;;
  *)
    echo "::error::version-parts must be 2 or 3, not ${VERSION_PARTS}"
    exit 1
    ;;
esac
echo "version=${VERSION}" >> "$GITHUB_OUTPUT"
echo "file_version=${FILE_VERSION}" >> "$GITHUB_OUTPUT"
