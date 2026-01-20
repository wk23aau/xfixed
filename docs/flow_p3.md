# XApply Flow - Part 3: Extension & Navigation

## Overview

| Part | Phases | Status |
|------|--------|--------|
| Part 1 | 1-2 | Done |
| Part 2 | 3-4 | Done |
| **Part 3** | 5-6 | **Extension and navigation** |
| Part 4 | 7-9 | Popups, tab monitor, login |
| Part 5 | 10-12 | Agents, Flask, ready |

---

## TODO / FIXES

> [!IMPORTANT]
> **Changes required in code**

| Item | Current | Change To | Status |
|------|---------|-----------|--------|
| Wait after extension | `time.sleep(5)` | **REMOVE** | TODO |
| Wait after navigation | `time.sleep(3)` | **Wait for element** | TODO |

---

## Phase 5: Extension Load

```mermaid
flowchart TD
    G10["Driver ready"] --> H1["Log CHROME waiting for extension"]
    H1 --> H2["Extension loads automatically"]
    H2 --> H3["Log CHROME extension loaded"]
    H3 --> H4{"Wait 5 seconds?"}
    H4 -->|REMOVE| H5["time.sleep 5"]
    H4 -->|Skip| H6["Continue immediately"]
    H5 --> H6["Extension ready"]

    style H2 fill:#4ade80,stroke:#16a34a
    style H4 fill:#fbbf24,stroke:#d97706
    style H5 fill:#ef4444,stroke:#dc2626
    style H6 fill:#4ade80,stroke:#16a34a
```

### Step-by-Step Explanation

| Step | What Happens | Log |
|------|--------------|-----|
| Extension loads | Chrome automatically loads extension from path | CHROME waiting |
| Extension ready | Extension scripts injected | CHROME loaded |
| Wait 5s | **REMOVE** - unnecessary delay | - |
| Continue | Proceed to navigation | - |

### Why Remove the 5s Wait?

| Reason | Explanation |
|--------|-------------|
| Unnecessary | Extension loads during Chrome startup |
| Slows startup | Adds 5 seconds to every launch |
| No benefit | No operations depend on this wait |

> **FIX**: Remove `time.sleep(5)` after extension load.

---

## Phase 6: Navigate to AI Studio

```mermaid
flowchart TD
    H6["Extension ready"] --> I1["Build AI Studio URL"]
    I1 --> I2["Base: aistudio.google.com"]
    I2 --> I3["Path: /apps/bundled/blank"]
    I3 --> I4["Param: showAssistant=true"]
    I4 --> I5["Param: showCode=true"]
    I5 --> I6["Full URL ready"]
    
    I6 --> I7["Log CHROME navigating"]
    I7 --> I8["driver.get URL"]
    I8 --> I9["Log CHROME navigation started"]
    I9 --> I10["Wait for page element"]
    I10 --> I11["Log CHROME page loaded"]

    style I1 fill:#60a5fa,stroke:#2563eb
    style I6 fill:#4ade80,stroke:#16a34a
    style I8 fill:#60a5fa,stroke:#2563eb
    style I10 fill:#4ade80,stroke:#16a34a
    style I11 fill:#4ade80,stroke:#16a34a
```

### AI Studio URL Construction

| Component | Value |
|-----------|-------|
| Base | `https://aistudio.google.com` |
| Path | `/apps/bundled/blank` |
| Param 1 | `?showAssistant=true` |
| Param 2 | `&showCode=true` |

**Full URL:**
```
https://aistudio.google.com/apps/bundled/blank?showAssistant=true&showCode=true
```

### Step-by-Step Explanation

| Step | Code | Purpose |
|------|------|---------|
| Build URL | String concatenation | Construct full URL |
| Navigate | `driver.get(url)` | Load the page |
| Wait for element | `WebDriverWait.until(element)` | Wait for page ready |
| Page loaded | Continue to popups | Ready for next phase |

### Wait for Element (Not Sleep)

| Old Way | New Way |
|---------|---------|
| `time.sleep(3)` | `wait.until(EC.presence_of_element_located(...))` |

> **FIX**: Replace `time.sleep(3)` with element wait. Faster and more reliable.

---

## Color Key

| Color | Meaning |
|-------|---------|
| Green | Success |
| Yellow | Decision |
| Red | Remove/Error |
| Blue | Action |

---

## Next: Part 4

Part 4 covers **Phase 7-9**: Popups, Tab Monitor, Login
