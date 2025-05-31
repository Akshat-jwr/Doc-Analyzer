import { useEffect, useRef, useState } from 'react';
import { DocumentStatus } from '@/types';

interface UseWebSocketProps {
  documentId: string;
  onStatusUpdate?: (status: DocumentStatus) => void;
}

export const useWebSocket = ({ documentId, onStatusUpdate }: UseWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastStatus, setLastStatus] = useState<DocumentStatus | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const maxReconnectAttempts = 5;
  const reconnectAttempts = useRef(0);

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/documents/${documentId}/progress`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        reconnectAttempts.current = 0;
        console.log('WebSocket connected');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.error) {
            console.error('WebSocket error:', data.error);
            return;
          }

          const status: DocumentStatus = {
            document_id: documentId,
            filename: '',
            processing_status: data.processing_status,
            pages: 0,
            tables_processed: data.tables_processed || 0,
            total_tables: data.total_tables || 0,
            general_queries_ready: data.general_queries_ready || false,
            analytical_queries_ready: data.analytical_queries_ready || false,
            message: getStatusMessage(data.processing_status, data),
            progress_percentage: data.progress_percentage || 0,
          };

          setLastStatus(status);
          onStatusUpdate?.(status);

          // Close connection if processing is complete
          if (data.processing_status === 'completed' || data.processing_status === 'failed') {
            wsRef.current?.close();
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');

        // Attempt to reconnect
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          console.log(`Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, Math.pow(2, reconnectAttempts.current) * 1000); // Exponential backoff
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  };

  useEffect(() => {
    if (documentId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [documentId]);

  return {
    isConnected,
    lastStatus,
    connect,
    disconnect,
  };
};

const getStatusMessage = (status: string, data: any): string => {
  switch (status) {
    case 'processing':
      return 'Processing document...';
    case 'text_images_complete':
      return '✅ Text extraction complete! Analytics loading...';
    case 'background_processing':
      return `🔄 Extracting tables... (${data.tables_processed}/${data.total_tables})`;
    case 'completed':
      return '🎉 Processing complete! All features ready.';
    case 'failed':
      return '❌ Processing failed';
    default:
      return 'Processing...';
  }
};
