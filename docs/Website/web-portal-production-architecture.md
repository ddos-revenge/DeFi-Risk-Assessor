# Web portal and script API (production)

Hodler Suite production splits the **customer-facing site** from the **legacy script API** that serves chain cache and internal tooling. They are separate processes and deploy units.

## Components

| Piece | Role | Typical unit |
| --- | --- | --- |
| **Web portal** | Flask app: accounts, billing, Live Assessment orchestration, support APIs | `hodler-web-portal.service` (Gunicorn), app root e.g. `/opt/hodler-suite/web_portal/` |
| **Script API** | `webhook_server:app` — cache health, token refresh hooks, deep health by chain | `hodler-script-api.service` (Gunicorn), working directory pointing at `scripts/v2.0` |

The portal **does not** import or run `webhook_server` inside the same worker. It talks to risk workers and optional HTTP helpers via configured base URLs and shared secrets, as documented in `deploy/risk/RISK_WORKER_RUNTIME.md` and related deploy packs.

## Supported deploy path

Only the repository **deploy scripts** (rsync to the server layout + `systemctl restart …`) are supported for production updates—manual copies of trees or ad hoc `flask run` on the VPS are out of scope for support.

- Web portal: `scripts/v2.0/web_portal/deploy/deploy_web_portal_safe.sh`
- Script API: `scripts/v2.0/web_portal/deploy/deploy_script_api_safe.sh` (see `deploy/status/SCRIPT_API_RUNTIME.md`)

The web portal deploy script **defaults to merge-only promote** (`WEB_PORTAL_PROMOTE_DELETE` unset or `0`): new/changed files from the staging rsync are copied into the live app dir **without** `--delete`, so stray server-only files are not pruned accidentally. Set **`WEB_PORTAL_PROMOTE_DELETE=1`** only when you deliberately want rsync to remove destination files that are absent from the stage (still excludes `venv/`, `.venv/`, `web_portal.env`, `data/`, databases, logs, etc.). Never add a blanket `--exclude '.env.*'` — it blocks **`.env.example`** and breaks recovery.

### Recover a destroyed portal venv (missing `venv/bin/gunicorn`)

If `ls /opt/hodler-suite/web_portal/venv/bin/gunicorn` fails, the interpreter environment must be recreated **on the VPS** (not on your laptop).

1. Copy the pinned dependency list to the server from your repo checkout (**run `git pull` first** so the file exists):

   `docs/Website/web-portal-runtime-requirements.txt` → `/opt/hodler-suite/web_portal/requirements-production.txt`

   ```bash
   cd /path/to/venv/repo
   scp docs/Website/web-portal-runtime-requirements.txt linuxuser@YOUR_HOST:/opt/hodler-suite/web_portal/requirements-production.txt
   ```

   **Env template:** the app’s `.env.example` may be missing on laptops where `scripts/v2.8/web_portal/` is not checked out. Use the tracked copy and install it on the server as `.env.example`, then derive `web_portal.env`:

   ```bash
   scp docs/Website/web_portal.env.example linuxuser@YOUR_HOST:/opt/hodler-suite/web_portal/.env.example
   ssh linuxuser@YOUR_HOST 'cd /opt/hodler-suite/web_portal && cp .env.example web_portal.env && chmod 600 web_portal.env'
   ```

   Edit `web_portal.env` on the server for real secrets before starting the unit.

2. On the server:

```bash
sudo systemctl stop hodler-web-portal.service || true
cd /opt/hodler-suite/web_portal
# Ubuntu: ensure venv support and headers for cryptography wheels
sudo apt-get update && sudo apt-get install -y python3-venv python3-dev build-essential libssl-dev libffi-dev
python3 -m venv venv
./venv/bin/pip install -U pip wheel setuptools
./venv/bin/pip install -r requirements-production.txt
./venv/bin/python -c "import flask, gunicorn; print('imports OK')"
sudo systemctl start hodler-web-portal.service
systemctl is-active hodler-web-portal.service
```

3. If systemd reports **`Failed to load environment files`**, open the unit and fix every **`EnvironmentFile=`** path:

```bash
systemctl cat hodler-web-portal.service
```

Typical layouts:

- **Under the app tree:** `EnvironmentFile=/opt/hodler-suite/web_portal/web_portal.env` — create/restore that file from **`.env.example`** in the app root (`cp .env.example web_portal.env` then edit; **`chmod 600 web_portal.env`**). The deploy script excludes `web_portal.env` from rsync so a normal deploy does not delete it. It **must not** exclude `.env.example` (older scripts used `--exclude '.env.*'`, which skipped `.env.example` on the server—re-run deploy from a fixed script or `scp` `.env.example` once).
- **Under `/etc/hodler-suite/`:** some installs use `/etc/hodler-suite/web_portal.env` instead — use `sudo ls -la /etc/hodler-suite/` and restore the file there if that is what the unit references.

4. **`venv` vs `.venv`:** if **`ExecStart=`** references **`.venv/bin/gunicorn`** but you only have **`venv/`**, either recreate the venv as `.venv` or point the interpreter layout at the unit (e.g. `cd /opt/hodler-suite/web_portal && ln -sfn venv .venv` as the service user so `.venv/bin/gunicorn` resolves).

5. **Secrets in systemd drop-ins:** never store API tokens in `*.conf` under `/etc/systemd/system/*.d/` (they appear in logs and `systemctl cat`). Revoke any exposed token, move values into `web_portal.env` (or another root-only file), `sudo systemctl daemon-reload`, then restart.

## Hosted documentation and TLS

Public docs should live on a **stable hostname** (e.g. `docs.example.com`) with TLS terminated at the edge (Nginx/Caddy/Cloudflare). DNS and certificate lifecycle are operator responsibilities; point the hostname at the docs static host or MkDocs output as you standardize.

## Optional: MkDocs / Zensical

A **non-production spike** to evaluate Zensical (or MkDocs 2.x) can live on a branch; keep the main docs pipeline unchanged until you cut over deliberately.
