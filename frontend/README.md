# Frontend - XAGENT Dashboard

## Your Domain

This folder is for the **frontend application**. You have full creative control here.

### Tech Stack (Recommended)

- **Vite + React + TypeScript**
- **Tailwind CSS** or vanilla CSS
- **Lucide React** for icons

### Setup

```bash
npm create vite@latest . -- --template react-ts
npm install
npm run dev
```

### Backend API

The backend runs on `http://127.0.0.1:5000`. Configure Vite proxy in `vite.config.ts`:

```ts
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:5000'
    }
  }
})
```

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | `{status: "online"/"offline", driver_initialized: bool}` |
| `/api/agents` | GET | `{agent_id: {url, created_at}, ...}` |
| `/api/roster` | GET | `{category: [{id, name, description}, ...], ...}` |
| `/api/spawn` | POST | Body: `{agent_id: "CTO-001"}` |
| `/api/chat` | POST | Body: `{message: "..."}` |

---

## ⚠️ IMPORTANT

### DO NOT touch the backend

The `../backend/main.py` contains **carefully curated selectors** for Google AI Studio automation. These are:

- Specific to AI Studio's current UI
- Discovered through extensive testing
- Fragile and should not be changed

If you need new API functionality, **request it** from the backend team.

### Your Responsibilities

✅ Build beautiful UI  
✅ Call API endpoints  
✅ Handle loading/error states  
✅ Implement responsive design  

❌ Do NOT modify `../backend/main.py`  
❌ Do NOT change selectors or timing  
❌ Do NOT add Flask routes yourself  
