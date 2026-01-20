
import { ActiveAgentMap, ParseResult, RosterResponse, SystemStatus, UploadedFile } from './types';

const API_BASE = '/api';

export const api = {
  getStatus: async (): Promise<SystemStatus> => {
    try {
      const res = await fetch(`${API_BASE}/status`);
      return await res.json();
    } catch (e) {
      return { status: 'offline', driver_initialized: false };
    }
  },

  getRoster: async (): Promise<RosterResponse> => {
    try {
      const res = await fetch(`${API_BASE}/roster`);
      return await res.json();
    } catch (e) {
      console.error(e);
      return {};
    }
  },

  getAgents: async (): Promise<ActiveAgentMap> => {
    try {
      const res = await fetch(`${API_BASE}/agents`);
      return await res.json();
    } catch (e) {
      return {};
    }
  },

  spawnAgent: async (agentId: string): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/spawn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      });
      return res.ok;
    } catch (e) {
      return false;
    }
  },

  deactivateAgent: async (agentId: string): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/deactivate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      });
      return res.ok;
    } catch (e) {
      return false;
    }
  },

  chat: async (message: string, agentId?: string): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, agent_id: agentId }),
      });
      return res.ok;
    } catch (e) {
      return false;
    }
  },

  getFiles: async (): Promise<UploadedFile[]> => {
    try {
      const res = await fetch(`${API_BASE}/files`);
      return await res.json();
    } catch (e) {
      return [];
    }
  },

  uploadFile: async (file: File): Promise<UploadedFile | null> => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });
      if (res.ok) return await res.json();
      return null;
    } catch (e) {
      return null;
    }
  },

  deleteFile: async (filename: string): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/delete-file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename }),
      });
      return res.ok;
    } catch (e) {
      return false;
    }
  },

  parseFile: async (filename: string): Promise<ParseResult | null> => {
    try {
      const res = await fetch(`${API_BASE}/parse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename }),
      });
      if (res.ok) return await res.json();
      return null;
    } catch (e) {
      return null;
    }
  }
};
