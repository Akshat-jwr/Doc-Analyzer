import React from 'react';
import { motion } from 'framer-motion';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Layout } from '@/components/layout/Layout';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useDocument } from '@/hooks/useDocuments';
import { 
  Download, 
  ArrowLeft,
  Table,
  FileText,
  Calendar,
  BarChart3,
  Eye,
  CheckCircle,
  Clock,
  AlertCircle,
  ExternalLink
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const DocumentViewPage: React.FC = () => {
  const router = useRouter();
  const { id } = router.query;
  const { document: documentData, loading, error } = useDocument(id as string);

  if (loading) {
    return (
      <Layout title="Loading Document...">
        <div className="flex items-center justify-center py-20">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  if (error || !documentData) {
    return (
      <Layout title="Document Not Found">
        <div className="text-center py-20">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Document Not Found</h2>
          <p className="text-blue-300/70 mb-6">The document you're looking for doesn't exist.</p>
          <Button onClick={() => router.push('/documents')} icon={<ArrowLeft />}>
            Back to Documents
          </Button>
        </div>
      </Layout>
    );
  }

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'completed':
        return { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-400/20', text: 'Ready' };
      case 'processing':
      case 'background_processing':
        return { icon: Clock, color: 'text-blue-400', bg: 'bg-blue-400/20', text: 'Processing' };
      case 'failed':
        return { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-400/20', text: 'Failed' };
      default:
        return { icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-400/20', text: 'Pending' };
    }
  };

  const statusConfig = getStatusConfig(documentData.document.processing_status);
  const StatusIcon = statusConfig.icon;

  return (
    <>
      <Head>
        <title>{documentData.document.filename} - DocAnalyzer</title>
        <meta name="description" content={`View ${documentData.document.filename}`} />
      </Head>

      <Layout title="Document Preview">
        {/* Fixed width container to prevent horizontal scroll */}
        <div className="max-w-7xl mx-auto w-full overflow-hidden">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center space-x-4 mb-6"
          >
            <Button
              variant="ghost"
              onClick={() => router.push('/documents')}
              icon={<ArrowLeft />}
              className="text-blue-400 hover:text-white hover:bg-blue-500/20"
            >
              Back
            </Button>
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold text-white truncate">
                {documentData.document.filename}
              </h1>
              <p className="text-blue-300/70 text-sm">
                Uploaded {formatDistanceToNow(new Date(documentData.document.uploaded_at+19800000))} ago
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                onClick={() => window.open(documentData.document.cloudinary_url, '_blank')}
                icon={<Download />}
                className="bg-blue-500/20 text-blue-300 hover:bg-blue-500/30"
              >
                Download
              </Button>
              {documentData.processing_info.analytical_queries_ready && (
                <Button
                  onClick={() => router.push(`/documents/${id}/tables`)}
                  icon={<Table />}
                  className="bg-gradient-to-r from-blue-500 to-cyan-500"
                >
                  Tables
                </Button>
              )}
            </div>
          </motion.div>

          {/* Main Content Grid */}
          <div className="grid lg:grid-cols-3 gap-6 overflow-hidden">
            {/* Document Preview - 2/3 width */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="lg:col-span-2 space-y-6"
            >
              {/* Document Viewer */}
              <div className="bg-gradient-to-br from-dark-800/50 to-dark-850/50 backdrop-blur-sm border border-blue-500/20 rounded-2xl p-6 h-[600px] overflow-hidden">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Document Preview</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => window.open(documentData.document.cloudinary_url, '_blank')}
                    icon={<ExternalLink />}
                    className="text-blue-400 hover:text-white hover:bg-blue-500/20"
                  >
                    Full Screen
                  </Button>
                </div>
                
                {/* PDF Embed or Fallback */}
                <div className="w-full h-full bg-dark-900/50 rounded-xl overflow-hidden border border-blue-500/10">
                  {documentData.document.cloudinary_url.includes('.pdf') ? (
                    <iframe
                      src={`${documentData.document.cloudinary_url}#toolbar=0&navpanes=0&scrollbar=0`}
                      className="w-full h-full"
                      title="Document Preview"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <div className="text-center">
                        <FileText className="w-20 h-20 text-blue-400 mx-auto mb-4" />
                        <h4 className="text-lg font-semibold text-white mb-2">Preview Not Available</h4>
                        <p className="text-blue-300/70 mb-4">This file type doesn't support preview</p>
                        <Button
                          onClick={() => window.open(documentData.document.cloudinary_url, '_blank')}
                          icon={<Download />}
                          className="bg-blue-500/20 text-blue-300 hover:bg-blue-500/30"
                        >
                          Download to View
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Content Preview */}
              {/* {documentData.page_texts.length > 0 && (
                <div className="bg-gradient-to-br from-dark-800/50 to-dark-850/50 backdrop-blur-sm border border-blue-500/20 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Content Preview</h3>
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {documentData.page_texts.slice(0, 3).map((pageText) => (
                      <div key={pageText.page_number} className="p-3 bg-dark-700/30 rounded-lg">
                        <div className="text-blue-400 text-sm font-medium mb-1">
                          Page {pageText.page_number}
                        </div>
                        <p className="text-blue-200/80 text-sm line-clamp-3">
                          {pageText.text || 'No text content found.'}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )} */}
            </motion.div>

            {/* Info Sidebar - 1/3 width */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
              className="space-y-6"
            >
              {/* Status Card */}
              <div className="bg-gradient-to-br from-dark-800/50 to-dark-850/50 backdrop-blur-sm border border-blue-500/20 rounded-2xl p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <div className={`w-10 h-10 ${statusConfig.bg} rounded-lg flex items-center justify-center`}>
                    <StatusIcon className={`w-5 h-5 ${statusConfig.color}`} />
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">Processing Status</h3>
                    <p className={`text-sm ${statusConfig.color}`}>{statusConfig.text}</p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-blue-300/70 text-sm">General Queries</span>
                    <span className={`text-sm font-medium ${documentData.processing_info.general_queries_ready ? 'text-green-400' : 'text-yellow-400'}`}>
                      {documentData.processing_info.general_queries_ready ? 'Ready' : 'Processing'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-blue-300/70 text-sm">Analytics</span>
                    <span className={`text-sm font-medium ${documentData.processing_info.analytical_queries_ready ? 'text-green-400' : 'text-yellow-400'}`}>
                      {documentData.processing_info.analytical_queries_ready ? 'Ready' : 'Processing'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="bg-gradient-to-br from-dark-800/50 to-dark-850/50 backdrop-blur-sm border border-blue-500/20 rounded-2xl p-6">
                <h3 className="text-white font-semibold mb-4 flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2 text-blue-400" />
                  Quick Analysis
                </h3>
                
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-blue-300/70 text-sm">Pages</span>
                    <span className="text-white font-bold">{documentData.document.page_count}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-blue-300/70 text-sm">Tables Found</span>
                    <span className="text-cyan-400 font-bold">{documentData.tables.length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-blue-300/70 text-sm">Images</span>
                    <span className="text-indigo-400 font-bold">{documentData.images.length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-blue-300/70 text-sm">Processing</span>
                    <span className="text-purple-400 font-bold">
                      {Math.round((documentData.document.tables_processed / Math.max(documentData.document.total_tables_found, 1)) * 100)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Document Info */}
              <div className="bg-gradient-to-br from-dark-800/50 to-dark-850/50 backdrop-blur-sm border border-blue-500/20 rounded-2xl p-6">
                <h3 className="text-white font-semibold mb-4 flex items-center">
                  <FileText className="w-5 h-5 mr-2 text-blue-400" />
                  Document Info
                </h3>
                
                <div className="space-y-3 text-sm">
                  <div className="flex items-center space-x-2">
                    <Calendar className="w-4 h-4 text-blue-400" />
                    <span className="text-blue-300/70">Upload Date:</span>
                  </div>
                  <p className="text-white ml-6">
                    {new Date(documentData.document.uploaded_at+19_800_000).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </p>
                  
                  <div className="flex items-center space-x-2 mt-4">
                    <Eye className="w-4 h-4 text-blue-400" />
                    <span className="text-blue-300/70">File Size:</span>
                  </div>
                  <p className="text-white ml-6">{documentData.document.page_count} pages</p>
                </div>
              </div>

              {/* Quick Actions */}
              {/* <div className="bg-gradient-to-br from-dark-800/50 to-dark-850/50 backdrop-blur-sm border border-blue-500/20 rounded-2xl p-6">
                <h3 className="text-white font-semibold mb-4">Quick Actions</h3>
                
                <div className="space-y-3">
                  <Button
                    variant="ghost"
                    onClick={() => window.open(documentData.document.cloudinary_url, '_blank')}
                    icon={<Download />}
                    className="w-full justify-start bg-blue-500/10 text-blue-300 hover:bg-blue-500/20"
                  >
                    Download Original
                  </Button>
                  
                  {documentData.processing_info.analytical_queries_ready && (
                    <Button
                      variant="ghost"
                      onClick={() => router.push(`/documents/${id}/tables`)}
                      icon={<Table />}
                      className="w-full justify-start bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20"
                    >
                      View All Tables
                    </Button>
                  )}
                  
                  <Button
                    variant="ghost"
                    onClick={() => router.push('/documents')}
                    icon={<ArrowLeft />}
                    className="w-full justify-start bg-gray-500/10 text-gray-300 hover:bg-gray-500/20"
                  >
                    Back to Documents
                  </Button>
                </div>
              </div> */}
            </motion.div>
          </div>
        </div>
      </Layout>
    </>
  );
};

export default DocumentViewPage;
