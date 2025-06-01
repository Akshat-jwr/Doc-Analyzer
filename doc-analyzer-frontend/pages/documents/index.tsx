import React, { useState } from 'react';
import { motion } from 'framer-motion';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Layout } from '@/components/layout/Layout';
import { DocumentList } from '@/components/documents/DocumentList';
import { FileUpload } from '@/components/common/FileUpload';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { useDocuments } from '@/hooks/useDocuments';
import { api } from '@/lib/api';
import { toast } from 'react-hot-toast';
import { Plus, Download } from 'lucide-react';

const DocumentsPage: React.FC = () => {
  const router = useRouter();
  const { documents, loading, mutate } = useDocuments();
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const result = await api.uploadDocument(file);
      if (result.success) {
        toast.success(`Document uploaded successfully!`);
        setShowUploadModal(false);
        mutate(); // Refresh documents list
        router.push(`/documents/${result.document_id}`);
      } else {
        throw new Error(result.error || 'Upload failed');
      }
    } catch (error: any) {
      toast.error(error.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleView = (id: string) => {
    router.push(`/documents/${id}`);
  };

  const handleDelete = async (id: string) => {

    try {
      await api.deleteDocument(id);
      toast.success('Document deleted successfully');
      mutate(); // Refresh documents list
    } catch (error: any) {
      toast.error(error.message || 'Failed to delete document');
    }
  };

  const handleDownload = (url: string, filename: string) => {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
  };

  const handleShowTables = (id: string) => {
    router.push(`/documents/${id}/tables`);
  };

  return (
    <>
      <Head>
        <title>Documents - DocAnalyzer</title>
        <meta name="description" content="Manage your documents and view processing status" />
      </Head>

      <Layout title="Documents">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div>
              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-3xl font-bold text-white"
              >
                Your Documents
              </motion.h1>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="text-dark-400 mt-1"
              >
                Manage and analyze your uploaded documents
              </motion.p>
            </div>

            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
            >
              <Button
                onClick={() => setShowUploadModal(true)}
                icon={<Plus />}
                className="bg-gradient-to-r from-primary-500 to-purple-600 hover:from-primary-600 hover:to-purple-700"
              >
                Upload Document
              </Button>
            </motion.div>
          </div>

          {/* Documents List */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <DocumentList
              documents={documents}
              loading={loading}
              onView={handleView}
              onDelete={handleDelete}
              onDownload={handleDownload}
              onShowTables={handleShowTables}
              onUpload={() => setShowUploadModal(true)}
            />
          </motion.div>
        </div>

        {/* Upload Modal */}
        <Modal
          isOpen={showUploadModal}
          onClose={() => setShowUploadModal(false)}
          title="Upload New Document"
        >
          <div className="p-6">
            <FileUpload
              onUpload={handleUpload}
              loading={uploading}
              maxSize={50}
              acceptedTypes={['.pdf', '.doc', '.docx', '.csv', '.xlsx', '.xls', '.png', '.jpg', '.jpeg']}
            />
          </div>
        </Modal>
      </Layout>
    </>
  );
};

export default DocumentsPage;
