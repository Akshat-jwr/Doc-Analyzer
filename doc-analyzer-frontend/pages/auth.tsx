import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import Head from 'next/head';
import { useAuth } from '@/hooks/useAuth';
import { AuthForm } from '@/components/auth/AuthForm';
import { AnimatedLogo } from '@/components/auth/AnimatedLogo';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

const AuthPage: React.FC = () => {
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && user) {
      window.location.href = '/';
    }
  }, [user, loading]);

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (user) {
    return null;
  }

  return (
    <>
      <Head>
        <title>Sign In - DocAnalyzer</title>
        <meta name="description" content="Sign in to your DocAnalyzer account" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-dark-950 via-dark-900 to-dark-800 relative overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-conic from-primary-500/5 via-purple-500/5 to-primary-500/5 rounded-full blur-3xl animate-spin" style={{ animationDuration: '60s' }} />
        </div>

        {/* Grid Pattern */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(59, 130, 246, 0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(59, 130, 246, 0.1) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px'
          }}
        />

        <div className="relative z-10 min-h-screen flex">
          {/* Left Side - Logo & Branding */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className="hidden lg:flex lg:w-1/2 flex-col justify-center items-center p-12"
          >
            <div className="max-w-lg">
              <AnimatedLogo />
              
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 1 }}
                className="mt-12 space-y-6"
              >
                <h2 className="text-3xl font-bold text-white">
                  Transform Documents into{' '}
                  <span className="bg-gradient-to-r from-primary-400 to-purple-500 bg-clip-text text-transparent">
                    Intelligent Data
                  </span>
                </h2>
                
                <p className="text-dark-300 text-lg leading-relaxed">
                  Upload any document and let our AI extract, analyze, and visualize your data. 
                  From PDFs to spreadsheets, get instant insights with natural language queries.
                </p>

                {/* Feature Pills */}
                <div className="flex flex-wrap gap-3 mt-8">
                  {[
                    '🚀 Instant Processing',
                    '📊 Smart Tables',
                    '💬 AI Chat',
                    '📈 Data Visualization',
                    '🔍 Intelligent Search',
                    '📱 Real-time Updates'
                  ].map((feature, index) => (
                    <motion.div
                      key={feature}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 1.2 + index * 0.1 }}
                      className="px-3 py-1.5 bg-dark-800/50 border border-dark-700/50 rounded-full text-sm text-dark-300"
                    >
                      {feature}
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </div>
          </motion.div>

          {/* Right Side - Auth Form */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className="w-full lg:w-1/2 flex items-center justify-center p-8"
          >
            <div className="w-full max-w-md">
              {/* Mobile Logo */}
              <div className="lg:hidden mb-8 text-center">
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className="flex items-center justify-center space-x-3 mb-4"
                >
                  <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl flex items-center justify-center">
                    <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-purple-500 bg-clip-text text-transparent">
                    DocAnalyzer
                  </h1>
                </motion.div>
                <p className="text-dark-400">AI-Powered Document Intelligence</p>
              </div>

              <AuthForm />
            </div>
          </motion.div>
        </div>
      </div>
    </>
  );
};

export default AuthPage;
