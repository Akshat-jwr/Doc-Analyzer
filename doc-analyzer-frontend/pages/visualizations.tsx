// app/visualizations/page.tsx
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Head from 'next/head';
import { Layout } from '@/components/layout/Layout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Button } from '@/components/ui/Button';
import { useDocuments } from '@/hooks/useDocuments';
import { useAuth } from '@/hooks/useAuth';
import { 
  Loader2, 
  BarChart3, 
  Trash2,
  Download,
  FileText,
  ImageIcon,
  Send,
  History,
  AlertCircle,
  X, // ✅ NEW: Import X icon for the close button
  Search // ✅ NEW: Using a magnifying glass icon for the hover effect
} from 'lucide-react';
import { api } from '@/lib/api'; // Adjust the import path as needed
import { toast } from 'react-hot-toast';

// Types (remains the same)
interface Visualization {
  id: string;
  query: string;
  chart_type: string;
  page_number?: number;
  document_name: string;
  image_base64: string | null;
  created_at: string;
  llm_description?: string;
  python_code?: string;
  selected_tables: { id: string; title: string; }[]; // Array of tables used
}

interface Document {
  id: string;
  filename: string;
}

// Time formatting helper (remains the same)
const formatISOTimeAgo = (isoDate: string) => {
  const date = new Date(isoDate);
  const now = new Date();
  const seconds = Math.round((now.getTime() - date.getTime()) / 1000);
  if (isNaN(seconds)) return "a few moments ago";
  const minutes = Math.round(seconds / 60);
  const hours = Math.round(minutes / 60);
  const days = Math.round(hours / 24);
  if (seconds < 60) return `${seconds} seconds ago`;
  if (minutes < 60) return `${minutes} minutes ago`;
  if (hours < 24) return `${hours} hours ago`;
  return `${days} days ago`;
};

// ✅ NEW: Image Modal Component
const ImageModal: React.FC<{ imageUrl: string; onClose: () => void; }> = ({ imageUrl, onClose }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50"
      onClick={onClose} // Close on backdrop click
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="relative max-w-4xl max-h-[90vh] p-4"
        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking on the image itself
      >
        <img src={imageUrl} alt="Expanded Visualization" className="w-full h-full object-contain" />
      </motion.div>
      <Button
        variant="ghost"
        size="sm"
        className="absolute top-4 right-4 text-white hover:text-white hover:bg-white/20"
        onClick={onClose}
      >
        <X className="w-8 h-8" />
      </Button>
    </motion.div>
  );
};


// VisualizationCard component with click-to-expand functionality
const VisualizationCard: React.FC<{ viz: Visualization; onDelete: (id: string)
=>void; onExpand: (imageUrl: string) => void; }> = ({ viz, onDelete, onExpand }) => {
  // ✅ NEW: State to manage the download loading indicator
  const [isDownloading, setIsDownloading] = useState(false);
  
  const handleDownloadPNG = () => {
    if (!viz.image_base64) return;
    const link = document.createElement('a');
    link.href = viz.image_base64;
    link.download = `visualization-${viz.id}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
const [exporting, setExporting] = useState(false);

  const handleDownloadExcel = async () => {
    // Ensure there is a table to download
    if (!viz.selected_tables || viz.selected_tables.length === 0) {
      alert("No associated table data found for this visualization.");
      return;
    }
    
    const tableId = viz.selected_tables[0].id; // Use the first table for download
    const title = viz.selected_tables[0].title || 'Visualization_Data';

    setExporting(true);
        try {
            console.log('Exporting table:', tableId);
            const blob = await api.exportSingleTable(tableId);

            const url = URL.createObjectURL(blob);
            const a = window.document.createElement('a');
            a.href = url;
            a.download = `${title.replace(/[^a-zA-Z0-9]/g, '_')}.xlsx`;
            a.click();
            URL.revokeObjectURL(url);

            toast.success('Table exported as Excel');
        } catch (error: any) {
            console.error('Export error:', error);
            toast.error(error.message || 'Export failed');
        } finally {
            setExporting(false);
        }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="bg-dark-800/50 border border-blue-500/20 rounded-2xl p-5 flex flex-col justify-between"
    >
      <div className="flex-1">
        {/* ✅ FIX: Image container now handles click to expand */}
        <div 
          className="mb-4 h-56 bg-dark-900 rounded-lg flex items-center justify-center overflow-hidden relative group"
          onClick={() => viz.image_base64 && onExpand(viz.image_base64)}
        >
          {viz.image_base64 ? (
            <>
              <img src={viz.image_base64} alt={viz.query} className="w-full h-full object-contain transition-transform duration-300 group-hover:scale-105" />
              <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 cursor-zoom-in">
                <Search className="w-12 h-12 text-white" />
              </div>
            </>
          ) : (
            <div className="text-center text-amber-400/50 p-4 flex flex-col items-center justify-center">
                <AlertCircle className="w-10 h-10 mb-2" />
                <span className="font-semibold text-sm">Image Not Available</span>
                <span className="text-xs">The visualization failed to generate.</span>
            </div>
          )}
        </div>
        <h3 className="font-semibold text-white mb-2">{viz.query}</h3>
        <p className="text-sm text-blue-300/70 mb-3">{viz.llm_description || 'AI-generated visualization.'}</p>
      </div>
      <div className="mt-auto pt-4 border-t border-blue-500/10">
        <div className="text-xs text-blue-400/60 mb-4">
          <p><strong>Document:</strong> {viz.document_name}</p>
          <p><strong>Created:</strong> {formatISOTimeAgo(viz.created_at)}</p>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button size="sm" variant="secondary" icon={<ImageIcon className="w-4 h-4"/>} onClick={handleDownloadPNG} disabled={!viz.image_base64}>PNG</Button>
            <Button size="sm" variant="secondary" icon={<FileText className="w-4 h-4"/>} onClick={handleDownloadExcel} disabled={!viz.selected_tables}>Data (Excel)</Button>
          </div>
          <Button size="sm" variant="ghost" className="text-gray-500 hover:text-red-400 hover:bg-red-500/10" onClick={() => onDelete(viz.id)}>
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </motion.div>
  );
};

// Main Visualization Page Component
const VisualizationPage: React.FC = () => {
  const { user } = useAuth();
  const { documents, loading: docsLoading } = useDocuments();
  const [selectedDoc, setSelectedDoc] = useState<string>('');
  const [query, setQuery] = useState('');
  const [pageNumber, setPageNumber] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [history, setHistory] = useState<Visualization[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  // ✅ NEW: State to manage the expanded image modal
  const [expandedImage, setExpandedImage] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    if (documents.length > 0 && !selectedDoc) {
      setSelectedDoc(documents[0].id);
    }
  }, [documents, selectedDoc]);

  const loadHistory = useCallback(async (documentId: string) => {
    if (!user || !documentId) return;
    setIsHistoryLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/llm-visualization/history?document_id=${documentId}&user_id=${user.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch history');
      const data = await response.json();
      if (data.success) {
        const formattedHistory = data.history.map((h: any) => ({
          ...h,
          document_name: documents.find(d => d.id === h.document_id)?.filename || 'Unknown Document'
        }));
        setHistory(formattedHistory);
      } else {
        throw new Error(data.error || 'API error');
      }
    } catch (err: any) {
      setError(`Failed to load history: ${err.message}`);
      setHistory([]);
    } finally {
      setIsHistoryLoading(false);
    }
  }, [user, documents, API_BASE]);

  useEffect(() => {
    if (selectedDoc && user) {
      loadHistory(selectedDoc);
    } else if (!user) {
      setIsHistoryLoading(false);
    }
  }, [selectedDoc, user, loadHistory]);

  const handleCreateVisualization = async (e: React.FormEvent) => {
    e.preventDefault();
    // ... (logic remains the same)
    setError(null);
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/llm-visualization/create`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: selectedDoc, query, page_number: parseInt(pageNumber, 10), user_id: user?.id })
      });
      const data = await response.json();
      if (data.success) {
        setQuery('');
        setPageNumber('');
        await loadHistory(selectedDoc);
      } else {
        setError(data.error || 'Failed to create visualization.');
      }
    } catch (err: any) {
      setError(`An error occurred: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (vizId: string) => {
    // ... (logic remains the same)
    if (!user) return;
    const originalHistory = [...history];
    setHistory(prev => prev.filter(v => v.id !== vizId));
    try {
      const token = localStorage.getItem('token');
      await fetch(`${API_BASE}/llm-visualization/history/${vizId}?user_id=${user.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (err) {
      setError('Failed to delete visualization. Reverting changes.');
      setHistory(originalHistory);
    }
  };

  const selectedDocFilename = documents.find(d => d.id === selectedDoc)?.filename || "selected document";

  return (
    <ProtectedRoute>
      <Head>
        <title>AI Visualizations - DocAnalyzer</title>
      </Head>
      <Layout title="AI Data Visualizations">
        <div className="max-w-7xl mx-auto p-6 space-y-10">
          {/* Create Form (remains the same) */}
          <div className="bg-dark-800/60 border border-blue-500/20 rounded-2xl p-8">
            <div className="flex items-center space-x-4 mb-6">
                <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl flex items-center justify-center">
                    <BarChart3 className="w-8 h-8 text-white" />
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-white">Create New Visualization</h2>
                    <p className="text-blue-300/70">Describe the chart you want to generate from your document's data.</p>
                </div>
            </div>
            
            <form onSubmit={handleCreateVisualization} className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
              {/* Form fields (remain the same) */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-blue-300">Document</label>
                <select value={selectedDoc} onChange={(e) => setSelectedDoc(e.target.value)} className="w-full bg-dark-700/50 border border-blue-500/30 rounded-xl px-4 py-3 text-white" disabled={docsLoading}>
                  {docsLoading ? <option>Loading documents...</option> : documents.map(doc => (<option key={doc.id} value={doc.id}>{doc.filename}</option>))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-blue-300">Page Number</label>
                <input type="number" value={pageNumber} onChange={(e) => setPageNumber(e.target.value)} placeholder="e.g., 5" className="w-full bg-dark-700/50 border border-blue-500/30 rounded-xl px-4 py-3 text-white" />
              </div>
              <div className="md:col-span-2 space-y-2">
                <label className="text-sm font-medium text-blue-300">Your Request</label>
                <div className="flex items-center gap-4">
                    <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g., 'Create a bar chart of assets by year'" className="w-full bg-dark-700/50 border border-blue-500/30 rounded-xl px-4 py-3 text-white" />
                    <Button type="submit" disabled={isLoading || !user || !query} loading={isLoading} icon={<Send />} className="bg-gradient-to-r from-emerald-500 to-green-600 py-3">Generate</Button>
                </div>
              </div>
            </form>
            {error && <p className="mt-4 text-red-400 text-sm">{error}</p>}
          </div>

          {/* History Section */}
          <div>
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center space-x-3">
                <History className="text-blue-400" />
                <span>Visualization History for "{selectedDocFilename}"</span>
            </h2>
            {isHistoryLoading ? (
              <div className="text-center py-20"><Loader2 className="w-12 h-12 animate-spin text-blue-400 mx-auto" /></div>
            ) : history.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <AnimatePresence>
                  {history.map(viz => 
                    <VisualizationCard 
                      key={viz.id} 
                      viz={viz} 
                      onDelete={handleDelete}
                      // ✅ NEW: Pass the expand handler to the card
                      onExpand={() => setExpandedImage(viz.image_base64)} 
                    />
                  )}
                </AnimatePresence>
              </div>
            ) : (
              <div className="text-center py-20 bg-dark-800/40 rounded-2xl">
                <ImageIcon className="w-16 h-16 text-blue-400/50 mx-auto mb-4" />
                <h3 className="text-xl font-bold">No Visualizations Yet</h3>
                <p className="text-blue-300/60 mt-2">Create one using the form above to get started.</p>
              </div>
            )}
          </div>
        </div>

        {/* ✅ NEW: Conditionally render the modal */}
        <AnimatePresence>
          {expandedImage && (
            <ImageModal imageUrl={expandedImage} onClose={() => setExpandedImage(null)} />
          )}
        </AnimatePresence>
      </Layout>
    </ProtectedRoute>
  );
};

export default VisualizationPage;
