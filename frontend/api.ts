import { ActiveAgentMap, RosterResponse, SystemStatus } from './types';

const BASE_URL = '/api';

export const api = {
  async getStatus(): Promise<SystemStatus> {
    try {
      const res = await fetch(`${BASE_URL}/status`);
      if (!res.ok) throw new Error('Status fetch failed');
      return await res.json();
    } catch (e) {
      return { status: 'offline', driver_initialized: false };
    }
  },

  async getAgents(): Promise<ActiveAgentMap> {
    try {
      const res = await fetch(`${BASE_URL}/agents`);
      if (!res.ok) throw new Error('Agents fetch failed');
      return await res.json();
    } catch (e) {
      console.error(e);
      return {};
    }
  },

  async getRoster(): Promise<RosterResponse> {
    try {
      const res = await fetch(`${BASE_URL}/roster`);
      if (!res.ok) throw new Error('Roster fetch failed');
      return await res.json();
    } catch (e) {
      console.error(e);
      return {};
    }
  },

  async spawnAgent(agentId: string): Promise<boolean> {
    try {
      const res = await fetch(`${BASE_URL}/spawn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      });
      return res.ok;
    } catch (e) {
      console.error(e);
      return false;
    }
  },

  async chat(message: string): Promise<boolean> {
    try {
      const res = await fetch(`${BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      return res.ok;
    } catch (e) {
      console.error(e);
      return false;
    }
  }
};
