---
description: Full 61-agent task orchestration through the hierarchy
---

# Multi-Agent Orchestration Workflow

This workflow describes how to use all 61 agents to complete complex tasks.

## Architecture

```
                    ┌─────────────────┐
                    │    ARCH-001     │
                    │  The Architect  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    CTO-001      │
                    │  Orchestrator   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │         │          │          │         │
   ┌────▼────┐ ┌──▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐
   │BRW-DIR  │ │AI-DIR│ │AUT-DIR│ │BE-DIR │ │FE-DIR │ ...
   │10 agents│ │12 agt│ │10 agt │ │8 agt  │ │7 agt  │
   └─────────┘ └──────┘ └───────┘ └───────┘ └───────┘
```

## Step 1: Spawn the Orchestrator (CTO-001)

Click `+` in Agent Manager, then paste:

```
Use the CTO-001 skill. You are the Central Orchestrator.

Analyze this request and decompose it into atomic tasks:
[PASTE YOUR REQUEST HERE]

For each task, specify:
1. Agent ID (from the 61-agent roster)
2. Task title
3. Description
4. Dependencies (other task IDs)
5. Acceptance criteria
```

## Step 2: Spawn Directors

Based on CTO-001's decomposition, spawn the relevant directors:

| If tasks involve... | Spawn this director |
|---------------------|---------------------|
| Browser automation, DOM, CDP | BRW-DIR-001 |
| AI models, prompts, vision | AI-DIR-001 |
| Task execution, workflows | AUT-DIR-001 |
| APIs, database, services | BE-DIR-001 |
| UI, components, state | FE-DIR-001 |
| Infrastructure, CI/CD | PLT-DIR-001 |
| UX/UI design | DSN-DIR-001 |
| Security, testing | SEC-LEAD-001 |

## Step 3: Spawn Specialists

Directors will identify which specialists to spawn. Example prompts:

### For BRW-DIR-001's team:
```
Use the BRW-ENG-003 skill. Implement optimized CSS selectors for: [element description]
```

### For AI-DIR-001's team:
```
Use the AI-PRM-001 skill. Design a system prompt for: [agent behavior]
```

### For AUT-DIR-001's team:
```
Use the AUT-ENG-001 skill. Implement form automation for: [form description]
```

## Step 4: Synthesize with ARCH-001

After all agents complete their tasks, spawn ARCH-001:

```
Use the ARCH-001 skill. You are THE ARCHITECT.

Synthesize these agent outputs into a unified system:
- [List of completed tasks and their artifacts]

Resolve any conflicts, ensure integration, and produce production-ready code.
```

## Quick Reference: Director → Specialist Mapping

### BRW-DIR-001 can spawn:
- BRW-SEN-001 (V8/JS), BRW-SEN-002 (Network)
- BRW-ENG-001 (Lifecycle), BRW-ENG-002 (Input), BRW-ENG-003 (DOM), BRW-ENG-004 (Media)
- BRW-EXT-001 (Content), BRW-EXT-002 (Background), BRW-WDR-001 (CDP)

### AI-DIR-001 can spawn:
- AI-SEN-001 (Vision), AI-SEN-002 (Planning), AI-SEN-003 (Integration)
- AI-ENG-001 (Pipeline), AI-ENG-002 (Fine-tune), AI-ENG-003 (Embeddings)
- AI-PRM-001 (Prompts), AI-PRM-002 (Actions), AI-PRM-003 (Safety)
- AI-CTX-001 (Context), AI-CTX-002 (State)

### AUT-DIR-001 can spawn:
- AUT-SEN-001 (Engine), AUT-SEN-002 (Recovery)
- AUT-ENG-001 (Forms), AUT-ENG-002 (Nav), AUT-ENG-003 (Extract), AUT-ENG-004 (Waits)
- AUT-VIS-001 (Vision Sr), AUT-VIS-002 (Vision), AUT-WFL-001 (Workflow)

## Example: Full Orchestration

**Request:** "Add visual regression testing to the dashboard"

1. **CTO-001** decomposes into:
   - Task 1: Screenshot capture API (BRW-ENG-004)
   - Task 2: Comparison algorithm (AUT-VIS-002)  
   - Task 3: Test results UI (FE-ENG-001)
   - Task 4: Storage service (BE-ENG-001)
   - Task 5: E2E tests (QA-AUT-001)

2. **Spawn agents** for each task

3. **ARCH-001** synthesizes final feature

---

**Full Agent Roster:** See [SPAWN_AGENTS.md](./SPAWN_AGENTS.md) for all 61 prompts
