import React, { useState } from 'react';
import { motion } from 'framer-motion';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Layout } from '@/components/layout/Layout';
import { FileUpload } from '@/components/common/FileUpload';
import { Button } from '@/components/ui/Button';
import { useDocuments } from '@/hooks/useDocuments';
import { api } from '@/lib/api';
import { toast } from 'react-hot-toast';
import { 
  Upload, 
  FileText, 
  TrendingUp, 
  Zap, 
  BarChart3,
  ArrowRight,
  Sparkles
} from 'lucide-react';

const HomePage: React.FC = () => {
  const router = useRouter();
  const { documents } = useDocuments();
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const result = await api.uploadDocument(file);
      if (result.success) {
        toast.success(`Document uploaded successfully! ${result.message}`);
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

  const stats = [
    {
      icon: FileText,
      label: 'Documents',
      value: documents.length,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
    },
    {
      icon: BarChart3,
      label: 'Tables Extracted',
      value: documents.reduce((acc, doc) => acc + doc.total_tables_found, 0),
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/20',
    },
    {
      icon: TrendingUp,
      label: 'Processing Rate',
      value: '99%',
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/20',
    },
    {
      icon: Zap,
      label: 'Avg Speed',
      value: '< 2min',
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/20',
    },
  ];

  const features = [
    {
      icon: Upload,
      title: 'Smart Upload',
      description: 'Support for PDF, Word, Excel, CSV, and image files with intelligent processing.',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      icon: Sparkles,
      title: 'AI Extraction',
      description: 'Advanced AI extracts tables, text, and images with 99% accuracy.',
      color: 'from-purple-500 to-pink-500',
    },
    {
      icon: BarChart3,
      title: 'Data Visualization',
      description: 'Transform extracted data into interactive charts and insights.',
      color: 'from-emerald-500 to-teal-500',
    },
  ];

  return (
    <>
      <Head>
        <title>Dashboard - DocAnalyzer</title>
        <meta name="description" content="AI-Powered Document Intelligence Dashboard" />
      </Head>

      <Layout title="Dashboard">
        <div className="space-y-8">
          {/* Welcome Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-4xl mx-auto"
          >
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-primary-200 to-purple-400 bg-clip-text text-transparent mb-4"
            >
              Transform Documents with AI
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-xl text-dark-300 mb-8"
            >
              Upload any document and get instant AI-powered insights, table extraction, and intelligent analysis.
            </motion.p>
          </motion.div>

          {/* Stats Grid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
          >
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.4 + index * 0.1 }}
                  whileHover={{ scale: 1.02, y: -2 }}
                  className="bg-dark-800/50 backdrop-blur-sm border border-dark-700/50 rounded-xl p-6 hover:border-primary-500/30 transition-all"
                >
                  <div className={`w-12 h-12 ${stat.bgColor} rounded-lg flex items-center justify-center mb-4`}>
                    <Icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-1">{stat.value}</h3>
                  <p className="text-dark-400 text-sm">{stat.label}</p>
                </motion.div>
              );
            })}
          </motion.div>

          {/* Upload Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-gradient-to-br from-dark-800/30 to-dark-900/30 backdrop-blur-sm border border-dark-700/50 rounded-2xl p-8"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-white mb-2">Upload New Document</h2>
              <p className="text-dark-400">
                Drag & drop your files or click to browse. Supports PDF, Word, Excel, CSV, and images.
              </p>
            </div>

            <FileUpload
              onUpload={handleUpload}
              loading={uploading}
              maxSize={50}
              acceptedTypes={['.pdf', '.doc', '.docx', '.csv', '.xlsx', '.xls', '.png', '.jpg', '.jpeg']}
            />

            <div className="mt-6 text-center">
              <Button
                variant="ghost"
                onClick={() => router.push('/documents')}
                icon={<ArrowRight />}
              >
                View All Documents
              </Button>
            </div>
          </motion.div>

          {/* Features Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="grid md:grid-cols-3 gap-6"
          >
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 + index * 0.1 }}
                  whileHover={{ y: -4, scale: 1.02 }}
                  className="bg-dark-800/30 backdrop-blur-sm border border-dark-700/50 rounded-xl p-6 hover:border-primary-500/30 transition-all group"
                >
                  <div className={`w-14 h-14 bg-gradient-to-br ${feature.color} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                    <Icon className="w-7 h-7 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                  <p className="text-dark-400 text-sm">{feature.description}</p>
                </motion.div>
              );
            })}
          </motion.div>

          {/* Recent Documents */}
          {documents.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
              className="bg-dark-800/30 backdrop-blur-sm border border-dark-700/50 rounded-xl p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Recent Documents</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push('/documents')}
                  icon={<ArrowRight />}
                >
                  View All
                </Button>
              </div>
              
              <div className="space-y-3">
                {documents.slice(0, 3).map((doc) => (
                  <motion.div
                    key={doc.id}
                    whileHover={{ x: 4 }}
                    className="flex items-center justify-between p-3 bg-dark-700/30 rounded-lg hover:bg-dark-700/50 transition-colors cursor-pointer"
                    onClick={() => router.push(`/documents/${doc.id}`)}
                  >
                    <div className="flex items-center space-x-3">
                      <FileText className="w-5 h-5 text-primary-400" />
                      <div>
                        <p className="text-white font-medium">{doc.filename}</p>
                        <p className="text-dark-400 text-sm">{doc.page_count} pages</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-emerald-400 text-sm font-medium">
                        {doc.processing_status === 'completed' ? 'Ready' : 'Processing...'}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </Layout>
    </>
  );
};

export default HomePage;
