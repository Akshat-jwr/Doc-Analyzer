import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Document } from '@/types';
import { DocumentCard } from './DocumentCard';
import { DocumentFilters } from './DocumentFilters';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Button } from '@/components/ui/Button';
import { Upload, FolderOpen } from 'lucide-react';

interface DocumentListProps {
  documents: Document[];
  loading: boolean;
  onView: (id: string) => void;
  onDelete: (id: string) => void;
  onDownload: (url: string, filename: string) => void;
  onShowTables: (id: string) => void;
  onUpload: () => void;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  loading,
  onView,
  onDelete,
  onDownload,
  onShowTables,
  onUpload,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    fileType: 'all',
    status: 'all',
  });
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'name' | 'size'>('newest');

  const filteredDocuments = useMemo(() => {
    let filtered = documents.filter(doc => 
      doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // File type filter
    if (filters.fileType !== 'all') {
      filtered = filtered.filter(doc => {
        const ext = doc.filename.split('.').pop()?.toLowerCase();
        switch (filters.fileType) {
          case 'pdf':
            return ext === 'pdf';
          case 'spreadsheet':
            return ['xlsx', 'xls', 'csv'].includes(ext || '');
          case 'image':
            return ['png', 'jpg', 'jpeg'].includes(ext || '');
          default:
            return true;
        }
      });
    }

    // Status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(doc => doc.processing_status === filters.status);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime();
        case 'oldest':
          return new Date(a.uploaded_at).getTime() - new Date(b.uploaded_at).getTime();
        case 'name':
          return a.filename.localeCompare(b.filename);
        case 'size':
          return b.page_count - a.page_count;
        default:
          return 0;
      }
    });

    return filtered;
  }, [documents, searchQuery, filters, sortBy]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <DocumentFilters
        onSearch={setSearchQuery}
        onFilterChange={setFilters}
        onSortChange={setSortBy}
      />

      {/* Empty State */}
      {documents.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-12"
        >
          <motion.div
            animate={{ 
              rotate: [0, 10, -10, 0],
              scale: [1, 1.1, 1]
            }}
            transition={{ 
              duration: 4, 
              repeat: Infinity, 
              ease: "easeInOut" 
            }}
            className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-primary-500/20 to-purple-500/20 rounded-full flex items-center justify-center"
          >
            <FolderOpen className="w-12 h-12 text-primary-400" />
          </motion.div>
          <h3 className="text-2xl font-bold text-white mb-2">No Documents Yet</h3>
          <p className="text-dark-400 mb-6 max-w-md mx-auto">
            Upload your first document to get started with AI-powered analysis and insights.
          </p>
          <Button
            onClick={onUpload}
            icon={<Upload />}
            className="bg-gradient-to-r from-primary-500 to-purple-600 hover:from-primary-600 hover:to-purple-700"
          >
            Upload Your First Document
          </Button>
        </motion.div>
      )}

      {/* No Results */}
      {documents.length > 0 && filteredDocuments.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-8"
        >
          <h3 className="text-xl font-semibold text-white mb-2">No documents found</h3>
          <p className="text-dark-400">Try adjusting your search or filter criteria.</p>
        </motion.div>
      )}

      {/* Document Grid */}
      {filteredDocuments.length > 0 && (
        <motion.div
          layout
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          <AnimatePresence>
            {filteredDocuments.map((document, index) => (
              <motion.div
                key={document.id}
                layout
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ delay: index * 0.1 }}
              >
                <DocumentCard
                  document={document}
                  onView={onView}
                  onDelete={onDelete}
                  onDownload={onDownload}
                  onShowTables={onShowTables}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Load More Button */}
      {filteredDocuments.length > 6 && (
        <div className="text-center">
          <Button variant="ghost" className="text-primary-400 hover:text-primary-300">
            Load More Documents
          </Button>
        </div>
      )}
    </div>
  );
};
