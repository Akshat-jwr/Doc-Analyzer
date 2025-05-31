import { api } from './api';
import { User, AuthResponse } from '@/types';

export const auth = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    try {
      const response = await api.login(email, password);
      if (response.access_token && response.user) {
        localStorage.setItem('token', response.access_token);
        localStorage.setItem('user', JSON.stringify(response.user));
        return { success: true, user: response.user };
      }
      return { success: false, error: 'Invalid response' };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  },

  register: async (email: string, password: string, fullName: string): Promise<AuthResponse> => {
    try {
      const response = await api.register(email, password, fullName);
      return { success: true, message: response.message };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  },

  verifyOTP: async (email: string, otp: string): Promise<AuthResponse> => {
    try {
      const response = await api.verifyOTP(email, otp);
      if (response.access_token && response.user) {
        localStorage.setItem('token', response.access_token);
        localStorage.setItem('user', JSON.stringify(response.user));
        return { success: true, user: response.user };
      }
      return { success: false, error: 'Invalid OTP' };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  },

  logout: (): void => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/auth';
  },

  getUser: (): User | null => {
    if (typeof window === 'undefined') return null;
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  getToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
  },

  isAuthenticated: (): boolean => {
    return !!auth.getToken();
  },
};
