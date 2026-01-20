# XApply - Session Changelog (2026-01-20)

> All fixes and changes applied during this session

---

## Summary

| Category | Count |
|----------|-------|
| Bug Fixes | 8 |
| Refactors | 2 |
| Features | 1 |
| Documentation | 1 |

---

## Commits (in order)

### 1. `[34065be]` Chat Input and Logging Improvements

**Problem:** 
- Terminal flooded with `/api/status` and `/api/agents` polling requests
- `pyautogui.hotkey('ctrl', 'v')` typed to wrong window (OS focus issue)

**Fix:**
- Added `StatusFilter` to hide polling requests from terminal logs
- Replaced `pyautogui.hotkey` with JavaScript `setValue`:
```python
driver.execute_script("""
    arguments[0].value = arguments[1];
    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
""", chatbox, message)
```

---

### 2. `[5726ad8]` Read Response from output.md via Monaco Editor

**Problem:** Old selectors couldn't find AI response (looking for chat bubbles)

**Fix:** Read from Monaco editor instead:
1. Click `output.md` in file tree (`mat-tree-node span.node-name`)
2. Wait for editor to load (`div.monaco-editor[data-uri*='output.md']`)
3. Read from `div.view-lines div.view-line`

---

### 3. `[c6f718d]` Improved Wait Logic for AI Response

**Problem:** Only checking running/thinking indicators

**Fix:** Added multiple checks:
- `button.send-button.running`
- `ms-thinking-indicator`
- `button.send-button[aria-label='Cancel']`
- `button.send-button[disabled]`

---

### 4. `[152214e]` Save Agent URL Only After First AI Response

**Problem:** URL saved before confirming agent works

**Fix:**
- `spawn_agent`: Set status to `"spawning"`, don't save drive_url
- `send_chat_message`: After first response, check if status is `"spawning"` → save URL and mark `"active"`

---

### 5. `[8d0df83]` Add /api/deactivate Endpoint

**Problem:** Frontend couldn't close agents (endpoint missing)

**Fix:** Added new endpoint:
```python
@app.route('/api/deactivate', methods=['POST'])
def api_deactivate():
    # Close browser tab
    # Remove from agent_handles
    # Update DB status to 'inactive'
```

---

### 6. `[7e84ddd]` Improve /api/deactivate with Better Error Handling

**Problem:** Deactivate returning 500 errors

**Fix:**
- Added `pause_monitor()` / `resume_monitor()`
- Tab close errors are non-fatal (continue to update DB)
- Always update DB to `inactive`
- Added detailed logging

---

### 7. `[6c35ca4]` P8 Spawn Improvements

**Issue 1 - Tab Navigation:**
- First agent: Navigate in current tab
- Subsequent agents: Open new tab then navigate

```python
is_first_agent = len(agent_handles) == 0
if is_first_agent:
    driver.get(saved_url)  # Use current tab
else:
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(saved_url)
```

**Issue 2 - Settings Panel:**
- Added `skip_close` param to `select_model()`
- Added `skip_open` param to `set_system_instructions()`
- Panel opens once instead of twice

---

### 8. `[34597fc]` Wait for AI to Finish Before Reading output.md

**Problem:** Reading stale content from zip template

**Fix:**
- Increased wait loop to 60 attempts (2 minutes)
- Added logging to show wait status
- Check for Checkpoint indicator

---

### 9. `[92b9376]` Event-Driven AI Wait Using WebDriverWait

**Problem:** Polling every 2 seconds is inefficient

**Fix:** Replaced polling with WebDriverWait:
```python
def ai_finished(driver):
    running = driver.find_elements(By.CSS_SELECTOR, "button.send-button.running")
    thinking = driver.find_elements(By.CSS_SELECTOR, "ms-thinking-indicator")
    cancel = driver.find_elements(By.CSS_SELECTOR, "button.send-button[aria-label='Cancel']")
    return not (running or thinking or cancel)

wait = WebDriverWait(driver, 120, poll_frequency=1)
wait.until(ai_finished)
```

---

### 10. `[5751744]` Correct Spawn Order

**Problem:** `upload_zip` running while settings panel still open

**Fix:** Reordered calls:
1. `select_model(skip_close=True)` - Opens panel
2. `set_system_instructions(skip_open=True)` - Uses panel, closes it
3. `upload_zip` - Panel now closed
4. `upload_files`
5. `save_app`

---

### 11. `[00552cc]` Add Comprehensive Documentation

**Added:**
- `docs/README.md` - Architecture overview
- `docs/SELECTORS.md` - All critical selectors with warnings
- `docs/flow_p1.md` through `docs/flow_p9.md` - Implementation phases

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/main.py` | All core fixes |
| `docs/README.md` | New |
| `docs/SELECTORS.md` | New |
| `docs/flow_p*.md` | Copied 9 files |

---

## Testing Checklist

- [ ] Spawn first agent → navigates in current tab
- [ ] Spawn second agent → opens new tab
- [ ] Settings panel opens once (not twice)
- [ ] Deactivate closes tab and updates DB
- [ ] Chat waits for AI to finish
- [ ] Response captured from output.md correctly
- [ ] URL saved after first response

---

## Next Steps

1. Test full spawn → chat → deactivate cycle
2. Test reactivation from saved URL
3. Monitor for any UI changes in AI Studio
