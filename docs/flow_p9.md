# XApply Flow - Part 9: Chat (Single Agent)

## Trigger

User types message and clicks **Send** in frontend.

---

## Complete Flow

```mermaid
flowchart TD
    subgraph Frontend["Frontend"]
        U1["User types message"] --> U2["User clicks Send"]
        U2 --> U3["Get selected agent ID"]
        U3 --> U4["POST /api/chat"]
    end

    subgraph Backend["Backend: /api/chat"]
        S1["Receive agent_id + message"] --> S2{"Agent active?"}
        S2 -->|No| S3["Return error: agent not active"]
        S2 -->|Yes| S4["Get handle from agent_handles"]
        
        S4 --> S5["Switch to agent tab"]
        S5 --> S6["Focus browser window"]
        S6 --> S7["Find chat input"]
        S7 --> S8["Clear input"]
        S8 --> S9["Paste message"]
        S9 --> S10["Find send button"]
        S10 --> S11["Click send"]
        S11 --> S12["Wait for response"]
        S12 --> S13["Read output.md"]
        S13 --> S14["Return response"]
    end

    U4 --> S1
    S3 --> U5["Show error"]
    S14 --> U6["Display response"]

    style U1 fill:#60a5fa,stroke:#2563eb
    style S2 fill:#fbbf24,stroke:#d97706
    style S3 fill:#ef4444,stroke:#dc2626
    style S5 fill:#4ade80,stroke:#16a34a
    style S11 fill:#60a5fa,stroke:#2563eb
    style S13 fill:#f97316,stroke:#ea580c
    style U6 fill:#4ade80,stroke:#16a34a
```

---

## Frontend Actions

| Step | Action |
|------|--------|
| 1 | User types message in chat input |
| 2 | User clicks Send button |
| 3 | Get currently selected agent ID |
| 4 | POST `/api/chat` with `{agent_id, message}` |
| 5 | Wait for response |
| 6 | Display response in chat UI |

---

## Backend Actions

### Phase 1: Validate Agent

| Step | Action |
|------|--------|
| Receive | `agent_id` and `message` from request |
| Check | Is agent in `agent_handles`? |
| If No | Return error: "Agent not active" |
| If Yes | Continue |

### Phase 2: Switch to Agent Tab

| Step | Action |
|------|--------|
| Get handle | `agent_handles[agent_id]` |
| Switch | `driver.switch_to.window(handle)` |
| Focus | `window.focus()` |

### Phase 3: Send Message

| Step | Action | Selector |
|------|--------|----------|
| Find chat input | Wait for textarea | `div.input-container textarea` |
| Click to focus | Activate input | Click element |
| Clear | Remove existing text | Ctrl+A, Delete |
| Paste message | Insert user message | Ctrl+V (clipboard) |
| Find send | Locate button | `button.send-button` |
| Click send | Submit message | Click element |

### Phase 4: Get Response

| Step | Action |
|------|--------|
| Wait | Agent processes message |
| Check output.md | Agent writes response to output.md |
| Read output.md | Get response content |
| Parse | Extract STATUS and RESULT |
| Return | Send response to frontend |

---

## output.md Format

Agent writes responses to `output.md`:

```markdown
STATUS: COMPLETE
TASK_ID: chat-001
RESULT: Here is my response to your question...
```

| Field | Values |
|-------|--------|
| STATUS | READY, PROCESSING, COMPLETE, ERROR |
| TASK_ID | Identifier for this task |
| RESULT | The actual response content |

---

## API Details

### Request

```
POST /api/chat
Content-Type: application/json

{
  "agent_id": "CTO-001",
  "message": "How should we structure the API?"
}
```

### Response (Success)

```json
{
  "success": true,
  "agent_id": "CTO-001",
  "response": "Here is my recommendation...",
  "status": "COMPLETE"
}
```

### Response (Error)

```json
{
  "success": false,
  "error": "Agent not active"
}
```

---

## Element Selectors

| Element | Selectors (with fallbacks) |
|---------|---------------------------|
| Chat container | `div.input-container`, `.chat-input`, `ms-autosize-textarea` |
| Textarea | `div.input-container textarea`, `ms-autosize-textarea textarea`, `textarea[placeholder*='message']` |
| Send button | `button.send-button`, `button[aria-label*='Send']`, `button[data-test-id='send-button']` |

---

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| Agent not active | Not in agent_handles | Return error |
| Tab switch failed | Handle invalid | Remove from handles, return error |
| Input not found | UI changed | Retry with fallbacks |
| Send failed | Button not found | Return error |
| Response timeout | Agent stuck | Return timeout error |

---

## State During Chat

| State | Value |
|-------|-------|
| Selected agent | User's choice in UI |
| Active tab | Switched to agent's tab |
| agent_handles | Unchanged |
| status | Unchanged (still active) |

---

## Next: Part 10

Part 10 covers **Broadcast Flow** - sending to all agents
