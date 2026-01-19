export interface AgentDefinition {
  id: string;
  name: string;
  description: string;
  category: string;
}

export interface ActiveAgent {
  url: string;
  created_at: string;
}

export type ActiveAgentMap = Record<string, ActiveAgent>;

// Backend returns roster as { "Category Name": [Agent1, Agent2], ... }
export type RosterResponse = Record<string, AgentDefinition[]>;

export interface SystemStatus {
  status: 'online' | 'offline';
  driver_initialized: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'system' | 'agent';
  content: string;
  timestamp: number;
}
