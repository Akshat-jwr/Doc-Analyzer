import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X } from 'lucide-react';
import { Button } from './Button';

interface DeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  loading?: boolean;
}

export const DeleteModal: React.FC<DeleteModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  loading = false,
}) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm"
          />

          {/* Modal */}
          <div className="flex min-h-full items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.8, y: 50 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: 50 }}
              onClick={(e) => e.stopPropagation()}
              className="relative w-full max-w-md bg-gradient-to-br from-dark-800 to-dark-850 border border-red-500/30 rounded-2xl shadow-2xl overflow-hidden"
            >
              {/* Background glow */}
              <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-orange-500/5" />
              
              {/* Content */}
              <div className="relative p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center">
                      <AlertTriangle className="w-6 h-6 text-red-400" />
                    </div>
                    <h2 className="text-xl font-bold text-white">{title}</h2>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onClose}
                    className="text-red-400 hover:text-white hover:bg-red-500/20"
                  >
                    <X className="w-5 h-5" />
                  </Button>
                </div>

                {/* Message */}
                <div className="mb-8">
                  <p className="text-blue-200/80 leading-relaxed">{message}</p>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-3">
                  <Button
                    variant="ghost"
                    onClick={onClose}
                    className="flex-1 border border-blue-500/30 text-blue-300 hover:text-white hover:bg-blue-500/20"
                    disabled={loading}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={onConfirm}
                    loading={loading}
                    className="flex-1 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );
};
