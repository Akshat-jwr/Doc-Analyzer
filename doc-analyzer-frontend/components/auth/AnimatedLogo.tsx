import React from 'react';
import { motion } from 'framer-motion';

export const AnimatedLogo: React.FC = () => {
  return (
    <div className="flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="relative"
      >
        {/* Main Logo Container */}
        <motion.div
          animate={{ 
            rotate: [0, 360],
            scale: [1, 1.05, 1] 
          }}
          transition={{ 
            rotate: { duration: 20, repeat: Infinity, ease: "linear" },
            scale: { duration: 2, repeat: Infinity, ease: "easeInOut" }
          }}
          className="w-32 h-32 relative"
        >
          {/* Outer Ring */}
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ duration: 1, delay: 0.2 }}
            className="absolute inset-0 rounded-full border-4 border-primary-500/30"
          />
          
          {/* Inner Ring */}
          <motion.div
            initial={{ scale: 0, rotate: 180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ duration: 1, delay: 0.4 }}
            className="absolute inset-2 rounded-full border-2 border-primary-400/50"
          />
          
          {/* Center Icon */}
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="absolute inset-0 flex items-center justify-center"
          >
            <svg
              className="w-12 h-12 text-primary-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </motion.div>
          
          {/* Floating Particles */}
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 bg-primary-500/60 rounded-full"
              style={{
                top: '50%',
                left: '50%',
              }}
              animate={{
                x: [0, Math.cos(i * 60 * Math.PI / 180) * 60],
                y: [0, Math.sin(i * 60 * Math.PI / 180) * 60],
                opacity: [0.6, 0.2, 0.6],
                scale: [1, 0.5, 1],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeInOut",
              }}
            />
          ))}
        </motion.div>
        
        {/* Glow Effect */}
        <motion.div
          animate={{ 
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.6, 0.3] 
          }}
          transition={{ 
            duration: 2, 
            repeat: Infinity, 
            ease: "easeInOut" 
          }}
          className="absolute inset-0 bg-primary-500/20 rounded-full blur-xl -z-10"
        />
      </motion.div>
      
      {/* Brand Text */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, delay: 0.8 }}
        className="ml-6"
      >
        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary-400 via-primary-500 to-purple-600 bg-clip-text text-transparent">
          DocAnalyzer
        </h1>
        <p className="text-dark-400 text-lg mt-1">AI-Powered Document Intelligence</p>
      </motion.div>
    </div>
  );
};
