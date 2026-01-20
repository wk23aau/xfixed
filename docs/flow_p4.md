# XApply Flow - Part 4: Popups, Tab Monitor, Login

## Overview

| Part | Phases | Status |
|------|--------|--------|
| Part 1 | 1-2 | Done |
| Part 2 | 3-4 | Done |
| Part 3 | 5-6 | Done |
| **Part 4** | 7-9 | **Popups, tab monitor, login** |
| Part 5 | 10-12 | Agents, Flask, ready |

---

## TODO / FIXES

> [!IMPORTANT]
> **Changes required in code**

| Item | Current | Change To | Status |
|------|---------|-----------|--------|
| Tab monitor | Always runs | **First time only** | TODO |

---

## Phase 7: Dismiss Popups

```mermaid
flowchart TD
    I11["Page loaded"] --> J1{"Cookie banner?"}
    J1 -->|Yes| J2["Find Disagree button"]
    J1 -->|No| J4
    J2 --> J3["Click Disagree"]
    J3 --> J4["Log POPUP cookie dismissed"]
    
    J4 --> J5{"ToS banner?"}
    J5 -->|Yes| J6["Find Dismiss button"]
    J5 -->|No| J8
    J6 --> J7["Click Dismiss"]
    J7 --> J8["Log POPUP ToS dismissed"]
    J8 --> J9["Popups cleared"]

    style J1 fill:#fbbf24,stroke:#d97706
    style J5 fill:#fbbf24,stroke:#d97706
    style J3 fill:#4ade80,stroke:#16a34a
    style J7 fill:#4ade80,stroke:#16a34a
    style J9 fill:#4ade80,stroke:#16a34a
```

### Popups to Handle

| Banner | Button | Selector |
|--------|--------|----------|
| Cookie consent | **Disagree** | Button text or aria-label |
| Terms of Service | **Dismiss** | Button text |

### Step-by-Step

| Step | Action | Log |
|------|--------|-----|
| Check cookie banner | Look for consent message | - |
| Click Disagree | Dismiss cookie popup | POPUP dismissed |
| Check ToS banner | Look for ToS notice | - |
| Click Dismiss | Dismiss ToS popup | POPUP dismissed |

> **NOTE**: Popups may not appear if profile has accepted before.

---

## Phase 8: Tab Monitor (First Time Only)

```mermaid
flowchart TD
    J9["Popups cleared"] --> K1{"Profile existed?"}
    K1 -->|No - First time| K2["Log TAB starting monitor"]
    K1 -->|Yes - Has profile| K3["Skip monitor"]
    
    K2 --> K4["Set driver_ref"]
    K4 --> K5["Get current_window_handle"]
    K5 --> K6["Set target_tab_handle"]
    K6 --> K7["Create daemon thread"]
    K7 --> K8["Start tab_monitor"]
    K8 --> K9["Log TAB monitor running"]
    
    K3 --> K10["Continue"]
    K9 --> K10

    style K1 fill:#fbbf24,stroke:#d97706
    style K2 fill:#f97316,stroke:#ea580c
    style K3 fill:#4ade80,stroke:#16a34a
    style K10 fill:#4ade80,stroke:#16a34a
```

### When to Run Tab Monitor

| Scenario | Run Monitor? | Why |
|----------|--------------|-----|
| **First time** (no profile) | Yes | Close unwanted tabs during login |
| **Has profile** | No | Session clean, save memory |

### Tab Monitor Purpose

| What it Does | Why |
|--------------|-----|
| Loops every 0.5s | Check for new tabs |
| Detects unwanted tabs | Microsoft, Adobe, etc |
| Closes unwanted tabs | Keep browser clean |
| Protects target tab | Never close main tab |

### Memory Concern

> **WARNING**: Tab monitor runs continuously and consumes memory. Only run when needed (first time).

---

## Phase 9: Login Check

```mermaid
flowchart TD
    K10["Continue"] --> L1["Get current_url"]
    L1 --> L2["Log LOGIN checking"]
    L2 --> L3{"URL contains accounts.google.com?"}
    
    L3 -->|Yes| L4["Log LOGIN required"]
    L3 -->|No| L20["Log LOGIN already authenticated"]
    
    L4 --> L5["Wait for email field"]
    L5 --> L6["Enter GOOGLE_EMAIL from .env"]
    L6 --> L7["Log LOGIN email entered"]
    L7 --> L8["Click Next"]
    
    L8 --> L9["Wait for password field"]
    L9 --> L10["Enter GOOGLE_PASSWORD from .env"]
    L10 --> L11["Log LOGIN password entered"]
    L11 --> L12["Click Next"]
    
    L12 --> L13["Wait for redirect"]
    L13 --> L14["Log LOGIN successful"]
    L14 --> L20

    style L3 fill:#fbbf24,stroke:#d97706
    style L4 fill:#f97316,stroke:#ea580c
    style L14 fill:#4ade80,stroke:#16a34a
    style L20 fill:#4ade80,stroke:#16a34a
```

### Login Decision

| URL Check | Result |
|-----------|--------|
| Contains `accounts.google.com` | Need to login |
| Is AI Studio URL | Already logged in |

### Auto-Login Flow

| Step | Action | Data Source |
|------|--------|-------------|
| **Keep tab focused** | Ensure login tab stays active | - |
| Enter email | Type into email field | `GOOGLE_EMAIL` from .env |
| Click Next | Submit email | - |
| Enter password | Type into password field | `GOOGLE_PASSWORD` from .env |
| Click Next | Submit login | - |
| Wait redirect | Back to AI Studio | - |

> [!IMPORTANT]
> **Keep login tab focused** until login completes. Do not switch tabs during login.

### Required .env Variables

```
GOOGLE_EMAIL=your.email@gmail.com
GOOGLE_PASSWORD=your_password
```

> **SECURITY**: Never commit .env to git. Add to .gitignore.

---

## Color Key

| Color | Meaning |
|-------|---------|
| Green | Success / Skip |
| Yellow | Decision |
| Orange | First-time only |
| Blue | Action |

---

## Next: Part 5

Part 5 covers **Phase 10-12**: Agents, Flask, Ready
