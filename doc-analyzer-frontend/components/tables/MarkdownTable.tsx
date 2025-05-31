import React from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownTableProps {
  content: string;
  title: string;
  pageInfo?: string;
}

export const MarkdownTable: React.FC<MarkdownTableProps> = ({ 
  content, 
  title, 
  pageInfo 
}) => {
  // Debug: Log the content to see what we're getting
  console.log('Table content for', title, ':', content);

  // Fallback: Parse markdown table manually if ReactMarkdown fails
  const parseMarkdownTable = (markdown: string) => {
    const lines = markdown.split('\n').filter(line => line.trim());
    const tableLines = lines.filter(line => line.includes('|'));
    
    if (tableLines.length < 2) return null;

    const headers = tableLines[0].split('|').map(h => h.trim()).filter(h => h);
    const separatorExists = tableLines[1].includes('---');
    const dataStartIndex = separatorExists ? 2 : 1;
    const rows = tableLines.slice(dataStartIndex).map(line => 
      line.split('|').map(cell => cell.trim()).filter(cell => cell)
    );

    return { headers, rows };
  };

  const tableData = parseMarkdownTable(content);

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
            <span className="text-blue-400 font-medium text-sm">Table Data</span>
          </div>
        </div>
      </div>

      {/* Table Content */}
      <div className="p-6">
        <div className="overflow-x-auto">
          {/* Try ReactMarkdown first */}
          <div className="markdown-table-container mb-4">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ children, ...props }) => (
                  <table className="w-full border-collapse border border-blue-500/20 bg-dark-800/30 rounded-lg overflow-hidden mb-4">
                    {children}
                  </table>
                ),
                thead: ({ children, ...props }) => (
                  <thead className="bg-blue-500/10">
                    {children}
                  </thead>
                ),
                tbody: ({ children, ...props }) => (
                  <tbody>
                    {children}
                  </tbody>
                ),
                th: ({ children, ...props }) => (
                  <th className="border border-blue-500/20 px-4 py-3 text-left font-semibold text-blue-300 bg-dark-700/50 whitespace-nowrap">
                    {children}
                  </th>
                ),
                td: ({ children, ...props }) => (
                  <td className="border border-blue-500/20 px-4 py-3 text-blue-200/90 whitespace-nowrap">
                    {children}
                  </td>
                ),
                tr: ({ children, ...props }) => (
                  <tr className="hover:bg-blue-500/5 transition-colors">
                    {children}
                  </tr>
                ),
              }}
            >
              {content}
            </ReactMarkdown>
          </div>

          {/* Fallback: Manual table rendering if ReactMarkdown doesn't work */}
          {tableData && (
            <div className="fallback-table">
              <h4 className="text-blue-300 text-sm mb-3">Manual Table Rendering:</h4>
              <table className="w-full border-collapse border border-blue-500/20 bg-dark-800/30 rounded-lg overflow-hidden">
                <thead className="bg-blue-500/10">
                  <tr>
                    {tableData.headers.map((header, index) => (
                      <th 
                        key={index}
                        className="border border-blue-500/20 px-4 py-3 text-left font-semibold text-blue-300 bg-dark-700/50 whitespace-nowrap"
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tableData.rows.map((row, rowIndex) => (
                    <tr key={rowIndex} className="hover:bg-blue-500/5 transition-colors">
                      {row.map((cell, cellIndex) => (
                        <td 
                          key={cellIndex}
                          className="border border-blue-500/20 px-4 py-3 text-blue-200/90 whitespace-nowrap"
                        >
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Debug: Show raw content */}
          <details className="mt-4 p-4 bg-dark-700/30 rounded-lg">
            <summary className="text-blue-300 cursor-pointer text-sm">Debug: Raw Content</summary>
            <pre className="text-xs text-blue-200/70 mt-2 whitespace-pre-wrap overflow-x-auto">
              {content}
            </pre>
          </details>
        </div>
      </div>
    </motion.div>
  );
};
