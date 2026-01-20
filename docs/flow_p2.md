# XApply Flow - Part 2: Chrome Setup & Launch

## Overview

| Part | Phases | Status |
|------|--------|--------|
| Part 1 | 1-2 | Done |
| **Part 2** | 3-4 | **Chrome setup and launch** |
| Part 3 | 5-6 | Extension and navigation |
| Part 4 | 7-9 | Popups, tab monitor, login |
| Part 5 | 10-12 | Agents, Flask, ready |

---

## TODO / FIXES

> [!IMPORTANT]
> **Changes required in code**

| Item | Current | Change To | Status |
|------|---------|-----------|--------|
| WebDriverWait | 30s | **5s** | TODO |

---

## Phase 3: Chrome Setup

```mermaid
flowchart TD
    L8["Logger ready"] --> D1["Create ChromeOptions"]
    D1 --> D2["Get extension path"]
    D2 --> D3["abspath: ../extension"]
    D3 --> D4["Log CHROME extension path"]
    
    D4 --> D5["Get profile path"]
    D5 --> D6["abspath: ../chrome_profile"]
    D6 --> D7["Log CHROME profile path"]
    
    D7 --> E1{"Profile directory exists?"}
    E1 -->|Yes| E2["Load saved session"]
    E1 -->|No| E3["Fresh Chrome instance"]
    
    E2 --> E4["Log PROFILE exists"]
    E3 --> E5["Log PROFILE not found"]
    
    E4 --> F1["add_argument: load-extension"]
    E5 --> F1
    F1 --> F2["add_argument: user-data-dir"]
    F2 --> F3["add_argument: no-first-run"]
    F3 --> F4["add_argument: no-default-browser-check"]
    F4 --> F5["Options complete"]

    style D1 fill:#60a5fa,stroke:#2563eb
    style E1 fill:#fbbf24,stroke:#d97706
    style E2 fill:#4ade80,stroke:#16a34a
    style E3 fill:#f97316,stroke:#ea580c
    style F5 fill:#4ade80,stroke:#16a34a
```

### Step-by-Step Explanation

| Step | Code | Purpose |
|------|------|---------|
| Create options | `uc.ChromeOptions()` | Container for Chrome settings |
| Extension path | `os.path.abspath("../extension")` | Browser extension location |
| Profile path | `os.path.abspath("../chrome_profile")` | Saved session location |
| Check profile | `os.path.exists(profile_path)` | Determine if session saved |

### Chrome Arguments

| Argument | Purpose |
|----------|---------|
| `--load-extension={path}` | Load our extension into Chrome |
| `--user-data-dir={path}` | Use saved profile for session |
| `--no-first-run` | Skip Chrome first-run wizard |
| `--no-default-browser-check` | Skip default browser popup |

### Profile Check Logic

| Profile Exists | What Happens |
|----------------|--------------|
| **Yes** | Load cookies, session, login state |
| **No** | Fresh Chrome, must login |

> **KEY**: Saved profile means faster startup - no login needed.

---

## Phase 4: Chrome Launch

```mermaid
flowchart TD
    F5["Options complete"] --> G1["Log CHROME launching"]
    G1 --> G2["driver = uc.Chrome"]
    G2 --> G3{"Launch successful?"}
    
    G3 -->|Yes| G4["Log CHROME launched OK"]
    G3 -->|No| G5["Log ERROR launch failed"]
    
    G5 --> G6["Print error message"]
    G6 --> G7["Exit code 1"]
    
    G4 --> G8["driver_ref = driver"]
    G8 --> G9["Create WebDriverWait 5s"]
    G9 --> G10["Log CHROME driver ready"]

    style G2 fill:#60a5fa,stroke:#2563eb
    style G3 fill:#fbbf24,stroke:#d97706
    style G4 fill:#4ade80,stroke:#16a34a
    style G5 fill:#ef4444,stroke:#dc2626
    style G7 fill:#ef4444,stroke:#dc2626
    style G10 fill:#4ade80,stroke:#16a34a
```

### Step-by-Step Explanation

| Step | Code | Purpose |
|------|------|---------|
| Launch Chrome | `uc.Chrome(options=options)` | Start browser with settings |
| Check success | try/except block | Catch launch failures |
| Store reference | `driver_ref = driver` | Global access to driver |
| Create wait | `WebDriverWait(driver, 5)` | 5 second timeout for waits |

### Launch Errors

| Error | Cause | Action |
|-------|-------|--------|
| ChromeDriver not found | Missing chromedriver | Exit |
| Chrome not installed | No Chrome browser | Exit |
| Profile locked | Another Chrome using profile | Exit |
| Extension invalid | Bad extension path | Exit |

> **CRITICAL**: Any launch error = script exits. Cannot continue without Chrome.

---

## Error Handling

```mermaid
flowchart TD
    E1["Launch attempt"] --> E2{"Exception?"}
    E2 -->|No| E3["Continue to Phase 5"]
    E2 -->|Yes| E4["Log ERROR"]
    E4 --> E5["Print traceback"]
    E5 --> E6["Exit 1"]

    style E2 fill:#fbbf24,stroke:#d97706
    style E3 fill:#4ade80,stroke:#16a34a
    style E6 fill:#ef4444,stroke:#dc2626
```

---

## Color Key

| Color | Meaning |
|-------|---------|
| Green | Success |
| Yellow | Decision |
| Red | Error/Exit |
| Blue | Action |
| Orange | First-time path |

---

## Next: Part 3

Part 3 covers **Phase 5-6**: Extension Load and Navigate to AI Studio
