import { useState, useEffect } from 'react';
import { auth } from '@/lib/auth';
import { User, AuthResponse } from '@/types';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = () => {
      const currentUser = auth.getUser();
      setUser(currentUser);
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string): Promise<AuthResponse> => {
    const result = await auth.login(email, password);
    if (result.success && result.user) {
      setUser(result.user);
    }
    return result;
  };

  const register = async (email: string, password: string, fullName: string): Promise<AuthResponse> => {
    return await auth.register(email, password, fullName);
  };

  const verifyOTP = async (email: string, otp: string): Promise<AuthResponse> => {
    const result = await auth.verifyOTP(email, otp);
    if (result.success && result.user) {
      setUser(result.user);
    }
    return result;
  };

  const logout = () => {
    setUser(null);
    auth.logout();
  };

  return {
    user,
    loading,
    login,
    register,
    verifyOTP,
    logout,
    isAuthenticated: !!user,
  };
};
