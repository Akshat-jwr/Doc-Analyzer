import { 
  AuthResponse, 
  Document, 
  DocumentDetailResponse, 
  DocumentStatus, 
  ChatQuery, 
  ChatResponse, 
  UploadResponse,
  Table,
  TableSummaryResponse,
  DocumentTablesResponse,
  SingleTableResponse,
  ExportTablesResponse
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

class ApiClient {
  private baseURL: string;

  constructor() {
    this.baseURL = API_URL || 'http://localhost:8000';
  }

  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getAuthToken();
    
    // Only add auth header for protected endpoints
    const isProtectedEndpoint = !endpoint.includes('/auth/');
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && isProtectedEndpoint && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Handle authentication errors
        if (response.status === 401 || response.status === 403) {
          // Clear invalid token and redirect to login
          if (typeof window !== 'undefined') {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            if (window.location.pathname !== '/auth') {
              window.location.href = '/auth';
            }
          }
        }
        
        throw new Error(errorData.detail || `API Error: ${response.status} ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return response as unknown as T;
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  // Auth endpoints (no token required)
  async sendOTP(email: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/send-otp', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async verifyOTP(email: string, otp_code: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ email, otp_code }),
    });
  }

  // Protected endpoints (token required)
  async uploadDocument(file: File): Promise<UploadResponse> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required. Please log in.');
    }

    const formData = new FormData();
    formData.append('file', file);
    
    return this.request<UploadResponse>('/documents/upload', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        // Don't set Content-Type for FormData
      },
      body: formData,
    });
  }

  async getDocuments(): Promise<Document[]> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required. Please log in.');
    }
    return this.request<Document[]>('/documents/list');
  }

  async getDocument(id: string): Promise<DocumentDetailResponse> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required. Please log in.');
    }
    return this.request<DocumentDetailResponse>(`/documents/${id}`);
  }

  async getDocumentStatus(id: string): Promise<DocumentStatus> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required. Please log in.');
    }
    return this.request<DocumentStatus>(`/documents/${id}/status`);
  }

  async deleteDocument(id: string): Promise<{ message: string }> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required. Please log in.');
    }
    return this.request<{ message: string }>(`/documents/${id}`, { method: 'DELETE' });
  }

  async chatWithDocument(id: string, query: ChatQuery): Promise<ChatResponse> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required. Please log in.');
    }
    return this.request<ChatResponse>(`/documents/${id}/chat`, {
      method: 'POST',
      body: JSON.stringify(query),
    });
  }

  async forceTableExtraction(id: string): Promise<{ message: string }> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required. Please log in.');
    }
    return this.request<{ message: string }>(`/documents/${id}/force-table-extraction`, {
      method: 'POST',
    });
  }

  // 🔥 NEW: Table endpoints
  async getDocumentTables(
    documentId: string, 
    page: number = 1, 
    limit: number = 10, 
    search?: string
  ): Promise<DocumentTablesResponse> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required. Please log in.');
    }

    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...(search && { search }),
    });
    
    return this.request<DocumentTablesResponse>(`/tables/document/${documentId}?${params}`);
  }

  async getDocumentTablesSummary(documentId: string): Promise<TableSummaryResponse> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required. Please log in.');
    }
    return this.request<TableSummaryResponse>(`/tables/document/${documentId}/summary`);
  }

  async getSingleTable(tableId: string): Promise<SingleTableResponse> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required. Please log in.');
    }
    return this.request<SingleTableResponse>(`/tables/${tableId}`);
  }

  async exportDocumentTables(
    documentId: string, 
    format: 'markdown' | 'csv' | 'json' = 'markdown'
  ): Promise<ExportTablesResponse> {
    const token = this.getAuthToken();
    if (!token) {
      throw new Error('Authentication required. Please log in.');
    }
    return this.request<ExportTablesResponse>(`/tables/document/${documentId}/export?format=${format}`, {
      method: 'POST',
    });
  }
}

export const api = new ApiClient();
