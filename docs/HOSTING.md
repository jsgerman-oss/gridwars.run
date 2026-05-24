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
4. Under **Account Resources**, select **Audit Identity** (account ID `4bf8ccaf39f18a8a46b21a317e2d3a1b`).
5. Click **Continue to summary** → **Create Token**.
6. Copy the token — it will not be shown again.

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
3. Enter `gridwars.run` → follow the prompts. Since the domain is already on Cloudflare (Audit Identity account), DNS records are added automatically.
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
| Cloudflare account | Audit Identity — ID `4bf8ccaf39f18a8a46b21a317e2d3a1b` |
| GitHub repo | `https://github.com/jsgerman-oss/gridwars.run` |
