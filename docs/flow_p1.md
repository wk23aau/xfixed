# XApply Flow - Part 1: Initialization & Logging

## Overview

| Part | Phases | What Happens |
|------|--------|--------------|
| **Part 1** | 1-2 | Import modules, setup logging |
| Part 2 | 3-4 | Chrome setup and launch |
| Part 3 | 5-6 | Extension and navigation |
| Part 4 | 7-9 | Popups, tab monitor, login |
| Part 5 | 10-12 | Agents, Flask, ready |

---

## Phase 1: Initialization

```mermaid
flowchart TD
    A["python main.py"] --> A1["Import time, os, json"]
    A1 --> A2["Import threading, zipfile"]
    A2 --> A3["Import Flask, CORS"]
    A3 --> A4["Import dotenv"]
    A4 --> A5["Import undetected_chromedriver"]
    A5 --> A6["Import selenium"]
    
    A6 --> B1{"pyautogui installed?"}
    B1 -->|Yes| B2["Import pyautogui"]
    B1 -->|No| B3["WARNING: missing"]
    B2 --> B4{"pyperclip installed?"}
    B3 --> B4
    B4 -->|Yes| B5["Import pyperclip"]
    B4 -->|No| B6["WARNING: missing"]
    
    B5 --> C1["load_dotenv"]
    B6 --> C1
    C1 --> C2["Set stop_tab_monitor = False"]
    C2 --> C3["Set pause_tab_monitor = False"]
    C3 --> C4["Set driver_ref = None"]
    C4 --> C5["Set target_tab_handle = None"]
    C5 --> C6["Set agent_handles = empty dict"]
    C6 --> C7["Set SKILLS_PATH"]

    style A fill:#4ade80,stroke:#16a34a
    style B1 fill:#fbbf24,stroke:#d97706
    style B4 fill:#fbbf24,stroke:#d97706
    style B3 fill:#ef4444,stroke:#dc2626
    style B6 fill:#ef4444,stroke:#dc2626
    style C7 fill:#60a5fa,stroke:#2563eb
```

### Step-by-Step Explanation

| Step | What Happens | Why |
|------|--------------|-----|
| `python main.py` | Script starts | Entry point |
| Import standard libs | time, os, json, threading, zipfile | Basic Python utilities |
| Import Flask, CORS | Web framework | API server needs these |
| Import dotenv | Load .env file | Credentials stored in .env |
| Import chromedriver | undetected_chromedriver | Avoids bot detection |
| Import selenium | By, WebDriverWait, EC | Web automation |

### Required Dependencies

| Package | Purpose | If Missing |
|---------|---------|------------|
| `pyautogui` | Native dialogs, keyboard | **FAILS** - Cannot handle file dialogs |
| `pyperclip` | Clipboard paste | **FAILS** - Cannot paste credentials |

> **REQUIRED**: Both packages must be installed. Script will fail without them.

### Environment Variables (.env)

| Variable | Purpose | When Used |
|----------|---------|-----------|
| `GOOGLE_EMAIL` | Google account email | Auto-login if not logged in |
| `GOOGLE_PASSWORD` | Google account password | Auto-login if not logged in |

> **AUTO-LOGIN**: If no saved profile OR not logged in, script uses .env credentials to login automatically.

### Global Variables

| Variable | Initial Value | Purpose |
|----------|---------------|---------|
| `stop_tab_monitor` | False | Signal to stop monitor thread |
| `pause_tab_monitor` | False | Pause monitoring temporarily |
| `driver_ref` | None | Chrome driver reference |
| `target_tab_handle` | None | Main tab to protect |
| `agent_handles` | {} | Map agent ID to tab handle |
| `SKILLS_PATH` | .agent/skills | Where skill files are |

---

## Phase 2: Logging Setup

```mermaid
flowchart TD
    C7["SKILLS_PATH set"] --> L1["Initialize Logger"]
    L1 --> L2["Get logs directory path"]
    L2 --> L3{"logs/ exists?"}
    L3 -->|No| L4["Create logs/ directory"]
    L3 -->|Yes| L5
    L4 --> L5["Open xapply.log for append"]
    L5 --> L6["Write STARTUP timestamp"]
    L6 --> L7["Write system info"]
    L7 --> L8["Logger ready"]

    style L1 fill:#f97316,stroke:#ea580c
    style L5 fill:#f97316,stroke:#ea580c
    style L8 fill:#4ade80,stroke:#16a34a
    style L3 fill:#60a5fa,stroke:#2563eb
```

### Step-by-Step Explanation

| Step | What Happens | Log Entry |
|------|--------------|-----------|
| Initialize Logger | Create logger object | - |
| Get logs path | `./logs/` relative to backend | - |
| Check exists | Does logs/ folder exist? | - |
| Create if needed | `os.makedirs(logs, exist_ok=True)` | - |
| Open log file | Append mode to preserve history | - |
| Write STARTUP | `{"level": "INFO", "category": "STARTUP"}` | Timestamp, begin |
| Write system info | Python version, OS, cwd | Debug info |

### Logging Rules

| Output | Level | Content |
|--------|-------|---------|
| **File** (logs/xapply.log) | DEBUG | Everything - very detailed |
| **Terminal** | INFO | Important flow steps only |

### Log Format (JSON)

```json
{
  "timestamp": "2024-01-20T10:42:00Z",
  "level": "INFO",
  "category": "STARTUP",
  "message": "Backend starting",
  "data": {
    "python": "3.11.0",
    "os": "Windows",
    "cwd": "C:/Users/.../backend"
  }
}
```

---

## Color Key

| Color | Meaning |
|-------|---------|
| Green | Success / Start point |
| Yellow | Decision / Check |
| Red | Warning / Error path |
| Blue | Important check |
| Orange | Logging related |

---

## Next: Part 2

Part 2 covers **Phase 3-4**: Chrome Setup and Launch
