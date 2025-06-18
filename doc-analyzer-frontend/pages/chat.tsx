// app/chat/page.tsx
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Head from 'next/head';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'
import { Layout } from '@/components/layout/Layout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';
import { FixedSizeList as List } from 'react-window';
import { useDocuments } from '@/hooks/useDocuments';
import { 
  Send, 
  MessageSquare, 
  BarChart3, 
  Bot,
  User,
  Trash2,
  Download,
  Plus,
  Sparkles,
  X,
  File,
  AlertTriangle
} from 'lucide-react';

// --- Types ---
interface ChatSession {
  session_id: string;
  chat_type: 'general' | 'analytical';
  title: string;
  document_id?: string;
  last_activity: string;
  document_name?: string; // Used for the welcome screen
}

interface ChatMessage {
  role: 'user' | 'assistant' | 'thinking'; // 'thinking' role for the indicator
  content: string;
  timestamp: string;
  metadata?: {
    show_download_button?: boolean;
    download_id?: string;
  };
}

interface Document {
  id: string;
  filename: string;
}

// --- Helper Functions ---
const formatISTDate = (isoDate: string) => {
  if (!isoDate) return "a moment ago";
  try {
    const date = new Date(isoDate);
    return date.toLocaleString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  } catch (e) {
    return "a moment ago";
  }
};

const VirtualizedTable: React.FC<{ markdown: string }> = ({ markdown }) => {
  // 1. Parse the markdown string into headers and rows
  const lines = markdown.trim().split('\n');
  const headers = lines[0].split('|').map(h => h.trim()).slice(1, -1);
  // Filter out the separator line ' |---|---| '
  const rows = lines.slice(2).map(line => line.split('|').map(cell => cell.trim()).slice(1, -1));

  // 2. Define the Row component that react-window will render
  const Row = ({ index, style }: { index: number, style: React.CSSProperties }) => (
    <div style={style} className="flex items-center border-b border-blue-500/20">
      {rows[index].map((cell, cellIndex) => (
        <div key={cellIndex} className="p-2 text-sm flex-1 min-w-[150px] truncate">
          {cell}
        </div>
      ))}
    </div>
  );

  return (
    <div className="bg-dark-900/50 border border-blue-500/30 rounded-lg overflow-hidden">
      {/* Fixed Header */}
      <div className="flex items-center bg-dark-700 font-bold text-white/90 sticky top-0 z-10">
        {headers.map((header, index) => (
          <div key={index} className="p-2 text-sm flex-1 min-w-[150px]">
            {header}
          </div>
        ))}
      </div>
      
      {/* Virtualized List Container */}
      <div className="w-full h-[400px]"> {/* Fixed height for the scrollable area */}
        <List
          height={400} // The height of the list viewport
          itemCount={rows.length} // Total number of rows
          itemSize={40} // The height of a single row in pixels
          width="100%" // Take the full width of the parent
        >
          {Row}
        </List>
      </div>
    </div>
  );
};

// --- Reusable UI Components ---

const MessageBubble: React.FC<{ message: ChatMessage; onDownload: (id: string) => void }> = ({ message, onDownload }) => {
  const isUser = message.role === 'user';
  
  if (message.role === 'thinking') {
    return (
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center bg-dark-700">
          <Bot className="w-5 h-5 text-blue-400" />
        </div>
        <div className="max-w-2xl rounded-2xl p-4 bg-dark-800 border border-blue-500/20 text-blue-100 rounded-bl-none">
          <motion.div className="flex gap-1.5">
            <motion.div animate={{ y: [0, -3, 0] }} transition={{ duration: 0.8, repeat: Infinity, delay: 0 }} className="w-2 h-2 bg-blue-400 rounded-full" />
            <motion.div animate={{ y: [0, -3, 0] }} transition={{ duration: 0.8, repeat: Infinity, delay: 0.1 }} className="w-2 h-2 bg-blue-400 rounded-full" />
            <motion.div animate={{ y: [0, -3, 0] }} transition={{ duration: 0.8, repeat: Infinity, delay: 0.2 }} className="w-2 h-2 bg-blue-400 rounded-full" />
          </motion.div>
        </div>
      </motion.div>
    );
  }

  const cleanContent = message.content.replace(/(\r\n|\n|\r)/gm, "\n").replace(/(\|---\|.*\|)(\s*\|)/g, '$1\n$2');

  // --- KEY LOGIC CHANGE ---
  // Heuristic: If a message has more than 20 lines and contains table syntax,
  // we assume it's a large table and use the virtualized renderer.
  const isLargeTable = cleanContent.split('\n').length > 20 && cleanContent.includes('|---|');


  return (
  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={`flex items-start gap-3 ${isUser ? 'justify-end' : ''}`}>
    {!isUser && (
        <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center bg-dark-700">
          <Bot className="w-5 h-5 text-blue-400" />
        </div>
    )}
    <div className={`max-w-3xl rounded-2xl p-4 ${isUser ? 'bg-blue-600 text-white rounded-br-none' : 'bg-dark-800 border border-blue-500/20 text-blue-100 rounded-bl-none'}`}>
      {
        // Heuristic: If a message has more than 20 lines and contains table syntax,
        // we assume it's a large table and use the virtualized renderer.
        cleanContent.split('\n').length > 20 && cleanContent.includes('|---|') ? (
          <VirtualizedTable markdown={cleanContent} />
        ) : (
          <ReactMarkdown
            className="prose prose-invert prose-sm max-w-none prose-table:w-full prose-table:table-auto prose-th:text-left prose-th:bg-dark-700 prose-th:p-2 prose-td:p-2 prose-tr:border-b prose-tr:border-blue-500/20"
            remarkPlugins={[remarkGfm]}
          >
            {cleanContent}
          </ReactMarkdown>
        )
      }

      {/* This logic will still work perfectly for the download button */}
      {message.metadata?.show_download_button && message.metadata.download_id && (
        <div className="mt-4 pt-4 border-t border-blue-500/30">
          <Button size="sm" variant="secondary" icon={<Download className="w-4 h-4" />} onClick={() => onDownload(message.metadata!.download_id!)}>
            Download Modified Table (Excel)
          </Button>
        </div>
      )}
    </div>
     {isUser && (
        <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center bg-blue-600">
          <User className="w-4 h-4 text-white" />
        </div>
    )}
  </motion.div>
);
};

const NewChatModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onStartChat: (type: 'general' | 'analytical', docId: string | null) => void;
  documents: Document[];
}> = ({ isOpen, onClose, onStartChat, documents }) => {
  const [tab, setTab] = useState<'general' | 'analytical'>('general');
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);

  const canStartAnalytical = documents.length > 0;
  const isStartDisabled = tab === 'analytical' && !selectedDoc;

  const handleStart = () => { onStartChat(tab, selectedDoc); onClose(); };

  if (!isOpen) return null;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={onClose}>
      <motion.div initial={{ scale: 0.95, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95, y: -20 }} onClick={(e) => e.stopPropagation()} className="bg-dark-800 border border-blue-500/20 w-full max-w-lg rounded-2xl shadow-xl flex flex-col">
        <div className="p-6 border-b border-blue-500/10 flex justify-between items-center">
          <h2 className="text-xl font-bold text-white">Start a New Chat</h2>
          <Button variant="ghost" size="sm" onClick={onClose}><X /></Button>
        </div>
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-2 bg-dark-900/50 p-1 rounded-lg">
            <Button variant={tab === 'general' ? 'secondary' : 'ghost'} onClick={() => setTab('general')}><MessageSquare className="w-4 h-4 mr-2" /> General</Button>
            <Button variant={tab === 'analytical' ? 'secondary' : 'ghost'} onClick={() => setTab('analytical')}><BarChart3 className="w-4 h-4 mr-2" /> Analytical</Button>
          </div>
          <div>
            {tab === 'general' && (
              <>
                <p className="text-sm text-blue-300/70 mb-3">Ask general questions or optionally select a document for context.</p>
                <select onChange={(e) => setSelectedDoc(e.target.value || null)} className="w-full bg-dark-700 border border-blue-500/30 rounded-lg px-3 py-2 text-white">
                  <option value="">No Document Selected</option>
                  {documents.map(doc => <option key={doc.id} value={doc.id}>{doc.filename}</option>)}
                </select>
              </>
            )}
            {tab === 'analytical' && (
              <>
                <p className="text-sm text-blue-300/70 mb-3">You must select a document to perform data analysis and ask specific questions.</p>
                {!canStartAnalytical ? (
                  <div className="text-center p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                    <AlertTriangle className="w-8 h-8 mx-auto text-amber-400 mb-2" />
                    <p className="font-semibold text-amber-300">No Documents Found</p>
                    <p className="text-xs text-amber-300/70">Please upload a document before starting an analytical chat.</p>
                  </div>
                ) : (
                  <select onChange={(e) => setSelectedDoc(e.target.value)} defaultValue="" className="w-full bg-dark-700 border border-blue-500/30 rounded-lg px-3 py-2 text-white">
                    <option value="" disabled>Select a document...</option>
                    {documents.map(doc => <option key={doc.id} value={doc.id}>{doc.filename}</option>)}
                  </select>
                )}
              </>
            )}
          </div>
        </div>
        <div className="p-6 border-t border-blue-500/10 flex justify-end">
          <Button onClick={handleStart} disabled={isStartDisabled} className="bg-gradient-to-r from-blue-500 to-cyan-500">Start Chat</Button>
        </div>
      </motion.div>
    </motion.div>
  );
};

const ChatSidebar: React.FC<{
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChatClick: () => void;
  onDeleteSession: (id: string) => void;
}> = ({ sessions, activeSessionId, onSelectSession, onNewChatClick, onDeleteSession }) => {
  return (
    <div className="bg-dark-900/50 border-r border-blue-500/20 flex flex-col h-full w-[340px]">
      <div className="p-4 flex-shrink-0"><h2 className="text-lg font-bold text-white">Chat History</h2></div>
      <div className="flex-1 overflow-y-auto px-4 space-y-3">
        {sessions.map(session => (
          <motion.div key={session.session_id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} onClick={() => onSelectSession(session.session_id)} className={`p-4 border rounded-xl cursor-pointer group relative transition-all duration-200 ${activeSessionId === session.session_id ? 'bg-blue-600/20 border-blue-500' : 'bg-dark-800/50 border-blue-500/20 hover:border-blue-500/50 hover:bg-dark-800'}`}>
            <p className="font-semibold text-white text-sm truncate mb-1">{session.title}</p>
            <div className="text-xs text-blue-300/60 flex items-center gap-2">
              {session.chat_type === 'analytical' ? <BarChart3 className="w-3 h-3" /> : <MessageSquare className="w-3 h-3" />}
              <span>{formatISTDate(session.last_activity)}</span>
            </div>
            <Button size="sm" variant="ghost" className="absolute top-2 right-2 opacity-0 group-hover:opacity-100" onClick={(e) => { e.stopPropagation(); onDeleteSession(session.session_id); }}><Trash2 className="w-4 h-4 text-red-500" /></Button>
          </motion.div>
        ))}
      </div>
      <div className="p-4 border-t border-blue-500/20">
        <Button onClick={onNewChatClick} className="w-full bg-gradient-to-r from-blue-500 to-cyan-500"><Plus className="w-5 h-5 mr-2" /> New Chat</Button>
      </div>
    </div>
  );
};

const ChatHome: React.FC = () => (
    <div className="flex flex-col items-center justify-center h-full text-center"><Sparkles className="w-16 h-16 text-blue-400 mb-4" /><h2 className="text-2xl font-bold text-white">AI Chat</h2><p className="text-blue-300/70 mt-2">Select a session from the sidebar or start a new chat.</p></div>
);

const NewChatWelcomeScreen: React.FC<{ session: ChatSession | undefined }> = ({ session }) => {
  if (!session) return <ChatHome />;
  const isAnalytical = session.chat_type === 'analytical';
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <div className="w-16 h-16 bg-dark-800 border border-blue-500/20 rounded-2xl flex items-center justify-center mb-4">
        {isAnalytical ? <BarChart3 className="w-8 h-8 text-blue-400" /> : <MessageSquare className="w-8 h-8 text-blue-400" />}
      </div>
      <h2 className="text-2xl font-bold text-white">New {isAnalytical ? 'Analytical' : 'General'} Chat</h2>
      <p className="text-blue-300/70 mt-2 max-w-md">
        {isAnalytical && session.document_name ? `You can now ask questions specifically about ${session.document_name}.` : 'Ready for your questions. Type in the input box below to get started.'}
      </p>
    </div>
  );
};

// --- Main Chat Page Component ---

const ChatPage: React.FC = () => {
  const { user } = useAuth();
  const { documents } = useDocuments();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => { if (user) loadChatSessions(); }, [user, documents]);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const loadChatSessions = async () => {
    if (!user) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/chat/sessions?limit=50`, { headers: { 'Authorization': `Bearer ${token}` } });
      const data = await response.json();
      if (data.success) {
        const mappedSessions = data.sessions.map((s: any) => ({ ...s, document_name: documents.find(d => d.id === s.document_id)?.filename || 'Unknown Document' }));
        setSessions(mappedSessions);
      }
    } catch (error) { console.error('Failed to load sessions:', error); }
  };

  const loadChatHistory = async (sessionId: string) => {
    setMessages([]);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}/history`, { headers: { 'Authorization': `Bearer ${token}` } });
      const data = await response.json();
      if (data.success) setMessages(data.messages);
    } catch (error) { console.error('Failed to load history:', error); }
  };

  const handleSelectSession = (sessionId: string) => {
    setActiveSessionId(sessionId);
    loadChatHistory(sessionId);
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${API_BASE}/chat/sessions/${sessionId}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } });
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
      loadChatSessions();
    } catch (error) { console.error('Failed to delete session:', error); }
  };

  const handleNewChat = async (chatType: 'general' | 'analytical', documentId: string | null) => {
    if (!user) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/chat/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ chat_type: chatType, document_id: documentId })
      });
      const data = await response.json();
      if (data.success) {
        await loadChatSessions();
        setActiveSessionId(data.session_id);
        setMessages([]);
      }
    } catch (error) { console.error('Failed to start new session:', error); }
  };

  const handleSendMessage = async () => {
    if (!inputText.trim() || !activeSessionId || !user || messages.some(m => m.role === 'thinking')) return;
    
    const userMessage: ChatMessage = { role: 'user', content: inputText.trim(), timestamp: new Date().toISOString() };
    const thinkingMessage: ChatMessage = { role: 'thinking', content: '', timestamp: new Date().toISOString() };
    
    setMessages(prev => [...prev, userMessage, thinkingMessage]);
    setInputText('');
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ session_id: activeSessionId, message: userMessage.content })
      });
      const data = await response.json();
      const assistantMessage: ChatMessage = { role: 'assistant', content: data.success ? data.response : 'Sorry, I encountered an error.', timestamp: new Date().toISOString(), metadata: data.success ? data.frontend : undefined };
      setMessages(prev => [...prev.slice(0, -1), assistantMessage]);
      if (data.success) loadChatSessions();
    } catch (error) {
      const errorMessage: ChatMessage = { role: 'assistant', content: 'There was a connection error. Please try again.', timestamp: new Date().toISOString() };
      setMessages(prev => [...prev.slice(0, -1), errorMessage]);
      console.error('Failed to send message:', error);
    }
  };

  const handleDownload = async (downloadId: string) => {
    try {
      const response = await fetch(`${API_BASE}/chat/download/table/${downloadId}?format=excel`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if(response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `table_data_${downloadId}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
      }
    } catch (error) { console.error('Download failed:', error); }
  };

  const activeSession = sessions.find(s => s.session_id === activeSessionId);
  const showNewChatWelcome = activeSessionId && messages.length === 0;

  return (
    <ProtectedRoute>
      <Head><title>AI Chat - Professional</title></Head>
      <Layout title="AI Chat Interface">
        <div className="flex h-[calc(100vh-80px)] bg-dark-900 text-white">
          <ChatSidebar sessions={sessions} activeSessionId={activeSessionId} onSelectSession={handleSelectSession} onNewChatClick={() => setIsModalOpen(true)} onDeleteSession={handleDeleteSession} />
          <main className="flex-1 flex flex-col">
            {activeSessionId ? (
              <>
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {showNewChatWelcome ? <NewChatWelcomeScreen session={activeSession} /> : messages.map((msg, idx) => <MessageBubble key={idx} message={msg} onDownload={handleDownload} />)}
                  <div ref={messagesEndRef} />
                </div>
                <div className="p-4 border-t border-blue-500/20">
                  <div className="flex items-center gap-4">
                    <textarea value={inputText} onChange={(e) => setInputText(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); }}} placeholder="Type your message..." className="w-full bg-dark-800 border border-blue-500/30 rounded-lg p-3 resize-none focus:ring-2 focus:ring-blue-500" rows={1} disabled={messages.some(m => m.role === 'thinking')} />
                    <Button onClick={handleSendMessage} disabled={!inputText.trim() || messages.some(m => m.role === 'thinking')}><Send className="w-5 h-5"/></Button>
                  </div>
                </div>
              </>
            ) : <ChatHome />}
          </main>
        </div>
        <AnimatePresence>
          {isModalOpen && <NewChatModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onStartChat={handleNewChat} documents={documents} />}
        </AnimatePresence>
      </Layout>
    </ProtectedRoute>
  );
};

export default ChatPage;
