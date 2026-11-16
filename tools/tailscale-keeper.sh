#!/usr/bin/env bash
# Keep tailscaled and the dashboard serve alive in this container.
#
# The container runs tailscaled in userspace mode (no TUN, no systemd). It gets
# reaped, and when it goes the web app at :8443 goes with it. This loop restarts
# the daemon, re-arms the serve, and waits. Klerik's mesh-health check reads the
# same state; this is the other half - keeping it true between checks.
set -u

SOCKET=/opt/data/state/tailscale/tailscaled.sock
STATE=/opt/data/state/tailscale/tailscaled.state
TS="/opt/data/bin/tailscale --socket=$SOCKET"
LOG=/opt/data/state/tailscale/keeper.log

log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }

daemon_up() { pgrep -f "tailscaled .*--socket=$SOCKET" >/dev/null 2>&1; }

start_daemon() {
  log "starting tailscaled"
  nohup /opt/data/bin/tailscaled \
    --tun=userspace-networking \
    --state="$STATE" \
    --socket="$SOCKET" \
    --socks5-server=localhost:1055 \
    >> "$LOG" 2>&1 &
  for _ in $(seq 1 20); do
    sleep 2
    if $TS status >/dev/null 2>&1; then
      log "daemon up"
      return 0
    fi
  done
  log "daemon failed to come up"
  return 1
}

ensure_serve() {
  # 8443 is the dashboard; 443 carries the TurboFit gateway.
  if $TS serve status 2>/dev/null | grep -q ":8443"; then
      return 0
  fi
  log "arming serve 8443 -> 9119"
  $TS serve --bg --https=8443 9119 >/dev/null 2>&1
}

log "keeper started"
while true; do
  if ! daemon_up; then
    start_daemon
  fi
  if daemon_up; then
    ensure_serve
  fi
  sleep 30
done
