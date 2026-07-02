# ntfy on Railway

Standalone deploy of the `ntfy` alerts server, split out of the local dLogs
stack so it stays reachable when this machine is off.

Live at `https://ntfy.divyeshvishwakarma.com` (custom domain) and
`https://dlogs-production-7b2e.up.railway.app` (Railway's generated
domain). Railway project `ntfy`, service `dLogs` — the service kept its
auto-generated name from the repo; only the project was renamed.

## No email notifications — outbound SMTP is blocked on Railway

Confirmed with two independent providers: Gmail (`smtp.gmail.com:587` and
`:465`) and Resend (`smtp.resend.com:587`) all fail identically —
`dial tcp <ip>:<port>: connect: connection timed out`, taking 2-5 minutes
to time out. This is Railway's network blocking outbound SMTP categorically
(anti-abuse policy), not a credentials or provider problem. Don't re-add
`NTFY_SMTP_SENDER_*` variables expecting this to work — it won't, on any
port, to any destination. The only way to get email notifications out of
this deployment would be a separate service that subscribes to ntfy's
message stream and calls an HTTP-based email API (e.g. Resend's
`api.resend.com`, plain HTTPS) directly — real new code, not a config
change.

## Railway setup (one-time)

1. New Railway project -> **Deploy from GitHub repo** -> `divyesh1099/dLogs`.
2. **Before the first deploy finishes**, go to the new service's
   **Settings -> Source** and set **Root Directory** to `deploy/ntfy`. Doing
   this after an initial root-level deploy leaves stale config behind —
   set it first.
3. Settings -> Variables, add just:
   - `NTFY_BASE_URL=https://ntfy.divyeshvishwakarma.com`
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
explicitly, which is what Railway's Dockerfile-deploy healthcheck expects
(confirmed Railway does assign a `PORT` env var per-deployment — one
instance got `:80`, another got `:8080`, both worked correctly with this
fix). If you ever rebuild this from scratch and hit the same "healthy
container, failing healthcheck" symptom, confirm with `railway logs
--deployment --latest` (plain `railway logs` shows build/healthcheck-
attempt logs, not the container's own stdout) before assuming it's a
config problem.

## Continuous deploy

`.github/workflows/deploy-ntfy.yml` runs `railway up --service dLogs` from
the repo root (not from inside `deploy/ntfy` — the service's Root
Directory setting already scopes the build; running `railway up` from
inside `deploy/ntfy` too double-applies that and breaks the build) on any
push to `main` that touches `deploy/ntfy/**`, using `railway.json` in this
directory for the build/deploy config. Trigger it manually too via
Actions > Deploy ntfy to Railway > Run workflow.

## DNS cutover (Cloudflare) — already done

`ntfy.divyeshvishwakarma.com` used to route through a Cloudflare Tunnel on
the local PC. Steps taken, for reference if this ever needs to be redone:

1. Removed the `ntfy.divyeshvishwakarma.com` Public Hostname route from
   the Cloudflare Tunnel config (Zero Trust > Networks > Tunnels) — this
   also removed the CNAME record it had auto-created. Left the rest of the
   tunnel (e.g. `dagent.divyeshvishwakarma.com`) untouched.
2. Registered the domain as a **Custom Domain** in Railway
   (`railway domain ntfy.divyeshvishwakarma.com --service dLogs`, or
   Settings -> Networking -> Custom Domain in the dashboard). A plain
   CNAME to the generated `*.up.railway.app` domain is **not** enough —
   Railway's edge routes by hostname and returns `404 Application not
   found` for any hostname it hasn't been told to expect, even if DNS
   resolves and TCP/TLS reaches Railway fine.
3. Railway returned a domain-specific CNAME target (different from the
   generated service domain!) plus a TXT verification record:
   - `CNAME ntfy -> xjegw624.up.railway.app`
   - `TXT _railway-verify.ntfy -> railway-verify=<value>`
   Added both in Cloudflare DNS. CNAME proxy status: Proxied (orange
   cloud) — works fine since Railway serves a valid public cert.
4. Ownership verification + certificate issuance took about 2 minutes
   after the TXT record went live (check with
   `railway domain status <domain-id>`).
5. Confirmed SSL/TLS mode is Full or Full (strict) in Cloudflare, not
   Flexible — Railway's origin only speaks HTTPS.

## Consumers using this exact hostname

Nothing needs to change in these once the domain still resolves the same:
- `dAgent` worker (`docker/automation-stack`) — publishes locally to
  `127.0.0.1:8080` in the old setup; check whether it should now point at
  the public URL or a Railway-internal address if dAgent itself ever
  moves off this PC.
- `llmFinetuner/run_feasibility.sh` — posts to
  `https://ntfy.divyeshvishwakarma.com/ml-training-alerts`.
