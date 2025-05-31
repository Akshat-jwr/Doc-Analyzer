import useSWR from 'swr';
import { api } from '@/lib/api';
import { Document, DocumentDetailResponse } from '@/types';

export const useDocuments = () => {
  const { data, error, mutate } = useSWR<Document[]>('documents', () => api.getDocuments());

  return {
    documents: data || [],
    loading: !error && !data,
    error,
    mutate,
  };
};

export const useDocument = (id: string) => {
  const { data, error, mutate } = useSWR<DocumentDetailResponse>(
    id ? `document-${id}` : null,
    () => api.getDocument(id)
  );

  return {
    document: data,
    loading: !error && !data,
    error,
    mutate,
  };
};
