import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, SortAsc, FileText, FileSpreadsheet, Image as ImageIcon } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

interface DocumentFiltersProps {
  onSearch: (query: string) => void;
  onFilterChange: (filters: FilterOptions) => void;
  onSortChange: (sort: SortOption) => void;
}

interface FilterOptions {
  fileType: 'all' | 'pdf' | 'spreadsheet' | 'image';
  status: 'all' | 'completed' | 'processing' | 'failed';
}

type SortOption = 'newest' | 'oldest' | 'name' | 'size';

export const DocumentFilters: React.FC<DocumentFiltersProps> = ({
  onSearch,
  onFilterChange,
  onSortChange,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterOptions>({
    fileType: 'all',
    status: 'all',
  });
  const [sortBy, setSortBy] = useState<SortOption>('newest');

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    onSearch(value);
  };

  const handleFilterChange = (key: keyof FilterOptions, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleSortChange = (value: SortOption) => {
    setSortBy(value);
    onSortChange(value);
  };

  const fileTypes = [
    { value: 'all', label: 'All Files', icon: null },
    { value: 'pdf', label: 'PDF', icon: FileText },
    { value: 'spreadsheet', label: 'Spreadsheets', icon: FileSpreadsheet },
    { value: 'image', label: 'Images', icon: ImageIcon },
  ];

  const statuses = [
    { value: 'all', label: 'All Status' },
    { value: 'completed', label: 'Completed' },
    { value: 'processing', label: 'Processing' },
    { value: 'failed', label: 'Failed' },
  ];

  const sortOptions = [
    { value: 'newest', label: 'Newest First' },
    { value: 'oldest', label: 'Oldest First' },
    { value: 'name', label: 'Name A-Z' },
    { value: 'size', label: 'File Size' },
  ];

  return (
    <div className="space-y-4">
      {/* Main Search and Filter Row */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="flex-1">
          <Input
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            icon={<Search />}
            className="w-full"
          />
        </div>

        {/* Filter Button */}
        <Button
          variant={showFilters ? 'primary' : 'secondary'}
          onClick={() => setShowFilters(!showFilters)}
          icon={<Filter />}
        >
          Filters
        </Button>

        {/* Sort Button */}
        <div className="relative">
          <select
            value={sortBy}
            onChange={(e) => handleSortChange(e.target.value as SortOption)}
            className="appearance-none bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 pr-8 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {sortOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <SortAsc className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dark-400 pointer-events-none" />
        </div>
      </div>

      {/* Expanded Filters */}
      <motion.div
        initial={{ height: 0, opacity: 0 }}
        animate={{ 
          height: showFilters ? 'auto' : 0, 
          opacity: showFilters ? 1 : 0 
        }}
        transition={{ duration: 0.3 }}
        className="overflow-hidden"
      >
        <div className="bg-dark-800/30 rounded-xl p-6 border border-dark-700/50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* File Type Filter */}
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-3">
                File Type
              </label>
              <div className="grid grid-cols-2 gap-2">
                {fileTypes.map((type) => {
                  const Icon = type.icon;
                  return (
                    <motion.button
                      key={type.value}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleFilterChange('fileType', type.value)}
                      className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                        filters.fileType === type.value
                          ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                          : 'bg-dark-700/50 text-dark-300 hover:text-white hover:bg-dark-600/50'
                      }`}
                    >
                      {Icon && <Icon className="w-4 h-4" />}
                      <span>{type.label}</span>
                    </motion.button>
                  );
                })}
              </div>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-3">
                Processing Status
              </label>
              <div className="grid grid-cols-2 gap-2">
                {statuses.map((status) => (
                  <motion.button
                    key={status.value}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleFilterChange('status', status.value)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      filters.status === status.value
                        ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                        : 'bg-dark-700/50 text-dark-300 hover:text-white hover:bg-dark-600/50'
                    }`}
                  >
                    {status.label}
                  </motion.button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
