import { 
  AuthResponse, 
  Document, 
  DocumentDetailResponse, 
  DocumentStatus, 
  ChatQuery, 
  ChatResponse, 
  UploadResponse 
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

class ApiClient {
  private baseURL: string;

  constructor() {
    this.baseURL = API_URL || 'http://localhost:8000';
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
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

  // Auth endpoints
  async login(email: string, password: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(email: string, password: string, full_name: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name }),
    });
  }

  async verifyOTP(email: string, otp_code: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ email, otp_code }),
    });
  }

  // Document endpoints
  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.request<UploadResponse>('/documents/upload', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it for FormData
      body: formData,
    });
  }

  async getDocuments(): Promise<Document[]> {
    return this.request<Document[]>('/documents/list');
  }

  async getDocument(id: string): Promise<DocumentDetailResponse> {
    return this.request<DocumentDetailResponse>(`/documents/${id}`);
  }

  async getDocumentStatus(id: string): Promise<DocumentStatus> {
    return this.request<DocumentStatus>(`/documents/${id}/status`);
  }

  async deleteDocument(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/documents/${id}`, { method: 'DELETE' });
  }

  async chatWithDocument(id: string, query: ChatQuery): Promise<ChatResponse> {
    return this.request<ChatResponse>(`/documents/${id}/chat`, {
      method: 'POST',
      body: JSON.stringify(query),
    });
  }

  async forceTableExtraction(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/documents/${id}/force-table-extraction`, {
      method: 'POST',
    });
  }
}

export const api = new ApiClient();
