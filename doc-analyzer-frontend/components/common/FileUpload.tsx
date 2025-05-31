import React, { useCallback, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, AlertCircle, CheckCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>;
  loading?: boolean;
  maxSize?: number; // in MB
  acceptedTypes?: string[];
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onUpload,
  loading = false,
  maxSize = 50,
  acceptedTypes = ['.pdf', '.doc', '.docx', '.csv', '.xlsx', '.xls', '.png', '.jpg', '.jpeg'],
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxSize * 1024 * 1024) {
      return `File size must be less than ${maxSize}MB`;
    }

    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!acceptedTypes.includes(fileExtension)) {
      return `File type not supported. Accepted types: ${acceptedTypes.join(', ')}`;
    }

    return null;
  };

  const handleFile = useCallback(async (file: File) => {
    setError(null);
    
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      setUploadProgress(0);
      await onUpload(file);
      setUploadProgress(100);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
      setUploadProgress(0);
    }
  }, [onUpload, maxSize, acceptedTypes]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setDragActive(true);
    }
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, [handleFile]);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-300 ${
          dragActive
            ? 'border-primary-500 bg-primary-500/10'
            : error
            ? 'border-red-500 bg-red-500/5'
            : 'border-dark-600 hover:border-primary-500/50 hover:bg-primary-500/5'
        }`}
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          onChange={handleFileInput}
          accept={acceptedTypes.join(',')}
          disabled={loading}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="space-y-4"
            >
              <LoadingSpinner size="lg" />
              <p className="text-white font-medium">Processing your document...</p>
              {uploadProgress > 0 && (
                <div className="w-full max-w-xs mx-auto">
                  <div className="bg-dark-700 rounded-full h-2 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                      className="h-full bg-gradient-to-r from-primary-500 to-purple-600"
                    />
                  </div>
                  <p className="text-sm text-dark-400 mt-1">{uploadProgress}%</p>
                </div>
              )}
            </motion.div>
          ) : error ? (
            <motion.div
              key="error"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="space-y-4"
            >
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
              <div>
                <p className="text-red-400 font-medium">Upload Failed</p>
                <p className="text-dark-400 text-sm mt-1">{error}</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setError(null)}
                icon={<X />}
              >
                Try Again
              </Button>
            </motion.div>
          ) : (
            <motion.div
              key="upload"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="space-y-4"
            >
              <motion.div
                animate={dragActive ? { scale: 1.1, rotate: 5 } : { scale: 1, rotate: 0 }}
                className="w-16 h-16 mx-auto bg-gradient-to-br from-primary-500/20 to-purple-500/20 rounded-full flex items-center justify-center"
              >
                <Upload className="w-8 h-8 text-primary-400" />
              </motion.div>
              
              <div>
                <h3 className="text-lg font-semibold text-white">
                  {dragActive ? 'Drop your file here' : 'Upload Document'}
                </h3>
                <p className="text-dark-400 mt-1">
                  Drag & drop or click to browse
                </p>
              </div>

              <div className="flex flex-wrap gap-2 justify-center">
                {acceptedTypes.slice(0, 6).map((type) => (
                  <span
                    key={type}
                    className="px-2 py-1 bg-dark-700/50 text-dark-300 text-xs rounded-full"
                  >
                    {type.toUpperCase().slice(1)}
                  </span>
                ))}
                {acceptedTypes.length > 6 && (
                  <span className="px-2 py-1 bg-dark-700/50 text-dark-300 text-xs rounded-full">
                    +{acceptedTypes.length - 6} more
                  </span>
                )}
              </div>

              <p className="text-dark-500 text-xs">
                Maximum file size: {maxSize}MB
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};
