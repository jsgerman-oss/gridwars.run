# Evennia Deploy Runbook

Use this runbook when you deploy `game.gridwars.run` for the first time.
Use it for redeploys, rollback, troubleshooting, and teardown.
Run the commands exactly as written unless the step tells you to substitute a value.

## Prerequisites

1. Install `flyctl`.
2. Confirm you can sign in to the Fly.io account that will own `gridwars-run`.
3. Confirm the Fly.io account has a payment method on file.
4. Confirm you can access the Cloudflare account with the `gridwars.run` zone.
5. Authenticate GitHub CLI with `gh auth login`.
6. Check out the repo commit you intend to deploy.
7. Confirm `gridwars/fly.toml` and the deployment Dockerfile exist.
8. Keep a non-LAN network available for smoke testing; a mobile hotspot is enough.

## First-Time Deploy

Complete this section once.
Budget about 30 minutes.

1. Run `fly auth login`.
   Success: the browser sign-in finishes and the CLI shows the expected Fly.io email.
   Failure: run `fly auth logout`, sign in again, and confirm the correct account.

2. Run `cd gridwars/`.
   Success: `pwd` ends with `/gridwars.run/gridwars`.
   Failure: stop and change into the game directory; Fly config resolves from this cwd.

3. Run `fly launch --no-deploy --name gridwars-run --region iad --copy-config`.
   Success: Fly creates or attaches the `gridwars-run` app using the existing config.
   Failure: confirm `gridwars/fly.toml` exists and that you are not running from repo root.

4. Decline the Postgres prompt.
   Success: Fly continues without creating a database add-on.
   Failure: if you accidentally created Postgres, stop and decide whether to destroy it.

5. Decline the Upstash Redis prompt.
   Success: Fly continues without creating a Redis add-on.
   Failure: if you accidentally created Redis, stop and decide whether to destroy it.

6. Run `fly apps list`.
   Success: `gridwars-run` appears in the app list.
   Failure: repeat the launch step and check the selected Fly organization.

7. Run `fly volumes create gridwars_data --region iad --size 1`.
   Success: Fly creates a 1 GB volume in `iad`.
   Failure: if Fly reports an existing volume, inspect it before creating another.

8. Run `fly volumes list`.
   Success: one `gridwars_data` volume appears in `iad`.
   Failure: recreate the volume in the app region; Fly volumes are region-pinned.

9. Run `fly secrets set EVENNIA_SECRET_KEY=$(openssl rand -base64 64)`.
   Success: Fly accepts the secret and may restart the app.
   Failure: generate an equivalent 64-byte random secret and rerun the command.

10. Run `fly secrets list`.
    Success: `EVENNIA_SECRET_KEY` appears, and its value is not printed.
    Failure: rerun the secret-setting command; never paste the value into chat or docs.

11. Run `fly deploy`.
    Success: the first Docker build completes and a machine starts in about 3 to 5 minutes.
    Failure: fix the build error, confirm cwd is `gridwars/`, and rerun `fly deploy`.

12. Run `fly logs`.
    Success: the Evennia banner appears and the process stays up for at least 30 seconds.
    Failure: leave logs open and jump to "Troubleshooting".

13. Run `fly ips list`.
    Success: Fly prints the app's public addresses.
    Failure: allocate an IPv4 address before configuring Cloudflare.

14. Copy the IPv4 anycast address.
    Success: you have the address for the Cloudflare A record.
    Failure: if only IPv6 exists, document it but allocate IPv4 for this runbook path.

15. Open Cloudflare, select the `gridwars.run` zone, and open **DNS**.
    Success: you can add or edit records in the zone.
    Failure: switch accounts or request zone access before continuing.

16. Add or update the `game` DNS record.
    Use type `A`, name `game`, IPv4 from Fly, TTL `5 min`, proxy status **DNS only**.
    Success: the record is saved with a grey cloud.
    Failure: remove duplicates or edit the existing `game` record.

17. Run `dig +short game.gridwars.run`.
    Success: the Fly IPv4 address appears.
    Failure: wait for TTL; if a Cloudflare proxy IP appears, disable proxying.

18. From a non-LAN network, run `telnet game.gridwars.run 4000`.
    Success: the Evennia login banner appears.
    Failure: retry from a mobile hotspot, then inspect Fly services and logs.

19. In telnet, type `create newplayer password`.
    Success: Evennia creates the smoke-test account.
    Failure: use another disposable name or capture the account-creation traceback.

20. Type `look`.
    Success: the world responds with room or sector output.
    Failure: inspect `fly logs` for the Evennia traceback.

21. Open `http://game.gridwars.run:4001/`.
    Success: the Evennia webclient UI loads.
    Failure: force `http://`, check `fly services list`, and redeploy once if needed.

22. Record the deploy result.
    Include release, app name, region, volume, DNS record, telnet result, and webclient result.
    Do not record secrets.

## Ongoing Deploys

Use this section for every production deploy after the first setup.

1. Run `git pull --rebase`.
   Success: the checkout contains the commit intended for production.
   Failure: resolve conflicts before deploying.

2. Run `cd gridwars/`.
   Success: `pwd` ends with `/gridwars.run/gridwars`.
   Failure: stop and correct cwd before any Fly command.

3. Run `fly deploy`.
   Success: Fly creates a new release and restarts the machine.
   Failure: fix the build or deploy error and rerun.

4. Run `fly logs`.
   Success: Evennia starts and stays up for at least 30 seconds.
   Failure: prepare rollback if the app crash loops.

5. Run `telnet game.gridwars.run 4000`.
   Success: the Evennia login banner appears.
   Failure: inspect `fly services list` before changing DNS.

6. Open `http://game.gridwars.run:4001/`.
   Success: the webclient loads.
   Failure: check the `:4001` service block and redeploy once.

## Rollback

Use rollback when the current release breaks boot, login, persistence, or core commands.

1. Run `fly releases list`.
   Success: you can identify the previous known-good deployment SHA.
   Failure: inspect deploy notes and do not guess blindly.

2. Run `fly deploy --image registry.fly.io/gridwars-run:deployment-<sha>`.
   Replace `<sha>` with the previous good deployment SHA.
   Success: Fly creates a new release from the older image.
   Failure: verify the SHA and image name from `fly releases list`.

3. Run `fly logs`.
   Success: Evennia starts cleanly and stays up.
   Failure: determine whether persistent data changed during the bad release.

4. Restore data if the bad release migrated the database.
   Success: restore from the most recent backup using the backup procedure.
   Failure: do not hand-edit live SQLite unless there is no backup path.

5. Smoke-test rollback.
   Run telnet on `game.gridwars.run 4000`, open the webclient, log in, and run `look`.
   Success: both telnet and webclient work before you declare rollback complete.

## Troubleshooting

- Telnet hangs immediately on connect.
  Try from a mobile hotspot; LAN firewall or routing rules are the usual cause.

- Telnet resolves but refuses the connection.
  Run `fly services list`; confirm TCP `4000` is exposed and the machine is running.

- `fly deploy` reports an error connecting to the remote builder.
  Run `fly wireguard reset`, then retry `fly deploy`.

- Evennia logs `Settings not configured`.
  Deploy from `gridwars/`; the settings module and Fly config assume that cwd.

- Fly cannot find `fly.toml`.
  Confirm you are in `gridwars/` and that the deploy config exists there.

- The volume mount fails on boot.
  Run `fly volumes list`; confirm `gridwars_data` is in the machine's region.

- The app boots with an empty or reset world.
  Confirm the volume mounted before Evennia started and check database path logs.

- The webclient on `:4001` is unreachable.
  Run `fly services list`; redeploy once if the second service did not bind.

- Cloudflare DNS resolves to unexpected addresses.
  Confirm the `game` A record is DNS only; orange-cloud proxying breaks telnet.

- `dig +short game.gridwars.run` returns no answer.
  Wait for propagation, then confirm the record exists in the correct Cloudflare zone.

- Browser HTTPS fails for the webclient.
  Use `http://game.gridwars.run:4001/`; the webclient port is plain HTTP.

- Login works but `look` errors.
  Capture the traceback from `fly logs`; treat this as an application regression.

- Deploy succeeds but old code still responds.
  Confirm the release number changed and that you deployed the intended checkout.

## Teardown

Use teardown only when the Fly deployment should be destroyed.
1. Run `fly apps destroy gridwars-run`.
   Success: Fly prompts twice and destroys the intended app.
   Failure: stop if the app name is not exactly `gridwars-run`.

2. Remove the Cloudflare DNS record.
   Delete the `game.gridwars.run` A record from the `gridwars.run` zone.
   Success: `dig +short game.gridwars.run` eventually returns no Fly IPv4 address.
   Failure: check for duplicate records or the wrong Cloudflare zone.

3. Record the teardown.
   Include who destroyed the app, when, why, and whether a backup was taken.
   Do not leave stale public connection instructions in release notes or incidents.
