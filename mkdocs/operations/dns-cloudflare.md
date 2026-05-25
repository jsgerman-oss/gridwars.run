# SPDX-License-Identifier: AGPL-3.0-or-later
# Cloudflare DNS for game.gridwars.run

Use this runbook when you set up DNS for the GridWars.run game backend. Bring these prerequisites:
- Cloudflare account access to the `gridwars.run` zone.
- Public Fly IPv4 address for the game app.
- A terminal with `dig` and `nc`.

Get the Fly IPv4 before you open Cloudflare:

```bash
fly ips list --json | jq -r '.[] | select(.Type=="v4") | .Address'
```

## Why This Must Be DNS Only

Keep `game.gridwars.run` unproxied.
Cloudflare's proxy handles HTTP and HTTPS on the free and pro tiers.
Do not put raw TCP game traffic behind the orange cloud.
Telnet uses TCP port `4000`.
An orange-cloud record resolves to Cloudflare edge addresses.
Those edge addresses do not forward the telnet service.
The client will connect to the wrong place and hang.
Use a grey-cloud record labeled **DNS only**.

## Add the A Record

Plan for about 5 minutes.

1. Open the Cloudflare dashboard.
2. Click **Websites**.
3. Click the `gridwars.run` zone.
4. In the left navigation, click **DNS**.
5. Click **Records**.
6. Click **Add record**.
7. Set **Type** to **A**.
8. Set **Name** to `game`.
9. Confirm Cloudflare shows the full name as `game.gridwars.run`.
10. Set **IPv4 address** to the Fly IPv4 from `fly ips list`.
11. Find **Proxy status**.
12. If the cloud is orange, click it once.
13. Confirm the cloud is grey.
14. Confirm the label says **DNS only**.
15. Set **TTL** to **5 min**.
16. Confirm Cloudflare shows `300` seconds if it exposes the raw value.
17. Click **Save**.
18. Confirm the records table shows `game`, type `A`, the Fly IPv4, and **DNS only**.

## Verify DNS

Plan for about 2 minutes.

Run this from your laptop:
```bash
dig +short game.gridwars.run
```
Expect exactly the Fly IPv4.

Run the same command from a non-LAN network when possible:
```bash
dig +short game.gridwars.run
```
Expect the same Fly IPv4.
Wait up to 60 seconds before retrying.

Smoke-test the telnet port:
```bash
nc -zv game.gridwars.run 4000
```
Expect a connection succeeded message.
Treat **Connection refused** as an app reachability issue, not a DNS issue.

## Common Issues

If `dig` returns `104.x`, `172.x`, or another Cloudflare edge address, the record is still proxied.
Toggle proxy status off and save again.

If `dig` returns `NXDOMAIN`, the record was not saved or you edited the wrong zone.
Open **Websites** again and confirm you are inside the `gridwars.run` zone.

If external telnet hangs forever, check the Fly app and service health.
Run `fly status` and confirm the services from `fly.toml` are healthy.

If TTL stays on **Auto**, confirm the record is grey-cloud **DNS only** first.
Cloudflare only honors custom TTL on unproxied records.

## Future Work

Defer the **AAAA** record until v0.3.
When ready, get the IPv6 from `fly ips list`, add an **AAAA** record for `game`, and keep it **DNS only**.

Defer the `telnet.gridwars.run` CNAME alias until operators decide the second name is worth maintaining.
If you add it later, point it at `game.gridwars.run` and keep it **DNS only**.

Treat **DNSSEC** as an operator preference.
Enable it at the Cloudflare zone level if the domain owner wants it.
