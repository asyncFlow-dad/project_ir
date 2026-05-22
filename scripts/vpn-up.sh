#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VPN_DIR="$ROOT/config/vpn"
LOG_DIR="$ROOT/logs"
PID_FILE="$LOG_DIR/openvpn.pid"
LOG_FILE="$LOG_DIR/openvpn.log"
AUTH_FILE="$VPN_DIR/auth.txt"

OPENVPN_BIN="${OPENVPN_BIN:-/opt/homebrew/sbin/openvpn}"
if [[ ! -x "$OPENVPN_BIN" ]]; then
  OPENVPN_BIN="$(command -v openvpn || true)"
fi

mkdir -p "$LOG_DIR"
chmod 600 "$AUTH_FILE" 2>/dev/null || true

if [[ ! -x "$OPENVPN_BIN" ]]; then
  echo "openvpn not found. Install: brew install openvpn" >&2
  exit 1
fi

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "OpenVPN already running (pid $(cat "$PID_FILE"))"
  exit 0
fi

OVPN_FILE="${OPENVPN_PROFILE:-}"
if [[ -z "$OVPN_FILE" ]]; then
for candidate in "$VPN_DIR"/client.ovpn "$VPN_DIR"/*.ovpn; do
  if [[ -f "$candidate" ]]; then
    OVPN_FILE="$candidate"
    break
  fi
done
fi

if [[ -z "$OVPN_FILE" ]]; then
  echo "Missing OpenVPN profile. Place contest .ovpn at:" >&2
  echo "  $VPN_DIR/client.ovpn" >&2
  exit 1
fi

echo "Starting OpenVPN with $OVPN_FILE"

# root(osascript/sudo) cannot read Desktop paths on macOS without Full Disk Access
STAGE_DIR="/tmp/ir-vpn-$$"
mkdir -p "$STAGE_DIR"
cp "$OVPN_FILE" "$STAGE_DIR/client.ovpn"
cp "$AUTH_FILE" "$STAGE_DIR/auth.txt"
chmod 600 "$STAGE_DIR/auth.txt"
chmod 644 "$STAGE_DIR/client.ovpn"
STAGED_OVPN="$STAGE_DIR/client.ovpn"
STAGED_AUTH="$STAGE_DIR/auth.txt"
STAGED_PID="$STAGE_DIR/openvpn.pid"
STAGED_LOG="$STAGE_DIR/openvpn.log"
ln -sf "$STAGED_PID" "$PID_FILE" 2>/dev/null || true
ln -sf "$STAGED_LOG" "$LOG_FILE" 2>/dev/null || true

OPENVPN_ARGS=(
  --config "$STAGED_OVPN"
  --auth-user-pass "$STAGED_AUTH"
  --auth-nocache
  --daemon
  --writepid "$STAGED_PID"
  --log "$STAGED_LOG"
  --verb 3
)

if [[ "$(uname -s)" == "Darwin" ]] && ! sudo -n true 2>/dev/null; then
  echo "Requesting administrator privileges (macOS password prompt)..."
  OPENVPN_CMD=$(printf '%q ' "$OPENVPN_BIN" "${OPENVPN_ARGS[@]}")
  osascript -e "do shell script \"${OPENVPN_CMD}\" with administrator privileges"
elif sudo -n true 2>/dev/null; then
  sudo "$OPENVPN_BIN" "${OPENVPN_ARGS[@]}"
else
  echo "OpenVPN needs root for TUN on macOS. Run: sudo $0" >&2
  exit 1
fi

sleep 3
VPN_PID=""
if [[ -f "$STAGED_PID" ]]; then
  VPN_PID="$(cat "$STAGED_PID" 2>/dev/null || true)"
fi
if [[ -n "$VPN_PID" ]] && ps -p "$VPN_PID" -o comm= 2>/dev/null | grep -q openvpn; then
  echo "OpenVPN started (pid $VPN_PID). Log: $STAGED_LOG"
  echo "Routes: 10.196.197.0/24 via VPN (utun). SSH: ssh ir_mac"
elif pgrep -f "openvpn.*${STAGE_DIR}" >/dev/null 2>&1; then
  VPN_PID="$(pgrep -f "openvpn.*${STAGE_DIR}" | head -1)"
  echo "OpenVPN started (pid $VPN_PID). Log: $STAGED_LOG"
else
  echo "OpenVPN failed to start. Check $STAGED_LOG" >&2
  sudo tail -15 "$STAGED_LOG" 2>/dev/null >&2 || tail -15 "$STAGED_LOG" 2>/dev/null >&2 || true
  exit 1
fi
