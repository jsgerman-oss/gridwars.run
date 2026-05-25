<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Evennia Deploy Architecture
## 1. Context
GridWars.run is a pre-alpha, open-source PvP MUD built on Evennia v6.0.0.
The landing site can remain on Cloudflare Pages, but the playable game needs a
host that accepts raw TCP for telnet and keeps the Evennia runtime supervised.

This document is for the operator deploying v0.2 and for future contributors
who need to understand why the first production shape is intentionally small:
one Fly.io app, one machine, one persistent SQLite database, and explicit
escape hatches for the next scale point.

The host decision is settled for v0.2: use Fly.io. Hetzner remains a fallback
if Fly volumes or pricing become a real blocker. Home hosting and tunnel-based
approaches are rejected for public launch because they add client friction and
more failure surfaces than the game needs right now.

## 2. Process Model
Fly runs one container instance as one machine with `restart_policy =
"on-failure"`. The container starts Evennia in the foreground with
`evennia start --log`, so Fly's supervisor watches the main process and restarts
the machine after a crash.

Evennia bundles the Portal and Server process model, including telnet and the
webclient, so v0.2 does not split the webclient into a separate service. The
default public process exposes telnet on `4000` and Evennia's HTTP/WebSocket
webclient on `4001`.

Run single-region for v0.2. Multi-region is deferred to v0.3+ because SQLite is
a single-writer database, character state must stay coherent during PvP, and
future duel arena state should not be split across regions without a deliberate
state model.

## 3. Data Persistence
Use SQLite at `/data/evennia.db3` on a Fly persistent volume. Start with a 1 GB
volume mounted at `/data`; the Docker image or runtime config should point
Evennia's SQLite database path there instead of storing the database in the
ephemeral container filesystem.

Postgres is a v0.3+ option, not a launch requirement. When concurrent players
consistently exceed roughly 30, plan a maintenance window, take a verified
SQLite backup, add a Postgres service, run Django migrations against Postgres,
and import the data through Django/Evennia-supported migration tooling rather
than direct table surgery.

Fly volumes are durable block storage tied to one machine in one region, not a
managed multi-region database. If Fly performs host maintenance or needs to
move the volume, expect a few minutes of downtime. That is acceptable for v0.2
as long as off-host backups exist and restore drills are routine.

## 4. DNS Plan
Keep the `gridwars.run` apex on Cloudflare Pages, proxied, for the landing
site. Do not route telnet through the apex record.

Create `game.gridwars.run` as an unproxied Cloudflare DNS record. Point its A
record at the Fly anycast IPv4 from `fly ips list`, leave it grey-clouded, and
set TTL to 300 seconds so the operator can repoint quickly if the host changes.
Cloudflare's free proxy does not support raw TCP, and enterprise TCP proxying is
not a sensible cost for a small MUD.

An optional `telnet.gridwars.run` alias can be added later if players need a
more explicit telnet hostname. Defer it for v0.2 to keep the launch DNS surface
small.

## 5. Network And Ports
Expose public TCP port `4000` for telnet and public TCP/HTTP port `4001` for
the Evennia webclient. Use identical internal ports in `fly.toml`; there is no
need for remapping in the first deploy.

The webclient currently serves HTTP and WebSocket traffic on the same Evennia
port. For v0.2, raw HTTP on `4001` is acceptable only because no production
logins should be encouraged through the webclient until TLS lands.

TLS for the webclient is a v0.3 follow-up. The likely options are Caddy in front
of Evennia or Cloudflare Tunnel for the webclient-only path. Telnet remains raw
TCP for compatibility with ordinary MUD clients.

Runtime egress should be effectively empty. The image build needs outbound
network access for dependency installation, but the running game does not need
third-party API calls for v0.2.

## 6. Secrets
Set Django's secret through Fly secrets:

```bash
fly secrets set EVENNIA_SECRET_KEY="$(openssl rand -base64 64)"
```

The value must never be committed. Runtime settings should read
`EVENNIA_SECRET_KEY` from the environment, with local developer settings kept in
the existing Evennia `secret_settings.py` path where needed.

Future SMTP credentials for password reset also belong in Fly secrets. They are
not part of the v0.2 launch surface.

## 7. Backups
Run a nightly backup job inside the container that first quiets interactive
activity and then uses SQLite's online backup command:

```bash
evennia menu --close && sqlite3 /data/evennia.db3 ".backup /tmp/backup-$(date +%Y%m%d).db3"
```

After the backup file is created, copy it off-host with `rclone copy` to
Cloudflare R2. The operator already has a Cloudflare account, and the R2 free
tier is sufficient for v0.2 database sizes.

Use simple GFS retention: 14 daily backups, 8 weekly backups, and 12 monthly
backups. The backup bucket should be private, with credentials stored as Fly
secrets and scoped only to the backup path.

Run a monthly restore drill. The operator should keep a calendar reminder for a
script that downloads a recent backup, restores it into a scratch SQLite file,
runs `evennia migrate --noinput`, and checks that expected row counts match the
source backup.

## 8. Logs And Monitoring
Use `fly logs -a gridwars-run` for live log tails during v0.2 operations.
Shipping logs to Loki, Axiom, or a similar archive is deferred until the service
has enough traffic to justify another dependency.

Add an external heartbeat. UptimeRobot free tier or Better Stack's free tier can
ping `https://game.gridwars.run:4001/` every 5 minutes and alert the operator by
email plus ntfy push.

Application-level metrics are deferred. No Prometheus, StatsD, or custom metrics
pipeline is needed for the first public launch.

## 9. Deploy Mechanism
For v0.2, deploy manually from the operator laptop with `fly deploy`.
Reproducibility comes from keeping the Dockerfile, `fly.toml`, and runtime
settings in the repository.

For v0.3+, add a GitHub Actions workflow that runs `fly deploy --remote-only`
on pushes to `main`, gated by a repository secret named `FLY_API_TOKEN`. File
that workflow as separate work; do not include it in the architecture-doc task.

Rollback uses Fly releases. Run `fly releases list` to find the previous image,
then redeploy that image with:

```bash
fly deploy --image registry.fly.io/gridwars-run:deployment-<sha>
```

## 10. Cost Model
At v0.2 scale, up to roughly 10 concurrent players, expect about $2-7 per month.
A single `shared-cpu-1x` machine with 256 MB RAM and a 1 GB volume often fits
within Fly's free allowance, but the plan should tolerate a small monthly bill.

At v0.3 scale, around 50 concurrent players, expect about $15-30 per month. That
probably means sizing up to `shared-cpu-2x` with 512 MB RAM, plus any R2 storage
growth and a possible Postgres service.

The `gridwars.run` domain is already paid through Cloudflare Registrar and does
not change the monthly hosting estimate.

## 11. Failure Modes And Responses
- Container OOM: Fly restarts the machine; detect through `fly logs` and
  heartbeat alerts, then resize memory if it repeats.
- Volume corruption: stop the app, preserve the damaged volume, restore the most
  recent verified R2 backup, run migrations, and restart.
- Fly maintenance window: expect short downtime because the volume is single
  region; announce if scheduled maintenance is known in advance.
- DNS misconfiguration: telnet or webclient stops resolving; verify Cloudflare
  grey-cloud status, A record target from `fly ips list`, and TTL 300.
- Secret rotation gone wrong: app fails boot or sessions invalidate; set the
  previous Fly secret value if available, otherwise rotate deliberately and
  accept session invalidation.

## 12. v0.3+ Deferred Items
- Webclient TLS through Caddy or a Cloudflare Tunnel path.
- GitHub Actions deploys using `fly deploy --remote-only`.
- Postgres migration after sustained concurrency exceeds roughly 30 players.
- Centralized log archive in Loki, Axiom, or similar.
- Application metrics and alerting beyond heartbeat checks.
- Optional `telnet.gridwars.run` DNS alias.
- Multi-region architecture with an explicit state-coherence design.
