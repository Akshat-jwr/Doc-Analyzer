import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Head from 'next/head';
import { Layout } from '@/components/layout/Layout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useDocuments } from '@/hooks/useDocuments';
import { formatTimeAgo } from '@/lib/dateUtils';
import { 
  Send, 
  Loader2, 
  MessageSquare, 
  FileText, 
  BarChart3, 
  Eye, 
  Sparkles,
  Bot,
  User,
  Settings,
  Trash2,
  Download
} from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  content: string;
  timestamp: Date;
  mode?: string;
}

const CHAT_MODES = [
  { 
    value: 'general', 
    label: 'General Queries', 
    icon: MessageSquare, 
    color: 'blue',
    description: 'Ask general questions about your document'
  },
  { 
    value: 'analytical', 
    label: 'Analytical Queries', 
    icon: BarChart3, 
    color: 'purple',
    description: 'Get insights and analysis from your data'
  },
  { 
    value: 'visualization', 
    label: 'Visualizations', 
    icon: Eye, 
    color: 'green',
    description: 'Generate charts and visual representations'
  },
  { 
    value: 'extraction', 
    label: 'Data Extraction', 
    icon: Download, 
    color: 'orange',
    description: 'Extract specific data points and information'
  },
];

const ChatPage: React.FC = () => {
  const { documents, loading: docsLoading } = useDocuments();
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [chatMode, setChatMode] = useState<string>('general');
  const [inputText, setInputText] = useState<string>('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isTyping]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Get selected document
  const selectedDocument = documents.find(doc => doc.id === selectedDocId);

  // Generate dummy responses based on mode
  const generateDummyResponse = (userMessage: string, mode: string): string => {
    const responses = {
      normal: [
        `I'm here to help! You asked: "${userMessage}". How can I assist you further?`,
        `That's an interesting question about "${userMessage}". Let me think about that...`,
        `I understand you're asking about "${userMessage}". Here's what I think...`,
      ],
      general: [
        `Based on your document "${selectedDocument?.filename}", here's what I found about "${userMessage}": This document contains relevant information that addresses your query. The content suggests several key points that might be helpful.`,
        `Looking at "${selectedDocument?.filename}", I can see that "${userMessage}" relates to the document's main themes. Let me highlight the relevant sections for you.`,
        `From analyzing "${selectedDocument?.filename}", your question about "${userMessage}" touches on important aspects covered in pages 2-5. Here's a comprehensive answer...`,
      ],
      analytical: [
        `📊 **Analytical Insights for "${userMessage}"**\n\nBased on the tables and data in "${selectedDocument?.filename}":\n• **Key Metric 1**: 45% increase from baseline\n• **Trend Analysis**: Positive correlation observed\n• **Statistical Significance**: 95% confidence level\n• **Recommendation**: Focus on top 3 performing segments`,
        `🔍 **Data Analysis Results**\n\nQuery: "${userMessage}"\nDocument: "${selectedDocument?.filename}"\n\n**Summary Statistics:**\n- Total Records: 1,247\n- Average Value: 78.3\n- Standard Deviation: 12.4\n- Outliers Detected: 3\n\n**Key Findings:** The data shows strong patterns that support your hypothesis.`,
        `📈 **Comprehensive Analysis**\n\nAnalyzing "${userMessage}" across your document reveals:\n\n1. **Primary Patterns**: Clear upward trend\n2. **Seasonal Variations**: Q4 shows 23% spike\n3. **Risk Factors**: Minimal exposure detected\n4. **Growth Opportunities**: 3 high-potential areas identified`,
      ],
      visualization: [
        `📊 **Visualization Generated for "${userMessage}"**\n\n🎯 **Chart Type**: Interactive Bar Chart\n📈 **Data Points**: 156 entries from "${selectedDocument?.filename}"\n🎨 **Visual Elements**:\n• Color-coded categories\n• Trend lines with confidence intervals\n• Interactive tooltips\n• Exportable to PNG/SVG\n\n*Note: In a real implementation, this would show an actual chart widget.*`,
        `📉 **Data Visualization Ready**\n\nCreated visualizations for "${userMessage}":\n\n🔸 **Line Chart**: Showing trends over time\n🔸 **Pie Chart**: Category distribution\n🔸 **Heat Map**: Correlation matrix\n🔸 **Scatter Plot**: Relationship analysis\n\nAll charts are based on data extracted from "${selectedDocument?.filename}" and are ready for download.`,
        `🎨 **Interactive Dashboard Created**\n\nFor your query "${userMessage}", I've generated:\n\n📊 **Multi-panel Dashboard**\n• Real-time data updates\n• Drill-down capabilities\n• Custom filtering options\n• Mobile-responsive design\n\nData source: "${selectedDocument?.filename}"\nLast updated: ${new Date().toLocaleTimeString()}`,
      ],
      extraction: [
        `🔍 **Data Extraction Complete**\n\nExtracted information for "${userMessage}" from "${selectedDocument?.filename}":\n\n**📋 Extracted Fields:**\n• Names: 45 entities found\n• Dates: 23 temporal references\n• Numbers: 167 numeric values\n• Locations: 12 geographic references\n\n**💾 Export Options:**\n• CSV format\n• JSON structure\n• Excel workbook\n• Database insert scripts`,
        `📤 **Information Extracted**\n\nQuery: "${userMessage}"\nSource: "${selectedDocument?.filename}"\n\n**Results:**\n✅ **Tables Found**: 8 structured datasets\n✅ **Key-Value Pairs**: 234 extracted\n✅ **Entities**: 89 named entities\n✅ **Relationships**: 45 connections mapped\n\nAll data is cleaned and ready for analysis.`,
      ],
    };

    const modeResponses = responses[mode as keyof typeof responses] || responses.normal;
    return modeResponses[Math.floor(Math.random() * modeResponses.length)];
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: inputText.trim(),
      timestamp: new Date(),
      mode: selectedDocId ? chatMode : 'normal',
    };

    setChatHistory(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    setIsTyping(true);

    // Simulate typing delay
    setTimeout(() => {
      setIsTyping(false);
      
      const botMessage: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'bot',
        content: generateDummyResponse(userMessage.content, selectedDocId ? chatMode : 'normal'),
        timestamp: new Date(),
        mode: selectedDocId ? chatMode : 'normal',
      };
      
      setChatHistory(prev => [...prev, botMessage]);
      setIsLoading(false);
    }, 1500 + Math.random() * 1000);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setChatHistory([]);
  };

  const handleDocumentSelect = (docId: string) => {
    setSelectedDocId(docId || null);
    if (docId && chatMode === 'normal') {
      setChatMode('general');
    }
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>AI Chat - DocAnalyzer</title>
        <meta name="description" content="Chat with your documents using AI" />
      </Head>

      <Layout title="AI Chat">
        <div className="flex flex-col h-[calc(100vh-100px)] max-w-6xl mx-auto">
          {/* Chat Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-dark-800/50 to-dark-850/50 backdrop-blur-sm border border-blue-500/20 rounded-t-2xl p-6"
          >
            <div className="flex flex-col lg:flex-row lg:items-center justify-between space-y-4 lg:space-y-0">
              {/* Title & Status */}
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
                  <Bot className="w-7 h-7 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-white via-blue-200 to-cyan-300 bg-clip-text text-transparent">
                    AI Assistant
                  </h2>
                  <div className="flex items-center space-x-2 text-sm">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    <span className="text-blue-300/70">
                      {selectedDocument ? `Analyzing ${selectedDocument.filename}` : 'Ready to chat'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Controls */}
              <div className="flex items-center space-x-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearChat}
                  disabled={chatHistory.length === 0}
                  icon={<Trash2 />}
                  className="text-red-400 hover:text-white hover:bg-red-500/20"
                >
                  Clear
                </Button>
              </div>
            </div>

            {/* Document & Mode Selection */}
            <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Document Selection */}
              <div>
                <label className="block text-blue-300/70 text-sm mb-2">Document Context</label>
                <select
                  value={selectedDocId || ''}
                  onChange={(e) => handleDocumentSelect(e.target.value)}
                  className="w-full bg-dark-700/50 border border-blue-500/30 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                >
                  <option value="">💬 General Chat Mode</option>
                  {!docsLoading && documents.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      📄 {doc.filename}
                    </option>
                  ))}
                </select>
              </div>

              {/* Mode Selection */}
              {selectedDocId && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                >
                  <label className="block text-blue-300/70 text-sm mb-2">Chat Mode</label>
                  <select
                    value={chatMode}
                    onChange={(e) => setChatMode(e.target.value)}
                    className="w-full bg-dark-700/50 border border-blue-500/30 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                  >
                    {CHAT_MODES.map((mode) => (
                      <option key={mode.value} value={mode.value}>
                        {mode.label}
                      </option>
                    ))}
                  </select>
                </motion.div>
              )}
            </div>

            {/* Mode Description */}
            {selectedDocId && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg"
              >
                <div className="flex items-center space-x-2">
                  {(() => {
                    const mode = CHAT_MODES.find(m => m.value === chatMode);
                    const Icon = mode?.icon || MessageSquare;
                    return <Icon className="w-5 h-5 text-blue-400" />;
                  })()}
                  <span className="text-blue-300 font-medium">
                    {CHAT_MODES.find(m => m.value === chatMode)?.label}
                  </span>
                </div>
                <p className="text-blue-300/70 text-sm mt-1">
                  {CHAT_MODES.find(m => m.value === chatMode)?.description}
                </p>
              </motion.div>
            )}
          </motion.div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto bg-gradient-to-br from-dark-850 to-dark-900 border-x border-blue-500/20 p-6">
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Welcome Message */}
              {chatHistory.length === 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-center py-12"
                >
                  <div className="w-20 h-20 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Sparkles className="w-10 h-10 text-blue-400 animate-pulse" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-4">
                    {selectedDocument ? `Ready to analyze ${selectedDocument.filename}` : 'How can I help you today?'}
                  </h3>
                  <p className="text-blue-300/70 max-w-md mx-auto">
                    {selectedDocument 
                      ? `I'm ready to answer questions about your document using ${CHAT_MODES.find(m => m.value === chatMode)?.label.toLowerCase()} mode.`
                      : 'Start a conversation by typing a message below. You can also select a document for context-aware assistance.'
                    }
                  </p>
                </motion.div>
              )}

              {/* Chat Messages */}
              <AnimatePresence>
                {chatHistory.map((message, index) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`flex items-start space-x-3 max-w-3xl ${message.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                      {/* Avatar */}
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
                        message.sender === 'user' 
                          ? 'bg-gradient-to-br from-blue-500 to-blue-600' 
                          : 'bg-gradient-to-br from-cyan-500 to-teal-600'
                      }`}>
                        {message.sender === 'user' ? (
                          <User className="w-5 h-5 text-white" />
                        ) : (
                          <Bot className="w-5 h-5 text-white" />
                        )}
                      </div>

                      {/* Message Bubble */}
                      <div className={`relative p-4 rounded-2xl shadow-lg ${
                        message.sender === 'user'
                          ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
                          : 'bg-gradient-to-br from-dark-700/50 to-dark-800/50 border border-blue-500/20 text-blue-100'
                      }`}>
                        {/* Message Content */}
                        <div className="whitespace-pre-wrap text-sm leading-relaxed">
                          {message.content}
                        </div>

                        {/* Timestamp & Mode */}
                        <div className={`flex items-center justify-between mt-3 pt-2 border-t ${
                          message.sender === 'user' 
                            ? 'border-blue-400/30' 
                            : 'border-blue-500/20'
                        }`}>
                          <span className={`text-xs ${
                            message.sender === 'user' 
                              ? 'text-blue-200/70' 
                              : 'text-blue-300/70'
                          }`}>
                            {message.timestamp.toLocaleTimeString([], { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </span>
                          {message.mode && message.mode !== 'normal' && (
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              message.sender === 'user'
                                ? 'bg-blue-400/20 text-blue-200'
                                : 'bg-blue-500/20 text-blue-300'
                            }`}>
                              {CHAT_MODES.find(m => m.value === message.mode)?.label || message.mode}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {/* Typing Indicator */}
              {isTyping && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start"
                >
                  <div className="flex items-start space-x-3 max-w-3xl">
                    <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-teal-600 rounded-full flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div className="bg-gradient-to-br from-dark-700/50 to-dark-800/50 border border-blue-500/20 p-4 rounded-2xl">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-dark-800/50 to-dark-850/50 backdrop-blur-sm border border-blue-500/20 rounded-b-2xl p-6"
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
                  onClick={handleSendMessage}
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
        </div>
      </Layout>
    </ProtectedRoute>
  );
};

export default ChatPage;
