# Hosting — Cloudflare Pages

> This document covers deployment of the gridwars.run **marketing landing page** to Cloudflare Pages. It is NOT a guide for hosting your own GridWars server — that is intentionally unsupported.

GridWars.run's landing site deploys automatically to [Cloudflare Pages](https://pages.cloudflare.com/) on every push to `main` that touches `landing/**`.

---

## How the deploy pipeline works

1. A push to `main` with changes under `landing/` or `.github/workflows/cf-pages-deploy.yml` triggers the `cf-pages-deploy` GitHub Actions workflow.
2. The workflow uses [`cloudflare/wrangler-action@v3`](https://github.com/cloudflare/wrangler-action) to run:
   ```
   wrangler pages deploy landing --project-name=gridwars-run --branch=main
   ```
3. Cloudflare Pages serves the contents of `landing/` (including `_headers` and `_redirects`) at the configured domain.

The workflow is at `.github/workflows/cf-pages-deploy.yml`.

---

## One-time Cloudflare setup

| Step | Status | Action |
|------|--------|--------|
| **1. Create Pages project** | **Done** | `wrangler pages project create gridwars-run --production-branch=main` already ran. The project is live at `https://gridwars-run.pages.dev/`. |
| **2. Create CF API token** | Pending | See below. |
| **3. Add token to GitHub Secrets** | Pending | See below. |
| **4. Add custom domain** | Pending | See below. |

### Step 2 — Create a Cloudflare API token

1. Go to [Cloudflare Dashboard → My Profile → API Tokens](https://dash.cloudflare.com/profile/api-tokens).
2. Click **Create Token**.
3. Use the **Custom token** option with these permissions:
   - **Account** → `Cloudflare Pages` → `Edit`
4. Click **Continue to summary** → **Create Token**.
5. Copy the token — it will not be shown again.

### Step 3 — Add the token to GitHub Secrets

1. Go to the repo → **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret**.
3. Name: `CLOUDFLARE_API_TOKEN`
4. Value: paste the token from Step 2.
5. Click **Add secret**.

The deploy workflow reads `${{ secrets.CLOUDFLARE_API_TOKEN }}` automatically.

### Step 4 — Add custom domain in CF dashboard

1. Go to [Cloudflare Dashboard → Pages → gridwars-run → Custom domains](https://dash.cloudflare.com/?to=/:account/pages/view/gridwars-run/domains).
2. Click **Set up a custom domain**.
3. Enter `gridwars.run` → follow the prompts. Since the domain is already on Cloudflare, DNS records are added automatically.
4. Repeat for `www.gridwars.run` if desired (the `landing/_redirects` file already redirects `www` → apex).

---

## Updating the landing page

Edit `landing/index.html` (or any file under `landing/`), commit, and push to `main`. The deploy workflow fires automatically within ~30 seconds. The new version is live at `https://gridwars.run` once the workflow completes (typically under 2 minutes).

```bash
# Example update flow
vim landing/index.html
git add landing/index.html
git commit -m "landing: update hero tagline"
git push
# GitHub Actions deploys to CF Pages automatically
```

---

## DNS

Both the apex and www should resolve to Cloudflare Pages.

| Record | Type | Value |
|--------|------|-------|
| `gridwars.run` | managed by CF Pages custom domain | set automatically in Step 4 |
| `www.gridwars.run` | managed by CF Pages custom domain | set automatically in Step 4 |

The `landing/_redirects` file ensures `www.gridwars.run/*` always redirects to `https://gridwars.run/` with a 301.

---

## Project URLs

| Environment | URL |
|-------------|-----|
| Production (CF Pages) | `https://gridwars-run.pages.dev/` |
| Production (custom domain, once Step 4 done) | `https://gridwars.run/` |
| GitHub repo | `https://github.com/jsgerman-oss/gridwars.run` |

---

## Gameplay-Loop Operations

This section covers day-to-day operational tasks for the Evennia game server. All shell snippets run via `evennia shell` (Django shell with the full game ORM loaded) unless noted otherwise.

---

### Queue monitoring

The duel queue is stored in `ServerConfig` under the key `gw_duel_queue`. To inspect its current state:

```python
from evennia.server.models import ServerConfig
from evennia.objects.models import ObjectDB

queue = list(ServerConfig.objects.conf("gw_duel_queue", default=list) or [])
print(f"Queue depth: {len(queue)}")
for cid in queue:
    try:
        char = ObjectDB.objects.get(id=cid)
        print(f"  #{cid} — {char.key}")
    except ObjectDB.DoesNotExist:
        print(f"  #{cid} — (object missing, stale entry)")
```

A stale entry (object missing) can accumulate if a character is deleted while queued. To remove it, call `clear_queue()` or manually rebuild the list without the bad ID:

```python
from world.queue_store import clear_queue
clear_queue()   # wipes the queue entirely — use with care during off-peak hours
```

**Note:** Queue state is lost on a backup restore because it lives in `ServerConfig` (Django ORM), not in a separate file. After a restore, verify the queue is empty and have waiting players re-queue. See [Backup/restore considerations](#backuprestore-considerations) below.

---

### Matchmaking script status

The `MatchmakingScript` is a persistent Evennia script that polls the queue every 5 seconds. It auto-starts via `at_server_startstop.at_server_start()` on every `evennia reload` or cold boot.

To verify it is running:

```python
from evennia.utils.search import search_script
scripts = search_script("matchmaking")
for s in scripts:
    print(f"key={s.key}  running={s.is_valid()}  interval={s.interval}s  next_repeat={s.time_until_next_repeat():.1f}s")
```

If the script is absent (empty result), restart it manually:

```python
from evennia.utils.create import create_script
from world.matchmaking import MatchmakingScript
create_script(MatchmakingScript)
```

The script is `persistent=True`, so a normal `evennia reload` is sufficient for it to survive restarts without manual intervention. If you see two `matchmaking` scripts after a reload anomaly, delete the duplicate:

```python
scripts = search_script("matchmaking")
# Keep the most recently created one; delete the rest.
for s in scripts[1:]:
    s.delete()
```

---

### Rating system

Player ratings are stored as the `rating` attribute on each `Character` object (default 1000, ELO K=32). For full formula details see [Rating and Leaderboard](PLAYER.md#rating-and-leaderboard).

**Inspect a player's current rating:**

```python
from evennia.utils.search import search_object
chars = search_object("PlayerName", typeclass="typeclasses.characters.Character")
char = chars[0]
print(f"{char.key}: rating={char.rating}")
```

**Manually adjust a rating:**

```python
char.rating = 1200   # set to any non-negative integer
```

**Reset to default (1000):**

```python
char.rating = 1000
```

**Export the leaderboard to CSV (stdout):**

```python
from evennia.objects.models import ObjectDB
import csv, sys

chars = ObjectDB.objects.filter(
    db_typeclass_path="typeclasses.characters.Character"
).order_by("-db_attributes__db_value")

# Fetch and sort in Python (AttributeProperty values are not SQL-sortable directly).
ranked = sorted(
    [(obj.db_key, getattr(obj, "rating", 1000)) for obj in chars],
    key=lambda x: x[1],
    reverse=True,
)

writer = csv.writer(sys.stdout)
writer.writerow(["rank", "name", "rating"])
for i, (name, rating) in enumerate(ranked, 1):
    writer.writerow([i, name, rating])
```

---

### Disc XP

Disc XP is stored on the `Disc` object (not directly on the character). Each character's equipped disc is tracked via `char.db.equipped_disc`.

**Inspect a player's disc level and XP:**

```python
from evennia.utils.search import search_object
chars = search_object("PlayerName", typeclass="typeclasses.characters.Character")
char = chars[0]
disc = char.db.equipped_disc
if disc:
    print(f"Disc: {disc.key}  level={disc.level}  xp={disc.xp}  damage_bonus={disc.damage_bonus}")
else:
    print("No disc equipped.")
```

**Grant XP to a disc manually (testing):**

```python
disc.gain_xp(100)   # triggers level-up check automatically
```

Thresholds: L2 = 100 XP, L3 = 300 XP, L4 = 700 XP, L5 = 1500 XP (totals, not increments). Level 5 is the cap; the method is safe to call past the cap.

---

### Backup/restore considerations

| State | Location | Survives restore? |
|-------|----------|-------------------|
| Player ratings | `Character.db.rating` (Evennia `Attribute` table) | Yes — stored in the main Django DB |
| Disc XP / level | `Disc.db.xp`, `Disc.db.level` | Yes — stored in the main Django DB |
| Duel queue | `ServerConfig["gw_duel_queue"]` | Yes — stored in the main Django DB |
| Active arenas | `DuelArena` objects in `ObjectDB` | Yes, but in an inconsistent in-flight state |

**Practical implications:**

- **Rating and disc state are durable.** A full DB backup and restore will preserve all player progress.
- **Active arenas after a restore** will exist as orphaned `DuelArena` rooms (tagged `duel-arena`/`ephemeral`). Players inside them will be stranded. Clean them up with:

```python
from evennia.utils.search import search_tag
arenas = search_tag("duel-arena", category="ephemeral")
for arena in arenas:
    print(f"Cleaning up: {arena.key}")
    arena.delete()   # participants will land in their `home` location
```

- **Queue entries** technically survive a restore but point to character IDs that existed at backup time. If characters were created or deleted since the backup, stale IDs may appear. Run the [queue inspection snippet](#queue-monitoring) after any restore and clear if needed.

---

### Debugging duel-end issues

The post-duel reward hook (`handle_duel_strike` in `world.duels_score`) fires when one player lands 3 strikes. It updates ELO ratings, awards XP, feeds disc XP, and calls `end_arena`. The module logs a structured line on every win:

```
[duel-end] <winner> (<old>→<new>) defeated <loser> (<old>→<new>)
```

**Verify the hook fired** by grepping the Evennia log:

```bash
grep "\[duel-end\]" server/logs/server.log | tail -20
```

**If an arena did not close** (both players are stuck in the room), call `end_arena` manually:

```python
from evennia.utils.search import search_tag
from world.duels import end_arena

arenas = search_tag("duel-arena", category="ephemeral")
for arena in arenas:
    print(f"Force-closing: {arena.key}  participants={arena.participants}")
    end_arena(arena)   # moves participants to their origin rooms, then deletes arena
```

**If ratings were not updated** (hook fired but rating unchanged), check whether the character's `rating` attribute exists:

```python
char = ...  # fetch as above
print(char.attributes.has("rating"), char.rating)
```

If missing, the attribute was never seeded. Set it to 1000 and the next duel will update from there.
