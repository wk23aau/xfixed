# Backend - XAGENT Automation Engine

## ⚠️ CRITICAL: DO NOT MODIFY

This backend contains **carefully curated** Selenium automation logic with specific CSS selectors and XPaths that work with Google AI Studio.

### Files

| File | Purpose |
|------|---------|
| `main.py` | Core automation engine (802 lines) |
| `agents.json` | Spawned agent registry |

### Why You Should NOT Touch This

1. **Selectors are battle-tested** - Each CSS selector and XPath was discovered through trial and error with AI Studio's UI
2. **Timing is critical** - Sleep durations are calibrated for UI animations
3. **Native dialog handling** - Uses pyautogui for Windows file dialogs which is fragile
4. **Multi-strategy fallbacks** - Functions try multiple selector strategies

### For Frontend Engineers

- Use the **API endpoints only** - don't modify the automation logic
- If you need a new endpoint, **request it** rather than adding it yourself
- All selectors in `main.py` are **off-limits**

### Running

```bash
cd backend
python main.py
```

Server runs on `http://127.0.0.1:5000`

### API Endpoints (Use These)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/agents` | GET | List spawned agents |
| `/api/roster` | GET | All available agents by category |
| `/api/spawn` | POST | Spawn an agent `{agent_id: "..."}` |
| `/api/chat` | POST | Send message `{message: "..."}` |
