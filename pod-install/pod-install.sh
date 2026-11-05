#!/usr/bin/env bash
# Forces CocoaPods' CDN client onto HTTP/1.1 (cocoapods_http11.rb) and retries transient CDN errors.
set -eo pipefail

# The xcodeproj gem CocoaPods uses can't open objectVersion 70 (Xcode 16+); Flutter's build migrates it back
sed -i '' 's/objectVersion = 70;/objectVersion = 56;/g' "${IOS_DIRECTORY}/Runner.xcodeproj/project.pbxproj"
export RUBYOPT="-r${SHIM}"
cd "$IOS_DIRECTORY"
for attempt in $(seq 1 "$ATTEMPTS"); do
  pod install --repo-update && exit 0
  if [ "$attempt" = "$ATTEMPTS" ]; then
    echo "::error::pod install failed after ${ATTEMPTS} attempts"
    exit 1
  fi
  echo "::warning::pod install attempt $attempt failed; retrying in $((attempt * 20))s"
  sleep $((attempt * 20))
done
