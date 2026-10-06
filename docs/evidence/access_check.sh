#!/usr/bin/env bash
# Shows the HTTP status of the label-count endpoint for: no login, a user without
# access to the task, and the task owner.
# Usage: access_check.sh <task_id> <owner_user> <owner_pass> <other_user> <other_pass> [server]
set -euo pipefail

task_id=$1
server=${6:-http://localhost:8080}
url="$server/api/tasks/$task_id/label-counts"

token() {
    curl -s -X POST "$server/api/auth/login" -H 'Content-Type: application/json' \
        -d "{\"username\": \"$1\", \"password\": \"$2\"}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["key"])'
}

echo "GET $url"
echo "no login:        $(curl -s -o /dev/null -w '%{http_code}' "$url")"
echo "user '$4':  $(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Token $(token "$4" "$5")" "$url")"
echo "owner '$2':  $(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Token $(token "$2" "$3")" "$url")"
