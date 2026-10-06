#!/usr/bin/env bash
# MO-1: 1 warm-up request, then 5 timed requests to the label-count endpoint.
# Token auth is used because basic auth hashes the password on every request,
# which would add its own cost to every measurement.
# Usage: measure.sh <task_id> <user> <pass> [server] [query]
set -euo pipefail

task_id=$1
server=${4:-http://localhost:8080}
query=${5:-}
url="$server/api/tasks/$task_id/label-counts$query"

key=$(curl -s -X POST "$server/api/auth/login" -H 'Content-Type: application/json' \
    -d "{\"username\": \"$2\", \"password\": \"$3\"}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["key"])')

echo "date: $(date -u +%FT%TZ)"
echo "url: $url"
curl -s -o /dev/null -H "Authorization: Token $key" "$url"
echo "warm-up done"

times=()
for run in 1 2 3 4 5; do
    t=$(curl -s -o /dev/null -w '%{time_total}' -H "Authorization: Token $key" "$url")
    echo "run $run: ${t}s"
    times+=("$t")
done

printf '%s\n' "${times[@]}" | sort -n | awk '
    { v[NR] = $1 * 1000 }
    END { printf "median: %.1f ms  min: %.1f ms  max: %.1f ms  spread: %.1f ms\n", v[3], v[1], v[5], v[5] - v[1] }'
