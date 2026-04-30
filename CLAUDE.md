# CLAUDE.md — Children of Israel Agent Swarm

This file is read by Claude Code at the start of every session.

---

## What This Repo Is

A **skills and governance framework** for AI agent swarms. Not an engine — a playbook. The repo contains SKILL.md files (following the [Caveman](https://github.com/JuliusBrussee/caveman) convention), YAML law/config data, and markdown docs. Any agent swarm (Hermes, Devin, Claude Code) reads these and aligns.

---

## Repository Structure

```
skills/
├── governance/SKILL.md         # Three-tier law layer (Constitution + Oral Law)
├── orchestration/SKILL.md      # Jethro 5-tier hierarchy + Hermes pipeline
├── mission/SKILL.md            # End-to-end mission execution spec
└── tribes/                     # 12 tribal agent persona skills
    ├── reuben/SKILL.md         # Pioneer / Scout (Tier 4, Hermes eligible)
    ├── simeon/SKILL.md         # Zealot / Enforcer (Tier 2)
    ├── levi/SKILL.md           # Priest / Steward (Tier 1)
    ├── judah/SKILL.md          # Commander / Leader (Tier 1)
    ├── issachar/SKILL.md       # Scholar / Analyst (Tier 3)
    ├── zebulun/SKILL.md        # Merchant / Connector (Tier 3)
    ├── dan/SKILL.md            # Judge / Arbitrator (Tier 1)
    ├── naphtali/SKILL.md       # Messenger / Swift (Tier 4, Hermes eligible)
    ├── gad/SKILL.md            # Warrior / Resilience (Tier 4)
    ├── asher/SKILL.md          # Optimizer / Enricher (Tier 3, Hermes eligible)
    ├── joseph/SKILL.md         # Visionary / Planner (Tier 1)
    └── benjamin/SKILL.md       # Guardian / Protector (Tier 4)

law/                            # Raw YAML governance data
config/                         # Mission + Hermes pipeline config
docs/                           # Architecture reference docs
```

---

## Pre-PR Health Check

Run this before every pull request. All checks must pass.

```bash
# 1. All SKILL.md files have valid frontmatter (--- delimited YAML with name + description)
for f in $(find skills -name 'SKILL.md'); do
  head -1 "$f" | grep -q '^---$' || echo "FAIL: $f missing frontmatter"
done && echo 'OK — all SKILL.md files have frontmatter'

# 2. Law layer — YAML must parse and have all 6 themes + 630 directives
python3 -c "
import yaml
data = yaml.safe_load(open('law/commandments.yaml').read())
themes = data['themes']
total = sum(sum(len(sc['directives']) for sc in t['subcategories']) for t in themes)
assert len(themes) == 6, f'Expected 6 themes, got {len(themes)}'
assert total >= 600, f'Expected 600+ directives, got {total}'
print(f'OK — {len(themes)} themes, {total} directives')
"

# 3. All 12 tribe skills exist
for tribe in reuben simeon levi judah issachar zebulun dan naphtali gad asher joseph benjamin; do
  test -f "skills/tribes/$tribe/SKILL.md" || echo "FAIL: missing skills/tribes/$tribe/SKILL.md"
done && echo 'OK — all 12 tribe skills present'

# 4. Core skills exist
for skill in governance orchestration mission; do
  test -f "skills/$skill/SKILL.md" || echo "FAIL: missing skills/$skill/SKILL.md"
done && echo 'OK — core skills present'

# 5. Config files parse
python3 -c "
import yaml
yaml.safe_load(open('config/mission.yaml'))
yaml.safe_load(open('config/hermes_pipeline.yaml'))
yaml.safe_load(open('law/constitution.yaml'))
yaml.safe_load(open('law/oral_law.yaml'))
yaml.safe_load(open('law/tribes/tribes.yaml'))
print('OK — all config/law YAML files parse')
"

# 6. No uncommitted changes
git status --short && echo 'OK — working tree clean'
```

### Expected output summary

| Check | Expected |
|-------|----------|
| SKILL.md frontmatter | `OK — all SKILL.md files have frontmatter` |
| Law layer | `6 themes, 630 directives` |
| Tribe skills | `OK — all 12 tribe skills present` |
| Core skills | `OK — core skills present` |
| YAML parsing | `OK — all config/law YAML files parse` |
| Git status | No output (clean) |

---

## Key Architectural Rules

- **Never bypass the Jethro hierarchy.** All escalations must follow tier order.
- **Dan is the only judge who writes precedents.** OL-002 precedent authority belongs to Dan alone.
- **Levi writes the audit log.** Append-only. Never truncate or overwrite.
- **Hermes-eligible tribes** (Reuben, Naphtali, Asher) can delegate to the Hermes parallel pipeline.
- **This repo is skills-only.** No runtime code. The engine lives in the agent that reads this.
