FROM binwiederhier/ntfy:latest
EXPOSE 80
ENTRYPOINT ["/bin/sh", "-c"]
# Starts the server first (an auth-file only gets created once ntfy has run
# at least once — `ntfy user add`/`ntfy access` error out otherwise), waits
# for the auth db to appear, then bootstraps a per-topic-locked user if
# NTFY_LOGS_USER/NTFY_LOGS_PASSWORD are set. Idempotent and safe to run on
# every boot: --ignore-exists no-ops the add, change-pass re-syncs the
# password from the env var every time (so it self-heals even without a
# persistent volume, since a fresh redeploy just recreates the same state),
# and the two `ntfy access` calls are last-write-wins, not additive.
# auth-default-access stays read-write, so every topic without an explicit
# rule (i.e. everything except what's bootstrapped here) is unaffected —
# other consumers of this shared ntfy instance keep working unmodified.
CMD ["set -e; \
AUTH_FILE=/data/auth.db; \
mkdir -p /data; \
ntfy serve --listen-http \":${PORT:-80}\" --auth-file \"$AUTH_FILE\" --auth-default-access read-write & \
SERVER_PID=$!; \
for i in $(seq 1 30); do [ -f \"$AUTH_FILE\" ] && break; sleep 0.5; done; \
if [ -n \"$NTFY_LOGS_USER\" ] && [ -n \"$NTFY_LOGS_PASSWORD\" ]; then \
  NTFY_PASSWORD=\"$NTFY_LOGS_PASSWORD\" ntfy user --auth-file \"$AUTH_FILE\" add --ignore-exists \"$NTFY_LOGS_USER\"; \
  NTFY_PASSWORD=\"$NTFY_LOGS_PASSWORD\" ntfy user --auth-file \"$AUTH_FILE\" change-pass \"$NTFY_LOGS_USER\"; \
  ntfy access --auth-file \"$AUTH_FILE\" \"$NTFY_LOGS_USER\" entrust-timer-logs rw; \
  ntfy access --auth-file \"$AUTH_FILE\" everyone entrust-timer-logs deny; \
fi; \
wait $SERVER_PID"]
