#!/usr/bin/env bash
set -euo pipefail

if [ -z "$VERSION" ]; then
  VERSION=$(gh api "repos/${REPO_SLUG}/tags" | jq -r --arg regex "$VERSION_REGEX" '[.[] | select(.name | test($regex))][0].name')
  if [ -z "$VERSION" ] || [ "$VERSION" = "null" ]; then
    echo "::error::No version tags matching '${VERSION_REGEX}' found in ${REPO_SLUG}"
    exit 1
  fi
fi

if [ "$READ_TAG" = "true" ] && { [ -z "$REF" ] || { [ "$REQUIRE_BUILD_RUN" = "true" ] && [ -z "$BUILD_RUN_ID" ]; }; }; then
  TAG=$(gh api "repos/${REPO_SLUG}/git/ref/tags/${VERSION}" --jq '.object.type + " " + .object.sha')
  read -r TAG_TYPE TAG_SHA <<< "$TAG"
  if [ "$TAG_TYPE" = "tag" ]; then
    REF=$(gh api "repos/${REPO_SLUG}/git/tags/${TAG_SHA}" --jq .object.sha)
    BUILD_RUN_ID=$(gh api "repos/${REPO_SLUG}/git/tags/${TAG_SHA}" --jq .message \
      | sed -n 's/^Build-Run: \([0-9]*\)$/\1/p')
  else
    REF="$TAG_SHA"
    BUILD_RUN_ID=""
  fi
fi

if [ "$REQUIRE_BUILD_RUN" = "true" ] && [ -z "$BUILD_RUN_ID" ]; then
  echo "::error::Tag ${VERSION} names no Build-Run, so its builds can't be found."
  exit 1
fi

echo "Resolved ${VERSION}${REF:+ at ${REF:0:7}}${BUILD_RUN_ID:+ (Build run ${BUILD_RUN_ID})}"
{
  echo "version=${VERSION}"
  echo "ref=${REF}"
  echo "build_run_id=${BUILD_RUN_ID}"
} >> "$GITHUB_OUTPUT"
