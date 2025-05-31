import { api } from './api';
import { User, AuthResponse } from '@/types';

export const auth = {
  // Send OTP to email (no password needed)
  sendOTP: async (email: string): Promise<AuthResponse> => {
    try {
      const response = await api.sendOTP(email);
      return { success: true, message: response.message };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  },

  // Verify OTP and login
  verifyOTP: async (email: string, otp: string): Promise<AuthResponse> => {
    try {
      const response = await api.verifyOTP(email, otp);
      if (response.access_token && response.user) {
        if (typeof window !== 'undefined') {
          localStorage.setItem('token', response.access_token);
          localStorage.setItem('user', JSON.stringify(response.user));
        }
        return { success: true, user: response.user };
      }
      return { success: false, error: 'Invalid OTP' };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  },

  logout: (): void => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/auth';
    }
  },

  getUser: (): User | null => {
    if (typeof window === 'undefined') return null;
    try {
      const user = localStorage.getItem('user');
      return user ? JSON.parse(user) : null;
    } catch {
      return null;
    }
  },

  getToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
  },

  isAuthenticated: (): boolean => {
    return !!auth.getToken();
  },
};
