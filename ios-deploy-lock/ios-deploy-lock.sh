#!/usr/bin/env bash
# Takes or releases a machine-wide lock so iOS deploys on a shared self-hosted Mac take turns: they share its keychain
# search list, ~/.appstoreconnect and provisioning profiles. A lock whose holder is gone, or older than any job may
# run, is broken.
# Inputs (environment): MODE (acquire or release), LOCK_PATH, STALE_MINUTES.
set -eo pipefail

LOCK="${LOCK_PATH/#\~/$HOME}"
OWNER="$GITHUB_REPOSITORY run $GITHUB_RUN_ID attempt $GITHUB_RUN_ATTEMPT"
case "$MODE" in
  acquire)
    # The owner file is "<runner process id> <run>"; the process lives exactly as long as the holding job
    until mkdir "$LOCK" 2>/dev/null; do
      HOLDER_PID=$(cut -d' ' -f1 "$LOCK/owner" 2>/dev/null || true)
      if { [ -n "$HOLDER_PID" ] && ! ps -p "$HOLDER_PID" > /dev/null; } \
        || [ -n "$(find "$LOCK" -maxdepth 0 -mmin +"$STALE_MINUTES" 2>/dev/null)" ]; then
        echo "::warning::Breaking a stale lock held by $(cut -d' ' -f2- "$LOCK/owner" 2>/dev/null)"
        rm -rf "$LOCK"
        continue
      fi
      echo "Waiting for $(cut -d' ' -f2- "$LOCK/owner" 2>/dev/null || echo 'another iOS deploy')"
      sleep 15
    done
    echo "$PPID $OWNER" > "$LOCK/owner"
    ;;
  release)
    if [ "$(cut -d' ' -f2- "$LOCK/owner" 2>/dev/null)" = "$OWNER" ]; then
      rm -rf "$LOCK"
    fi
    ;;
  *)
    echo "::error::mode must be acquire or release, not ${MODE}"
    exit 1
    ;;
esac
