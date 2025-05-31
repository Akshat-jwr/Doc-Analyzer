import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { X, Download, MessageCircle, Table, Image as ImageIcon } from 'lucide-react';
import { DocumentDetailResponse } from '@/types';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { StatusIndicator } from './StatusIndicator';

interface DocumentPreviewProps {
  document: DocumentDetailResponse;
  onClose: () => void;
  onDownload: (url: string, filename: string) => void;
  onChat: () => void;
  onShowTables: () => void;
}

export const DocumentPreview: React.FC<DocumentPreviewProps> = ({
  document,
  onClose,
  onDownload,
  onChat,
  onShowTables,
}) => {
  const [activeTab, setActiveTab] = useState<'text' | 'images' | 'info'>('text');

  const tabs = [
    { id: 'text', label: 'Text Content', icon: MessageCircle },
    { id: 'images', label: `Images (${document.images.length})`, icon: ImageIcon },
    { id: 'info', label: 'Information', icon: Table },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.8, y: 50 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.8, y: 50 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-dark-900 border border-dark-700 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-700">
          <div className="flex items-center space-x-4">
            <div>
              <h2 className="text-xl font-bold text-white">{document.document.filename}</h2>
              <div className="flex items-center space-x-4 mt-1">
                <span className="text-dark-400 text-sm">
                  {document.document.page_count} pages
                </span>
                <StatusIndicator status={document.document.processing_status as any} />
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDownload(document.document.cloudinary_url, document.document.filename)}
              icon={<Download />}
            >
              Download
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onChat}
              icon={<MessageCircle />}
            >
              Chat
            </Button>
            {document.processing_info.analytical_queries_ready && (
              <Button
                variant="primary"
                size="sm"
                onClick={onShowTables}
                icon={<Table />}
              >
                View Tables
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              icon={<X />}
            />
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-dark-700">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 px-6 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'text-primary-400 border-b-2 border-primary-400'
                    : 'text-dark-400 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-auto">
          {/* Text Content */}
          {activeTab === 'text' && (
            <div className="space-y-4">
              {document.page_texts.length > 0 ? (
                document.page_texts.map((pageText) => (
                  <motion.div
                    key={pageText.page_number}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-dark-800/30 rounded-lg p-4 border border-dark-700/50"
                  >
                    <h4 className="text-primary-400 font-medium mb-2">
                      Page {pageText.page_number}
                    </h4>
                    <p className="text-dark-300 text-sm leading-relaxed whitespace-pre-wrap">
                      {pageText.text || 'No text content found on this page.'}
                    </p>
                  </motion.div>
                ))
              ) : (
                <div className="text-center py-8">
                  <p className="text-dark-400">No text content available.</p>
                </div>
              )}
            </div>
          )}

          {/* Images */}
          {activeTab === 'images' && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {document.images.length > 0 ? (
                document.images.map((image, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className="relative group"
                  >
                    <img
                      src={image.cloudinary_url}
                      alt={`Page ${image.page_number} Image`}
                      className="w-full h-40 object-cover rounded-lg border border-dark-700"
                    />
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
                      <span className="text-white text-sm font-medium">
                        Page {image.page_number}
                      </span>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="col-span-full text-center py-8">
                  <ImageIcon className="w-12 h-12 text-dark-400 mx-auto mb-2" />
                  <p className="text-dark-400">No images found in this document.</p>
                </div>
              )}
            </div>
          )}

          {/* Document Info */}
          {activeTab === 'info' && (
            <div className="space-y-6">
              {/* Processing Info */}
              <div className="bg-dark-800/30 rounded-lg p-4 border border-dark-700/50">
                <h4 className="text-white font-medium mb-3">Processing Status</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-dark-400 text-sm">General Queries</p>
                    <p className={`font-medium ${document.processing_info.general_queries_ready ? 'text-emerald-400' : 'text-yellow-400'}`}>
                      {document.processing_info.general_queries_ready ? 'Ready' : 'Processing'}
                    </p>
                  </div>
                  <div>
                    <p className="text-dark-400 text-sm">Analytics</p>
                    <p className={`font-medium ${document.processing_info.analytical_queries_ready ? 'text-emerald-400' : 'text-yellow-400'}`}>
                      {document.processing_info.analytical_queries_ready ? 'Ready' : 'Processing'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Tables Summary */}
              <div className="bg-dark-800/30 rounded-lg p-4 border border-dark-700/50">
                <h4 className="text-white font-medium mb-3">Tables Extracted</h4>
                {document.tables.length > 0 ? (
                  <div className="space-y-2">
                    {document.tables.slice(0, 3).map((table) => (
                      <div key={table.id} className="flex items-center justify-between">
                        <span className="text-dark-300 text-sm">{table.title}</span>
                        <span className="text-dark-400 text-xs">
                          {table.row_count} rows × {table.column_count} cols
                        </span>
                      </div>
                    ))}
                    {document.tables.length > 3 && (
                      <p className="text-dark-400 text-sm">
                        +{document.tables.length - 3} more tables
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-dark-400 text-sm">No tables found in this document.</p>
                )}
              </div>

              {/* Document Stats */}
              <div className="bg-dark-800/30 rounded-lg p-4 border border-dark-700/50">
                <h4 className="text-white font-medium mb-3">Document Statistics</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-dark-400">Upload Date</p>
                    <p className="text-white">{new Date(document.document.uploaded_at).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <p className="text-dark-400">File Size</p>
                    <p className="text-white">{document.document.page_count} pages</p>
                  </div>
                  <div>
                    <p className="text-dark-400">Images</p>
                    <p className="text-white">{document.images.length} found</p>
                  </div>
                  <div>
                    <p className="text-dark-400">Tables</p>
                    <p className="text-white">{document.tables.length} extracted</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};
