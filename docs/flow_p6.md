# XApply Flow - Part 6: Frontend Init & Status

## Overview

| Part | Phases | Status |
|------|--------|--------|
| Part 1-5 | 1-12 | Backend complete |
| **Part 6** | F1-F3 | **Frontend init, status** |
| Part 7 | F4-F5 | Roster, render |

---

## Frontend Startup Order

> [!IMPORTANT]
> **Backend MUST be running before frontend starts**

```
Backend ready on :5000
        ↓
npm run dev
        ↓  
Frontend starts on :5173
```

---

## Phase F1: Frontend Initialization

```mermaid
flowchart TD
    T1["npm run dev"] --> T2["Initialize Logger"]
    T2 --> T3["Log FRONTEND starting"]
    T3 --> T4["Read vite.config.ts"]
    T4 --> T5["Setup proxy /api to :5000"]
    T5 --> T6["Start Vite dev server"]
    T6 --> T7["Listen on :5173"]
    T7 --> T8["Log FRONTEND Vite ready"]

    style T1 fill:#60a5fa,stroke:#2563eb
    style T2 fill:#f97316,stroke:#ea580c
    style T7 fill:#4ade80,stroke:#16a34a
```

### What This Does

| Step | Purpose |
|------|---------|
| Initialize Logger | Setup console logging |
| Read config | Load vite.config.ts |
| Setup proxy | Forward /api/* to backend :5000 |
| Start Vite | Development server |
| Listen :5173 | Frontend port |

### Vite Proxy Configuration

```typescript
server: {
  proxy: {
    '^/api/': {
      target: 'http://127.0.0.1:5000',
      changeOrigin: true
    }
  }
}
```

> **WHY PROXY**: Frontend on :5173 can call /api/* which forwards to backend :5000.

---

## Phase F2: React Load

```mermaid
flowchart TD
    T8["Vite ready"] --> U1["Browser opens :5173"]
    U1 --> U2["Load index.html"]
    U2 --> U3["Load main.tsx"]
    U3 --> U4["Log FRONTEND React mounting"]
    U4 --> U5["Mount App component"]
    U5 --> U6["Log FRONTEND App mounted"]
    U6 --> U7["Trigger useEffect"]

    style U1 fill:#60a5fa,stroke:#2563eb
    style U5 fill:#4ade80,stroke:#16a34a
    style U7 fill:#fbbf24,stroke:#d97706
```

### What This Does

| Step | Purpose |
|------|---------|
| Browser opens | Navigate to localhost:5173 |
| Load index.html | Entry point |
| Load main.tsx | React entry |
| Mount App | Render root component |
| useEffect | Trigger API calls on mount |

---

## Phase F3: Status Check

```mermaid
flowchart TD
    U7["useEffect triggered"] --> V1["Call api.getStatus"]
    V1 --> V2["Log API requesting /api/status"]
    V2 --> V3["fetch /api/status"]
    V3 --> V4{"Response?"}
    
    V4 -->|200 OK| V5["Parse JSON"]
    V4 -->|Error| V10["Log ERROR connection failed"]
    
    V5 --> V6{"status ready?"}
    V6 -->|Yes| V7["Set state ONLINE"]
    V6 -->|No| V8["Set state WARNING"]
    V7 --> V9["Continue to roster"]
    V8 --> V9
    
    V10 --> V11["Set state OFFLINE"]
    V11 --> V12["Increment retry count"]
    V12 --> V13{"Retry under 3?"}
    V13 -->|Yes| V14["Wait 3 seconds"]
    V14 --> V1
    V13 -->|No| V15["Show error message"]

    style V4 fill:#fbbf24,stroke:#d97706
    style V7 fill:#4ade80,stroke:#16a34a
    style V10 fill:#ef4444,stroke:#dc2626
    style V15 fill:#ef4444,stroke:#dc2626
```

### Status Check Logic

| Response | Action |
|----------|--------|
| 200 OK, status ready | Set ONLINE |
| 200 OK, status not ready | Set WARNING |
| Error/timeout | Set OFFLINE, retry |

### Retry Logic

| Attempt | Action |
|---------|--------|
| 1 | Try → Fail → Wait 3s |
| 2 | Try → Fail → Wait 3s |
| 3 | Try → Fail → Show error |

> **MAX RETRIES**: 3 attempts before showing error to user.

### API Response Format

```json
{
  "status": "ready",
  "driver_initialized": true
}
```

---

## Error States

| State | UI Shows | Cause |
|-------|----------|-------|
| ONLINE | Green indicator | Backend ready |
| WARNING | Yellow indicator | Backend starting |
| OFFLINE | Red indicator | Backend not running |

---

## Color Key

| Color | Meaning |
|-------|---------|
| Green | Success |
| Yellow | Decision/Warning |
| Orange | Logging |
| Blue | Action |
| Red | Error |

---

## Next: Part 7

Part 7 covers **Phase F4-F5**: Load Roster, Render UI
