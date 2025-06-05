export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  success: boolean;
  access_token?: string;
  user?: User;
  message?: string;
  error?: string;
}

export interface Document {
  id: string;
  filename: string;
  page_count: number;
  processing_status: ProcessingStatus;
  uploaded_at: string;
  cloudinary_url: string;
  tables_processed: number;
  total_tables_found: number;
}

export interface DocumentDetails extends Document {
  text_images_completed_at?: string;
  fully_completed_at?: string;
  background_error?: string;
}

export interface DocumentStatus {
  document_id: string;
  filename: string;
  processing_status: string;
  pages: number;
  tables_processed: number;
  total_tables: number;
  general_queries_ready: boolean;
  analytical_queries_ready: boolean;
  message: string;
  progress_percentage: number;
}

export interface Table {
  id: string;
  title: string;
  start_page: number;
  end_page: number;
  column_count: number;
  row_count: number;
  markdown_content: string;
  markdown_preview?: string;
}

export interface PageText {
  page_number: number;
  text: string;
}

export interface DocumentImage {
  page_number: number;
  cloudinary_url: string;
}

export interface DocumentDetailResponse {
  document: DocumentDetails;
  processing_info: {
    general_queries_ready: boolean;
    analytical_queries_ready: boolean;
    background_error?: string;
  };
  page_texts: PageText[];
  tables: Table[];
  images: DocumentImage[];
}

export enum ProcessingStatus {
  UPLOADED = 'uploaded',
  PROCESSING = 'processing',
  TEXT_IMAGES_COMPLETE = 'text_images_complete',
  BACKGROUND_PROCESSING = 'background_processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum FileType {
  PDF = 'pdf',
  WORD = 'word',
  SPREADSHEET = 'spreadsheet',
  IMAGE = 'image',
}

export interface UploadResponse {
  success: boolean;
  message: string;
  phase: string;
  document_id?: string;
  processing_time?: number;
  pages_processed?: number;
  images_extracted?: number;
  general_queries_ready?: boolean;
  analytical_queries_ready?: boolean;
  cloudinary_url?: string;
  status?: string;
  error?: string;
}

export interface ApiError {
  message: string;
  status: number;
}
// Add these new types to your existing types/index.ts:

export interface TableSummary {
  total_tables: number;
  total_rows: number;
  total_columns: number;
  average_columns: number;
  pages_with_tables: number[];
  page_count: number;
}

export interface TablePagination {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  total_tables?: number;
  page_count?: number;
}

export interface DocumentTablesResponse {
  success: boolean;
  tables: Table[];
  pagination: TablePagination;
  document: DocumentInfo;
}

export interface TableSummaryResponse {
  success: boolean;
  summary: TableSummary;
  document: DocumentInfo;
}

export interface SingleTableResponse {
  success: boolean;
  table: Table;
  document: DocumentInfo;
}

export interface ExportTablesResponse {
  success: boolean;
  format: string;
  content: string | any[];
  filename: string;
}

// Update the existing Table interface to match backend response:
export interface Table {
  id: string;
  title: string;
  table_number: number;
  start_page: number;
  end_page: number;
  column_count: number;
  row_count: number;
  markdown_content: string;
  created_at?: string;
}

// Add these if they don't exist:
export interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  content: string;
  timestamp: Date;
  mode?: string;
}

export interface ChatQuery {
  message: string;
  document_id?: string;
  mode?: string;
}

export interface ChatResponse {
  success: boolean;
  response: string;
  mode: string;
  timestamp: string;
}

