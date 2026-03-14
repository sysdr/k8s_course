# Log Platform

## One command to fix "localhost refused to connect"

From the **k8s-log-platform** directory run:

```bash
./scripts/run-all.sh
```

Then open in your browser: **http://localhost:3000**

If you see "This site can't be reached" or "connection refused":

1. **Try http://127.0.0.1:3000** instead of localhost (helps on WSL/Windows).
2. Wait 30 seconds after `run-all.sh` and refresh the page.
3. Check that containers are running:
   ```bash
   docker compose -f local/docker-compose.yaml ps
   ```
   You should see `log-api` and `log-frontend` with status "Up" and ports 8000 and 3000.

---

## What runs where

| Service   | URL                    | Port |
|----------|------------------------|------|
| Frontend | http://localhost:3000  | 3000 |
| API      | http://localhost:8000  | 8000 |

Both run in Docker. The dashboard calls the API via **same origin** (`/api`), so "Send demo logs" works from the UI.

---

## Manual steps (if run-all.sh is not used)

1. Start the stack:
   ```bash
   docker compose -f local/docker-compose.yaml up -d --build
   ```
2. Wait for the API (about 15–20 seconds), then open **http://localhost:3000** (or http://127.0.0.1:3000).

---

## Send demo data / "Send demo logs" not updating

1. **From the UI:** Click **"Send demo logs"** on the dashboard. A snackbar will show success or an error (e.g. if the API is unreachable).
2. **If metrics still stay at 0:** Rebuild and restart the frontend so the `/api` proxy and latest UI are in use:
   ```bash
   docker compose -f local/docker-compose.yaml build --no-cache log-frontend
   docker compose -f local/docker-compose.yaml up -d --force-recreate log-frontend
   ```
   Then hard-refresh the page (Ctrl+Shift+R) and click "Send demo logs" again.
3. **From the command line:** `./scripts/demo.sh` then in the dashboard choose "All Services" or "demo-script".

---

## Stop everything

```bash
docker compose -f local/docker-compose.yaml down
```
