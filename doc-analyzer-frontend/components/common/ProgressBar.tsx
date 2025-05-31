import React from 'react';
import { motion } from 'framer-motion';

interface ProgressBarProps {
  progress: number;
  label?: string;
  color?: 'primary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  label,
  color = 'primary',
  size = 'md',
  animated = true,
}) => {
  const colorClasses = {
    primary: 'from-primary-500 to-purple-600',
    success: 'from-emerald-500 to-teal-600',
    warning: 'from-yellow-500 to-orange-600',
    danger: 'from-red-500 to-pink-600',
  };

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-dark-300">{label}</span>
          <span className="text-sm text-dark-400">{Math.round(clampedProgress)}%</span>
        </div>
      )}
      
      <div className={`w-full bg-dark-700 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${clampedProgress}%` }}
          transition={{ duration: animated ? 0.5 : 0, ease: 'easeOut' }}
          className={`h-full bg-gradient-to-r ${colorClasses[color]} relative`}
        >
          {animated && clampedProgress > 0 && clampedProgress < 100 && (
            <motion.div
              animate={{ x: ['-100%', '100%'] }}
              transition={{ repeat: Infinity, duration: 1.5, ease: 'easeInOut' }}
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
            />
          )}
        </motion.div>
      </div>
    </div>
  );
};
