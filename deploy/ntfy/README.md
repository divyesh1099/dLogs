# ntfy on Railway

Standalone deploy of the `ntfy` alerts server, split out of the local dLogs
stack so it stays reachable when this machine is off.

## Railway setup

1. New Railway service -> Deploy from this repo.
2. Set the service's **Root Directory** to `deploy/ntfy` (Settings > Source).
   Railway will build `Dockerfile` and detect the exposed port automatically.
3. Set these service variables (Settings > Variables), values from the old
   `docker-compose.yml` ntfy block:
   - `NTFY_BASE_URL=https://ntfy.divyeshvishwakarma.com`
   - `NTFY_SMTP_SENDER_ADDR=smtp.gmail.com:587`
   - `NTFY_SMTP_SENDER_USER=divyesh1099@gmail.com`
   - `NTFY_SMTP_SENDER_PASS=<the Gmail app password from the old GMAIL_APP_PASSWORD secret>`
   - `NTFY_SMTP_SENDER_FROM=divyesh1099@gmail.com`
4. Deploy, then grab the generated `*.up.railway.app` domain from
   Settings > Networking.

## DNS cutover (Cloudflare)

`ntfy.divyeshvishwakarma.com` is currently routed through a Cloudflare
Tunnel on the local PC — that's the piece going away.

1. In Cloudflare DNS, replace the tunnel-managed `ntfy` record with a
   `CNAME` pointing at the Railway domain from step 4 above.
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
4. Verify before deleting anything on the PC side: `curl -I https://ntfy.divyeshvishwakarma.com/v1/health`
   should return 200 from the new Railway-backed origin.

## Consumers using this exact hostname

Nothing needs to change in these once the domain still resolves the same:
- `dAgent` worker (`docker/automation-stack`) — publishes locally to
  `127.0.0.1:8080` in the old setup; check whether it should now point at
  the public URL or a Railway-internal address if dAgent itself ever
  moves off this PC.
- `llmFinetuner/run_feasibility.sh` — posts to
  `https://ntfy.divyeshvishwakarma.com/ml-training-alerts`.
