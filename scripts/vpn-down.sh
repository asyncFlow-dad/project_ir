#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT/logs/openvpn.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No OpenVPN pid file at $PID_FILE"
  exit 0
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
  sudo kill "$PID"
  echo "Stopped OpenVPN (pid $PID)"
else
  echo "OpenVPN not running (stale pid $PID)"
fi

rm -f "$PID_FILE"
