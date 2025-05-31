import React from 'react';
import { motion } from 'framer-motion';
import { ProcessingStatus } from '@/types';
import { CheckCircle, Clock, AlertCircle, Loader2 } from 'lucide-react';

interface StatusIndicatorProps {
  status: ProcessingStatus;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, size = 'md' }) => {
  const sizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-6 h-6',
  };

  const getStatusConfig = (status: ProcessingStatus) => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return {
          icon: CheckCircle,
          color: 'text-emerald-500',
          bgColor: 'bg-emerald-500/20',
          label: 'Completed',
          animation: 'none',
        };
      case ProcessingStatus.BACKGROUND_PROCESSING:
        return {
          icon: Loader2,
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-500/20',
          label: 'Processing',
          animation: 'spin',
        };
      case ProcessingStatus.TEXT_IMAGES_COMPLETE:
        return {
          icon: Clock,
          color: 'text-blue-500',
          bgColor: 'bg-blue-500/20',
          label: 'Analyzing',
          animation: 'pulse',
        };
      case ProcessingStatus.FAILED:
        return {
          icon: AlertCircle,
          color: 'text-red-500',
          bgColor: 'bg-red-500/20',
          label: 'Failed',
          animation: 'none',
        };
      default:
        return {
          icon: Clock,
          color: 'text-gray-500',
          bgColor: 'bg-gray-500/20',
          label: 'Processing',
          animation: 'pulse',
        };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      className={`flex items-center space-x-2 px-2 py-1 rounded-full ${config.bgColor}`}
    >
      <Icon 
        className={`${sizes[size]} ${config.color} ${
          config.animation === 'spin' ? 'animate-spin' : 
          config.animation === 'pulse' ? 'animate-pulse' : ''
        }`} 
      />
      <span className={`text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    </motion.div>
  );
};
