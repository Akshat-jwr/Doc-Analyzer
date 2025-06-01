import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Search, Table as TableIcon, Filter, X } from 'lucide-react';
import { Table, TablePagination } from '@/types';
import { SimpleTable } from './SimpleTable';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

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
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    tableName: '',
    pageNumber: '',
    minRows: '',
    maxRows: '',
  });
  const [filteredTables, setFilteredTables] = useState(tables);

  // 🔧 FIX: Proper debouncing for search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (onSearchChange && localSearch !== searchQuery) {
        onSearchChange(localSearch);
      }
    }, 500); // Increased debounce time to 500ms

    return () => clearTimeout(timer);
  }, [localSearch]); // Removed onSearchChange and searchQuery from dependencies

  // 🔧 FIX: Local filtering for advanced filters
  useEffect(() => {
    let filtered = tables;

    // Apply local filters
    if (filters.tableName) {
      filtered = filtered.filter(table => 
        table.title.toLowerCase().includes(filters.tableName.toLowerCase())
      );
    }

    if (filters.pageNumber) {
      const pageNum = parseInt(filters.pageNumber);
      if (!isNaN(pageNum)) {
        filtered = filtered.filter(table => 
          table.start_page === pageNum || 
          (table.start_page <= pageNum && table.end_page >= pageNum)
        );
      }
    }

    if (filters.minRows) {
      const minRows = parseInt(filters.minRows);
      if (!isNaN(minRows)) {
        filtered = filtered.filter(table => table.row_count >= minRows);
      }
    }

    if (filters.maxRows) {
      const maxRows = parseInt(filters.maxRows);
      if (!isNaN(maxRows)) {
        filtered = filtered.filter(table => table.row_count <= maxRows);
      }
    }

    setFilteredTables(filtered);
  }, [tables, filters]);

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

  const clearAllFilters = () => {
    setLocalSearch('');
    setFilters({
      tableName: '',
      pageNumber: '',
      minRows: '',
      maxRows: '',
    });
    if (onSearchChange) {
      onSearchChange('');
    }
  };

  const hasActiveFilters = localSearch || filters.tableName || filters.pageNumber || filters.minRows || filters.maxRows;

  // Use filtered tables for display
  const displayTables = hasActiveFilters ? filteredTables : tables;

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
          This document doesn't contain any extracted tables.
        </p>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col space-y-4">
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">Document Tables</h2>
            <p className="text-blue-300/70">
              {hasActiveFilters ? (
                <>
                  {displayTables.length} of {tables.length} table{tables.length !== 1 ? 's' : ''}
                  {localSearch && ` • Search: "${localSearch}"`}
                </>
              ) : (
                <>
                  {pagination ? `${pagination.total} table${pagination.total !== 1 ? 's' : ''} found` : `${tables.length} table${tables.length !== 1 ? 's' : ''}`}
                </>
              )}
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="w-64">
              <Input
                placeholder="Quick search..."
                value={localSearch}
                onChange={(e) => setLocalSearch(e.target.value)}
                icon={<Search />}
              />
            </div>
            <Button
              variant="ghost"
              onClick={() => setShowFilters(!showFilters)}
              icon={<Filter />}
              className={`${showFilters ? 'bg-blue-500/20 text-blue-300' : 'text-blue-400'} hover:text-white hover:bg-blue-500/20`}
            >
              Filters
            </Button>
            {hasActiveFilters && (
              <Button
                variant="ghost"
                onClick={clearAllFilters}
                icon={<X />}
                className="text-red-400 hover:text-white hover:bg-red-500/20"
              >
                Clear
              </Button>
            )}
          </div>
        </div>

        {/* Advanced Filters Panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-dark-800/30 backdrop-blur-sm border border-blue-500/20 rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4">Advanced Filters</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-blue-300/70 text-sm mb-2">Table Name</label>
                  <Input
                    placeholder="Filter by name..."
                    value={filters.tableName}
                    onChange={(e) => setFilters(prev => ({ ...prev, tableName: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="block text-blue-300/70 text-sm mb-2">Page Number</label>
                  <Input
                    type="number"
                    placeholder="Page number..."
                    value={filters.pageNumber}
                    onChange={(e) => setFilters(prev => ({ ...prev, pageNumber: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="block text-blue-300/70 text-sm mb-2">Min Rows</label>
                  <Input
                    type="number"
                    placeholder="Minimum rows..."
                    value={filters.minRows}
                    onChange={(e) => setFilters(prev => ({ ...prev, minRows: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="block text-blue-300/70 text-sm mb-2">Max Rows</label>
                  <Input
                    type="number"
                    placeholder="Maximum rows..."
                    value={filters.maxRows}
                    onChange={(e) => setFilters(prev => ({ ...prev, maxRows: e.target.value }))}
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* No Results */}
      {displayTables.length === 0 && tables.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-12"
        >
          <Search className="w-16 h-16 text-blue-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Tables Found</h3>
          <p className="text-blue-300/70 mb-6">
            No tables match your current filters. Try adjusting your search criteria.
          </p>
          <Button
            onClick={clearAllFilters}
            icon={<X />}
            className="text-blue-400 hover:text-white"
          >
            Clear All Filters
          </Button>
        </motion.div>
      )}

      {/* Pagination - Only show if not using local filters */}
      {!hasActiveFilters && pagination && pagination.pages > 1 && (
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
          
          <div className="flex items-center space-x-4">
            <span className="text-blue-300 text-sm">
              Page {currentPage} of {pagination.pages}
            </span>
            <span className="text-dark-400">•</span>
            <span className="text-blue-300 text-sm">
              Showing {tables.length} tables
            </span>
          </div>
          
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
          key={`${currentPage}-${localSearch}-${JSON.stringify(filters)}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          className="space-y-6"
        >
          {displayTables.map((table, index) => (
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
                tableId={table.id}
                documentTitle={documentTitle}
              />
            </motion.div>
          ))}
        </motion.div>
      </AnimatePresence>

      {/* Results Info */}
      {displayTables.length > 0 && (
        <div className="text-center py-4">
          <p className="text-blue-300/70 text-sm">
            {hasActiveFilters ? (
              `Showing ${displayTables.length} filtered table${displayTables.length !== 1 ? 's' : ''}`
            ) : (
              pagination ? 
                `Showing ${tables.length} of ${pagination.total} tables` : 
                `${tables.length} table${tables.length !== 1 ? 's' : ''} displayed`
            )}
          </p>
        </div>
      )}
    </div>
  );
};
