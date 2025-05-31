import React from 'react';
import { motion } from 'framer-motion';

interface SimpleTableProps {
  content: string;
  title: string;
  pageInfo?: string;
}

export const SimpleTable: React.FC<SimpleTableProps> = ({ 
  content, 
  title, 
  pageInfo 
}) => {
  // Parse markdown table into structured data with null/undefined safety
  const parseTable = (markdown: string | undefined | null) => {
    // ✅ FIX: Check for null, undefined, or non-string values
    if (!markdown || typeof markdown !== 'string') {
      return { 
        headers: [], 
        rows: [], 
        error: 'No content provided or content is not a string' 
      };
    }

    try {
      const lines = markdown.split('\n').filter(line => line.trim());
      const tableLines = lines.filter(line => line.includes('|') && line.trim() !== '|');
      
      if (tableLines.length === 0) {
        return { 
          headers: [], 
          rows: [], 
          error: 'No table data found in content' 
        };
      }

      // Extract headers (first line with |)
      const headerLine = tableLines[0];
      const headers = headerLine
        .split('|')
        .map(h => h.trim())
        .filter(h => h && h !== '---' && !h.match(/^-+$/));

      if (headers.length === 0) {
        return { 
          headers: [], 
          rows: [], 
          error: 'No valid headers found' 
        };
      }

      // Find separator line (contains ---)
      const separatorIndex = tableLines.findIndex(line => line.includes('---'));
      const dataStartIndex = separatorIndex > 0 ? separatorIndex + 1 : 1;

      // Extract data rows
      const rows = tableLines
        .slice(dataStartIndex)
        .map(line => {
          const cells = line
            .split('|')
            .map(cell => cell.trim())
            .filter(cell => cell);
          
          // Ensure row has same number of columns as headers
          while (cells.length < headers.length) {
            cells.push('');
          }
          
          return cells.slice(0, headers.length);
        })
        .filter(row => row.some(cell => cell)); // Remove completely empty rows

      return { headers, rows, error: null };

    } catch (error) {
      return { 
        headers: [], 
        rows: [], 
        error: `Parse error: ${error instanceof Error ? error.message : 'Unknown error'}` 
      };
    }
  };

  // ✅ FIX: Pass content safely to parseTable
  const { headers, rows, error } = parseTable(content);

  // ✅ FIX: Add console log for debugging
  console.log('SimpleTable Debug:', {
    title,
    contentType: typeof content,
    contentLength: content?.length,
    hasContent: !!content,
    error,
    headersCount: headers.length,
    rowsCount: rows.length
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-dark-800/30 backdrop-blur-sm border border-blue-500/20 rounded-2xl overflow-hidden"
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-blue-500/20 bg-dark-800/50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white capitalize">
              {title.replace(/_/g, ' ')}
            </h3>
            {pageInfo && (
              <p className="text-blue-300/70 text-sm mt-1">{pageInfo}</p>
            )}
          </div>
          
          <div className="bg-blue-500/20 px-3 py-1 rounded-full">
            <span className="text-blue-400 font-medium text-sm">
              {error ? 'Error' : `${rows.length} rows`}
            </span>
          </div>
        </div>
      </div>

      {/* Table Content */}
      <div className="p-6">
        {error ? (
          <div className="text-center py-8">
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-4">
              <p className="text-red-400 font-medium mb-2">⚠️ Table Parsing Error</p>
              <p className="text-red-300/80 text-sm">{error}</p>
            </div>
            
            {/* Show raw content for debugging */}
            <details className="text-left bg-dark-700/30 rounded-lg p-4">
              <summary className="text-blue-300 cursor-pointer text-sm mb-2">
                🔍 Debug: Show Raw Content
              </summary>
              <div className="space-y-2">
                <p className="text-blue-200/70 text-xs">
                  <strong>Content Type:</strong> {typeof content}
                </p>
                <p className="text-blue-200/70 text-xs">
                  <strong>Content Length:</strong> {content?.length || 0}
                </p>
                <p className="text-blue-200/70 text-xs">
                  <strong>Has Content:</strong> {!!content ? 'Yes' : 'No'}
                </p>
                <pre className="text-xs text-blue-200/70 p-3 bg-dark-700/50 rounded overflow-x-auto whitespace-pre-wrap">
                  {content || 'No content available'}
                </pre>
              </div>
            </details>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-blue-500/20 bg-dark-800/30 rounded-lg overflow-hidden">
              {/* Headers */}
              <thead className="bg-blue-500/10">
                <tr>
                  {headers.map((header, index) => (
                    <th 
                      key={index}
                      className="border border-blue-500/20 px-4 py-3 text-left font-semibold text-blue-300 bg-dark-700/50"
                    >
                      {header || `Column ${index + 1}`}
                    </th>
                  ))}
                </tr>
              </thead>
              
              {/* Body */}
              <tbody>
                {rows.length > 0 ? (
                  rows.map((row, rowIndex) => (
                    <tr key={rowIndex} className="hover:bg-blue-500/5 transition-colors">
                      {row.map((cell, cellIndex) => (
                        <td 
                          key={cellIndex}
                          className="border border-blue-500/20 px-4 py-3 text-blue-200/90"
                        >
                          {cell || '-'}
                        </td>
                      ))}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td 
                      colSpan={headers.length || 1}
                      className="border border-blue-500/20 px-4 py-8 text-center text-blue-300/70"
                    >
                      No data rows found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </motion.div>
  );
};
