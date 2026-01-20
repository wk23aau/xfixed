# XApply - Critical Selectors Documentation

> [!CAUTION]
> **DO NOT MODIFY THESE SELECTORS WITHOUT EXTENSIVE TESTING**
> 
> These CSS/XPath selectors are the lifeline of XApply automation. They interact with Google AI Studio's UI, which can change without notice. Each selector was carefully tested and verified.

---

## Table of Contents

- [Chat Input Selectors](#chat-input-selectors)
- [Send Button Selectors](#send-button-selectors)
- [AI Processing Indicators](#ai-processing-indicators)
- [File Tree Selectors](#file-tree-selectors)
- [Monaco Editor Selectors](#monaco-editor-selectors)
- [Settings Panel Selectors](#settings-panel-selectors)
- [Model Selection Selectors](#model-selection-selectors)
- [System Instructions Selectors](#system-instructions-selectors)
- [File Upload Selectors](#file-upload-selectors)
- [Save App Selectors](#save-app-selectors)
- [Popup Dismissal Selectors](#popup-dismissal-selectors)

---

## Chat Input Selectors

| Selector | Element | Why It's Important |
|----------|---------|-------------------|
| `div.input-container textarea` | Chat textarea | Primary chat input field |
| `textarea[aria-label*='chat']` | Chat textarea | Fallback selector |
| `textarea.ms-textarea` | Chat textarea | Another fallback |
| `ms-autosize-textarea textarea` | Wrapped textarea | Component-based selector |

> [!WARNING]
> The chat textarea is inside an Angular component (`ms-autosize-textarea`). Direct `send_keys()` may not trigger Angular's change detection. We use JavaScript to set value:
> ```javascript
> arguments[0].value = arguments[1];
> arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
> arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
> ```

---

## Send Button Selectors

| Selector | State | Purpose |
|----------|-------|---------|
| `button.send-button:not([disabled])` | Ready to send | Click to send message |
| `button.send-button.running` | AI processing | Don't click, wait |
| `button.send-button[aria-label='Cancel']` | Cancel mode | AI is running |
| `button.send-button[disabled]` | Disabled | Empty input |

> [!IMPORTANT]
> Always check button state before clicking. The button cycles through states:
> 1. `disabled` → Empty input
> 2. `:not([disabled])` → Ready to send
> 3. `.running` / `aria-label='Cancel'` → AI processing
> 4. Back to `:not([disabled])` → AI finished

---

## AI Processing Indicators

| Selector | Meaning |
|----------|---------|
| `button.send-button.running` | AI is generating response |
| `ms-thinking-indicator` | "Thinking..." animation visible |
| `button.send-button[aria-label='Cancel']` | AI running, can cancel |
| `//div[contains(text(), 'Checkpoint')]` | AI finished writing to file |

> [!NOTE]
> We use WebDriverWait with a custom condition that checks ALL these indicators. The AI is "finished" when NONE of these are present OR when Checkpoint appears.

---

## File Tree Selectors

| Selector | Element | Purpose |
|----------|---------|---------|
| `ms-console-file-tree` | File tree container | Parent component |
| `mat-tree` | Tree widget | Angular Material tree |
| `mat-tree-node` | File/folder node | Each item in tree |
| `span.node-name` | Filename text | Contains "output.md" |

**To click a file:**
```python
file_nodes = driver.find_elements(By.CSS_SELECTOR, "mat-tree-node span.node-name")
for node in file_nodes:
    if node.text.strip().lower() == "output.md":
        parent = node.find_element(By.XPATH, "./ancestor::mat-tree-node")
        driver.execute_script("arguments[0].click();", parent)
```

> [!WARNING]
> Click the `mat-tree-node` (parent), NOT the `span.node-name` itself.

---

## Monaco Editor Selectors

| Selector | Element | Purpose |
|----------|---------|---------|
| `ms-console-editor` | Editor component | Wrapper |
| `div.monaco-editor` | Monaco container | Has `data-uri` attribute |
| `div.monaco-editor[data-uri*='output.md']` | Specific file open | Verify output.md is shown |
| `div.view-lines.monaco-mouse-cursor-text` | Content container | All visible lines |
| `div.view-line` | Single line | Each line of content |
| `span.mtk1, span.mtk8` | Token spans | Actual text within lines |

**To read content:**
```python
view_lines = driver.find_elements(By.CSS_SELECTOR, 
    "div.view-lines.monaco-mouse-cursor-text div.view-line")
lines = [line.text.strip() for line in view_lines if line.text.strip()]
content = "\n".join(lines)
```

---

## Settings Panel Selectors

| Selector | Element |
|----------|---------|
| `//button[contains(@aria-label, 'settings')]` | Open settings button |
| `//button[contains(@aria-label, 'Settings')]` | Alternative casing |

> [!IMPORTANT]
> The settings panel opens as a side drawer. Model selection and System Instructions are BOTH accessed via this panel.

---

## Model Selection Selectors

| Selector | Element |
|----------|---------|
| `mat-select[aria-label='Select the model for the code assistant']` | Model dropdown |
| `//mat-option[contains(., 'Gemini 3 Pro Preview')]` | Model option |

**Flow:**
1. Open settings panel
2. Click model dropdown (`mat-select`)
3. Click desired option (`mat-option`)
4. ESC to close (unless continuing to System Instructions)

---

## System Instructions Selectors

| Selector | Element |
|----------|---------|
| `button[data-test-id='instructions-button']` | System Instructions card |
| `#custom-si-textarea` | System instructions textarea |
| `//button[contains(@class, 'ms-button-primary') and contains(., 'Save changes')]` | Save button |

**Flow:**
1. Open settings panel (or reuse if already open)
2. Click System Instructions button
3. Focus textarea, clear, paste content
4. Click Save changes
5. ESC x3 to close all panels

> [!CAUTION]
> Use `pyperclip.copy()` + `pyautogui.hotkey('ctrl', 'v')` for pasting long content. `send_keys()` is too slow.

---

## File Upload Selectors

### Zip Upload (via Import App button)
| Selector | Element |
|----------|---------|
| `//button[@aria-label='Import app']` | Import app button (three dots menu) |
| `//button[contains(@class, 'menu') and contains(., 'Import from zip')]` | Menu item |
| Native file dialog | Handled via pyautogui |

### File Upload (via Upload files)
| Selector | Element |
|----------|---------|
| `//button[contains(@class, 'upload-button')]` | Upload button |
| `input[type='file']` | Hidden file input |
| Native file dialog | Handled via pyautogui |

> [!WARNING]
> File dialogs are OS-native. We use `pyautogui` for:
> - `Alt+N` to focus filename field
> - Type path
> - Enter to confirm

---

## Save App Selectors

| Selector | Element |
|----------|---------|
| `//button[@aria-label='Save app']` | Save button |
| `#name-input` | App name input in dialog |
| Primary button in dialog | Confirm save |

---

## Popup Dismissal Selectors

| Selector | Popup Type |
|----------|-----------|
| `button.glue-cookie-notification-bar__accept` | Cookie consent |
| `div.banner-container button.dismiss` | Terms of Service |

> [!NOTE]
> These popups appear on first visit. We dismiss them during startup.

---

## Key Implementation Notes

### 1. JavaScript Click vs Selenium Click
```python
# Use JavaScript click for reliable clicking through overlays
driver.execute_script("arguments[0].click();", element)

# NOT: element.click() - may fail if element is covered
```

### 2. Input Value Setting
```python
# For Angular inputs, must dispatch events:
driver.execute_script("""
    arguments[0].value = arguments[1];
    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
""", element, value)
```

### 3. Waiting for AI
```python
def ai_finished(driver):
    running = driver.find_elements(By.CSS_SELECTOR, "button.send-button.running")
    thinking = driver.find_elements(By.CSS_SELECTOR, "ms-thinking-indicator")
    cancel = driver.find_elements(By.CSS_SELECTOR, "button.send-button[aria-label='Cancel']")
    return not (running or thinking or cancel)

wait = WebDriverWait(driver, 120, poll_frequency=1)
wait.until(ai_finished)
```

### 4. Tab Monitor Pausing
Always pause the tab monitor during sensitive operations:
```python
pause_monitor()
try:
    # ... do work ...
finally:
    resume_monitor()
```

---

## Version History

| Date | Change |
|------|--------|
| 2026-01-20 | Initial documentation |
| 2026-01-20 | Added Monaco editor selectors |
| 2026-01-20 | Added WebDriverWait approach |

---

> [!CAUTION]
> **FINAL WARNING**
> 
> Google AI Studio is a rapidly evolving product. These selectors were valid as of January 2026. If automation breaks:
> 1. Open browser DevTools (F12)
> 2. Inspect the failing element
> 3. Update the selector in `main.py`
> 4. Test thoroughly before committing
> 
> **NEVER CHANGE SELECTORS WITHOUT CAPTURING NEW `selector.html` FOR REFERENCE**
