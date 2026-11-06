#!/usr/bin/env bash
# iOS deploys on a shared self-hosted Mac share its keychain search list, ~/.appstoreconnect and provisioning
# profiles, so they take turns. A lock whose holder is gone, or older than any job may run, is broken.
set -eo pipefail

LOCK="${LOCK_PATH/#\~/$HOME}"
OWNER="$GITHUB_REPOSITORY run $GITHUB_RUN_ID attempt $GITHUB_RUN_ATTEMPT"

# Whether [pid] is a live runner job process (an id reused by something else isn't).
is_job_process() {
  ps -o command= -p "$1" 2>/dev/null | grep -q 'Runner\.Worker'
}

# The job's runner process (Runner.Worker), which lives exactly as long as the job. This step's own shell exits with
# the step, so it can't stand for the holder. "-" when there's none above this script.
job_process() {
  local pid=$PPID
  while [ -n "$pid" ] && [ "$pid" -gt 1 ]; do
    if is_job_process "$pid"; then
      echo "$pid"
      return
    fi
    pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
  done
  echo "-"
}

case "$MODE" in
  acquire)
    # The owner file is "<job process id> <run>"; with no job process known ("-"), only its age breaks it
    until mkdir "$LOCK" 2>/dev/null; do
      HELD_BY=$(cat "$LOCK/owner" 2>/dev/null || true)
      HOLDER_PID=${HELD_BY%% *}
      if { [[ "$HOLDER_PID" =~ ^[0-9]+$ ]] && ! is_job_process "$HOLDER_PID"; } \
        || [ -n "$(find "$LOCK" -maxdepth 0 -mmin +"$STALE_MINUTES" 2>/dev/null)" ]; then
        # Only the lock judged stale: another waiter may have broken it and taken a fresh one meanwhile
        if [ "$(cat "$LOCK/owner" 2>/dev/null || true)" = "$HELD_BY" ]; then
          echo "::warning::Breaking a stale lock held by ${HELD_BY#* }"
          rm -rf "$LOCK"
        fi
        continue
      fi
      echo "Waiting for ${HELD_BY#* }"
      sleep "${POLL_SECONDS:-15}"
    done
    echo "$(job_process) $OWNER" > "$LOCK/owner"
    ;;
  release)
    if [ "$(cut -d' ' -f2- "$LOCK/owner" 2>/dev/null)" = "$OWNER" ]; then
      rm -rf "$LOCK"
    fi
    ;;
  *)
    echo "::error::\"mode\" must be \"acquire\" or \"release\", not ${MODE}"
    exit 1
    ;;
esac
