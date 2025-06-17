'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Head from 'next/head';
import ReactMarkdown from 'react-markdown';
import { Layout } from '@/components/layout/Layout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';
import { useDocuments } from '@/hooks/useDocuments';
import { formatTimeAgo } from '@/lib/dateUtils';
import { 
  Send, 
  Loader2, 
  MessageSquare, 
  BarChart3, 
  Eye, 
  Bot,
  User,
  Trash2,
  Download,
  Plus,
  FileText,
  AlertCircle,
  Upload,
  X,
  ChevronDown,
  Sparkles,
  History
} from 'lucide-react';

// Types
interface ChatSession {
  session_id: string;
  chat_type: string;
  title: string;
  document_id?: string;
  message_count: number;
  created_at: string;
  updated_at: string;
  last_activity: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: {
    response_type?: string;
    show_download_button?: boolean;
    download_id?: string;
    modified_table_markdown?: string;
    has_image?: boolean;
    image_base64?: string;
    images_analyzed?: string[];
  };
}

interface ApiResponse {
  success: boolean;
  response: string;
  metadata?: {
    image_base64?: string;
    [key: string]: any;
  };
  frontend?: {
    response_type: string;
    show_download_button: boolean;
    download_id?: string;
    has_image: boolean;
    modified_table?: string;
  };
}

const CHAT_MODES = [
  { 
    value: 'general', 
    label: 'General Chat', 
    icon: MessageSquare, 
    color: 'from-blue-500 to-blue-600',
    description: 'Ask general questions',
    requiresDocument: false
  },
  { 
    value: 'analytical', 
    label: 'Analytical Chat', 
    icon: BarChart3, 
    color: 'from-purple-500 to-purple-600',
    description: 'Analyze data and tables',
    requiresDocument: true
  },
  { 
    value: 'visualization', 
    label: 'Visualization Chat', 
    icon: Eye, 
    color: 'from-emerald-500 to-emerald-600',
    description: 'Generate charts and graphs',
    requiresDocument: true
  }
];

// ✅ TYPING ANIMATION COMPONENT
const TypingIndicator: React.FC = () => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    className="flex items-center space-x-2 p-4 bg-dark-800/80 rounded-2xl rounded-bl-md max-w-xs border border-blue-500/20"
  >
    <div className="flex space-x-1">
      <motion.div
        className="w-2 h-2 bg-blue-400 rounded-full"
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
      />
      <motion.div
        className="w-2 h-2 bg-blue-400 rounded-full"
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
      />
      <motion.div
        className="w-2 h-2 bg-blue-400 rounded-full"
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
      />
    </div>
    <span className="text-sm text-blue-300 font-medium">AI is thinking...</span>
  </motion.div>
);

// ✅ CHAT STARTER COMPONENT
const ChatStarter: React.FC<{
  onStartChat: (chatType: string, documentId: string | null) => void;
  documents: any[];
}> = ({ onStartChat, documents }) => {
  const [selectedMode, setSelectedMode] = useState<string>('general');
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);
  const [showDocumentRequired, setShowDocumentRequired] = useState(false);

  const selectedModeInfo = CHAT_MODES.find(m => m.value === selectedMode);
  const requiresDocument = selectedModeInfo?.requiresDocument || false;
  const hasDocuments = documents.length > 0;

  const handleStartChat = () => {
    if (requiresDocument && !selectedDoc && hasDocuments) {
      setShowDocumentRequired(true);
      return;
    }

    onStartChat(selectedMode, selectedDoc);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto p-8"
    >
      <div className="text-center mb-12">
        <div className="w-20 h-20 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <Sparkles className="w-10 h-10 text-blue-400" />
        </div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-blue-200 to-cyan-300 bg-clip-text text-transparent mb-4">
          AI-Powered Document Chat
        </h1>
        <p className="text-xl text-blue-300/70 max-w-2xl mx-auto">
          Choose your chat mode and start conversing with your documents using advanced AI
        </p>
      </div>

      {/* Chat Mode Selection */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold text-white mb-6 text-center">Select Chat Mode</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {CHAT_MODES.map((mode) => {
            const Icon = mode.icon;
            return (
              <motion.div
                key={mode.value}
                className={`p-6 rounded-2xl border-2 cursor-pointer transition-all ${
                  selectedMode === mode.value
                    ? 'border-blue-500 bg-blue-500/10 shadow-lg shadow-blue-500/20'
                    : 'border-blue-500/20 hover:border-blue-500/40 bg-dark-800/50'
                }`}
                onClick={() => {
                  setSelectedMode(mode.value);
                  setShowDocumentRequired(false);
                  if (mode.requiresDocument && documents.length > 0 && !selectedDoc) {
                    setSelectedDoc(documents[0].id);
                  }
                }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="flex flex-col items-center text-center">
                  <div className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${mode.color} flex items-center justify-center mb-4`}>
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-bold text-white mb-2">{mode.label}</h4>
                  <p className="text-sm text-blue-300/70 mb-3">{mode.description}</p>
                  {mode.requiresDocument && (
                    <div className="flex items-center">
                      <AlertCircle className="w-4 h-4 text-amber-400 mr-2" />
                      <span className="text-xs text-amber-400">Document required</span>
                    </div>
                  )}
                  {selectedMode === mode.value && (
                    <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center mt-3">
                      <div className="w-3 h-3 bg-white rounded-full" />
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Document Selection */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold text-white mb-6 text-center">
          Select Document 
          {requiresDocument && (
            <span className="text-red-400 text-sm ml-2">(Required for {selectedModeInfo?.label})</span>
          )}
        </h3>

        {!hasDocuments ? (
          <div className="text-center py-12 bg-dark-800/50 rounded-2xl border-2 border-dashed border-blue-500/20">
            <Upload className="w-16 h-16 text-blue-400 mx-auto mb-4" />
            <h4 className="text-2xl font-bold text-white mb-3">No Documents Available</h4>
            <p className="text-blue-300/70 mb-6 max-w-md mx-auto">
              {requiresDocument 
                ? `${selectedModeInfo?.label} requires a document to analyze data and tables.`
                : 'Upload documents to enhance your chat experience.'
              }
            </p>
            <p className="text-sm text-blue-400/60">
              {requiresDocument 
                ? 'You can still create this chat, but you\'ll need to upload a document first.'
                : 'General chat works without documents.'
              }
            </p>
          </div>
        ) : (
          <div className="max-w-2xl mx-auto space-y-3">
            {!requiresDocument && (
              <motion.div
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  selectedDoc === null
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-blue-500/20 hover:border-blue-500/40 bg-dark-800/50'
                }`}
                onClick={() => setSelectedDoc(null)}
                whileHover={{ scale: 1.01 }}
              >
                <div className="flex items-center space-x-4">
                  <MessageSquare className="w-6 h-6 text-blue-400" />
                  <span className="font-medium text-white">No Document (General Chat)</span>
                  {selectedDoc === null && (
                    <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center ml-auto">
                      <div className="w-2 h-2 bg-white rounded-full" />
                    </div>
                  )}
                </div>
              </motion.div>
            )}
            
            {documents.map((doc) => (
              <motion.div
                key={doc.id}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  selectedDoc === doc.id
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-blue-500/20 hover:border-blue-500/40 bg-dark-800/50'
                }`}
                onClick={() => {
                  setSelectedDoc(doc.id);
                  setShowDocumentRequired(false);
                }}
                whileHover={{ scale: 1.01 }}
              >
                <div className="flex items-center space-x-4">
                  <FileText className="w-6 h-6 text-blue-400" />
                  <span className="font-medium text-white flex-1">{doc.filename}</span>
                  {selectedDoc === doc.id && (
                    <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                      <div className="w-2 h-2 bg-white rounded-full" />
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {showDocumentRequired && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl max-w-2xl mx-auto"
          >
            <div className="flex items-center space-x-3">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <span className="text-red-400">
                Please select a document for {selectedModeInfo?.label}
              </span>
            </div>
          </motion.div>
        )}
      </div>

      {/* Start Chat Button */}
      <div className="text-center">
        <Button
          onClick={handleStartChat}
          size="lg"
          className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-lg px-12 py-4 rounded-2xl shadow-lg shadow-blue-500/25"
          icon={<Plus />}
          disabled={requiresDocument && hasDocuments && !selectedDoc}
        >
          {requiresDocument && !hasDocuments 
            ? `Start ${selectedModeInfo?.label} (Upload Document First)`
            : `Start ${selectedModeInfo?.label}`
          }
        </Button>
      </div>
    </motion.div>
  );
};

const ChatPage: React.FC = () => {
  // Auth and documents
  const { user } = useAuth();
  const { documents, loading: docsLoading } = useDocuments();

  // Chat state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState<boolean>(true);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [showSessions, setShowSessions] = useState<boolean>(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // API Base URL
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Load sessions on mount
  useEffect(() => {
    loadChatSessions();
  }, []);

  // Focus input
  useEffect(() => {
    inputRef.current?.focus();
  }, [activeSessionId]);

  // Clean base64 string function
  const cleanBase64String = (base64String: string): string => {
    if (!base64String) return '';
    const cleaned = base64String.replace(/[^A-Za-z0-9+/=]/g, '');
    const padded = cleaned + '='.repeat((4 - (cleaned.length % 4)) % 4);
    return padded;
  };

  // Enhanced message content renderer
  const renderMessageContent = (message: ChatMessage) => {
    if (message.metadata?.has_image && message.metadata?.image_base64) {
      const cleanedBase64 = cleanBase64String(message.metadata.image_base64);
      
      return (
        <div>
          <ReactMarkdown
            className="prose prose-invert prose-sm max-w-none text-blue-100"
            components={{
              img: () => null,
              table: ({ children }) => (
                <div className="overflow-x-auto my-4">
                  <table className="min-w-full border border-blue-500/20 rounded-lg">
                    {children}
                  </table>
                </div>
              ),
              th: ({ children }) => (
                <th className="border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-left font-semibold text-blue-100">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="border border-blue-500/20 px-4 py-2 text-blue-200">
                  {children}
                </td>
              )
            }}
          >
            {message.content.replace(/!\[.*?\]\(data:image.*?\)/g, '')}
          </ReactMarkdown>
          
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-6 flex justify-center"
          >
            <img 
              src={`data:image/png;base64,${cleanedBase64}`}
              alt="Generated Visualization"
              className="max-w-full h-auto rounded-xl shadow-lg border border-blue-500/20"
              style={{ maxHeight: '500px' }}
              onError={(e) => {
                console.error('Image failed to load');
                e.currentTarget.style.display = 'none';
              }}
            />
          </motion.div>
        </div>
      );
    }

    return (
      <ReactMarkdown
        className="prose prose-invert prose-sm max-w-none text-blue-100"
        components={{
          img: ({ src, alt }) => (
            <img 
              src={src} 
              alt={alt} 
              className="max-w-full h-auto rounded-xl shadow-lg my-4"
            />
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full border border-blue-500/20 rounded-lg">
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-left font-semibold text-blue-100">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-blue-500/20 px-4 py-2 text-blue-200">
              {children}
            </td>
          )
        }}
      >
        {message.content}
      </ReactMarkdown>
    );
  };

  // Load chat sessions
  const loadChatSessions = async () => {
    try {
      setIsLoadingSessions(true);
      const response = await fetch(`${API_BASE}/chat/sessions`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSessions(data.sessions);
        }
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setIsLoadingSessions(false);
    }
  };

  // ✅ FIXED: Start new chat session
  const startNewSession = async (chatType: string, documentId: string | null) => {
    try {
      const response = await fetch(`${API_BASE}/chat/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          chat_type: chatType,
          document_id: documentId,
          title: documentId 
            ? `${chatType.charAt(0).toUpperCase() + chatType.slice(1)} - ${documents.find(d => d.id === documentId)?.filename}`
            : `${chatType.charAt(0).toUpperCase() + chatType.slice(1)} Chat`
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setActiveSessionId(data.session_id);
          setMessages([]);
          await loadChatSessions();

          // Add welcome message for document-required modes
          const modeInfo = CHAT_MODES.find(m => m.value === chatType);
          if (modeInfo?.requiresDocument && !documentId) {
            const welcomeMessage: ChatMessage = {
              role: 'assistant',
              content: `# ${modeInfo.label} Mode

I'm ready to help with ${chatType} tasks! However, this mode requires a document with tables and data to analyze.

**What you can do:**
1. 📄 Upload a document using the main upload feature
2. 🔄 Switch to **General Chat** for document-free conversations  
3. 📊 Once you have documents, I can help with data analysis and insights

**Supported document types:** PDF, DOCX, XLSX with tables and structured data.`,
              timestamp: new Date().toISOString()
            };
            setMessages([welcomeMessage]);
          }
        }
      }
    } catch (error) {
      console.error('Failed to start new session:', error);
    }
  };

  // Load chat history
  const loadChatHistory = async (sessionId: string) => {
    try {
      setIsLoadingHistory(true);
      const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}/history`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setMessages(data.messages);
        }
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // Select session
  const selectSession = async (sessionId: string) => {
    setActiveSessionId(sessionId);
    setShowSessions(false);
    await loadChatHistory(sessionId);
  };

  // Send message
  const sendMessage = async () => {
    if (!inputText.trim() || !activeSessionId) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    setIsTyping(true);

    try {
      const response = await fetch(`${API_BASE}/chat/message`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: activeSessionId,
          message: userMessage.content
        })
      });

      if (response.ok) {
        const data: ApiResponse = await response.json();
        if (data.success) {
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          setIsTyping(false);
          
          const assistantMessage: ChatMessage = {
            role: 'assistant',
            content: data.response,
            timestamp: new Date().toISOString(),
            metadata: {
              response_type: data.frontend?.response_type || 'text',
              show_download_button: data.frontend?.show_download_button || false,
              download_id: data.frontend?.download_id,
              modified_table_markdown: data.frontend?.modified_table,
              has_image: data.frontend?.has_image || false,
              image_base64: data.metadata?.image_base64
            }
          };

          setMessages(prev => [...prev, assistantMessage]);
          await loadChatSessions();
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setIsTyping(false);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Delete session
  const deleteSession = async (sessionId: string) => {
    try {
      const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        if (activeSessionId === sessionId) {
          setActiveSessionId(null);
          setMessages([]);
        }
        await loadChatSessions();
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  // Download table
  const downloadTable = async (downloadId: string) => {
    try {
      const response = await fetch(`${API_BASE}/chat/download/table/${downloadId}?format=excel`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `modified_table_${downloadId}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Failed to download table:', error);
    }
  };

  // Handle key down
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Get current session info
  const currentSession = sessions.find(s => s.session_id === activeSessionId);
  const currentMode = currentSession ? CHAT_MODES.find(m => m.value === currentSession.chat_type) : null;

  return (
    <ProtectedRoute>
      <Head>
        <title>AI Chat - DocAnalyzer</title>
        <meta name="description" content="Chat with your documents using AI" />
      </Head>

      {/* ✅ INTEGRATED WITH EXISTING LAYOUT */}
      <Layout title="AI Chat">
        <div className="h-[calc(100vh-100px)] bg-gradient-to-br from-dark-900 to-dark-950 flex flex-col">
          
          {/* ✅ TOP BAR WITH SESSIONS */}
          {sessions.length > 0 && (
            <div className="bg-dark-800/50 border-b border-blue-500/20 p-4">
              <div className="flex items-center justify-between max-w-6xl mx-auto">
                <div className="flex items-center space-x-4">
                  <Button
                    onClick={() => setShowSessions(!showSessions)}
                    variant="ghost"
                    className="text-blue-300 hover:text-white"
                    icon={<History />}
                  >
                    Recent Chats ({sessions.length})
                    <ChevronDown className={`w-4 h-4 ml-2 transition-transform ${showSessions ? 'rotate-180' : ''}`} />
                  </Button>
                  
                  {currentSession && (
                    <div className="flex items-center space-x-2 text-sm">
                      {currentMode && <currentMode.icon className="w-4 h-4 text-blue-400" />}
                      <span className="text-blue-300">{currentSession.title}</span>
                    </div>
                  )}
                </div>
                
                <Button
                  onClick={() => {
                    setActiveSessionId(null);
                    setMessages([]);
                  }}
                  className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
                  icon={<Plus />}
                >
                  New Chat
                </Button>
              </div>

              {/* ✅ COLLAPSIBLE SESSIONS LIST */}
              <AnimatePresence>
                {showSessions && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-4 max-w-6xl mx-auto"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto">
                      {sessions.map((session) => {
                        const mode = CHAT_MODES.find(m => m.value === session.chat_type);
                        const Icon = mode?.icon || MessageSquare;
                        
                        return (
                          <motion.div
                            key={session.session_id}
                            className={`p-3 rounded-xl cursor-pointer transition-all group relative ${
                              activeSessionId === session.session_id
                                ? 'bg-blue-500/20 border border-blue-500/40'
                                : 'bg-dark-700/50 hover:bg-dark-700 border border-transparent'
                            }`}
                            onClick={() => selectSession(session.session_id)}
                            whileHover={{ scale: 1.02 }}
                          >
                            <div className="flex items-center space-x-3">
                              <Icon className="w-4 h-4 text-blue-400 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-white truncate">
                                  {session.title}
                                </p>
                                <p className="text-xs text-blue-300/70">
                                  {formatTimeAgo(new Date(session.last_activity))}
                                </p>
                              </div>
                            </div>
                            
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteSession(session.session_id);
                              }}
                              className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 transition-all p-1"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </motion.div>
                        );
                      })}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* ✅ MAIN CONTENT AREA */}
          <div className="flex-1 overflow-hidden">
            {!activeSessionId ? (
              // ✅ CHAT STARTER
              <div className="h-full overflow-y-auto">
                <ChatStarter onStartChat={startNewSession} documents={documents} />
              </div>
            ) : (
              <div className="h-full flex flex-col">
                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto p-6">
                  <div className="max-w-4xl mx-auto space-y-6">
                    {isLoadingHistory ? (
                      <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
                      </div>
                    ) : (
                      <AnimatePresence>
                        {messages.map((message, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 20, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            transition={{ delay: index * 0.1 }}
                            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                          >
                            <div className={`flex items-start space-x-3 max-w-3xl ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                              {/* Avatar */}
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                                message.role === 'user' 
                                  ? 'bg-gradient-to-br from-blue-500 to-blue-600' 
                                  : 'bg-gradient-to-br from-cyan-500 to-teal-600'
                              }`}>
                                {message.role === 'user' ? (
                                  <User className="w-4 h-4 text-white" />
                                ) : (
                                  <Bot className="w-4 h-4 text-white" />
                                )}
                              </div>

                              {/* Message Bubble */}
                              <div className={`p-4 rounded-2xl shadow-lg ${
                                message.role === 'user'
                                  ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-br-md'
                                  : 'bg-gradient-to-br from-dark-700/50 to-dark-800/50 border border-blue-500/20 text-blue-100 rounded-bl-md'
                              }`}>
                                <div className="text-sm leading-relaxed">
                                  {renderMessageContent(message)}
                                </div>

                                {/* Download Button */}
                                {message.metadata?.show_download_button && message.metadata?.download_id && (
                                  <motion.div 
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="mt-4 pt-3 border-t border-blue-500/20"
                                  >
                                    <Button
                                      onClick={() => downloadTable(message.metadata!.download_id!)}
                                      size="sm"
                                      icon={<Download />}
                                      className="bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30"
                                    >
                                      Download Excel File
                                    </Button>
                                  </motion.div>
                                )}

                                {/* Timestamp */}
                                <div className="mt-3 pt-2 border-t border-blue-500/20">
                                  <span className={`text-xs ${message.role === 'user' ? 'text-blue-100' : 'text-blue-300/70'}`}>
                                    {new Date(message.timestamp).toLocaleTimeString([], { 
                                      hour: '2-digit', 
                                      minute: '2-digit' 
                                    })}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </motion.div>
                        ))}
                        
                        {/* Typing Indicator */}
                        {isTyping && (
                          <motion.div className="flex justify-start">
                            <div className="flex items-start space-x-3 max-w-3xl">
                              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-teal-600 flex items-center justify-center shrink-0">
                                <Bot className="w-4 h-4 text-white" />
                              </div>
                              <TypingIndicator />
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                </div>

                {/* Input Area */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-gradient-to-r from-dark-800/50 to-dark-850/50 backdrop-blur-sm border-t border-blue-500/20 p-6"
                >
                  <div className="max-w-4xl mx-auto">
                    <div className="flex items-end space-x-4">
                      {/* Message Input */}
                      <div className="flex-1 relative">
                        <textarea
                          ref={inputRef}
                          value={inputText}
                          onChange={(e) => setInputText(e.target.value)}
                          onKeyDown={handleKeyDown}
                          placeholder="Type your message..."
                          rows={1}
                          disabled={isLoading}
                          className="w-full bg-dark-700/50 border border-blue-500/30 rounded-xl px-4 py-3 text-white placeholder-blue-300/50 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all resize-none"
                          style={{ 
                            minHeight: '48px',
                            maxHeight: '120px',
                            height: Math.min(Math.max(48, inputText.split('\n').length * 24), 120)
                          }}
                        />
                      </div>

                      {/* Send Button */}
                      <Button
                        onClick={sendMessage}
                        disabled={isLoading || !inputText.trim()}
                        loading={isLoading}
                        icon={<Send />}
                        className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 disabled:opacity-50 px-6 py-3"
                      >
                        Send
                      </Button>
                    </div>

                    {/* Input Hint */}
                    <div className="flex items-center justify-between mt-3 text-xs text-blue-300/50">
                      <span>Press Enter to send, Shift+Enter for new line</span>
                      <span className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                        <span>AI Ready</span>
                      </span>
                    </div>
                  </div>
                </motion.div>
              </div>
            )}
          </div>
        </div>
      </Layout>
    </ProtectedRoute>
  );
};

export default ChatPage;
