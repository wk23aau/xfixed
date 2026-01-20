
import React, { useState, useEffect, useRef, useMemo } from 'react';
import { api } from './api';
import { ActiveAgentMap, SystemStatus, ChatMessage, RosterResponse, UploadedFile } from './types';
import {
  Terminal, Cpu, Activity, Box, ExternalLink, Search, Send, FileText,
  Trash2, Play, Upload, FileCode, HardDrive, Power, ChevronDown, Radio
} from 'lucide-react';

// ============================================
// DEBUG UTILITIES
// ============================================
const DEBUG = true; // Master debug switch

const debugLog = (component: string, action: string, data?: any) => {
  if (!DEBUG) return;
  const timestamp = new Date().toISOString().split('T')[1].slice(0, 12);
  console.log(`%c[${timestamp}] ${component}: ${action}`, 'color: #10b981; font-weight: bold;', data || '');
};

const debugState = (name: string, value: any) => {
  if (!DEBUG) return;
  console.log(`%c[STATE] ${name}:`, 'color: #3b82f6; font-weight: bold;', value);
};

const debugEvent = (handler: string, event?: any) => {
  if (!DEBUG) return;
  console.log(`%c[EVENT] ${handler}`, 'color: #f59e0b; font-weight: bold;', event || '');
  debugger; // BREAKPOINT: Event handler
};

const debugRender = (component: string, props?: any) => {
  if (!DEBUG) return;
  console.log(`%c[RENDER] ${component}`, 'color: #8b5cf6;', props || '');
};

export default function App() {
  debugRender('App', { timestamp: Date.now() });
  debugger; // BREAKPOINT: App component render

  // ============================================
  // STATE DECLARATIONS
  // ============================================

  // System State
  const [status, setStatus] = useState<SystemStatus>({ status: 'offline', driver_initialized: false });
  debugState('status', status);

  const [activeAgents, setActiveAgents] = useState<ActiveAgentMap>({});
  debugState('activeAgents', Object.keys(activeAgents));

  const [roster, setRoster] = useState<RosterResponse>({});
  debugState('roster', Object.keys(roster));

  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  debugState('selectedCategory', selectedCategory);

  const [spawning, setSpawning] = useState<string | null>(null);
  debugState('spawning', spawning);

  // Chat State
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  debugState('chatHistory.length', chatHistory.length);

  const [targetAgentId, setTargetAgentId] = useState<string | null>(null);
  debugState('targetAgentId', targetAgentId);

  const [showTargetMenu, setShowTargetMenu] = useState(false);

  // File State
  const [files, setFiles] = useState<UploadedFile[]>([]);
  debugState('files', files.map(f => f.filename));

  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // Search State
  const [searchTerm, setSearchTerm] = useState('');

  // P7: Toast State for error messages
  const [toast, setToast] = useState<{ message: string, type: 'error' | 'success' } | null>(null);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const targetMenuRef = useRef<HTMLDivElement>(null);

  // Helper: Show toast
  const showToast = (message: string, type: 'error' | 'success' = 'error') => {
    debugLog('showToast', message, type);
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000); // Auto-dismiss after 5s
  };

  // ============================================
  // EFFECTS
  // ============================================

  // Initial Fetch (P7: with error handling)
  useEffect(() => {
    debugLog('useEffect', 'Initial fetch - mounting');
    debugger; // BREAKPOINT: Component mount

    const initRoster = async () => {
      debugLog('initRoster', 'Fetching roster...');
      debugger; // BREAKPOINT: Before roster fetch
      try {
        const data = await api.getRoster();
        debugLog('initRoster', 'Roster received', data);
        debugger; // BREAKPOINT: After roster fetch
        setRoster(data);
        const categories = Object.keys(data);
        debugLog('initRoster', 'Categories', categories);
        debugLog('initRoster', `Loaded ${categories.length} categories, ${Object.values(data).flat().length} agents`);
        if (categories.length > 0) {
          debugLog('initRoster', 'Setting first category', categories[0]);
          setSelectedCategory(categories[0]);
        }
      } catch (e) {
        debugLog('initRoster', 'Roster fetch error', e);
        setRoster({});  // Empty roster on error
        showToast('Failed to load roster. Is the backend running?', 'error');
      }
    };

    initRoster();
    fetchFiles();

    return () => {
      debugLog('useEffect', 'Initial fetch - cleanup');
    };
  }, []);

  // P6: Status Check with Retry Logic
  const [retryCount, setRetryCount] = useState(0);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const MAX_RETRIES = 3;
  const RETRY_DELAY_MS = 3000;

  // Initial status check with retry
  useEffect(() => {
    debugLog('useEffect', 'Initial status check with retry');
    let isMounted = true;

    const checkStatus = async (attempt: number): Promise<boolean> => {
      debugLog('checkStatus', `Attempt ${attempt} of ${MAX_RETRIES}`);
      try {
        const s = await api.getStatus();
        debugLog('checkStatus', 'Status received', s);
        if (isMounted) {
          setStatus(s);
          setRetryCount(0);
          setConnectionError(null);
        }
        return true;
      } catch (e) {
        debugLog('checkStatus', `Attempt ${attempt} failed`, e);
        if (isMounted) {
          setStatus({ status: 'offline', driver_initialized: false });
        }
        return false;
      }
    };

    const initWithRetry = async () => {
      for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        debugLog('initWithRetry', `Starting attempt ${attempt}`);
        const success = await checkStatus(attempt);
        if (success) {
          debugLog('initWithRetry', 'Connection successful');
          return;
        }
        if (attempt < MAX_RETRIES) {
          debugLog('initWithRetry', `Waiting ${RETRY_DELAY_MS}ms before retry...`);
          if (isMounted) setRetryCount(attempt);
          await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
        }
      }
      // Max retries reached
      debugLog('initWithRetry', 'Max retries reached, showing error');
      if (isMounted) {
        setConnectionError('Backend unreachable after 3 attempts. Is the backend running?');
        setRetryCount(MAX_RETRIES);
      }
    };

    initWithRetry();

    return () => {
      isMounted = false;
    };
  }, []);

  // Polling (after initial connection established)
  useEffect(() => {
    if (status.status === 'offline' && connectionError) {
      debugLog('useEffect', 'Polling skipped - connection error');
      return;
    }

    debugLog('useEffect', 'Polling setup');
    debugger; // BREAKPOINT: Polling setup

    const poll = async () => {
      debugLog('poll', 'Polling cycle start');
      try {
        debugLog('poll', 'Fetching status...');
        const s = await api.getStatus();
        debugLog('poll', 'Status received', s);
        debugger; // BREAKPOINT: Status update
        setStatus(s);
        setConnectionError(null);

        debugLog('poll', 'Fetching agents...');
        const a = await api.getAgents();
        debugLog('poll', 'Agents received', Object.keys(a));
        debugger; // BREAKPOINT: Agents update
        setActiveAgents(a);

        debugLog('poll', 'Polling cycle complete');
      } catch (e) {
        debugLog('poll', 'Polling error', e);
        debugger; // BREAKPOINT: Polling error
        setStatus({ status: 'offline', driver_initialized: false });
      }
    };

    poll();
    const interval = setInterval(() => {
      debugLog('poll', 'Interval tick');
      poll();
    }, 2000);

    return () => {
      debugLog('useEffect', 'Polling cleanup');
      clearInterval(interval);
    };
  }, [connectionError]);

  // Auto-scroll chat
  useEffect(() => {
    debugLog('useEffect', 'Chat auto-scroll', { historyLength: chatHistory.length });
    debugger; // BREAKPOINT: Chat scroll
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // Click outside listener for target menu
  useEffect(() => {
    debugLog('useEffect', 'Click outside listener setup');

    function handleClickOutside(event: MouseEvent) {
      debugEvent('handleClickOutside', { target: event.target });
      if (targetMenuRef.current && !targetMenuRef.current.contains(event.target as Node)) {
        debugLog('handleClickOutside', 'Closing target menu');
        setShowTargetMenu(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      debugLog('useEffect', 'Click outside listener cleanup');
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [targetMenuRef]);

  // ============================================
  // HANDLERS
  // ============================================

  const handleSpawn = async (agentId: string) => {
    debugEvent('handleSpawn', { agentId });
    debugger; // BREAKPOINT: Spawn start
    console.log('[FLOW] handleSpawn: Starting spawn sequence');
    console.log('[FLOW] handleSpawn: Agent ID:', agentId);

    setSpawning(agentId);
    debugLog('handleSpawn', 'Set spawning state', agentId);

    addToLog('system', `> INITIATING SPAWN SEQUENCE: ${agentId}`);
    debugLog('handleSpawn', 'Added log message');

    try {
      console.log('[FLOW] handleSpawn: Calling API...');
      debugger; // BREAKPOINT: Before spawn API call
      const success = await api.spawnAgent(agentId);
      console.log('[FLOW] handleSpawn: API response:', success);
      debugger; // BREAKPOINT: After spawn API call

      if (success) {
        debugLog('handleSpawn', 'Spawn success', agentId);
        addToLog('system', `> COMMAND SENT: SPAWN ${agentId}`);
      } else {
        debugLog('handleSpawn', 'Spawn failed', agentId);
        addToLog('system', `> ERROR: FAILED TO SPAWN ${agentId}`);
      }
    } catch (e) {
      debugLog('handleSpawn', 'Spawn error', e);
      debugger; // BREAKPOINT: Spawn error
      addToLog('system', `> ERROR: CONNECTION FAILED`);
    }

    setSpawning(null);
    debugLog('handleSpawn', 'Spawn sequence complete');
  };

  const handleKill = async (agentId: string) => {
    debugEvent('handleKill', { agentId });
    debugger; // BREAKPOINT: Kill start
    console.log('[FLOW] handleKill: Terminating agent:', agentId);

    addToLog('system', `> TERMINATING: ${agentId}`);
    debugLog('handleKill', 'Added termination log');

    debugger; // BREAKPOINT: Before deactivate API call
    await api.deactivateAgent(agentId);
    debugLog('handleKill', 'Deactivation complete');
    debugger; // BREAKPOINT: After deactivate API call

    // Optimistic update
    const newActive = { ...activeAgents };
    delete newActive[agentId];
    debugLog('handleKill', 'Updating active agents', Object.keys(newActive));
    setActiveAgents(newActive);

    if (targetAgentId === agentId) {
      debugLog('handleKill', 'Clearing target agent');
      setTargetAgentId(null);
    }

    debugLog('handleKill', 'Kill sequence complete');
  };

  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    debugEvent('handleSendChat', { inputLength: chatInput.length });
    debugger; // BREAKPOINT: Chat send start

    console.log('[FLOW] handleSendChat: Form submitted');
    console.log('[FLOW] handleSendChat: Input:', chatInput);
    console.log('[FLOW] handleSendChat: Target:', targetAgentId);

    if (!chatInput.trim()) {
      debugLog('handleSendChat', 'Empty input, ignoring');
      return;
    }

    const msg = chatInput;
    debugLog('handleSendChat', 'Message captured', msg.substring(0, 50));
    setChatInput('');
    debugLog('handleSendChat', 'Input cleared');

    const targetDisplay = targetAgentId ? `[@${targetAgentId}] ` : '';
    debugLog('handleSendChat', 'Target display', targetDisplay);
    addToLog('user', `${targetDisplay}${msg}`, targetAgentId || undefined);
    debugLog('handleSendChat', 'Added user message to log');

    try {
      console.log('[FLOW] handleSendChat: Calling chat API...');
      debugger; // BREAKPOINT: Before chat API call
      const result = await api.chat(msg, targetAgentId || undefined);
      console.log('[FLOW] handleSendChat: API response:', result);
      debugger; // BREAKPOINT: After chat API call

      if (!result.success) {
        debugLog('handleSendChat', 'Chat send failed');
        addToLog('system', '> ERROR: MESSAGE FAILED TO SEND');
      } else if (result.broadcast && result.results) {
        // P10: Broadcast mode - display responses from all agents
        debugLog('handleSendChat', 'BROADCAST response received');
        const agentIds = Object.keys(result.results);
        let successCount = 0;
        let errorCount = 0;

        for (const agentId of agentIds) {
          const agentResult = result.results[agentId];
          if (agentResult.success) {
            successCount++;
            if (agentResult.response) {
              addToLog('agent', agentResult.response, agentId);
            } else {
              addToLog('agent', '(No response captured)', agentId);
            }
          } else {
            errorCount++;
            addToLog('system', `> ${agentId}: ERROR - ${agentResult.error || 'Unknown error'}`);
          }
        }

        addToLog('system', `> BROADCAST COMPLETE: ${successCount}/${agentIds.length} agents responded`);
      } else {
        debugLog('handleSendChat', 'Chat send success');
        // Display agent response if available
        if (result.response) {
          debugLog('handleSendChat', 'Agent response received', result.response.substring(0, 100));
          addToLog('agent', result.response, targetAgentId || undefined);
        } else {
          addToLog('system', '> Message sent (no response captured)');
        }
      }
    } catch (e) {
      debugLog('handleSendChat', 'Chat error', e);
      debugger; // BREAKPOINT: Chat error
      addToLog('system', '> ERROR: BACKEND UNREACHABLE');
    }

    debugLog('handleSendChat', 'Chat send complete');
  };

  const addToLog = (role: ChatMessage['role'], content: string, agentId?: string) => {
    debugLog('addToLog', 'Adding message', { role, contentPreview: content.substring(0, 30), agentId });
    debugger; // BREAKPOINT: Adding log message

    const newMessage = {
      id: Date.now().toString(),
      role,
      content,
      timestamp: Date.now(),
      agentId
    };

    debugLog('addToLog', 'New message object', newMessage);
    setChatHistory(prev => {
      debugLog('addToLog', 'Previous history length', prev.length);
      const newHistory = [...prev, newMessage];
      debugLog('addToLog', 'New history length', newHistory.length);
      return newHistory;
    });
  };

  // ============================================
  // FILE HANDLERS
  // ============================================

  const fetchFiles = async () => {
    debugLog('fetchFiles', 'Fetching files list');
    debugger; // BREAKPOINT: Fetch files start
    const data = await api.getFiles();
    debugLog('fetchFiles', 'Files received', data);
    debugger; // BREAKPOINT: Fetch files complete
    setFiles(data);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    debugEvent('handleFileChange', { files: e.target.files });
    debugger; // BREAKPOINT: File input change
    const file = e.target.files?.[0];
    if (file) {
      debugLog('handleFileChange', 'File selected', { name: file.name, size: file.size });
      await processUpload(file);
    }
  };

  const processUpload = async (file: File) => {
    debugLog('processUpload', 'Starting upload', { name: file.name, size: file.size, type: file.type });
    debugger; // BREAKPOINT: Upload start

    setUploading(true);
    debugLog('processUpload', 'Set uploading state');

    addToLog('system', `> UPLOADING: ${file.name}`);

    debugger; // BREAKPOINT: Before upload API call
    const result = await api.uploadFile(file);
    debugger; // BREAKPOINT: After upload API call

    if (result) {
      debugLog('processUpload', 'Upload success', result);
      addToLog('system', `> UPLOADED: ${result.filename} (${Math.round(result.size / 1024)}KB)`);
      await fetchFiles();
    } else {
      debugLog('processUpload', 'Upload failed');
      debugger; // BREAKPOINT: Upload failed
      addToLog('system', '> ERROR: Upload failed');
    }

    setUploading(false);
    debugLog('processUpload', 'Upload complete');
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    debugEvent('handleDragOver');
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    debugEvent('handleDragLeave');
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    debugEvent('handleDrop', { files: e.dataTransfer.files });
    debugger; // BREAKPOINT: File dropped

    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      debugLog('handleDrop', 'File dropped', { name: file.name, size: file.size });
      await processUpload(file);
    }
  };

  const handleParse = async (filename: string) => {
    debugEvent('handleParse', { filename });
    debugger; // BREAKPOINT: Parse start

    addToLog('system', `> PARSING: ${filename}`);
    debugLog('handleParse', 'Starting parse');

    debugger; // BREAKPOINT: Before parse API call
    const result = await api.parseFile(filename);
    debugger; // BREAKPOINT: After parse API call

    if (result) {
      debugLog('handleParse', 'Parse success', { length: result.text.length });
      addToLog('system', `> EXTRACTED ${result.length} chars from ${filename}`);
      const preview = result.text.substring(0, 500);
      addToLog('agent', `[${filename} PREVIEW]\n${preview}${result.text.length > 500 ? '...(truncated)' : ''}`);
    } else {
      debugLog('handleParse', 'Parse failed');
      debugger; // BREAKPOINT: Parse failed
      addToLog('system', '> ERROR: Parse failed');
    }
  };

  const handleDeleteFile = async (filename: string) => {
    debugEvent('handleDeleteFile', { filename });
    debugger; // BREAKPOINT: Delete file start

    debugger; // BREAKPOINT: Before delete API call
    await api.deleteFile(filename);
    debugger; // BREAKPOINT: After delete API call

    debugLog('handleDeleteFile', 'File deleted, refreshing list');
    await fetchFiles();
    addToLog('system', `> DELETED: ${filename}`);
  };

  // ============================================
  // COMPUTED VALUES
  // ============================================

  const filteredRoster = useMemo(() => {
    debugLog('useMemo', 'Computing filteredRoster', { searchTerm });
    debugger; // BREAKPOINT: Computing filtered roster

    if (!searchTerm) {
      debugLog('filteredRoster', 'No search term, returning full roster');
      return roster;
    }

    const filtered: RosterResponse = {};
    Object.keys(roster).forEach(cat => {
      const matches = roster[cat].filter(agent =>
        agent.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        agent.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
      if (matches.length > 0) filtered[cat] = matches;
    });

    debugLog('filteredRoster', 'Filtered result', { categories: Object.keys(filtered), totalAgents: Object.values(filtered).flat().length });
    return filtered;
  }, [roster, searchTerm]);

  // Auto-expand category if search is active
  useEffect(() => {
    debugLog('useEffect', 'Search category expansion', { searchTerm });
    if (searchTerm) {
      const firstCat = Object.keys(filteredRoster)[0];
      if (firstCat) {
        debugLog('useEffect', 'Expanding category', firstCat);
        setSelectedCategory(firstCat);
      }
    }
  }, [searchTerm, filteredRoster]);

  const activeAgentList = Object.keys(activeAgents);
  debugState('activeAgentList', activeAgentList);

  const categories = Object.keys(filteredRoster);
  debugState('categories', categories);

  // ============================================
  // RENDER
  // ============================================

  debugLog('App', 'Rendering JSX', {
    statusOnline: status.status === 'online',
    activeAgentCount: activeAgentList.length,
    categoryCount: categories.length,
    fileCount: files.length,
    chatMessageCount: chatHistory.length
  });
  debugger; // BREAKPOINT: Before JSX render

  return (
    <div className="flex h-screen bg-background text-text font-mono overflow-hidden selection:bg-primary/30">
      <div className="scanline"></div>

      {/* P7: Toast Notification */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg border shadow-lg animate-in fade-in slide-in-from-top-2 ${toast.type === 'error'
          ? 'bg-red-500/10 border-red-500/30 text-red-400'
          : 'bg-primary/10 border-primary/30 text-primary'
          }`}>
          <div className="flex items-center gap-2">
            <span className="text-sm">{toast.message}</span>
            <button
              onClick={() => setToast(null)}
              className="text-xs opacity-50 hover:opacity-100"
            >
              ✕
            </button>
          </div>
        </div>
      )}

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
            <div className={`px-2 py-1 rounded border flex items-center gap-2 transition-colors ${status.status === 'online' ? 'bg-primary/10 text-primary border-primary/30' : retryCount > 0 && retryCount < MAX_RETRIES ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30' : 'bg-red-500/10 text-red-400 border-red-500/30'}`}>
              <div className={`w-1.5 h-1.5 rounded-full ${status.status === 'online' ? 'bg-primary animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]' : retryCount > 0 && retryCount < MAX_RETRIES ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'}`}></div>
              {status.status === 'online' ? 'ONLINE' : retryCount > 0 && retryCount < MAX_RETRIES ? `RETRY ${retryCount}/${MAX_RETRIES}` : 'OFFLINE'}
            </div>
            <div className={`px-2 py-1 rounded border ${status.driver_initialized ? 'border-accent/30 text-accent bg-accent/10' : 'border-border text-textDim'}`}>
              DRIVER: {status.driver_initialized ? 'ON' : 'OFF'}
            </div>
          </div>

          {/* P6: Connection Error Message */}
          {connectionError && (
            <div className="mb-4 p-2 bg-red-500/10 border border-red-500/30 rounded text-red-400 text-xs">
              {connectionError}
            </div>
          )}
          <div className="relative group">
            <div className="absolute left-2.5 top-1/2 -translate-y-1/2 text-textDim group-focus-within:text-primary transition-colors">
              <Search size={14} />
            </div>
            <input
              type="text"
              placeholder="SEARCH AGENTS..."
              value={searchTerm}
              onChange={(e) => {
                debugEvent('searchInput.onChange', { value: e.target.value });
                setSearchTerm(e.target.value);
              }}
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
                  onClick={() => {
                    debugEvent('categoryButton.onClick', { category, wasSelected: category === selectedCategory });
                    setSelectedCategory(category === selectedCategory ? null : category);
                  }}
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
                                onClick={(e) => {
                                  e.stopPropagation();
                                  debugEvent('spawnButton.onClick', { agentId: agent.id });
                                  handleSpawn(agent.id);
                                }}
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
                          onClick={() => {
                            debugEvent('killButton.onClick', { agentId: id });
                            handleKill(id);
                          }}
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
                          onClick={() => debugEvent('externalLink.onClick', { agentId: id, url: activeAgents[id].url })}
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
                        onClick={() => {
                          debugEvent('parseButton.onClick', { filename: file.filename });
                          handleParse(file.filename);
                        }}
                        className="p-1 hover:bg-primary/20 hover:text-primary rounded"
                        title="Parse Text"
                      >
                        <FileText size={12} />
                      </button>
                      <button
                        onClick={() => {
                          debugEvent('deleteButton.onClick', { filename: file.filename });
                          handleDeleteFile(file.filename);
                        }}
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
                  onClick={() => {
                    debugEvent('targetMenuButton.onClick', { showTargetMenu: !showTargetMenu });
                    setShowTargetMenu(!showTargetMenu);
                  }}
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
                        onClick={() => {
                          debugEvent('broadcastButton.onClick');
                          setTargetAgentId(null);
                          setShowTargetMenu(false);
                        }}
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
                          onClick={() => {
                            debugEvent('targetAgentButton.onClick', { agentId: id });
                            setTargetAgentId(id);
                            setShowTargetMenu(false);
                          }}
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
                  onChange={(e) => {
                    debugEvent('chatInput.onChange', { value: e.target.value.substring(0, 20) });
                    setChatInput(e.target.value);
                  }}
                  placeholder={targetAgentId ? `Command ${targetAgentId}...` : "Broadcast command to all agents..."}
                  className="w-full bg-background/80 border border-border rounded-lg pl-10 pr-24 py-3.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 text-white placeholder-textDim/30 shadow-inner font-mono transition-all"
                />
                <button
                  type="submit"
                  disabled={!chatInput.trim()}
                  onClick={() => debugEvent('sendButton.onClick', { hasInput: !!chatInput.trim() })}
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
