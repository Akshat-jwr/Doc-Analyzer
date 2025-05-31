import React, { useState } from 'react';
import { motion } from 'framer-motion';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Layout } from '@/components/layout/Layout';
import { TableView } from '@/components/tables/TableView';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useDocumentTables, useDocumentTablesSummary } from '@/hooks/useDocuments';
import { 
  ArrowLeft, 
  Table, 
  AlertCircle, 
  BarChart3, 
  Columns
} from 'lucide-react';

const DocumentTablesPage: React.FC = () => {
  const router = useRouter();
  const { id } = router.query;
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const { 
    tables, 
    pagination, 
    document: documentInfo, 
    loading: tablesLoading, 
    error: tablesError,
    mutate
  } = useDocumentTables(id as string, currentPage, searchQuery);

  const { 
    summary, 
    loading: summaryLoading, 
    error: summaryError 
  } = useDocumentTablesSummary(id as string);

  if (tablesLoading || summaryLoading) {
    return (
      <Layout title="Loading Tables...">
        <div className="flex items-center justify-center py-20">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  if (tablesError || summaryError || !documentInfo) {
    return (
      <Layout title="Tables Not Found">
        <div className="text-center py-20">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Unable to Load Tables</h2>
          <p className="text-blue-300/70 mb-6">
            {tablesError?.message || summaryError?.message || 'Document not found'}
          </p>
          <Button onClick={() => router.push('/documents')} icon={<ArrowLeft />}>
            Back to Documents
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <>
      <Head>
        <title>Tables - {documentInfo.filename} - DocAnalyzer</title>
      </Head>

      <Layout title="Document Tables">
        <div className="space-y-6">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center space-x-4"
          >
            <Button
              variant="ghost"
              onClick={() => router.push(`/documents/${id}`)}
              icon={<ArrowLeft />}
              className="text-blue-400 hover:text-white hover:bg-blue-500/20"
            >
              Back
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-white">Document Tables</h1>
              <p className="text-blue-300/70">
                {summary?.total_tables || 0} tables from {documentInfo.filename}
              </p>
            </div>
          </motion.div>

          {/* Stats */}
          {summary && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="grid grid-cols-1 md:grid-cols-3 gap-4"
            >
              <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-xl p-6 border border-blue-500/20">
                <Table className="w-8 h-8 text-blue-400 mb-3" />
                <h3 className="text-2xl font-bold text-white mb-1">{summary.total_tables}</h3>
                <p className="text-blue-300/70 text-sm">Total Tables</p>
              </div>
              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-xl p-6 border border-purple-500/20">
                <BarChart3 className="w-8 h-8 text-purple-400 mb-3" />
                <h3 className="text-2xl font-bold text-white mb-1">{summary.total_rows}</h3>
                <p className="text-purple-300/70 text-sm">Total Rows</p>
              </div>
              <div className="bg-gradient-to-br from-emerald-500/10 to-teal-500/10 rounded-xl p-6 border border-emerald-500/20">
                <Columns className="w-8 h-8 text-emerald-400 mb-3" />
                <h3 className="text-2xl font-bold text-white mb-1">{summary.average_columns}</h3>
                <p className="text-emerald-300/70 text-sm">Avg Columns</p>
              </div>
            </motion.div>
          )}

          {/* Tables */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <TableView 
              tables={tables}
              pagination={pagination}
              documentTitle={documentInfo.filename}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              currentPage={currentPage}
              onPageChange={setCurrentPage}
              documentId={id as string}
            />
          </motion.div>
        </div>
      </Layout>
    </>
  );
};

export default DocumentTablesPage;
