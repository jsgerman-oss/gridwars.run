#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This script is intended to run inside the Fly application container, either
# from a scheduled Fly Machine or from a host-side cron job that executes it in
# the container. A future operator wiring step can look like:
#
#   fly machine run --schedule daily --command "/app/bin/backup-evennia.sh" ...
#
# Configure the rclone remote separately before scheduling this. Local retention
# is count-based via --keep. Remote retention is intentionally not managed here;
# configure R2 bucket lifecycle rules separately.

set -eu

DB=/data/evennia.db3
KEEP=7
REMOTE=r2:gridwars-backups
DRY_RUN=0

usage() {
    cat <<EOF
Usage: backup-evennia.sh [OPTIONS]

Options:
  --dry-run          Print commands that would run without executing them
  --keep N           Keep N most recent local /tmp/backup-*.db3 files (default: 7)
  --remote REMOTE    rclone remote destination (default: r2:gridwars-backups)
  --db PATH          SQLite database path (default: /data/evennia.db3)
  --help             Show this help and exit
EOF
}

die_usage() {
    printf '%s\n' "$1" >&2
    usage >&2
    exit 64
}

run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '+'
        for arg in "$@"; do
            printf ' %s' "$arg"
        done
        printf '\n'
        return 0
    fi

    "$@"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --keep)
            [ "$#" -ge 2 ] || die_usage "missing value for --keep"
            KEEP=$2
            shift 2
            ;;
        --remote)
            [ "$#" -ge 2 ] || die_usage "missing value for --remote"
            REMOTE=$2
            shift 2
            ;;
        --db)
            [ "$#" -ge 2 ] || die_usage "missing value for --db"
            DB=$2
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            die_usage "unknown option: $1"
            ;;
    esac
done

case "$KEEP" in
    ''|*[!0-9]*)
        die_usage "--keep must be a non-negative integer"
        ;;
esac

if [ ! -f "$DB" ]; then
    printf 'missing database: %s\n' "$DB" >&2
    exit 1
fi

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
LOCAL=/tmp/backup-$STAMP.db3

if ! run sqlite3 "$DB" ".backup $LOCAL"; then
    printf 'sqlite backup failed: %s -> %s\n' "$DB" "$LOCAL" >&2
    exit 2
fi

if [ "$DRY_RUN" -eq 1 ]; then
    printf '+ sqlite3 %s PRAGMA integrity_check;\n' "$LOCAL"
    CHECK=ok
else
    CHECK=$(sqlite3 "$LOCAL" "PRAGMA integrity_check;") || CHECK=failed
fi

if [ "$CHECK" != "ok" ]; then
    printf 'integrity check failed for %s: %s\n' "$LOCAL" "$CHECK" >&2
    exit 3
fi

if ! run rclone copy "$LOCAL" "$REMOTE/" --progress; then
    printf 'rclone upload failed: %s -> %s/\n' "$LOCAL" "$REMOTE" >&2
    exit 4
fi

START=$((KEEP + 1))
if [ "$DRY_RUN" -eq 1 ]; then
    printf '+ sh -c %s\n' "ls -t /tmp/backup-*.db3 2>/dev/null | tail -n +$START | xargs rm -f"
    BYTES=dry-run
else
    ls -t /tmp/backup-*.db3 2>/dev/null | tail -n +"$START" | xargs rm -f
    BYTES=$(stat -c%s "$LOCAL")
fi

printf 'OK: backed up to %s/backup-%s.db3 (%s bytes)\n' "$REMOTE" "$STAMP" "$BYTES"
