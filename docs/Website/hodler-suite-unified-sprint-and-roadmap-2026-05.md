# Hodler Suite — Unified Sprint Backlog & Roadmap (2026)

Last updated: **2026-05-04**

This document is the **single source of truth** for program sequencing. It merges:

- [defi-risk-web-integration-sprint-seasons-2026.md](./defi-risk-web-integration-sprint-seasons-2026.md) (Seasons 1–9 + kickoff progress),
- [production-release-sprint-sessions-2026.md](./production-release-sprint-sessions-2026.md) (Sessions P0–P11),
- [web-port-security-implementation-plan-2026.md](./web-port-security-implementation-plan-2026.md) (open product/security backlog, where still applicable).

Older files keep **historical narrative**; **do not** re-open work listed under *Completed milestone archive* unless a regression appears.

---

## 1. Strategic roadmap (product, SaaS, business)

### 1.1 Business direction

Hodler Suite is positioned as a **B2B / serious retail SaaS** for **explainable token risk**: one consistent workflow from contract address to defensible scores, aimed at **AML analysts, listing teams, exchanges, funds, and institutional risk** users who cannot afford black-box “scores in a vacuum.”

Near-term revenue is **subscription-led** (plan tiers with clear entitlements), crypto checkout (NOWPayments), and **trust as the product**—honest limits when data is stale, suppressed, or plan-gated (“affidability” in internal language).

### 1.2 SaaS trajectory (horizons)

| Horizon | Theme | Outcomes |
| --- | --- | --- |
| **Now (live)** | Trustworthy core SaaS | Web portal on Flask + Jinja + vanilla JS; ETH / BSC / TRON; Live Assessment + job pipeline; Services Status telemetry; billing + reconciliation patterns; support ticketing + operator marketing-send tooling; defense-in-depth on web/API (CSP evolution, rate limits, sessions, audits). |
| **2026 H1** | **Release-grade engine + enforcement** | Worker path consumes **real** legacy scoring output (not placeholders); parity harness vs desktop baselines; formal **threat model** + release gate evidence; **server-side plan enforcement** on every paid surface; chain UX (single source of truth from server); **credential / API Center** direction per Session P3; Script API + risk worker **production stability** (7-day evidence, tuned alerts). |
| **2026 H2** | **Data plane & operator excellence** | Perpetual cache / fallback discipline (Season 4 + Session P4); SLO/error-budget culture; operator dashboards for job latency and provider health; incident runbooks for queue backlog / provider outage; optional **staging + load rehearsal** (Session P10) before scale-out. |
| **2027** | **Platform & API program** | Versioned partner APIs; org/teams and stronger audit exports; watchlists + alerting (Seasons 5–6 themes); deeper **score explainability** in-product (confidence, freshness, suppression reasons). |
| **Horizon (optional)** | **Scale & adjacency** | Second app tier + shared DB/object store without rewrite; managed DB path where SQLite limits bite; optional **wallet exposure** module; custom integration / governance reporting packs for large desks. |

### 1.3 Principles (non-negotiable)

1. **Security first** — no UI-only gates for paid or sensitive actions.  
2. **Integrity of scores** — stale/fallback data labeled; no false certainty.  
3. **Efficiency** — smart caching, fewer redundant provider calls.  
4. **Migration-friendly contracts** — versioned APIs, explicit job schemas, 12-factor config; **no** mandated framework swap in this program track.

---

## 2. Completed milestone archive (do not re-queue)

Use this section to avoid **copy-pasting finished work** into future “seasons.”

### 2.1 Web portal / security program (through early 2026)

From [web-port-security-implementation-plan-2026.md](./web-port-security-implementation-plan-2026.md) snapshot: route boundaries, core pages (home, dashboard, live assessment, settings, account, help, FAQ, docs, checkout), Turnstile/rate limits on intake, billing webhook verification + reconciliation tooling, status sampler + Services Status board, Script API probe auth/HMAC, telemetry retention + purge jobs, failed-auth lockout + privileged-action audit stream, Trustpilot relay, inbound email resilience packs, deploy-pack verification passes, legacy webhook hardening on `webhook_server.py`.

### 2.2 Integration sprint kickoff (2026-03-05)

From [defi-risk-web-integration-sprint-seasons-2026.md](./defi-risk-web-integration-sprint-seasons-2026.md):

- **Season 1 (partial):** service boundary artifact; `risk_job_store` + `/api/v1/risk/jobs` scaffold + env wiring.  
- **Season 2 (partial):** Script API / chain card key isolation; probe thresholds + `status_probe` alerts; Services Status trend fields; **deploy pack artifacts** for Script API + watchdog (runtime enablement is **ops**, not code-complete “done”).  
- **Season 3 (partial):** queue claim + worker internal endpoints; dashboard/live-assessment bound to real job state; risk-worker + risk-runtime cards on Services Status; Public Edge + Infrastructure cards.

### 2.3 Production sessions (selected)

From [production-release-sprint-sessions-2026.md](./production-release-sprint-sessions-2026.md):

- **P2 (major progress 2026-04-19):** Crypto List ↔ Live Assessment cross-link; list queue flow; server-side chain/address validation on token list writes.  
- **P11 slices 1–4 (through 2026-04-24):** marketing outreach templates API + Support UI + send path + abuse/compliance guardrails (caps, unsubscribe, `List-Unsubscribe` headers).

### 2.4 Security engineering (May 2026)

Consolidated **CodeQL / application security** remediation wave (URL sanitization, safe redirects, SSRF allowlists, logging redaction, workflow permissions, action pinning, weak crypto cleanup, etc.) — tracked in GitHub / `SECURITY.md`; not duplicated here as open backlog.

---

## 3. Unified open backlog (single sprint list)

Items are **deduplicated** and ordered roughly by **dependency / release value**. IDs are stable for discussion (`U-###`).

### 3.1 Foundation — engine fidelity & runtime evidence

| ID | Item | Source | Notes |
| --- | --- | --- | --- |
| **U-001** | Replace placeholder / deterministic risk results with **direct adapter** from legacy `defi_complete_risk_assessment_clean.py` output mapping | Season 3 Next | Blocks honest “prod release” claims. |
| **U-002** | **Parity harness**: representative tokens vs desktop baseline samples; failure taxonomy stable | Season 3 Next | Pair with U-001. |
| **U-003** | Deploy + enable Script API runtime + watchdog on **staging/prod**; collect **7-day stability** window; tune thresholds | Season 2 Next | Code packs exist; needs operational evidence. |
| **U-004** | Same for **risk-worker** timer/service: sustained throughput + failure-rate evidence | Season 2–3 | Align with Services Status cards. |
| **U-005** | Legacy webhook caller **compatibility contract** documented + validated (signed/auth traffic) | Season 1 Next | Rollout already prioritized in security plan; keep one owner. |

### 3.2 Release gate — threat model & verification

| ID | Item | Source |
| --- | --- | --- |
| **U-010** | Formal **threat model** refresh: web, Script API, risk worker, Slack/GitHub/Cursor automation, payments, email inbound | P0 |
| **U-011** | **Prod evidence**: security verification + deploy-pack reports; gap list with owners | P0 |
| **U-012** | **Incident response**: on-call paths, log retention, Slack alerting coverage confirmed | P0 |

### 3.3 Product — plans, quotas, UX

| ID | Item | Source |
| --- | --- | --- |
| **U-020** | **Plan enforcement completion**: every new/paid surface authoritative in Flask + worker (`child` vs `admin`/`master`) | P1 |
| **U-021** | **Per-plan usage dashboards** for operators (aggregate; no PII leakage) — extend beyond current visit/subscription digests | P1 partial |
| **U-022** | **Multi-token scan**: batch/queue semantics, partial failures, quota consumption per plan | P2 |
| **U-023** | **Token list selection** hardening: persisted lists; no client-only trust (ongoing vigilance on new endpoints) | P2 |
| **U-024** | **Chain dropdown** (or equivalent) on token flows — server-driven allowed chains | P5 |
| **U-025** | **Accessibility + mobile** pass on Live Assessment / token flows (`site.css` patterns) | P5 |

### 3.4 Credentials, cache policy, trustworthiness

| ID | Item | Source |
| --- | --- | --- |
| **U-030** | **Credential inventory** UX + storage rules: rotation, audit of access, admin-only rotation — aligned with API Center | P3 |
| **U-031** | Separate **operator vs application** credentials; never expose prod secrets to client JS | P3 |
| **U-032** | **Cache TTL + fallback / stale-data TTL** exposed where product allows; safe defaults; admin overrides + audit | P4 |
| **U-033** | In-product documentation: **what each score means**, confidence, suppression / stale labels | P7 |

### 3.5 Reliability & operations

| ID | Item | Source |
| --- | --- | --- |
| **U-040** | Profile risk pipeline + Script API; reduce duplicate provider calls | P6 |
| **U-041** | Set **internal SLO targets** (availability, job latency percentiles) using existing boards | P6 |
| **U-042** | **Chaos-lite** drills: worker kill, provider timeout, queue backlog — document outcomes | P6 |
| **U-043** | Services monitoring: **sampler/timer health** + alerting for stale samples (verify prod) | Web port remaining |

### 3.6 Security & abuse (ongoing streams)

| ID | Item | Source |
| --- | --- | --- |
| **U-050** | **Payments abuse**: IPN replay tests; rate limits on checkout/account; fraud-adjacent signals (min PII) | P8 |
| **U-051** | **Automation pipeline** (Slack/GitHub/Cursor): template-based payloads, max lengths, allow-listed fields; no OS command composition from ticket text | P9 |
| **U-052** | Periodic **dependency audit** for integration scripts | P9 |
| **U-053** | **OIDC migration** (optional program): preserve MFA + RBAC | Web port remaining product #1 |
| **U-054** | **Sanitized live log streaming** + durable run history (productized) | Web port remaining product #2 |
| **U-055** | **Help desk**: SLA/assignment/escalation from category + confidence | Web port remaining |
| **U-056** | **Docs CI redaction gate** before public docs publish | Web port remaining |
| **U-057** | **Privacy**: field-level redaction / export for data subject requests | Web port remaining |
| **U-066** | **New-device login verification** ("Confirm Device"): block login for unrecognized devices until a signed email confirmation link is clicked; add verified/unverified/revoked state to Known Devices | P12 |

### 3.7 Season themes not fully superseded by sessions above

| ID | Item | Source |
| --- | --- | --- |
| **U-060** | **Season 4** — cache warmers, jitter/backoff, upstream fallback policy, freshness metrics | Season 4 |
| **U-061** | **Season 5** — Live Assessment progress bound to **worker events** (not log-scrape-only); provider attestation footer | Season 5 |
| **U-062** | **Season 6** — dashboard cards fully data-driven under degradation | Season 6 |
| **U-063** | **Season 7** — settings IA: `/settings/overview`, `/settings/api-center`, `/settings/crypto-list` + centralized entitlement middleware | Season 7 |
| **U-064** | **Season 8** — daily scan limits, API caps, audit logs, immutable entitlement decisions | Season 8 |
| **U-065** | **Season 9** — SLO gate + error budgets + incident runbooks + confidentiality checklist ≥ target | Season 9 |

### 3.8 Optional / deferred (explicitly lower priority)

| ID | Item | Source |
| --- | --- | --- |
| **O-001** | **Session P10** — staging mirror + load test + scale-out runbook rehearsal | P10 optional |
| **O-002** | **Resend send path** for marketing (SMTP path shipped) | P11 next slices |
| **O-003** | Campaign consent/basis capture + richer send analytics | P11 next slices |
| **O-004** | **ADBLOCK_GATE** productization polish (`ADBLOCK_GATE_ENABLED`) | Production side-task |
| **O-005** | AI ticket pre-triage worker (Chatwoot / Dify-class) — self-hosted preference | Web port plan |
| **O-006** | Status subdomain / public status page | Web port DNS optional |
| **O-007** | Wallet exposure module | JSX / Season “Later” theme |

---

## 4. Optional hardenings still worth doing

Cross-cutting items that do not block feature work but **raise the security bar**:

- **Infrastructure**: SSH `Banner`, `fail2ban` local overrides (`jail.local`), Lynis follow-ups, `libpam-tmpdir` where available, Certbot **webroot** workflow (avoid standalone) — align with ops runbooks.  
- **CI/CD**: keep **minimum GitHub Actions permissions**, **pinned Actions SHAs**, and periodic **secret scanning** / CodeQL on default branch.  
- **Application**: CSP tightening iterations; rate limit review on new routes; **step-up 2FA** expansion to any newly sensitive mutation; session fixation resistance checks on cookie changes.  
- **Data**: encrypted backups + **restore drill** evidence; WAL + SQLite contention review before multi-worker writes.  
- **Process**: external pen-test window before large marketing pushes; tabletop IR exercise.

---

## 5. Suggested execution waves (not separate “seasons”)

To avoid parallel season numbering confusion:

1. **Wave A — Truthful scores** — U-001, U-002, U-020 (minimal set to trust outputs).  
2. **Wave B — Release gate** — U-010–U-012, U-005 rollout verification.  
3. **Wave C — Operator + UX** — U-003, U-004, U-024, U-021, U-040–U-042.  
4. **Wave D — Platform policy** — U-030–U-032, U-060, U-064.  
5. **Wave E — Differentiation** — U-022, U-061–U-063, U-033.  

Waves can overlap by owner; **Wave A** is the critical path for external “audit-ready” narratives.

---

## 6. References

- [defi-risk-web-integration-sprint-seasons-2026.md](./defi-risk-web-integration-sprint-seasons-2026.md)  
- [production-release-sprint-sessions-2026.md](./production-release-sprint-sessions-2026.md)  
- [web-port-security-implementation-plan-2026.md](./web-port-security-implementation-plan-2026.md)  
- [defi-risk-season1-service-boundary-map-2026-03-05.md](./defi-risk-season1-service-boundary-map-2026-03-05.md)  
- [web-portal-production-architecture.md](./web-portal-production-architecture.md)
