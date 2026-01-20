
import React, { useState, useEffect, useRef, useMemo } from 'react';
import { api } from './api';
import { ActiveAgentMap, SystemStatus, ChatMessage, RosterResponse, UploadedFile } from './types';
import {
  Terminal, Cpu, Activity, Box, ExternalLink, Search, Send, FileText,
  Trash2, Play, Upload, FileCode, HardDrive, Power, ChevronDown, Radio
} from 'lucide-react';

export default function App() {
  // State
  const [status, setStatus] = useState<SystemStatus>({ status: 'offline', driver_initialized: false });
  const [activeAgents, setActiveAgents] = useState<ActiveAgentMap>({});
  const [roster, setRoster] = useState<RosterResponse>({});
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [spawning, setSpawning] = useState<string | null>(null);

  // Chat State
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [targetAgentId, setTargetAgentId] = useState<string | null>(null); // null = broadcast
  const [showTargetMenu, setShowTargetMenu] = useState(false);

  // File State
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // Search State
  const [searchTerm, setSearchTerm] = useState('');

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const targetMenuRef = useRef<HTMLDivElement>(null);

  // --- Effects ---

  // Initial Fetch
  useEffect(() => {
    api.getRoster().then(data => {
      setRoster(data);
      const categories = Object.keys(data);
      if (categories.length > 0) setSelectedCategory(categories[0]);
    });
    fetchFiles();
  }, []);

  // Polling
  useEffect(() => {
    const poll = async () => {
      try {
        const s = await api.getStatus();
        setStatus(s);
        const a = await api.getAgents();
        setActiveAgents(a);
      } catch (e) {
        // Silent fail on poll
      }
    };
    poll();
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // Click outside listener for target menu
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (targetMenuRef.current && !targetMenuRef.current.contains(event.target as Node)) {
        setShowTargetMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [targetMenuRef]);

  // --- Handlers ---

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

  const handleKill = async (agentId: string) => {
    addToLog('system', `> TERMINATING: ${agentId}`);
    await api.deactivateAgent(agentId);
    // Optimistic update
    const newActive = { ...activeAgents };
    delete newActive[agentId];
    setActiveAgents(newActive);
    if (targetAgentId === agentId) setTargetAgentId(null);
  };

  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const msg = chatInput;
    setChatInput('');

    const targetDisplay = targetAgentId ? `[@${targetAgentId}] ` : '';
    addToLog('user', `${targetDisplay}${msg}`, targetAgentId || undefined);

    try {
      const success = await api.chat(msg, targetAgentId || undefined);
      if (!success) {
        addToLog('system', '> ERROR: MESSAGE FAILED TO SEND');
      }
    } catch (e) {
      addToLog('system', '> ERROR: BACKEND UNREACHABLE');
    }
  };

  const addToLog = (role: ChatMessage['role'], content: string, agentId?: string) => {
    setChatHistory(prev => [...prev, {
      id: Date.now().toString(),
      role,
      content,
      timestamp: Date.now(),
      agentId
    }]);
  };

  // --- File Handlers ---

  const fetchFiles = async () => {
    const data = await api.getFiles();
    setFiles(data);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) await processUpload(file);
  };

  const processUpload = async (file: File) => {
    setUploading(true);
    addToLog('system', `> UPLOADING: ${file.name}`);
    const result = await api.uploadFile(file);
    if (result) {
      addToLog('system', `> UPLOADED: ${result.filename} (${Math.round(result.size / 1024)}KB)`);
      fetchFiles();
    } else {
      addToLog('system', '> ERROR: Upload failed');
    }
    setUploading(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) await processUpload(file);
  };

  const handleParse = async (filename: string) => {
    addToLog('system', `> PARSING: ${filename}`);
    const result = await api.parseFile(filename);
    if (result) {
      addToLog('system', `> EXTRACTED ${result.length} chars from ${filename}`);
      const preview = result.text.substring(0, 500);
      addToLog('agent', `[${filename} PREVIEW]\n${preview}${result.text.length > 500 ? '...(truncated)' : ''}`);
    } else {
      addToLog('system', '> ERROR: Parse failed');
    }
  };

  const handleDeleteFile = async (filename: string) => {
    await api.deleteFile(filename);
    fetchFiles();
    addToLog('system', `> DELETED: ${filename}`);
  };

  // --- Computed ---

  const filteredRoster = useMemo(() => {
    if (!searchTerm) return roster;
    const filtered: RosterResponse = {};
    Object.keys(roster).forEach(cat => {
      const matches = roster[cat].filter(agent =>
        agent.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        agent.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
      if (matches.length > 0) filtered[cat] = matches;
    });
    return filtered;
  }, [roster, searchTerm]);

  // Auto-expand category if search is active
  useEffect(() => {
    if (searchTerm) {
      const firstCat = Object.keys(filteredRoster)[0];
      if (firstCat) setSelectedCategory(firstCat);
    }
  }, [searchTerm, filteredRoster]);

  const activeAgentList = Object.keys(activeAgents);
  const categories = Object.keys(filteredRoster);

  return (
    <div className="flex h-screen bg-background text-text font-mono overflow-hidden selection:bg-primary/30">
      <div className="scanline"></div>

      {/* Sidebar: Roster */}
      <div className="w-80 border-r border-border flex flex-col bg-surface z-10 shadow-2xl">
        <div className="p-4 border-b border-border bg-surfaceHighlight/10">
          <div className="flex items-center space-x-3 mb-4">
            <div className="bg-primary/10 p-2 rounded-lg border border-primary/20 text-primary shadow-[0_0_15px_rgba(16,185,129,0.15)]">
              <Cpu size={20} />
            </div>
            <div>
              <h1 className="font-bold tracking-[0.2em] text-lg text-white">XAGENT</h1>
              <p className="text-[10px] text-primary tracking-widest uppercase opacity-80">Command Center</p>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-[10px] uppercase mb-4">
            <div className={`px-2 py-1 rounded border flex items-center gap-2 transition-colors ${status.status === 'online' ? 'bg-primary/10 text-primary border-primary/30' : 'bg-red-500/10 text-red-400 border-red-500/30'}`}>
              <div className={`w-1.5 h-1.5 rounded-full ${status.status === 'online' ? 'bg-primary animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-red-500'}`}></div>
              {status.status}
            </div>
            <div className={`px-2 py-1 rounded border ${status.driver_initialized ? 'border-accent/30 text-accent bg-accent/10' : 'border-border text-textDim'}`}>
              DRIVER: {status.driver_initialized ? 'ON' : 'OFF'}
            </div>
          </div>

          <div className="relative group">
            <div className="absolute left-2.5 top-1/2 -translate-y-1/2 text-textDim group-focus-within:text-primary transition-colors">
              <Search size={14} />
            </div>
            <input
              type="text"
              placeholder="SEARCH AGENTS..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-background border border-border rounded-md pl-8 pr-3 py-1.5 text-xs text-white placeholder-textDim/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar bg-surface/50">
          {categories.length === 0 ? (
            <div className="p-8 text-center text-textDim text-xs flex flex-col items-center gap-2 opacity-60">
              <Search size={24} />
              <span>{searchTerm ? 'No agents match filter' : 'Loading roster...'}</span>
            </div>
          ) : (
            categories.map(category => (
              <div key={category} className="border-b border-border/30">
                <button
                  onClick={() => setSelectedCategory(category === selectedCategory ? null : category)}
                  className={`w-full text-left px-4 py-3 text-xs font-bold uppercase tracking-wider flex justify-between items-center transition-all duration-200 ${selectedCategory === category ? 'text-white bg-surfaceHighlight border-l-2 border-l-primary' : 'text-textDim hover:text-white hover:bg-surfaceHighlight/30 border-l-2 border-l-transparent'}`}
                >
                  {category}
                  <span className={`text-[9px] px-1.5 py-0.5 rounded ${selectedCategory === category ? 'bg-black/30 text-primary' : 'bg-surfaceHighlight text-textDim'}`}>
                    {filteredRoster[category].length}
                  </span>
                </button>

                {selectedCategory === category && (
                  <div className="bg-background/30 animate-in slide-in-from-top-1 duration-200">
                    {filteredRoster[category].map(agent => {
                      const isActive = !!activeAgents[agent.id];
                      return (
                        <div key={agent.id} className="p-3 pl-5 border-l-[3px] border-transparent hover:border-l-primary/50 hover:bg-surfaceHighlight/20 transition-all group relative">
                          <div className="flex justify-between items-start mb-1">
                            <span className={`text-xs font-bold font-mono ${isActive ? 'text-primary' : 'text-accent group-hover:text-white'}`}>{agent.id}</span>
                            {isActive ? (
                              <span className="text-[9px] bg-primary/20 text-primary px-1.5 rounded border border-primary/20 flex items-center gap-1">
                                <Activity size={8} /> ACTIVE
                              </span>
                            ) : (
                              <button
                                onClick={(e) => { e.stopPropagation(); handleSpawn(agent.id); }}
                                disabled={spawning !== null}
                                className="opacity-0 group-hover:opacity-100 bg-white text-black text-[9px] font-bold px-2 py-0.5 rounded hover:bg-gray-200 disabled:opacity-50 transition-opacity flex items-center gap-1 shadow-md"
                              >
                                {spawning === agent.id ? <Activity size={10} className="animate-spin" /> : <Play size={10} fill="currentColor" />}
                                {spawning === agent.id ? '...' : 'SPAWN'}
                              </button>
                            )}
                          </div>
                          <div className="text-[11px] text-text mb-0.5 truncate">{agent.name}</div>
                          <div className="text-[10px] text-textDim leading-tight line-clamp-2 opacity-70 group-hover:opacity-100 transition-opacity">{agent.description}</div>
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
      <div className="flex-1 flex flex-col z-10 bg-gradient-to-br from-background to-surface/50">

        {/* Top Rail: Active Agents */}
        <div className="h-44 border-b border-border bg-surface/40 p-4 flex flex-col backdrop-blur-sm">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-bold text-textDim uppercase tracking-wider flex items-center gap-2">
              <Activity size={14} className={activeAgentList.length > 0 ? "text-primary animate-pulse" : ""} />
              Active Grid ({activeAgentList.length})
            </h2>
          </div>

          <div className="flex-1 overflow-x-auto flex gap-3 pb-2 custom-scrollbar">
            {activeAgentList.length === 0 ? (
              <div className="flex-1 border-2 border-dashed border-border/50 rounded-lg flex flex-col items-center justify-center text-textDim text-xs bg-surface/10 gap-2">
                <Box size={24} className="opacity-50" />
                <span className="opacity-70">Grid offline. Spawn an agent from the roster.</span>
              </div>
            ) : (
              activeAgentList.map(id => (
                <div key={id} className="flex-shrink-0 w-64 bg-surfaceHighlight/80 border border-border/50 rounded-lg p-3 flex flex-col justify-between hover:border-primary/50 transition-all shadow-lg group relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-bl from-primary/10 to-transparent rounded-bl-3xl -mr-8 -mt-8 transition-opacity opacity-50 group-hover:opacity-100 pointer-events-none"></div>
                  <div>
                    <div className="flex justify-between items-start mb-2">
                      <div className="w-8 h-8 rounded bg-gradient-to-br from-primary/20 to-accent/20 border border-white/10 flex items-center justify-center text-white font-bold text-[10px] shadow-inner">
                        {id.substring(0, 2)}
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleKill(id)}
                          className="text-textDim hover:text-red-400 transition-colors p-1 hover:bg-white/10 rounded"
                          title="Terminate Agent"
                        >
                          <Power size={14} />
                        </button>
                        <a
                          href={activeAgents[id].url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-textDim hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
                          title="Open in AI Studio"
                        >
                          <ExternalLink size={14} />
                        </a>
                      </div>
                    </div>
                    <div className="font-bold text-sm text-white mb-1 font-mono tracking-tight">{id}</div>
                    <div className="text-[10px] text-primary flex items-center gap-1.5">
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                      </span>
                      OPERATIONAL
                    </div>
                  </div>
                  <div className="text-[9px] text-textDim font-mono border-t border-white/10 pt-2 mt-2 flex justify-between">
                    <span>UPTIME: {activeAgents[id].created_at.split(' ')[1]}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Mid Rail: File Deck */}
        <div
          className={`border-b border-border bg-surface/30 p-4 transition-colors ${isDragging ? 'bg-primary/10 border-primary/30' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-bold text-textDim uppercase tracking-wider flex items-center gap-2">
              <HardDrive size={14} />
              Data Deck ({files.length})
            </h2>
            <label className={`text-[10px] px-3 py-1.5 bg-accent/10 text-accent border border-accent/30 rounded cursor-pointer hover:bg-accent/20 hover:border-accent/50 transition-all flex items-center gap-2 font-bold ${uploading ? 'opacity-50 cursor-wait' : ''}`}>
              {uploading ? (
                <Activity size={12} className="animate-spin" />
              ) : (
                <Upload size={12} />
              )}
              {uploading ? 'UPLOADING...' : 'UPLOAD DATA'}
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".pdf,.docx,.txt,.md"
                className="hidden"
                disabled={uploading}
              />
            </label>
          </div>

          {files.length === 0 ? (
            <div className={`text-center text-textDim text-xs py-6 border-2 border-dashed rounded-lg transition-all flex flex-col items-center gap-2 ${isDragging ? 'border-primary/50 bg-primary/5 text-primary' : 'border-border/50 hover:border-border hover:bg-surface/30'}`}>
              <FileText size={24} className={isDragging ? 'animate-bounce' : 'opacity-50'} />
              <span>{isDragging ? 'DROP FILE TO UPLOAD' : 'Drag & drop files here or click Upload'}</span>
              <span className="text-[10px] opacity-50">Supports PDF, DOCX, TXT, MD</span>
            </div>
          ) : (
            <div className="flex gap-3 overflow-x-auto pb-2 custom-scrollbar">
              {files.map(file => (
                <div key={file.filename} className="flex-shrink-0 w-48 bg-surfaceHighlight border border-border rounded px-3 py-3 text-xs group hover:border-accent/50 transition-colors">
                  <div className="flex items-center gap-2 mb-2">
                    <FileCode size={16} className="text-accent" />
                    <span className="text-white truncate font-medium flex-1" title={file.filename}>{file.filename}</span>
                  </div>
                  <div className="flex justify-between items-center mt-3">
                    <div className="text-textDim text-[9px] font-mono">{Math.round(file.size / 1024)} KB</div>
                    <div className="flex gap-1 opacity-50 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleParse(file.filename)}
                        className="p-1 hover:bg-primary/20 hover:text-primary rounded"
                        title="Parse Text"
                      >
                        <FileText size={12} />
                      </button>
                      <button
                        onClick={() => handleDeleteFile(file.filename)}
                        className="p-1 hover:bg-red-500/20 hover:text-red-400 rounded"
                        title="Delete"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Bottom Rail: Terminal */}
        <div className="flex-1 flex flex-col bg-background relative overflow-hidden shadow-inner">
          <div className="absolute top-0 left-0 right-0 h-9 bg-surfaceHighlight/30 border-b border-border flex items-center px-4 backdrop-blur-sm z-20 justify-between">
            <div className="flex items-center gap-2">
              <Terminal size={14} className="text-primary" />
              <span className="text-xs text-textDim tracking-widest font-bold">SYSTEM_CONSOLE</span>
            </div>
            <div className="flex gap-1.5">
              <div className="w-2 h-2 rounded-full bg-red-500/20"></div>
              <div className="w-2 h-2 rounded-full bg-yellow-500/20"></div>
              <div className="w-2 h-2 rounded-full bg-green-500/20"></div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 pt-12 space-y-4 font-mono text-sm">
            {chatHistory.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-textDim opacity-20 select-none">
                <Terminal size={48} className="mb-4" />
                <p className="text-xs tracking-[0.3em]">SYSTEM READY. AWAITING INPUT.</p>
              </div>
            )}

            {chatHistory.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                <div
                  className={`max-w-[85%] rounded-lg p-3 border shadow-sm backdrop-blur-sm
                  ${msg.role === 'user'
                      ? 'bg-accent/10 border-accent/20 text-blue-100 rounded-br-none'
                      : msg.role === 'system'
                        ? 'bg-primary/5 border-primary/20 text-green-100 rounded-bl-none border-l-4 border-l-primary/50'
                        : 'bg-surfaceHighlight/50 border-border text-gray-200 rounded-bl-none border-l-4 border-l-purple-500/50'
                    }`}
                >
                  <div className="flex items-center gap-2 mb-1.5 border-b border-white/5 pb-1">
                    <span className={`text-[9px] font-bold uppercase tracking-wider ${msg.role === 'user' ? 'text-accent' :
                        msg.role === 'system' ? 'text-primary' : 'text-purple-400'
                      }`}>
                      {msg.role === 'agent' ? 'AGENT RESPONSE' : msg.role}
                      {msg.agentId && <span className="ml-2 opacity-70">[{msg.agentId}]</span>}
                    </span>
                    <span className="text-[9px] text-white/20 ml-auto font-mono">
                      {new Date(msg.timestamp).toLocaleTimeString([], { hour12: false })}
                    </span>
                  </div>
                  <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 bg-surface/50 border-t border-border z-20 backdrop-blur-md">
            <form onSubmit={handleSendChat} className="relative flex items-center gap-2">

              {/* Target Selector Dropdown */}
              <div className="relative" ref={targetMenuRef}>
                <button
                  type="button"
                  onClick={() => setShowTargetMenu(!showTargetMenu)}
                  className={`h-full flex items-center gap-2 px-3 py-3.5 rounded-lg border text-xs font-bold transition-all ${targetAgentId
                      ? 'bg-accent/20 border-accent text-accent'
                      : 'bg-surfaceHighlight border-border text-textDim hover:text-white'
                    }`}
                >
                  {targetAgentId || "BROADCAST"}
                  <ChevronDown size={12} className={`transition-transform ${showTargetMenu ? 'rotate-180' : ''}`} />
                </button>

                {showTargetMenu && (
                  <div className="absolute bottom-full left-0 mb-2 w-48 bg-surface border border-border rounded-lg shadow-xl overflow-hidden z-50">
                    <div className="p-1">
                      <button
                        type="button"
                        onClick={() => { setTargetAgentId(null); setShowTargetMenu(false); }}
                        className={`w-full text-left px-3 py-2 rounded text-xs flex items-center gap-2 ${!targetAgentId ? 'bg-primary/20 text-primary' : 'text-textDim hover:bg-white/5'}`}
                      >
                        <Radio size={12} /> BROADCAST (ALL)
                      </button>
                      <div className="h-px bg-border my-1" />
                      <div className="px-2 py-1 text-[10px] text-textDim font-bold uppercase opacity-50">Active Agents</div>
                      {activeAgentList.length === 0 && (
                        <div className="px-3 py-2 text-[10px] text-textDim italic">No active agents</div>
                      )}
                      {activeAgentList.map(id => (
                        <button
                          key={id}
                          type="button"
                          onClick={() => { setTargetAgentId(id); setShowTargetMenu(false); }}
                          className={`w-full text-left px-3 py-2 rounded text-xs flex items-center gap-2 ${targetAgentId === id ? 'bg-accent/20 text-accent' : 'text-textDim hover:bg-white/5 hover:text-white'}`}
                        >
                          <div className={`w-1.5 h-1.5 rounded-full ${targetAgentId === id ? 'bg-accent' : 'bg-white/30'}`} />
                          {id}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <div className="relative flex-1 group">
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-primary animate-pulse">{'>'}</div>
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder={targetAgentId ? `Command ${targetAgentId}...` : "Broadcast command to all agents..."}
                  className="w-full bg-background/80 border border-border rounded-lg pl-10 pr-24 py-3.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 text-white placeholder-textDim/30 shadow-inner font-mono transition-all"
                />
                <button
                  type="submit"
                  disabled={!chatInput.trim()}
                  className="absolute right-2 top-1/2 -translate-y-1/2 bg-surfaceHighlight hover:bg-primary hover:text-black text-textDim text-xs font-bold px-4 py-2 rounded-md transition-all disabled:opacity-50 disabled:hover:bg-surfaceHighlight disabled:hover:text-textDim flex items-center gap-2"
                >
                  SEND <Send size={12} />
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
