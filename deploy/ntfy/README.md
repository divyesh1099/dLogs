# ntfy on Railway

Standalone deploy of the `ntfy` alerts server, split out of the local dLogs
stack so it stays reachable when this machine is off.

Live at: `https://dlogs-production-7b2e.up.railway.app` (Railway project
`ntfy`, service `dLogs` — the service kept its auto-generated name from the
repo; only the project was renamed). `ntfy.divyeshvishwakarma.com` should be
CNAME'd here — see below.

## Railway setup (one-time)

1. New Railway project -> **Deploy from GitHub repo** -> `divyesh1099/dLogs`.
2. **Before the first deploy finishes**, go to the new service's
   **Settings -> Source** and set **Root Directory** to `deploy/ntfy`. Doing
   this after an initial root-level deploy leaves stale config behind —
   set it first.
3. Settings -> Variables, add:
   - `NTFY_BASE_URL=https://ntfy.divyeshvishwakarma.com`
   - `NTFY_SMTP_SENDER_ADDR=smtp.gmail.com:587`
   - `NTFY_SMTP_SENDER_USER=divyesh1099@gmail.com`
   - `NTFY_SMTP_SENDER_PASS=<the Gmail app password from the old GMAIL_APP_PASSWORD secret>`
   - `NTFY_SMTP_SENDER_FROM=divyesh1099@gmail.com`
4. Deploy, then Settings -> Networking -> **Generate Domain** for the
   `*.up.railway.app` URL.
5. Create a **Project Token** (Project Settings -> Tokens, scoped to this
   project + environment) and add it to the GitHub repo as the
   `RAILWAY_TOKEN` secret (Settings -> Secrets and variables -> Actions).

### Gotcha: healthcheck fails even though the container is running

The `binwiederhier/ntfy` image binds `:80` by default, and `EXPOSE 80` in
the Dockerfile alone was **not** enough for Railway's healthcheck/routing
to find it — the container logged `Listening on :80` and served stats
fine, but `/v1/health` kept timing out from Railway's side. The fix baked
into `Dockerfile` here overrides the entrypoint to bind `${PORT:-80}`
explicitly, which is what Railway's Dockerfile-deploy healthcheck expects.
If you ever rebuild this from scratch and hit the same "healthy container,
failing healthcheck" symptom, confirm with `railway logs --deployment
--latest` (plain `railway logs` shows build/healthcheck-attempt logs, not
the container's own stdout) before assuming it's a config problem.

## Continuous deploy

`.github/workflows/deploy-ntfy.yml` runs `railway up --service dLogs` from
the repo root (not from inside `deploy/ntfy` — the service's Root
Directory setting already scopes the build; running `railway up` from
inside `deploy/ntfy` too double-applies that and breaks the build) on any
push to `main` that touches `deploy/ntfy/**`, using `railway.json` in this
directory for the build/deploy config. Trigger it manually too via
Actions > Deploy ntfy to Railway > Run workflow.

## DNS cutover (Cloudflare)

`ntfy.divyeshvishwakarma.com` is currently routed through a Cloudflare
Tunnel on the local PC — that's the piece going away.

1. In Cloudflare DNS, replace the tunnel-managed `ntfy` record with a
   `CNAME` pointing at `dlogs-production-7b2e.up.railway.app`.
2. If the zone has a Cloudflare Tunnel with a named ingress rule for
   `ntfy.divyeshvishwakarma.com` (Zero Trust > Networks > Tunnels), delete
   just that hostname route — leave the rest of the tunnel (e.g.
   `dagent.divyeshvishwakarma.com`) untouched.
3. Railway serves HTTPS on its own domain already; if the CNAME is
   proxied (orange cloud) Cloudflare terminates TLS at the edge and
   forwards to Railway over HTTPS — that's fine. If you'd rather Railway
   terminate TLS directly, add the hostname as a custom domain in Railway
   (Settings > Networking > Custom Domain) and set the CNAME to DNS-only
   (grey cloud).
4. Verify before deleting anything on the PC side:
   `curl -I https://ntfy.divyeshvishwakarma.com/v1/health` should return
   200 from the new Railway-backed origin.

## Consumers using this exact hostname

Nothing needs to change in these once the domain still resolves the same:
- `dAgent` worker (`docker/automation-stack`) — publishes locally to
  `127.0.0.1:8080` in the old setup; check whether it should now point at
  the public URL or a Railway-internal address if dAgent itself ever
  moves off this PC.
- `llmFinetuner/run_feasibility.sh` — posts to
  `https://ntfy.divyeshvishwakarma.com/ml-training-alerts`.
