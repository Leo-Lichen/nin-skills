# Ninther Skills

**Turn a business idea into something you can test. Connect diagnosis, business planning, and action.**

[简体中文](README.md) · English · [Getting started — Chinese](docs/getting-started.md) · [License](LICENSE)

Ninther Skills, also called **Nin-skills** or **nin**, is a collection of **18 AI agent skills** for starting and running a business. It draws on Han Shujie's *创业地图：商业计划书与创业行动指南* (2020) and covers diagnosis, customers and products, costs and cash, business plans, experiments, and project records.

Current version: **v1.0.2**. Start with `$nin` when you are unsure which skill fits your task.

## Who it is for

Use it for local services, courses and consulting, freelance work, small product teams, business services, or an idea that still needs testing. A stable small business and a company seeking investment have different goals; the work starts from the goal you choose.

The skills run inside an agent that supports local Skills. They produce analysis, drafts, calculations, and proposed actions. Customer purchases and delivery outcomes still need evidence from the real business.

## Six ways to use it

| Situation | Useful output |
| --- | --- |
| Friends like a companionship-service idea, and you are about to pay for an app | A project assessment, the main evidence gap, and a small manual-service test |
| Companies praise a scheduling trial but do not purchase | A distinction between users and buyers, alternatives, purchasing blockers, and follow-up actions |
| You have no paying customers yet but need a plan for a potential partner | An editable business plan with facts, assumptions, capacity, and revenue scenarios separated |
| A course sells, but advertising, refunds, and your own work consume the proceeds | Comparable costs and revenue, unit economics, and cash conditions |
| You have 90 seconds to ask a store partner for access to potential customers | A script to rehearse, a time budget, and key questions with grounded answers |
| Total receipts cover expenses, but bills fall due before customers pay | A dated cash table, the first shortfall, its amount, and possible adjustments |

These are example tasks, not promised business outcomes. Missing information stays visible while the agent completes what the available evidence supports.

## Start a conversation

After installation, type this in a **Codex conversation**, not in a terminal:

```text
$nin I run a local pet-care service with 12 paying customers, all from personal referrals.
I have at most 40 hours a month for the whole business.
I want to try store referrals. Help me decide what to test first.
```

Use `/nin` in a host that supports slash commands. Once the skills are loaded, you can also refer to the toolkit in ordinary language as **Nin**, **nin**, or **Nin-skills**. Skill discovery and selection depend on the host.

For a specific task:

```text
$nin-bp Draft a business plan for a potential partner. Use the information provided and mark unknowns.
$nin-model Separate revenue, refunds, delivery costs, and my own time for these orders.
$nin-project Save this conclusion and its evidence in my chosen project folder.
```

## Download and install

### Download a ZIP from GitHub

1. Open the [Ninther Skills repository](https://github.com/Leo-Lichen/nin-skills).
2. Select **Code**, then **Download ZIP**.
3. Extract the archive. Open the folder containing `skills`, `scripts`, and `manifest.json`.
4. Open a terminal in that folder and run the installation command below.

Downloading a public repository ZIP does not require a GitHub account or knowledge of Git.

### Python installer

You need **Python 3.10 or later**. The installer uses the Python standard library and does not require additional Python packages.

Preview the destination, then install for Codex:

```bash
python scripts/install.py --target codex --dry-run
python scripts/install.py --target codex
```

Other installation targets:

```bash
python scripts/install.py --target claude
python scripts/install.py --target agents
```

These targets select the skill directories for Codex, Claude Code, and general Agents use. Add `--dry-run` to preview any target. The installer stops if a skill folder already exists; it does not overwrite existing files. Reopen or refresh your host session after installation and check that the skills have loaded.

### Manual installation

Copy all **18 complete skill folders** inside this repository's `skills/` folder to your host's skill directory. Preserve each folder's `SKILL.md`, references, and any scripts.

| Host | Common user-level skill directory |
| --- | --- |
| Codex | `~/.codex/skills/` |
| Claude Code | `~/.claude/skills/` |
| General Agents | `~/.agents/skills/` |

`~` means your user home directory. If `CODEX_HOME` is set, the installer uses its `skills/` subdirectory for Codex. Follow the host's configuration for other custom locations. Copy the skill folders themselves; do not copy only `SKILL.md` or nest the whole repository as a single skill.

## All 18 skills

These are skill names. In Codex, prefix a name with `$`; in hosts with slash commands, use `/`.

| Skill | When to use it | Main output |
| --- | --- | --- |
| [nin](skills/nin/SKILL.md) | Choose where to start | Route the current task using information already supplied |
| [nin-diagnosis](skills/nin-diagnosis/SKILL.md) | Assess an idea or diagnose a bottleneck | Evidence checks across the problem, solution, team, and business modules |
| [nin-positioning](skills/nin-positioning/SKILL.md) | Explain what the business does and for whom | A concise positioning statement and project introduction |
| [nin-market](skills/nin-market/SKILL.md) | Examine customers, needs, and market opportunity | Customer segments, alternatives, competition, and market definitions |
| [nin-product](skills/nin-product/SKILL.md) | Define a product or service and choose features | A link between needs, capabilities, delivery, and outcome evidence |
| [nin-model](skills/nin-model/SKILL.md) | Understand pricing, acquisition, delivery, and earnings | Transaction structure, costs, unit economics, and cash distinctions |
| [nin-team](skills/nin-team/SKILL.md) | Plan roles, cooperation, and resources | Capability gaps, responsibilities, and unresolved partnership terms |
| [nin-progress](skills/nin-progress/SKILL.md) | Check what has actually been achieved | An evidence table, supportable claims, and the next evidence gap |
| [nin-strategy](skills/nin-strategy/SKILL.md) | Convert a goal into work | Milestones, capacity, budget, dependencies, and revision conditions |
| [nin-risk](skills/nin-risk/SKILL.md) | Identify conditions that could disrupt the business | Failure conditions, signals, owners, and responses |
| [nin-funding](skills/nin-funding/SKILL.md) | Decide whether, how much, and why to raise money | Funding needs, source comparisons, uses, and the period supported |
| [nin-bp](skills/nin-bp/SKILL.md) | Write or revise a business plan | A substantive draft, key arguments, and evidence still needed |
| [nin-pitch](skills/nin-pitch/SKILL.md) | Prepare a pitch, partner introduction, or Q&A | A spoken script, time budget, and answer cards |
| [nin-investor](skills/nin-investor/SKILL.md) | Examine a project from an investor's perspective | Supporting and contrary evidence, due-diligence questions, and preparation priorities |
| [nin-experiment](skills/nin-experiment/SKILL.md) | Test a business assumption with a small experiment | Participants, offer, limits, observations, and decision criteria |
| [nin-survival](skills/nin-survival/SKILL.md) | Address a cash shortage or reduce commitments | A cash timeline, shortfall, and conditions for continuing or adjusting |
| [nin-founder](skills/nin-founder/SKILL.md) | Weigh business, employment, and personal commitments | Alternatives, resource boundaries, and conditions for reconsidering |
| [nin-project](skills/nin-project/SKILL.md) | Save, resume, update, or summarize project work | Traceable project records and reports |

## Method and evidence

The source framework is Han Shujie's *创业地图：商业计划书与创业行动指南* (2020), including problem, solution, and team value, and the business-plan structure of nine modules and 36 points. Each skill retains its method references. Routing, evidence labels, experiment cards, and local record workflows are adaptations for agent use.

- Keep interest, letters of intent, deposits, purchases, and completed delivery distinct.
- Separate user statements, source records, external verification, inferences, and untested assumptions.
- Distinguish revenue, profit, cash received, and obligations still to be delivered.
- Make plans fit available time, people, cash, and existing commitments.
- Keep earlier conclusions and the reasons for changing them.

Historical examples do not establish present market conditions. Current external facts need their own verification; unsupported numbers remain unknown or are explicitly labeled as scenario assumptions.

## What has been checked

Local checks cover the structure and references of all 18 skills. Behavioral exercises include seven original scenarios, with three same-task comparisons, plus three new scenario reviews. They examine substantive output, calculations, evidence boundaries, and resource constraints.

This is a limited local sample. It does not mean every model, operating system, or application has been tested, and it does not establish general superiority over other skill collections. An installation destination and successful loading by a host are separate checks. Results such as actual speaking time still need rehearsal or real-world feedback.

## Repository and license

```text
nin-skills/
├── skills/             # 18 skills and their supporting material
├── scripts/            # Installation and other local tools
├── docs/               # User documentation
├── manifest.json       # Name, version, and skill inventory
└── VERSION
```

This project is publicly available under **CC BY-NC 4.0**. Noncommercial use, sharing, and adaptation are allowed with attribution, a license link, and an indication of changes. Commercial use requires separate permission.

See [LICENSE](LICENSE) for the full terms. For permission inquiries, use the [GitHub profile](https://github.com/Leo-Lichen) or a [repository issue](https://github.com/Leo-Lichen/nin-skills/issues). This license does not change the rights in the source book or other third-party material.
