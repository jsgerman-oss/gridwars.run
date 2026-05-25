# Evennia hosting options for gridwars.run v0.2

> Prices Q2-2026, recheck before commit. Scope: minimum viable production host for the Evennia telnet backend so players can connect to a public address.

## Problem

The Evennia game server listens on telnet `:4000` (and webclient/websocket on `:4001`). Today that port is dark — only reachable on the operator's LAN. Cloudflare Pages, which serves the `gridwars.run` landing site, does NOT proxy arbitrary TCP, so the game traffic cannot ride the same edge. We need a host that:

1. Accepts inbound TCP on a public port (telnet 4000 minimum; websocket 4001 next).
2. Keeps the Evennia process supervised and restarts on crash.
3. Costs at most a small-coffee-per-month at v0.2 scale (single-digit concurrent players, no persistence yet beyond local SQLite).

## DNS constraint (load-bearing)

The apex `gridwars.run` is owned by Cloudflare Pages (proxied, orange-cloud). Telnet cannot ride a proxied record — Cloudflare's proxy is HTTP(S)-only on the free tier. The plan is to add a SECOND DNS record, e.g. `game.gridwars.run`, as an **unproxied (DNS-only, grey-cloud) A record** pointing at the chosen host's public IPv4. Every option below assumes this.

## Shortlist

Cloud-megavendor (AWS/GCP/Azure) is intentionally excluded — overkill at v0.2 scale and the cognitive overhead would slow iteration.

### Comparison

| Host | Monthly cost (v0.2) | TCP :4000 effort | Ops burden | Restart-on-crash |
| --- | --- | --- | --- | --- |
| **Fly.io** (shared-cpu-1x, 256MB) | ~$2-7 (free allowance covers most of it) | Native — declare TCP service in `fly.toml` with `internal_port=4000` | Low — managed runtime, `fly deploy` from local | Built-in — VM restart policy + health checks |
| **Hetzner CX22 VPS** | €4.51 (~$5) flat | Trivial — `ufw allow 4000`, point DNS at the static IPv4 | Medium — operator owns OS patching, systemd unit, log rotation | systemd `Restart=on-failure` |
| **Home server + Cloudflare Tunnel** | $0 marginal | Possible but awkward — CF Tunnel is HTTP-first; TCP needs `cloudflared access tcp` on every client OR a separate `tcp` ingress on a public-named hostname. Telnet from arbitrary MUD clients won't traverse a CF Access TCP tunnel without the client wrapper. | High — home network reliability (NAT, ISP IP changes, uptime, fan noise) | `systemd` on the home box, but the tunnel itself is a second failure surface |

### Tailscale Funnel — considered, ruled out

Tailscale Funnel currently exposes HTTPS/HTTP/TCP-over-TLS only; raw telnet on a registered port without TLS is not in its supported feature set as of Q2-2026. Mentioned here so the decision is on record.

## Recommendation: Fly.io

Pick **Fly.io**. Three reasons:

1. **TCP :4000 is a first-class config**, not a workaround. `fly.toml` declares the port, fly's edge proxies it, the player's MUD client sees a normal telnet socket. No tunnel client, no NAT-traversal weirdness.
2. **Cognitive distance from current stack is small.** The operator already runs serverless edge on Cloudflare — Fly's deploy model (push a Dockerfile, get a region-pinned VM) is the closest neighbor and won't require a new mental model for ops.
3. **Cost is in the noise at v0.2.** A `shared-cpu-1x` with 256MB and 1GB volume runs around $2-7/mo depending on uptime, well within the free allowance for a single-region single-app deployment. If we outgrow it, Hetzner is a clean exit.

The Hetzner CX22 is the fallback if Fly throws a real blocker (e.g. SQLite persistence on the volume is too slow, or the operator wants EU-region data residency that Fly's free tier doesn't pin). Home-server-tunnel is parked — too many failure surfaces for a public-facing service.

## Open questions for the operator

1. Region — Fly defaults to the nearest edge. Pin to `iad` (US-east), `sjc` (US-west), or `fra` (EU)? Affects baseline latency for the playerbase.
2. Persistence — Evennia ships with SQLite by default. Acceptable for v0.2, or do we want a managed Postgres (Fly Postgres add-on, ~$2/mo extra) from day one to avoid a later migration?
3. Webclient port — `:4001` (websocket) should be exposed alongside `:4000` so the in-browser client works. Confirm in scope for the first deploy.
4. Backup cadence — do we snapshot the SQLite volume nightly off-host (R2 / B2 / Hetzner Storage Box), or accept the risk that a Fly volume loss = full reset until v0.3?
5. Secrets — Evennia's `SECRET_KEY` and any future API keys live in `fly secrets set`, NOT in the repo. Confirm operator is OK with Fly being the secret store.
