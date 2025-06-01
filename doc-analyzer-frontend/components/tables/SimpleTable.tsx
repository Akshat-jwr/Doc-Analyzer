import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Download, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'react-hot-toast';

interface SimpleTableProps {
    content: string;
    title: string;
    pageInfo?: string;
    tableId?: string;
    documentTitle?: string;
}

export const SimpleTable: React.FC<SimpleTableProps> = ({
    content,
    title,
    pageInfo,
    tableId,
    documentTitle
}) => {
    const [showDebug, setShowDebug] = useState(false);
    const [exporting, setExporting] = useState(false);

    // Debug logging
    console.log('SimpleTable Props:', {
        title,
        tableId,
        hasTableId: !!tableId,
        contentLength: content?.length
    });

    // Parse markdown table into structured data with null/undefined safety
    const parseTable = (markdown: string | undefined | null) => {
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

    const handleExportSingle = async () => {
        if (!tableId) {
            console.error('No tableId provided for export!');
            toast.error('Table ID not available');
            return;
        }

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

    const { headers, rows, error } = parseTable(content);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-dark-800/30 backdrop-blur-sm border border-blue-500/20 rounded-2xl overflow-hidden"
        >
            {/* Header */}
            <div className="px-6 py-4 border-b border-blue-500/20 bg-dark-800/50">
                <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                        <h3 className="text-lg font-semibold text-white capitalize truncate">
                            {title.replace(/_/g, ' ')}
                        </h3>
                        {pageInfo && (
                            <p className="text-blue-300/70 text-sm mt-1">{pageInfo}</p>
                        )}
                    </div>

                    <div className="flex items-center space-x-3 ml-4">
                        {/* Status Badge */}
                        <div className="bg-blue-500/20 px-3 py-1 rounded-full">
                            <span className="text-blue-400 font-medium text-sm">
                                {error ? 'Error' : `${rows.length} rows`}
                            </span>
                        </div>

                        {/* Export Button - Always show for debugging */}
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={handleExportSingle}
                            //   disabled={exporting || !tableId || error}
                            className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 hover:bg-green-500/30 border border-green-500/30 hover:border-green-400/40 text-green-300 hover:text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            title={!tableId ? "Table ID not available" : "Export table as Excel"}
                        >
                            <Download className="w-4 h-4" />
                            <span className="text-sm font-medium">
                                {exporting ? 'Exporting...' : !tableId ? 'No ID' : 'Export Excel'}
                            </span>
                        </motion.button>
                    </div>
                </div>
            </div>

            {/* Table Content */}
            <div className="p-6">
                {error ? (
                    <div className="text-center py-8">
                        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 mb-4">
                            <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-3" />
                            <p className="text-red-400 font-medium mb-2">⚠️ Table Parsing Error</p>
                            <p className="text-red-300/80 text-sm">{error}</p>
                        </div>

                        {/* Debug Toggle */}
                        <button
                            onClick={() => setShowDebug(!showDebug)}
                            className="flex items-center space-x-2 text-blue-300 hover:text-white text-sm mx-auto bg-dark-700/30 px-3 py-2 rounded-lg transition-colors"
                        >
                            <span>🔍 Debug Information</span>
                            {showDebug ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>

                        {/* Debug Panel */}
                        {showDebug && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                className="mt-4 text-left bg-dark-700/30 rounded-lg p-4 overflow-hidden"
                            >
                                <div className="space-y-2 text-xs">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <p className="text-blue-200/70">
                                                <strong>Content Type:</strong> {typeof content}
                                            </p>
                                            <p className="text-blue-200/70">
                                                <strong>Content Length:</strong> {content?.length || 0}
                                            </p>
                                            <p className="text-blue-200/70">
                                                <strong>Has Content:</strong> {!!content ? 'Yes' : 'No'}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-blue-200/70">
                                                <strong>Table ID:</strong> {tableId || 'Not provided'}
                                            </p>
                                            <p className="text-blue-200/70">
                                                <strong>Headers Found:</strong> {headers.length}
                                            </p>
                                            <p className="text-blue-200/70">
                                                <strong>Rows Found:</strong> {rows.length}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="mt-4">
                                        <p className="text-blue-200/70 mb-2"><strong>Raw Content:</strong></p>
                                        <pre className="text-blue-200/70 p-3 bg-dark-700/50 rounded overflow-x-auto whitespace-pre-wrap max-h-40 text-xs">
                                            {content || 'No content available'}
                                        </pre>
                                    </div>
                                </div>
                            </motion.div>
                        )}
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
                                            className="border border-blue-500/20 px-4 py-3 text-left font-semibold text-blue-300 bg-dark-700/50 whitespace-nowrap"
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
                                                    className="border border-blue-500/20 px-4 py-3 text-blue-200/90 max-w-xs"
                                                >
                                                    <div className="truncate" title={cell || '-'}>
                                                        {cell || '-'}
                                                    </div>
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

                        {/* Table Footer with Stats */}
                        {rows.length > 0 && (
                            <div className="mt-4 flex items-center justify-between text-xs text-blue-300/70 bg-dark-700/20 rounded-lg p-3">
                                <div className="flex items-center space-x-4">
                                    <span>📊 {headers.length} columns × {rows.length} rows</span>
                                    {documentTitle && (
                                        <span>📄 {documentTitle}</span>
                                    )}
                                    {pageInfo && (
                                        <span>📖 {pageInfo.split('•')[0].trim()}</span>
                                    )}
                                </div>
                                <span>💡 Scroll horizontally to view all data</span>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Export Status Overlay */}
            {exporting && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="absolute inset-0 bg-dark-900/80 backdrop-blur-sm flex items-center justify-center rounded-2xl"
                >
                    <div className="flex items-center space-x-3 bg-dark-800 border border-blue-500/30 rounded-lg px-6 py-3">
                        <div className="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-blue-300 font-medium">Exporting to Excel...</span>
                    </div>
                </motion.div>
            )}
        </motion.div>
    );
};
