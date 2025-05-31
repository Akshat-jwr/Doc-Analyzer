import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Download, Search, Table as TableIcon } from 'lucide-react';
import { Table, TablePagination } from '@/types';
import { SimpleTable } from './SimpleTable';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { api } from '@/lib/api';
import { toast } from 'react-hot-toast';

interface TableViewProps {
  tables: Table[];
  pagination?: TablePagination;
  documentTitle: string;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  currentPage?: number;
  onPageChange?: (page: number) => void;
  documentId?: string;
}

export const TableView: React.FC<TableViewProps> = ({ 
  tables, 
  pagination,
  documentTitle,
  searchQuery = '',
  onSearchChange,
  currentPage = 1,
  onPageChange,
  documentId
}) => {
  const [localSearch, setLocalSearch] = useState(searchQuery);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (onSearchChange) {
        onSearchChange(localSearch);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [localSearch, onSearchChange]);

  const handlePrevious = () => {
    if (onPageChange && currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (onPageChange && pagination && currentPage < pagination.pages) {
      onPageChange(currentPage + 1);
    }
  };

  const handleExport = async (format: 'markdown' | 'json' = 'markdown') => {
    if (!documentId) {
      toast.error('Document ID not available');
      return;
    }

    try {
      const response = await api.exportDocumentTables(documentId, format);
      
      if (response.success) {
        const blob = new Blob(
          [typeof response.content === 'string' ? response.content : JSON.stringify(response.content, null, 2)], 
          { type: format === 'json' ? 'application/json' : 'text/markdown' }
        );
        
        const url = URL.createObjectURL(blob);
        const a = window.document.createElement('a');
        a.href = url;
        a.download = response.filename;
        a.click();
        URL.revokeObjectURL(url);
        
        toast.success(`Tables exported as ${format.toUpperCase()}`);
      }
    } catch (error: any) {
      toast.error(error.message || 'Export failed');
    }
  };

  if (tables.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center py-12"
      >
        <TableIcon className="w-16 h-16 text-blue-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-white mb-2">No Tables Found</h3>
        <p className="text-blue-300/70">
          {searchQuery ? 'No tables match your search criteria.' : 'This document doesn\'t contain any extracted tables.'}
        </p>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Document Tables</h2>
          <p className="text-blue-300/70">
            {pagination ? `${pagination.total} table${pagination.total !== 1 ? 's' : ''} found` : `${tables.length} table${tables.length !== 1 ? 's' : ''}`}
            {localSearch && ` • Searching for "${localSearch}"`}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="w-64">
            <Input
              placeholder="Search tables..."
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              icon={<Search />}
            />
          </div>
          <Button
            variant="ghost"
            onClick={() => handleExport('markdown')}
            icon={<Download />}
            className="bg-green-500/20 text-green-300 hover:bg-green-500/30"
          >
            Export
          </Button>
        </div>
      </div>

      {/* Pagination */}
      {pagination && pagination.pages > 1 && (
        <div className="flex items-center justify-between bg-dark-800/30 rounded-lg p-4">
          <Button
            variant="ghost"
            onClick={handlePrevious}
            disabled={currentPage === 1}
            icon={<ChevronLeft />}
            className="text-blue-300 hover:text-white disabled:opacity-50"
          >
            Previous
          </Button>
          
          <span className="text-blue-300">
            Page {currentPage} of {pagination.pages} • Showing {tables.length} tables
          </span>
          
          <Button
            variant="ghost"
            onClick={handleNext}
            disabled={currentPage === pagination.pages}
            icon={<ChevronRight />}
            className="text-blue-300 hover:text-white disabled:opacity-50"
          >
            Next
          </Button>
        </div>
      )}

      {/* Tables */}
      <AnimatePresence mode="wait">
        <motion.div
          key={`${currentPage}-${localSearch}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="space-y-6"
        >
          {tables.map((table, index) => (
            <motion.div
              key={table.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <SimpleTable
                content={table.markdown_content || ''}
                title={table.title}
                pageInfo={`Page ${table.start_page}${table.start_page !== table.end_page ? `-${table.end_page}` : ''} • ${table.row_count} rows × ${table.column_count} columns`}
              />
            </motion.div>
          ))}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};
