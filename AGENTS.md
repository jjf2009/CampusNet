# Agent Instructions

## Project

- CampusNet is a localhost prototype: FreeRADIUS events → FastAPI/SQLite → Next.js.
- Treat `AGENT.md` as the complete product specification.
- Never use real credentials or expose passwords, RADIUS secrets, keys, or debug output.

## Commands

```bash
cd backend && python -m pytest
cd frontend && npm run build
```

Run the backend with `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` and the frontend with `npm run dev`.

## System changes

- Do not modify `/etc/raddb`, permissions, SELinux policy, or system services without explicit approval.
- Inspect and back up FreeRADIUS configuration before proposing changes; provide rollback steps.
- Keep APIs and dashboard bound to localhost by default.

## Quality

- Use real persisted event data; label fixtures and simulations clearly.
- Test malformed records, duplicates, restart/log rotation behavior, API filters, and empty/error UI states.
- Report what is genuinely verified and what remains unimplemented.

## Commit Attribution

AI commits must include a `Co-Authored-By` trailer identifying the agent model.

