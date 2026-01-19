import React, { useState, useEffect, useRef } from 'react';
import { api } from './api';
import { AgentDefinition, ActiveAgentMap, SystemStatus, ChatMessage, RosterResponse } from './types';

// Icons
const IconTerminal = () => <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>;
const IconCpu = () => <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>;
const IconActivity = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>;
const IconBox = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>;
const IconExternalLink = () => <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>;

export default function App() {
  const [status, setStatus] = useState<SystemStatus>({ status: 'offline', driver_initialized: false });
  const [activeAgents, setActiveAgents] = useState<ActiveAgentMap>({});
  const [roster, setRoster] = useState<RosterResponse>({});
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [spawning, setSpawning] = useState<string | null>(null);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initial fetch
  useEffect(() => {
    api.getRoster().then(data => {
      setRoster(data);
      const categories = Object.keys(data);
      if (categories.length > 0) setSelectedCategory(categories[0]);
    });
  }, []);

  // Polling
  useEffect(() => {
    const poll = async () => {
      const s = await api.getStatus();
      setStatus(s);
      const a = await api.getAgents();
      setActiveAgents(a);
    };
    poll();
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleSpawn = async (agentId: string) => {
    setSpawning(agentId);
    addToLog('system', `> INITIATING SPAWN SEQUENCE: ${agentId}`);
    try {
      const success = await api.spawnAgent(agentId);
      if (success) {
        addToLog('system', `> COMMAND SENT: SPAWN ${agentId}`);
      } else {
        addToLog('system', `> ERROR: FAILED TO SPAWN ${agentId}`);
      }
    } catch (e) {
      addToLog('system', `> ERROR: CONNECTION FAILED`);
    }
    setSpawning(null);
  };

  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    const msg = chatInput;
    setChatInput('');
    addToLog('user', msg);
    
    try {
      const success = await api.chat(msg);
      if (!success) {
        addToLog('system', '> ERROR: MESSAGE FAILED TO SEND');
      }
    } catch(e) {
      addToLog('system', '> ERROR: BACKEND UNREACHABLE');
    }
  };

  const addToLog = (role: ChatMessage['role'], content: string) => {
    setChatHistory(prev => [...prev, {
      id: Date.now().toString(),
      role,
      content,
      timestamp: Date.now()
    }]);
  };

  const activeAgentCount = Object.keys(activeAgents).length;
  const categories = Object.keys(roster);

  return (
    <div className="flex h-screen bg-background text-text font-mono overflow-hidden">
      <div className="scanline"></div>
      
      {/* Sidebar: Roster */}
      <div className="w-80 border-r border-border flex flex-col bg-surface z-10">
        <div className="p-4 border-b border-border">
          <div className="flex items-center space-x-3 mb-2">
            <div className="bg-primary/10 p-2 rounded border border-primary/20 text-primary">
              <IconCpu />
            </div>
            <div>
              <h1 className="font-bold tracking-widest text-lg text-white">XAGENT</h1>
              <p className="text-[10px] text-primary tracking-widest uppercase">Orchestration</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-[10px] uppercase mt-2">
            <div className={`px-2 py-0.5 rounded-sm flex items-center gap-2 ${status.status === 'online' ? 'bg-primary/20 text-primary border border-primary/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
              <div className={`w-1.5 h-1.5 rounded-full ${status.status === 'online' ? 'bg-primary animate-pulse' : 'bg-red-500'}`}></div>
              {status.status}
            </div>
            <div className={`px-2 py-0.5 rounded-sm border ${status.driver_initialized ? 'border-accent/30 text-accent bg-accent/10' : 'border-border text-textDim'}`}>
              DRIVER: {status.driver_initialized ? 'ON' : 'OFF'}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {categories.length === 0 ? (
            <div className="p-8 text-center text-textDim text-xs">
              Waiting for backend roster...
            </div>
          ) : (
            categories.map(category => (
              <div key={category} className="border-b border-border/50">
                <button
                  onClick={() => setSelectedCategory(category === selectedCategory ? null : category)}
                  className={`w-full text-left px-4 py-3 text-xs font-bold uppercase tracking-wider flex justify-between items-center transition-colors ${selectedCategory === category ? 'text-white bg-surfaceHighlight' : 'text-textDim hover:text-white hover:bg-surfaceHighlight/50'}`}
                >
                  {category}
                  <span className="text-[10px] opacity-50">{roster[category].length}</span>
                </button>
                
                {selectedCategory === category && (
                  <div className="bg-background/50">
                    {roster[category].map(agent => {
                      const isActive = !!activeAgents[agent.id];
                      return (
                        <div key={agent.id} className="p-3 border-l-2 border-transparent hover:border-primary/50 hover:bg-surfaceHighlight/20 transition-all group">
                          <div className="flex justify-between items-start mb-1">
                            <span className={`text-xs font-bold ${isActive ? 'text-primary' : 'text-accent'}`}>{agent.id}</span>
                            {isActive ? (
                              <span className="text-[9px] bg-primary/20 text-primary px-1.5 rounded border border-primary/20">ACTIVE</span>
                            ) : (
                              <button
                                onClick={(e) => { e.stopPropagation(); handleSpawn(agent.id); }}
                                disabled={spawning !== null}
                                className="opacity-0 group-hover:opacity-100 bg-white text-black text-[9px] font-bold px-2 py-0.5 rounded hover:bg-gray-200 disabled:opacity-50 transition-opacity"
                              >
                                {spawning === agent.id ? '...' : 'SPAWN'}
                              </button>
                            )}
                          </div>
                          <div className="text-[11px] text-text mb-1 truncate">{agent.name}</div>
                          <div className="text-[10px] text-textDim leading-tight line-clamp-2">{agent.description}</div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Area */}
      <div className="flex-1 flex flex-col z-10">
        
        {/* Active Agents Rail */}
        <div className="h-48 border-b border-border bg-surface/30 p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-bold text-textDim uppercase tracking-wider flex items-center gap-2">
              <IconActivity />
              Active Agents ({activeAgentCount})
            </h2>
          </div>
          
          <div className="flex-1 overflow-x-auto flex gap-3 pb-2 custom-scrollbar">
            {activeAgentCount === 0 ? (
              <div className="flex-1 border border-dashed border-border rounded-lg flex flex-col items-center justify-center text-textDim text-xs bg-surface/20">
                <IconBox />
                <span className="mt-2">No agents active. Spawn one from the roster.</span>
              </div>
            ) : (
              Object.entries(activeAgents).map(([id, agent]) => (
                <div key={id} className="flex-shrink-0 w-64 bg-surfaceHighlight border border-border rounded-lg p-3 flex flex-col justify-between hover:border-primary/50 transition-colors shadow-lg">
                  <div>
                    <div className="flex justify-between items-start mb-2">
                      <div className="w-6 h-6 rounded bg-gradient-to-br from-primary to-accent flex items-center justify-center text-black font-bold text-[10px]">
                        {id.substring(0, 2)}
                      </div>
                      <a 
                        href={agent.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-textDim hover:text-white transition-colors"
                      >
                        <IconExternalLink />
                      </a>
                    </div>
                    <div className="font-bold text-sm text-white mb-1">{id}</div>
                    <div className="text-[10px] text-primary animate-pulse">● Running</div>
                  </div>
                  <div className="text-[9px] text-textDim font-mono border-t border-border/50 pt-2 mt-2">
                    Started: {agent.created_at.split(' ')[1]}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Terminal Chat */}
        <div className="flex-1 flex flex-col bg-background relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-8 bg-surfaceHighlight/50 border-b border-border flex items-center px-4 backdrop-blur-sm z-20">
            <IconTerminal />
            <span className="ml-2 text-xs text-textDim tracking-wider">SYSTEM_CONSOLE</span>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 pt-12 space-y-3">
            {chatHistory.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-textDim opacity-30">
                <div className="text-4xl mb-4">_</div>
                <p className="text-xs tracking-widest">SYSTEM READY. AWAITING INPUT.</p>
              </div>
            )}
            
            {chatHistory.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded p-3 text-sm border ${
                  msg.role === 'user' 
                    ? 'bg-accent/10 border-accent/20 text-blue-100' 
                    : msg.role === 'system'
                    ? 'bg-primary/5 border-primary/20 text-green-100 font-mono text-xs'
                    : 'bg-surfaceHighlight border-border'
                }`}>
                  <div className={`text-[9px] uppercase mb-1 opacity-50 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                    {msg.role}
                  </div>
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 bg-surface border-t border-border z-20">
            <form onSubmit={handleSendChat} className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-primary">{'>'}</div>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Broadcast command to all agents..."
                className="w-full bg-background border border-border rounded pl-8 pr-24 py-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 text-white placeholder-textDim/30"
              />
              <button 
                type="submit"
                disabled={!chatInput.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-surfaceHighlight hover:bg-primary hover:text-black text-textDim text-xs font-bold px-3 py-1.5 rounded transition-all disabled:opacity-50"
              >
                SEND
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
