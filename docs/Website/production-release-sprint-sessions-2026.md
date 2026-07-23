# Production Release — Sprint Sessions (2026)

Last updated: 2026-04-19

**Canonical backlog:** **[hodler-suite-unified-sprint-and-roadmap-2026-05.md](./hodler-suite-unified-sprint-and-roadmap-2026-05.md)** merges this file with the web-integration seasons and security plan, deduplicates completed work, and tracks optional hardenings (updated 2026-05-04).

This document complements [`defi-risk-web-integration-sprint-seasons-2026.md`](./defi-risk-web-integration-sprint-seasons-2026.md). It focuses on **official production release readiness**: efficiency, reliability, **confidentiality**, **authenticity / trustworthiness of scores (affidability)**, service hardening, and **security as the non-negotiable priority**—while keeping **migration paths open** when the platform moves beyond a single Vultr instance and the current Flask + vanilla JS stack.

---

## Guiding principles

1. **Security first** — Every new feature ships with server-side enforcement, least privilege, secret hygiene, and abuse controls. No feature ships “UI-only.”
2. **Confidentiality & integrity of scores** — Outputs, prompts to automated systems, and customer data stay segmented; tamper-evident and access-logged where feasible.
3. **Authenticity & trustworthiness of published scores (“affidability”)** — What we show users must be explainable, tied to defined inputs and data freshness, and honest about limits (plan tier, stale or fallback data, suppressed signals). No cosmetic certainty when confidence or coverage is partial.
4. **Reliability before raw speed** — Measured SLOs, backoff, stale-data policy, and observable failures beat silent wrong answers.
5. **Efficiency at the current footprint** — Profile hot paths, cache smartly, reduce redundant provider calls; avoid premature microservices while **designing contracts** that survive scale-out later.
6. **Future scale without rewrite traps** — Prefer stateless app instances behind a load balancer, explicit job queues, externalized secrets, versioned APIs, and migration-friendly SQLite → managed DB path where growth demands it—**without** abandoning security reviews per change.

---

## Cross-cutting security backlog (ongoing)

Treat these as **parallel workstreams** that every season must not regress.

| Area | Objective |
| --- | --- |
| **Web & API surface** | CSRF, session fixation resistance, rate limits, strict Content Security Policy evolution, dependency and SAST in CI. |
| **Auth & sessions** | Step-up 2FA for sensitive actions, short-lived tokens where applicable, secure cookie flags, session invalidation on privilege change. |
| **Bug / AI automation pipeline** | Never execute user-controlled strings as shell or code; sanitize and size-limit Slack/GitHub bodies; ClamAV on attachments; no prompt injection into privileged tools—**structured, validated inputs only**. |
| **Payments (NOWPayments)** | Webhook HMAC verification, idempotency, amount/plan reconciliation, admin visibility without leaking PII in logs. |
| **File uploads & tickets** | Type/size caps, ClamAV, isolated storage, no inline execution of user content in agents. |
| **Secrets** | `/etc/…` or secret manager pattern; no secrets in repo; rotation playbooks for webhooks and API keys. |
| **Operational access** | SSH hardening, sudo scope, separate deploy vs DB backup roles; audit who can touch production env files. |

### Side-task (2026-04-24): Browser integrity / adblock gate

- Optional post-Turnstile gate (`ADBLOCK_GATE_ENABLED`) checks same-origin browser behavior for common content blockers that can break security, checkout, and assessment scripts.
- User-facing copy must stay non-accusatory: “a browser extension or privacy setting may be blocking required scripts.”
- Data minimization: session boolean + timestamp only; do not store extension names, filter lists, or detailed browser fingerprints.

---

## Scalability & migration readiness (non-breaking)

Do **not** mandate a framework swap in these sessions. Do **mandate** patterns that make a later move easier:

- **12-factor style config** — All behavior toggles and endpoints from environment; no hard-coded hosts.
- **Job contracts** — Risk jobs: stable JSON schema, idempotency keys, explicit timeouts—ready for a queue worker fleet later.
- **HTTP APIs** — Versioned routes (`/api/v1/...`); forward-compatible error shapes.
- **Data stores** — Document which SQLite DBs are candidates for Postgres (or equivalent) under connection pooling; avoid implicit “single-machine” assumptions in new code.
- **Static assets** — Cache-friendly URLs; later CDN is a config change, not a rewrite.
- **Frontend** — Keep vanilla JS modular; new UI components should be **progressive enhancement**, not a parallel SPA, unless explicitly approved—reduces attack surface and migration risk.

---

## Session list (ordered for release)

Below, **Session** = a planned sprint-sized chunk. Dependencies are noted inline.

### Session P0 — Release gate & threat model

- Formal **threat model** update: web, Script API, risk worker, Slack/GitHub/Cursor automation, payments, email inbound.
- **Prod evidence**: run security verification + deploy-pack reports; document gaps.
- **Incident response**: confirm on-call paths, log retention, and Slack alerting coverage.

### Session P1 — Plan enforcement & quotas (server-side)

- **Restrict usage of each service by plan** — Risk jobs, Live Assessment, API Center actions, token editor limits: **authoritative checks** in Flask routes and worker env (already started; extend to every new surface).
- Metrics: per-plan usage dashboards for operators (no customer PII leakage). **Partial (2026-04-12):** aggregate platform visit/subscription Slack digests + master-only 7-day table on `/services-status` (not yet per-plan customer usage dashboards); see [`defi-risk-web-integration-sprint-seasons-2026.md`](./defi-risk-web-integration-sprint-seasons-2026.md) § *Platform usage & Slack statistics*.

### Session P2 — Multi-token scan & token list selection

- **Multi-token scan** — Batch or queued assessments with clear progress, partial failure semantics, and quota consumption defined per plan.
- **Token list selection** — Persisted lists per account; validation of addresses per chain; **no trust in client-only checks**.
- **Progress (2026-04-19):** From **Settings → Crypto List**, when a list is open and the account has list-scan entitlement + token-editor rights, operators can **Queue Live Assessment** (same API as Live Assessment list mode) and land on the job page. Live Assessment + Crypto List templates now **cross-link** both flows; deep links use `?list=<id>` on Crypto List where an active list is known. Token-list writes now validate supported chain codes and address shape server-side; all-invalid CSV replace imports fail without clearing the existing list.

### Session P3 — Secure credential system

- Central **credential inventory** for engine/API keys: storage rules (encrypted at rest where applicable), rotation, audit log of last access, admin-only rotation UI—aligned with API Center direction.
- Separate **operator** vs **application** credentials; never pass production secrets to client JS.

### Session P4 — Cache & fallback lifetime settings

- User- or plan-aware **cache TTL** and **fallback / stale-data TTL** where product allows—**defaults safe for integrity** (prefer stale-with-label over silent wrong freshness).
- Admin overrides with audit trail; tie to data-plane metrics already on Services Status.

### Session P5 — Token / chain UX (settings & live flows)

- **Dropdown (or equivalent) for supported blockchains** on token selection flows—single source of truth from server (ETH / BSC / TRON per current product).
- Reduce user error (wrong chain) = security and score reliability win.
- Accessibility and mobile-friendly patterns consistent with existing `site.css` conventions.

### Session P6 — Efficiency & reliability hardening

- Profile risk pipeline and Script API; reduce duplicate provider calls; tighten disk/network usage on workers.
- **SLO dashboards** already present—set internal targets for prod (availability, job latency percentiles, error budget).
- Chaos-lite drills: worker kill, provider timeout, queue backlog—document outcomes.

### Session P7 — Confidentiality & score trustworthiness

- Document **what each score means**, confidence bands, and when outputs are suppressed due to stale data or plan tier.
- Review logs and API responses for **information leakage** (cross-tenant, internal paths, stack traces).

### Session P8 — Payments & abuse hardening

- Replay tests for IPN; rate limits on checkout and account endpoints; fraud-adjacent signals (without storing unnecessary PII).
- Review refund/chargeback operational flow if applicable.

### Session P9 — Automation pipeline security (bug handling / Cursor / Slack)

- **Prompt and payload injection** resistance: fixed templates, max lengths, allow-listed fields for GitHub/branch creation.
- Verify **no OS command** composition from ticket text; subprocess only with static commands + validated paths.
- Periodic **dependency audit** for integration scripts.

### Session P10 — Migration rehearsal (optional pre-scale)

- **Staging** mirror with load test on stateless web tier + single worker (or small queue).
- Runbook: “Add second app server + shared DB/object store” **when** business requires—no commitment to date.

### Session P11 — Operator outbound marketing email (Support area)

- **Goal:** Controlled, auditable **operator-only** tooling from the Support / operator surface: **support SMTP now** (optional Resend send path later), **named HTML templates**, **CSV/TXT batching**, queue + retry semantics—**not** a bulk spam engine.
- **Compliance:** Explicit consent / legitimate-interest basis documented per campaign; **List-Unsubscribe** and one-click unsubscribe where product requires; no scraping of customer inboxes; PII minimization in logs and Slack.
- **Slice 1 (2026-04-12):** SQLite `marketing_outreach.db` + `MarketingOutreachStore`; **master-only** JSON API `GET/POST /api/v1/support/outreach-templates` (create + list metadata; no sends yet). Env: `WEB_PORTAL_MARKETING_OUTREACH_DB`. Regression: `tests/test_api_center.py` (outreach template API).
- **Slice 2 (2026-04-19):** Support Tickets page — **Marketing outbound** panel (master only): lists templates, **Preview HTML** via `GET /api/v1/support/outreach-templates/<id>`, create form posting to `POST /support-tickets/outreach-templates` (CSRF + `_audit_privileged_operation`). Masters without DB path see a short configure hint.
- **Slice 3 (2026-04-21):** **Send** saved templates to customer recipients from Support Tickets: `POST /support-tickets/marketing-send` (master + admin, CSRF), support **SMTP**, any ticket status, outbound marketing thread rows, manual recipient chips, CSV/TXT recipient upload + validation, empty-file examples, and high-contrast preview/source panels. Admins get a send-only panel + API template reads; template **create/delete** stays master-only.
- **Slice 4 (2026-04-24):** Marketing abuse/compliance guardrails: per-request, per-operator/hour, and per-recipient/day caps; unsubscribe suppression list; `List-Unsubscribe` + `List-Unsubscribe-Post: List-Unsubscribe=One-Click` headers; public `/marketing/unsubscribe` endpoint.
- **Next slices:** Optional Resend *send* API path; campaign consent/basis capture; richer send analytics.

---

### Session P12 — New-device login verification (“Confirm Device”)

**Status: scoped 2026-07-22, not started.** Raised during an emergency web-portal recovery session; deliberately queued rather than built same-session since it changes live auth behavior and deserves its own implementation + test pass.

- **Goal:** Require explicit email confirmation before a login from a previously-unrecognized device/browser is allowed to complete. Today, **Known Devices** is purely informational (UUID, OS, browser, last IP, country, first/last seen) — there is no verified/unverified state and login is never gated on device recognition.
- **Confirmed by code review (2026-07-22):** no `device_approv*` / `device_verif*` / `device_confirm*` concept exists anywhere in `app/`. The email infrastructure to build on already exists and is confirmed working: `account_mailer.py`’s signed-token pattern (see `send_signup_code`, `send_password_reset_email`) plus SMTP delivery confirmed live via the Services Status → Core Services → **Support Mail Delivery** card.
- **Scope:**
  - DB migration: verification state on the devices table (e.g. `verified_at` nullable timestamp, or `status: pending|verified|revoked`).
  - Login-notification email gains a signed, single-use, expiring “Confirm this device” link, reusing the existing signed-token pattern in `account_mailer.py`.
  - New route to handle the confirm click: validates token, marks the device verified; a stale or reused link must fail closed, not silently succeed.
  - Login-flow gate: an unrecognized/unverified device is blocked from completing login until confirmed, with a clear user-facing state (“check your email to approve this device”), not a generic auth error.
  - **Known Devices** UI: add a Verified / Unverified / Revoked column; likely an admin action to revoke a device’s verified status.
- **Open decisions before implementation (need product input):**
  - Confirmation link expiry window, and the resend flow if it lapses unclicked.
  - Is there a “remember this device for N days,” or does every new device always require re-confirmation?
  - Are devices already known today (rows that predate this feature) grandfathered as verified, or forced through confirmation once on next login?
  - Rate limiting on the confirm route to resist link-guessing/brute force.
  - Admin visibility: can masters/admins see or revoke other users’ device approvals from an ops surface?
- **Regression coverage needed:** device-gate blocks unverified login; confirm route rejects expired/reused/tampered tokens; pre-existing verified/known devices unaffected; email delivery uses the SMTP path already confirmed working.

---

## Exit criteria for “official prod release” (suggested)

- Threat model reviewed and **residual risks** accepted in writing.
- Plan enforcement verified by automated tests for **each** paid surface.
- Multi-token + list selection + chain UX shipped with **server validation**.
- Credential and cache/fallback policies documented and **operator-tested**.
- Security verification + key runtime reports **green on prod** (or waivers tracked).
- No known **critical** issues open in payments, auth, or file ingestion.

---

## Relationship to prior sprint doc

Features listed here that were **scoped but not fully delivered** in earlier seasons (multi-token scan, token lists, credential UX, cache/fallback settings, chain dropdown, plan restrictions) are **first-class** in Sessions P1–P5. Security and scale-readiness sessions (P0, P6–P10) wrap those deliveries so new functionality does not **weaken** the security posture.

For historical delivery status, see [`defi-risk-web-integration-sprint-seasons-2026.md`](./defi-risk-web-integration-sprint-seasons-2026.md).
