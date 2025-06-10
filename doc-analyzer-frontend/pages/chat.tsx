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
  History,
  Settings
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
    image_base64?: string;  // ✅ Added this
    images_analyzed?: string[];
  };
}

interface ApiResponse {
  success: boolean;
  response: string;
  metadata?: {
    image_base64?: string;  // ✅ Added this
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
    color: 'blue',
    description: 'Ask general questions about your document'
  },
  { 
    value: 'analytical', 
    label: 'Analytical Chat', 
    icon: BarChart3, 
    color: 'purple',
    description: 'Get insights, analysis, and modify tables'
  },
  { 
    value: 'visualization', 
    label: 'Visualization Chat', 
    icon: Eye, 
    color: 'green',
    description: 'Generate charts and visual representations'
  }
];

const ChatPage: React.FC = () => {
  // Auth and documents
  const { user } = useAuth();
  const { documents, loading: docsLoading } = useDocuments();

  // Chat state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [chatMode, setChatMode] = useState<string>('general');
  const [inputText, setInputText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState<boolean>(true);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // API Base URL
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load sessions on mount
  useEffect(() => {
    loadChatSessions();
  }, []);

  // Focus input
  useEffect(() => {
    inputRef.current?.focus();
  }, [activeSessionId]);

  // ✅ ENHANCED: Clean base64 string function
  const cleanBase64String = (base64String: string): string => {
    if (!base64String) return '';
    // Remove any non-base64 characters and ensure proper padding
    const cleaned = base64String.replace(/[^A-Za-z0-9+/=]/g, '');
    // Ensure proper padding
    const padded = cleaned + '='.repeat((4 - (cleaned.length % 4)) % 4);
    return padded;
  };

  // ✅ ENHANCED: Message content renderer
  const renderMessageContent = (message: ChatMessage) => {
    // Check if this is a visualization with image
    if (message.metadata?.has_image && message.metadata?.image_base64) {
      const cleanedBase64 = cleanBase64String(message.metadata.image_base64);
      
      return (
        <div>
          {/* Render text content without any image markdown */}
          <ReactMarkdown
            className="prose prose-invert prose-sm max-w-none"
            components={{
              // Remove img components to prevent markdown image rendering
              img: () => null,
              table: ({ children }) => (
                <div className="overflow-x-auto my-4">
                  <table className="min-w-full border border-blue-500/20 rounded-lg">
                    {children}
                  </table>
                </div>
              ),
              th: ({ children }) => (
                <th className="border border-blue-500/20 bg-blue-500/10 px-3 py-2 text-left">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="border border-blue-500/20 px-3 py-2">
                  {children}
                </td>
              )
            }}
          >
            {message.content.replace(/!\[.*?\]\(data:image.*?\)/g, '')}
          </ReactMarkdown>
          
          {/* Render image separately with error handling */}
          <div className="mt-4 flex justify-center">
            <img 
              src={`data:image/png;base64,${cleanedBase64}`}
              alt="Generated Visualization"
              className="max-w-full h-auto rounded-lg shadow-lg border border-blue-500/20"
              style={{ maxHeight: '500px' }}
              onError={(e) => {
                console.error('Image failed to load');
                e.currentTarget.style.display = 'none';
                // Show fallback message
                const fallback = document.createElement('div');
                fallback.innerHTML = '❌ Visualization failed to render';
                fallback.className = 'text-red-400 p-4 border border-red-500/20 rounded-lg text-center';
                e.currentTarget.parentNode?.appendChild(fallback);
              }}
              onLoad={() => {
                console.log('✅ Visualization image loaded successfully');
              }}
            />
          </div>
        </div>
      );
    }

    // Regular message rendering for non-visualization messages
    return (
      <ReactMarkdown
        className="prose prose-invert prose-sm max-w-none"
        components={{
          img: ({ src, alt }) => (
            <img 
              src={src} 
              alt={alt} 
              className="max-w-full h-auto rounded-lg shadow-lg my-4"
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
            <th className="border border-blue-500/20 bg-blue-500/10 px-3 py-2 text-left">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-blue-500/20 px-3 py-2">
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

  // Start new chat session
  const startNewSession = async () => {
    try {
      const response = await fetch(`${API_BASE}/chat/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          chat_type: chatMode,
          document_id: selectedDocId,
          title: selectedDocId 
            ? `${chatMode.charAt(0).toUpperCase() + chatMode.slice(1)} - ${documents.find(d => d.id === selectedDocId)?.filename}`
            : `${chatMode.charAt(0).toUpperCase() + chatMode.slice(1)} Chat`
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setActiveSessionId(data.session_id);
          setMessages([]);
          await loadChatSessions();
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
    const session = sessions.find(s => s.session_id === sessionId);
    if (session) {
      setChatMode(session.chat_type);
      setSelectedDocId(session.document_id || null);
    }
    await loadChatHistory(sessionId);
  };

  // ✅ ENHANCED: Send message with proper image metadata handling
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
              image_base64: data.metadata?.image_base64  // ✅ Get image from metadata
            }
          };

          setMessages(prev => [...prev, assistantMessage]);
          await loadChatSessions();
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
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

  // Get selected document
  const selectedDocument = documents.find(doc => doc.id === selectedDocId);

  return (
    <ProtectedRoute>
      <Head>
        <title>AI Chat - DocAnalyzer</title>
        <meta name="description" content="Chat with your documents using AI" />
      </Head>

      <Layout title="AI Chat">
        <div className="flex h-[calc(100vh-100px)] max-w-full mx-auto bg-gradient-to-br from-dark-900 to-dark-950">
          
          {/* Chat History Sidebar */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="w-80 bg-gradient-to-b from-dark-800/50 to-dark-850/50 backdrop-blur-sm border-r border-blue-500/20 flex flex-col"
          >
            {/* Sidebar Header */}
            <div className="p-4 border-b border-blue-500/20">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center">
                  <History className="w-5 h-5 mr-2 text-blue-400" />
                  Chat History
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={startNewSession}
                  icon={<Plus />}
                  className="text-blue-400 hover:text-white hover:bg-blue-500/20"
                >
                  New
                </Button>
              </div>

              {/* Document Selection */}
              <div className="mb-3">
                <label className="block text-blue-300/70 text-xs mb-1">Document</label>
                <select
                  value={selectedDocId || ''}
                  onChange={(e) => setSelectedDocId(e.target.value || null)}
                  className="w-full bg-dark-700/50 border border-blue-500/30 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                >
                  <option value="">No Document</option>
                  {documents.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {doc.filename}
                    </option>
                  ))}
                </select>
              </div>

              {/* Mode Selection */}
              <div>
                <label className="block text-blue-300/70 text-xs mb-1">Chat Mode</label>
                <select
                  value={chatMode}
                  onChange={(e) => setChatMode(e.target.value)}
                  className="w-full bg-dark-700/50 border border-blue-500/30 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                >
                  {CHAT_MODES.map((mode) => (
                    <option key={mode.value} value={mode.value}>
                      {mode.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Sessions List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {isLoadingSessions ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
                </div>
              ) : sessions.length === 0 ? (
                <div className="text-center py-8 text-blue-300/50">
                  <MessageSquare className="w-8 h-8 mx-auto mb-2" />
                  <p>No chat sessions yet</p>
                </div>
              ) : (
                sessions.map((session) => (
                  <motion.div
                    key={session.session_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`p-3 rounded-lg cursor-pointer transition-all group ${
                      activeSessionId === session.session_id
                        ? 'bg-blue-500/20 border border-blue-500/40'
                        : 'bg-dark-700/30 hover:bg-dark-700/50 border border-transparent'
                    }`}
                    onClick={() => selectSession(session.session_id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          {(() => {
                            const mode = CHAT_MODES.find(m => m.value === session.chat_type);
                            const Icon = mode?.icon || MessageSquare;
                            return <Icon className="w-4 h-4 text-blue-400 shrink-0" />;
                          })()}
                          <span className="text-white text-sm font-medium truncate">
                            {session.title}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2 text-xs text-blue-300/70">
                          <span>{session.message_count} messages</span>
                          <span>•</span>
                          <span>{formatTimeAgo(new Date(session.last_activity))}</span>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteSession(session.session_id);
                        }}
                        className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-white hover:bg-red-500/20 ml-2"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </motion.div>

          {/* Chat Area */}
          <div className="flex-1 flex flex-col">
            {/* Chat Header */}
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-r from-dark-800/50 to-dark-850/50 backdrop-blur-sm border-b border-blue-500/20 p-6"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                    <Bot className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold bg-gradient-to-r from-white via-blue-200 to-cyan-300 bg-clip-text text-transparent">
                      {activeSessionId ? 'AI Assistant' : 'Start New Chat'}
                    </h2>
                    <div className="flex items-center space-x-2 text-sm">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                      <span className="text-blue-300/70">
                        {selectedDocument 
                          ? `Analyzing ${selectedDocument.filename}` 
                          : activeSessionId 
                            ? `${CHAT_MODES.find(m => m.value === chatMode)?.label} Mode`
                            : 'Select document and mode to start'
                        }
                      </span>
                    </div>
                  </div>
                </div>

                {activeSessionId && (
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-blue-300/70 bg-blue-500/10 px-2 py-1 rounded">
                      {CHAT_MODES.find(m => m.value === chatMode)?.label}
                    </span>
                  </div>
                )}
              </div>
            </motion.div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto bg-gradient-to-br from-dark-850 to-dark-900 p-6">
              <div className="max-w-4xl mx-auto space-y-6">
                {!activeSessionId ? (
                  // Welcome screen
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center py-12"
                  >
                    <div className="w-20 h-20 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                      <Bot className="w-10 h-10 text-blue-400" />
                    </div>
                    <h3 className="text-2xl font-bold text-white mb-4">
                      Welcome to AI Chat
                    </h3>
                    <p className="text-blue-300/70 max-w-md mx-auto mb-6">
                      Select a document and chat mode, then click "New" to start a conversation.
                    </p>
                    <Button
                      onClick={startNewSession}
                      disabled={!chatMode}
                      icon={<Plus />}
                      className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
                    >
                      Start New Chat
                    </Button>
                  </motion.div>
                ) : isLoadingHistory ? (
                  // Loading history
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
                  </div>
                ) : messages.length === 0 ? (
                  // Empty chat
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center py-12"
                  >
                    <MessageSquare className="w-16 h-16 text-blue-400 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">Ready to Chat</h3>
                    <p className="text-blue-300/70">
                      Type a message below to start the conversation.
                    </p>
                  </motion.div>
                ) : (
                  // Messages
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
                              ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
                              : 'bg-gradient-to-br from-dark-700/50 to-dark-800/50 border border-blue-500/20 text-blue-100'
                          }`}>
                            {/* ✅ ENHANCED: Use the new message content renderer */}
                            <div className="text-sm leading-relaxed">
                              {renderMessageContent(message)}
                            </div>

                            {/* Download Button for Table Modifications */}
                            {message.metadata?.show_download_button && message.metadata?.download_id && (
                              <div className="mt-4 pt-3 border-t border-blue-500/20">
                                <Button
                                  onClick={() => downloadTable(message.metadata!.download_id!)}
                                  size="sm"
                                  icon={<Download />}
                                  className="bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30"
                                >
                                  Download Excel File
                                </Button>
                              </div>
                            )}

                            {/* Timestamp */}
                            <div className="mt-3 pt-2 border-t border-blue-500/20">
                              <span className="text-xs text-blue-300/70">
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
                  </AnimatePresence>
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input Area */}
            {activeSessionId && (
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
                        placeholder={selectedDocument 
                          ? `Ask about ${selectedDocument.filename}...` 
                          : "Type your message..."
                        }
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
                      <div className="w-2 h-2 bg-green-400 rounded-full" />
                      <span>AI Ready</span>
                    </span>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </Layout>
    </ProtectedRoute>
  );
};

export default ChatPage;
