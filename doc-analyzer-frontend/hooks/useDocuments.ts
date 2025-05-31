import useSWR from 'swr';
import { api } from '@/lib/api';
import { Document, DocumentDetailResponse, Table, TableSummary, DocumentInfo } from '@/types';

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

// 🔥 NEW: Table-specific hooks
export const useDocumentTables = (
  documentId: string, 
  page: number = 1, 
  search?: string
) => {
  const { data, error, mutate } = useSWR(
    documentId ? `tables-${documentId}-${page}-${search || ''}` : null,
    () => api.getDocumentTables(documentId, page, 10, search)
  );

  return {
    tables: data?.tables || [],
    pagination: data?.pagination,
    document: data?.document,
    loading: !error && !data,
    error,
    mutate,
  };
};

export const useDocumentTablesSummary = (documentId: string) => {
  const { data, error, mutate } = useSWR(
    documentId ? `tables-summary-${documentId}` : null,
    () => api.getDocumentTablesSummary(documentId)
  );

  return {
    summary: data?.summary,
    document: data?.document,
    loading: !error && !data,
    error,
    mutate,
  };
};

export const useSingleTable = (tableId: string) => {
  const { data, error, mutate } = useSWR(
    tableId ? `table-${tableId}` : null,
    () => api.getSingleTable(tableId)
  );

  return {
    table: data?.table,
    document: data?.document,
    loading: !error && !data,
    error,
    mutate,
  };
};
