
export interface SystemStatus {
  status: 'online' | 'offline';
  driver_initialized: boolean;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
}

export interface ActiveAgent {
  url: string;
  created_at: string;
}

export interface ActiveAgentMap {
  [id: string]: ActiveAgent;
}

export interface RosterResponse {
  [category: string]: Agent[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  timestamp: number;
  agentId?: string; // Which agent sent this or was targeted
}

export interface UploadedFile {
  filename: string;
  size: number;
  type: string;
}

export interface ParseResult {
  filename: string;
  text: string;
  length: number;
}
