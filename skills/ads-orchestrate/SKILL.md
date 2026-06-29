---
name: ads-orchestrate
description: "Autonomous orchestration of AI agents and n8n workflows for end-to-end paid advertising. Monitors trending topics in a niche, then chains brand DNA, competitor intel, planning, creative, budget and social content into best-practice campaigns. Outputs orchestration-plan.md and an editorial calendar. Use when user says autonomous orchestration, orchestrate agents, n8n workflow, trend monitoring, trending topics, content calendar, social content, marketing automation, autopilot, or always-on campaigns."
user-invokable: false
tested_date: 2026-06-29
tested_with: claude-code v2.x
---

# Ads Orchestrate: Autonomous Campaign & Content Engine

Coordinates the existing claude-ads sub-skills into a continuous, mostly-autonomous
loop: watch what is trending in the niche, refresh brand and competitor context,
plan and produce on-brand campaigns + social content, and keep budgets in bounds.
Self-hosted — runs locally or on any n8n/Docker host the user controls. No VPS,
no third-party credentials baked in; secrets stay in the user's `.env`.

Operates under the **10-Principle Thinking Framework** (see
`ads/references/thinking-framework.md`). OBSERVE the trend signal, LISTEN to the
brand voice, CONNECT trend to product, ACCEPT the budget guardrails, CREATE the
deliverable, GROW from each cycle's results. Autonomy without these gates is just
spam at scale.

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/ads orchestrate` | Full chain → `orchestration-plan.md` + `content-calendar.md` |
| `/ads orchestrate --niche perfume` | Scope trend monitoring to a niche |
| `/ads orchestrate --dry-run` | Plan only; no agent dispatch, no spend |

## Pipeline

The chain reuses existing sub-skills — it adds orchestration, not new ad logic:

```
trends.py → ads-dna → ads-competitor → ads-plan → ads-create → ads-generate → ads-budget → calendar
```

1. **OBSERVE — Trends**: run `scripts/trends.py --niche <niche>` for trending
   topics, hashtags, and seasonal hooks. Output JSON → `trends.json`.
2. **Brand DNA**: if `brand-profile.json` is missing, run `/ads dna <url>` first.
3. **Competitor**: run `/ads competitor` for live ad-library gaps.
4. **Plan**: run `/ads plan` calibrated to industry + monthly budget.
5. **Create**: run `/ads create` — map each trend to a campaign concept + copy.
6. **Generate**: run `/ads generate` / `/ads photoshoot` for on-brand visuals.
7. **Budget**: run `/ads budget` + `/ads math` for allocation and ROAS guardrails.
8. **Calendar**: write `content-calendar.md` (IG/TikTok/FB cadence from templates).

## Autonomy Levels

| Level | Behavior | Human review |
|-------|----------|--------------|
| L1 Suggest | Produce plan + drafts only | Every output |
| L2 Assist | Draft + schedule, hold publish | Approve before publish |
| L3 Auto | Publish within guardrails | Spot-check + budget alerts |

Default is **L2**. Never jump to L3 without explicit user opt-in.

## Human-Review Gates (never auto-skip)

- Brand safety: trend must pass FEEL gate (no tragedy/controversy hijacking).
- Budget: any campaign exceeding `--max-daily` is held for approval (budget-guard).
- Compliance: special ad categories + per-platform policy always reviewed.
- New visuals: first asset of each concept reviewed before bulk generation.

## n8n Workflows (self-hosted)

Import-ready templates in `workflows/`. They contain **no secrets** — wire your
own credentials in n8n's credential store. Run locally with Docker:

```bash
docker run -d --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n docker.n8n.io/n8nio/n8n
```

| File | Purpose | Trigger |
|------|---------|---------|
| `trend-monitor.json` | Poll RSS/Trends, dedupe, store hot topics | cron |
| `campaign-factory.json` | Trend → claude-ads chain → drafts | webhook |
| `budget-guard.json` | Watch spend, pause >3x target CPA | cron |
| `content-calendar.json` | Schedule social drafts across platforms | cron |

## Process

1. Context intake (niche, platforms, monthly budget, autonomy level).
2. Run `trends.py`; rank topics by relevance × momentum.
3. Run pipeline above; honor review gates.
4. Test E2E in a sandbox (dry-run) before any live dispatch.
5. Present `orchestration-plan.md` + `content-calendar.md` and request review.

## Community Footer

After completing the full orchestration deliverable, append the standard
community footer (see `ads/SKILL.md` → Community Footer).
