# XApply Flow - Part 8: Spawn Agent

## Trigger

User clicks **Spawn** button on agent card.

---

## Complete Flow

```mermaid
flowchart TD
    subgraph Frontend["Frontend"]
        U1["User clicks Spawn"] --> U2["Get agent ID"]
        U2 --> U3["POST /api/spawn"]
    end

    subgraph Backend["Backend: /api/spawn"]
        S1["Receive agent_id"] --> S0{"Agent has URL in DB?"}
        
        S0 -->|Yes| R1["Open new tab"]
        R1 --> R2["Navigate to saved URL"]
        R2 --> R3["Store handle"]
        R3 --> R4["Update status = active"]
        R4 --> D3["Return success"]
        
        S0 -->|No| S2["get_agent_skill"]
        S2 --> S3["create_agent_zip"]
        S3 --> S4["Navigate to AI Studio"]
        
        S4 --> M1["select_model: Gemini 3 Pro Preview"]
        M1 --> M2["ESC x2 to close"]
        
        M2 --> F1["upload_zip: agent zip"]
        F1 --> F2["upload_files: core.txt"]
        
        F2 --> I1["set_system_instructions"]
        I1 --> I2["ESC x3 to close"]
        
        I2 --> A1["save_app: AGENT: id"]
        A1 --> A2["get_app_url"]
        A2 --> A3["save_agent_url to JSON"]
        
        A3 --> C1["send_chat_message: init"]
        C1 --> C2["Store handle"]
        C2 --> D2["Update status = active"]
        D2 --> D3
    end

    U3 --> S1
    D3 --> U4["Update UI: agent active"]

    style U1 fill:#60a5fa,stroke:#2563eb
    style S0 fill:#fbbf24,stroke:#d97706
    style R2 fill:#4ade80,stroke:#16a34a
    style S3 fill:#f97316,stroke:#ea580c
    style A3 fill:#a78bfa,stroke:#7c3aed
    style D2 fill:#a78bfa,stroke:#7c3aed
    style U4 fill:#4ade80,stroke:#16a34a
```

---

## Reactivation (if URL exists in DB)

| Step | Action |
|------|--------|
| Check DB | Agent has `drive_url`? |
| Open tab | New Chrome tab |
| Navigate | Go to saved URL |
| Store handle | `agent_handles[id] = handle` |
| Update status | `active` |
| Return | Skip all other steps |

> **FAST PATH**: If spawned before, just open saved URL.

---

## Agent Zip Contents

`create_agent_zip()` creates `{agent_id}.agent.zip` containing:

| File | Content |
|------|---------|
| `core_instructions.md` | Skill content from SKILL.md |
| `input.md` | "# Input\n\nAwaiting input..." |
| `output.md` | Output format template |
| `memory.json` | `{}` empty JSON |

> **NOTE**: input.md, output.md, memory.json are IN the zip, not uploaded separately.

---

## Files Uploaded

| # | File | How |
|---|------|-----|
| 1 | `{agent_id}.agent.zip` | `upload_zip()` |
| 2 | `core.txt` | `upload_files()` (if exists) |

---

## Settings Configuration

| Step | Function | Details |
|------|----------|---------|
| Model | `select_model()` | "Gemini 3 Pro Preview" |
| Close | ESC x2 | pyautogui |
| System Instructions | `set_system_instructions()` | Paste skill content |
| Close | ESC x3 | pyautogui |

---

## Save App

| Step | Action | Selector |
|------|--------|----------|
| Click Save | `save_app()` | `//button[@aria-label='Save app']` |
| Dialog opens | Wait | - |
| Enter name | Type | `#name-input` → "AGENT: {id}" |
| Confirm | Click | Primary button in dialog |
| Get URL | `get_app_url()` | `driver.current_url` |
| Save URL | `save_agent_url()` | To `agents.json` |

---

## Init Message

`send_chat_message()` sends:

```
First, analyze core.txt to understand the full project context.

Then read your core_instructions.md file to understand your role.

You are {name}.
{description}

CRITICAL: Write ALL responses to output.md file, NOT in chat.

Format:
STATUS: [READY|PROCESSING|COMPLETE|ERROR]
TASK_ID: [task identifier]
RESULT: [your response]

Confirm by editing output.md with STATUS: READY.
```

---

## State After Spawn

| Storage | Before | After |
|---------|--------|-------|
| `agent_handles` | `{}` | `{"CTO-001": handle}` |
| `status` | inactive | **active** |
| `agents.json` | - | Contains URL |

---

## Error Handling

| Phase | Error | Action |
|-------|-------|--------|
| get_agent_skill | Not found | Return False |
| create_agent_zip | Failed | Return False |
| upload_zip | Failed | Return False |
| save_app | Failed | Continue (logged) |
| send_chat_message | Failed | Continue (logged) |

---

## Next: Part 9

Part 9 covers **Chat Flow**
