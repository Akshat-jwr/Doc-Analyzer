import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { 
  FileText, 
  Download, 
  Eye, 
  Trash2, 
  Table,
  Image,
  FileSpreadsheet,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  MoreVertical
} from 'lucide-react';
import { Document, ProcessingStatus } from '@/types';
import { Button } from '@/components/ui/Button';
import { DeleteModal } from '@/components/ui/DeleteModal';

interface DocumentCardProps {
  document: Document;
  onView: (id: string) => void;
  onDelete: (id: string) => void;
  onDownload: (url: string, filename: string) => void;
  onShowTables: (id: string) => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onView,
  onDelete,
  onDownload,
  onShowTables,
}) => {
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf':
        return <FileText className="w-6 h-6 text-red-400" />;
      case 'xlsx':
      case 'xls':
      case 'csv':
        return <FileSpreadsheet className="w-6 h-6 text-green-400" />;
      case 'png':
      case 'jpg':
      case 'jpeg':
        return <Image className="w-6 h-6 text-blue-400" />;
      default:
        return <FileText className="w-6 h-6 text-gray-400" />;
    }
  };

  const getStatusIndicator = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'processing':
      case 'background_processing':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Ready';
      case 'processing':
        return 'Processing';
      case 'background_processing':
        return 'Analyzing';
      case 'failed':
        return 'Failed';
      default:
        return 'Pending';
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await onDelete(document.id);
      setShowDeleteModal(false);
    } catch (error) {
      console.error('Delete failed:', error);
    } finally {
      setDeleting(false);
    }
  };

  const isProcessingComplete = document.processing_status === 'completed';
  const hasTableData = document.total_tables_found > 0;

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ y: -4, scale: 1.02 }}
        className="group relative bg-gradient-to-br from-dark-800/50 to-dark-850/50 backdrop-blur-sm border border-blue-500/20 rounded-2xl p-5 hover:border-blue-400/40 transition-all duration-300 shadow-lg hover:shadow-xl overflow-hidden"
      >
        {/* Background glow on hover */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
        
        {/* Header */}
        <div className="relative flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3 flex-1 min-w-0 pr-2">
            <motion.div
              whileHover={{ scale: 1.1, rotate: 5 }}
              className="p-2.5 bg-dark-700/50 rounded-lg border border-blue-500/20 group-hover:border-blue-400/40 transition-colors shrink-0"
            >
              {getFileIcon(document.filename)}
            </motion.div>
            <div className="flex-1 min-w-0">
              <h3 className="text-white font-semibold truncate group-hover:text-blue-300 transition-colors text-sm leading-tight">
                {document.filename}
              </h3>
              <div className="flex items-center space-x-2 mt-1">
                <p className="text-blue-300/70 text-xs">
                  {document.page_count} pages
                </p>
                <span className="text-blue-500/50">•</span>
                {/* <p className="text-blue-300/70 text-xs truncate">
                  {formatDistanceToNow(new Date(document.uploaded_at))} ago
                </p> */}
              </div>
            </div>
          </div>
          
          {/* Status */}
          <div className="flex items-center space-x-1 bg-dark-700/30 px-2 py-1 rounded-lg border border-blue-500/20 shrink-0">
            {getStatusIndicator(document.processing_status)}
            <span className="text-xs font-medium text-blue-300 whitespace-nowrap">
              {getStatusText(document.processing_status)}
            </span>
          </div>
        </div>

        {/* Stats */}
        <div className="relative grid grid-cols-2 gap-2 mb-4">
          <div className="bg-dark-700/30 rounded-lg p-2.5 border border-blue-500/10">
            <p className="text-blue-300/70 text-xs uppercase tracking-wide font-medium">Tables</p>
            <p className="text-white text-lg font-bold">{document.total_tables_found}</p>
          </div>
          <div className="bg-dark-700/30 rounded-lg p-2.5 border border-blue-500/10">
            <p className="text-blue-300/70 text-xs uppercase tracking-wide font-medium">Processed</p>
            <p className="text-blue-300 text-lg font-bold">{document.tables_processed}</p>
          </div>
        </div>

        {/* Actions - FIXED LAYOUT */}
        <div className="relative grid grid-cols-4 gap-1.5">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onView(document.id)}
            icon={<Eye className="w-4 h-4" />}
            className="text-blue-300 hover:text-white hover:bg-blue-500/20 border border-blue-500/20 hover:border-blue-400/40 text-xs px-2 py-1.5"
          >
            View
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => onShowTables(document.id)}
            disabled={!hasTableData || !isProcessingComplete}
            icon={<Table className="w-4 h-4" />}
            className="text-cyan-300 hover:text-white hover:bg-cyan-500/20 border border-cyan-500/20 hover:border-cyan-400/40 disabled:opacity-50 disabled:cursor-not-allowed text-xs px-2 py-1.5"
          >
            Tables
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => onDownload(document.cloudinary_url, document.filename)}
            icon={<Download className="w-4 h-4" />}
            className="text-green-400 hover:text-white hover:bg-green-500/20 border border-green-500/20 hover:border-green-400/40 text-xs px-2 py-1.5"
          />

          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowDeleteModal(true)}
            icon={<Trash2 className="w-4 h-4" />}
            className="text-red-400 hover:text-white hover:bg-red-500/20 border border-red-500/20 hover:border-red-400/40 text-xs px-2 py-1.5"
          />
        </div>

        {/* Progress Bar for processing */}
        {!isProcessingComplete && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="relative mt-4"
          >
            <div className="h-1 bg-dark-700 rounded-full overflow-hidden">
              <motion.div
                animate={{ x: ['-100%', '100%'] }}
                transition={{ repeat: Infinity, duration: 1.5, ease: 'easeInOut' }}
                className="h-full w-1/3 bg-gradient-to-r from-blue-500 to-cyan-500"
              />
            </div>
            <p className="text-blue-300/70 text-xs mt-2 text-center">
              Processing your document...
            </p>
          </motion.div>
        )}
      </motion.div>

      {/* Delete Modal */}
      <DeleteModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDelete}
        loading={deleting}
        title="Delete Document"
        message={`Are you sure you want to delete "${document.filename}"? This action cannot be undone and will permanently remove the document and all its extracted data.`}
      />
    </>
  );
};
