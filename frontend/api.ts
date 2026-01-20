
import { ActiveAgentMap, ParseResult, RosterResponse, SystemStatus, UploadedFile } from './types';

const API_BASE = '/api';

// Debug helper - logs all API calls with timing
const debugLog = (method: string, endpoint: string, data?: any, response?: any, error?: any) => {
  const timestamp = new Date().toISOString();
  console.group(`🔍 [API] ${method} ${endpoint}`);
  console.log('⏰ Time:', timestamp);
  if (data) console.log('📤 Request:', data);
  if (response) console.log('📥 Response:', response);
  if (error) console.error('❌ Error:', error);
  console.groupEnd();
  debugger; // BREAKPOINT: API call complete
};

export const api = {
  getStatus: async (): Promise<SystemStatus> => {
    debugger; // BREAKPOINT: getStatus start
    console.log('[API] getStatus: Starting request');
    const startTime = performance.now();
    try {
      console.log('[API] getStatus: Fetching /api/status');
      const res = await fetch(`${API_BASE}/status`);
      console.log('[API] getStatus: Response status:', res.status);
      debugger; // BREAKPOINT: getStatus response received
      const data = await res.json();
      console.log('[API] getStatus: Parsed data:', data);
      debugLog('GET', '/status', null, data);
      console.log(`[API] getStatus: Completed in ${(performance.now() - startTime).toFixed(2)}ms`);
      return data;
    } catch (e) {
      debugger; // BREAKPOINT: getStatus error
      console.error('[API] getStatus: ERROR:', e);
      debugLog('GET', '/status', null, null, e);
      return { status: 'offline', driver_initialized: false };
    }
  },

  getRoster: async (): Promise<RosterResponse> => {
    debugger; // BREAKPOINT: getRoster start
    console.log('[API] getRoster: Starting request');
    const startTime = performance.now();
    try {
      console.log('[API] getRoster: Fetching /api/roster');
      const res = await fetch(`${API_BASE}/roster`);
      console.log('[API] getRoster: Response status:', res.status);
      debugger; // BREAKPOINT: getRoster response received
      const data = await res.json();
      console.log('[API] getRoster: Categories:', Object.keys(data));
      console.log('[API] getRoster: Total agents:', Object.values(data).flat().length);
      debugLog('GET', '/roster', null, data);
      console.log(`[API] getRoster: Completed in ${(performance.now() - startTime).toFixed(2)}ms`);
      return data;
    } catch (e) {
      debugger; // BREAKPOINT: getRoster error
      console.error('[API] getRoster: ERROR:', e);
      debugLog('GET', '/roster', null, null, e);
      return {};
    }
  },

  getAgents: async (): Promise<ActiveAgentMap> => {
    debugger; // BREAKPOINT: getAgents start
    console.log('[API] getAgents: Starting request');
    try {
      const res = await fetch(`${API_BASE}/agents`);
      console.log('[API] getAgents: Response status:', res.status);
      debugger; // BREAKPOINT: getAgents response received
      const data = await res.json();
      console.log('[API] getAgents: Active agents:', Object.keys(data));
      debugLog('GET', '/agents', null, data);
      return data;
    } catch (e) {
      debugger; // BREAKPOINT: getAgents error
      console.error('[API] getAgents: ERROR:', e);
      return {};
    }
  },

  spawnAgent: async (agentId: string): Promise<boolean> => {
    debugger; // BREAKPOINT: spawnAgent start
    console.log('[API] spawnAgent: Starting spawn for:', agentId);
    console.log('[API] spawnAgent: Request payload:', { agent_id: agentId });
    const startTime = performance.now();
    try {
      console.log('[API] spawnAgent: POSTing to /api/spawn');
      debugger; // BREAKPOINT: spawnAgent sending request
      const res = await fetch(`${API_BASE}/spawn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      });
      console.log('[API] spawnAgent: Response status:', res.status);
      console.log('[API] spawnAgent: Response ok:', res.ok);
      debugger; // BREAKPOINT: spawnAgent response received
      debugLog('POST', '/spawn', { agent_id: agentId }, { ok: res.ok });
      console.log(`[API] spawnAgent: Completed in ${(performance.now() - startTime).toFixed(2)}ms`);
      return res.ok;
    } catch (e) {
      debugger; // BREAKPOINT: spawnAgent error
      console.error('[API] spawnAgent: ERROR:', e);
      debugLog('POST', '/spawn', { agent_id: agentId }, null, e);
      return false;
    }
  },

  deactivateAgent: async (agentId: string): Promise<boolean> => {
    debugger; // BREAKPOINT: deactivateAgent start
    console.log('[API] deactivateAgent: Deactivating:', agentId);
    try {
      console.log('[API] deactivateAgent: POSTing to /api/deactivate');
      debugger; // BREAKPOINT: deactivateAgent sending request
      const res = await fetch(`${API_BASE}/deactivate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      });
      console.log('[API] deactivateAgent: Response status:', res.status);
      debugger; // BREAKPOINT: deactivateAgent response received
      debugLog('POST', '/deactivate', { agent_id: agentId }, { ok: res.ok });
      return res.ok;
    } catch (e) {
      debugger; // BREAKPOINT: deactivateAgent error
      console.error('[API] deactivateAgent: ERROR:', e);
      return false;
    }
  },

  chat: async (message: string, agentId?: string): Promise<{
    success: boolean,
    response?: string,
    broadcast?: boolean,
    results?: Record<string, { success: boolean, response?: string, error?: string }>
  }> => {
    debugger; // BREAKPOINT: chat start
    console.log('[API] chat: Starting chat');
    console.log('[API] chat: Message:', message.substring(0, 100) + (message.length > 100 ? '...' : ''));
    console.log('[API] chat: Target agent:', agentId || 'BROADCAST');
    console.log('[API] chat: Message length:', message.length);
    const startTime = performance.now();
    try {
      console.log('[API] chat: POSTing to /api/chat');
      debugger; // BREAKPOINT: chat sending request
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, agent_id: agentId }),
      });
      console.log('[API] chat: Response status:', res.status);
      console.log('[API] chat: Response ok:', res.ok);
      debugger; // BREAKPOINT: chat response received

      const data = await res.json();
      console.log('[API] chat: Response data:', data);
      debugLog('POST', '/chat', { message: message.substring(0, 50), agent_id: agentId }, data);
      console.log(`[API] chat: Completed in ${(performance.now() - startTime).toFixed(2)}ms`);

      // P10: Handle broadcast response format
      if (data.broadcast) {
        console.log('[API] chat: BROADCAST response detected');
        console.log('[API] chat: Success:', data.success_count, '/', data.total);
        return {
          success: res.ok,
          broadcast: true,
          results: data.results
        };
      }

      // Single agent response
      return {
        success: res.ok,
        response: data.response || null
      };
    } catch (e) {
      debugger; // BREAKPOINT: chat error
      console.error('[API] chat: ERROR:', e);
      debugLog('POST', '/chat', { message, agent_id: agentId }, null, e);
      return { success: false };
    }
  },

  getFiles: async (): Promise<UploadedFile[]> => {
    debugger; // BREAKPOINT: getFiles start
    console.log('[API] getFiles: Starting request');
    try {
      const res = await fetch(`${API_BASE}/files`);
      console.log('[API] getFiles: Response status:', res.status);
      debugger; // BREAKPOINT: getFiles response received
      const data = await res.json();
      console.log('[API] getFiles: Files count:', data.length);
      console.log('[API] getFiles: File names:', data.map((f: any) => f.filename));
      debugLog('GET', '/files', null, data);
      return data;
    } catch (e) {
      debugger; // BREAKPOINT: getFiles error
      console.error('[API] getFiles: ERROR:', e);
      return [];
    }
  },

  uploadFile: async (file: File): Promise<UploadedFile | null> => {
    debugger; // BREAKPOINT: uploadFile start
    console.log('[API] uploadFile: Starting upload');
    console.log('[API] uploadFile: File name:', file.name);
    console.log('[API] uploadFile: File size:', file.size, 'bytes');
    console.log('[API] uploadFile: File type:', file.type);
    const startTime = performance.now();
    const formData = new FormData();
    formData.append('file', file);
    console.log('[API] uploadFile: FormData created');
    try {
      console.log('[API] uploadFile: POSTing to /api/upload');
      debugger; // BREAKPOINT: uploadFile sending request
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });
      console.log('[API] uploadFile: Response status:', res.status);
      debugger; // BREAKPOINT: uploadFile response received
      if (res.ok) {
        const data = await res.json();
        console.log('[API] uploadFile: Upload successful:', data);
        debugLog('POST', '/upload', { filename: file.name, size: file.size }, data);
        console.log(`[API] uploadFile: Completed in ${(performance.now() - startTime).toFixed(2)}ms`);
        return data;
      }
      console.warn('[API] uploadFile: Upload failed, response not ok');
      debugger; // BREAKPOINT: uploadFile failed
      return null;
    } catch (e) {
      debugger; // BREAKPOINT: uploadFile error
      console.error('[API] uploadFile: ERROR:', e);
      debugLog('POST', '/upload', { filename: file.name }, null, e);
      return null;
    }
  },

  deleteFile: async (filename: string): Promise<boolean> => {
    debugger; // BREAKPOINT: deleteFile start
    console.log('[API] deleteFile: Deleting:', filename);
    try {
      console.log('[API] deleteFile: POSTing to /api/delete-file');
      debugger; // BREAKPOINT: deleteFile sending request
      const res = await fetch(`${API_BASE}/delete-file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename }),
      });
      console.log('[API] deleteFile: Response status:', res.status);
      debugger; // BREAKPOINT: deleteFile response received
      debugLog('POST', '/delete-file', { filename }, { ok: res.ok });
      return res.ok;
    } catch (e) {
      debugger; // BREAKPOINT: deleteFile error
      console.error('[API] deleteFile: ERROR:', e);
      return false;
    }
  },

  parseFile: async (filename: string): Promise<ParseResult | null> => {
    debugger; // BREAKPOINT: parseFile start
    console.log('[API] parseFile: Parsing:', filename);
    const startTime = performance.now();
    try {
      console.log('[API] parseFile: POSTing to /api/parse');
      debugger; // BREAKPOINT: parseFile sending request
      const res = await fetch(`${API_BASE}/parse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename }),
      });
      console.log('[API] parseFile: Response status:', res.status);
      debugger; // BREAKPOINT: parseFile response received
      if (res.ok) {
        const data = await res.json();
        console.log('[API] parseFile: Parse successful');
        console.log('[API] parseFile: Text length:', data.text?.length || 0);
        debugLog('POST', '/parse', { filename }, { length: data.text?.length });
        console.log(`[API] parseFile: Completed in ${(performance.now() - startTime).toFixed(2)}ms`);
        return data;
      }
      console.warn('[API] parseFile: Parse failed');
      debugger; // BREAKPOINT: parseFile failed
      return null;
    } catch (e) {
      debugger; // BREAKPOINT: parseFile error
      console.error('[API] parseFile: ERROR:', e);
      debugLog('POST', '/parse', { filename }, null, e);
      return null;
    }
  }
};
