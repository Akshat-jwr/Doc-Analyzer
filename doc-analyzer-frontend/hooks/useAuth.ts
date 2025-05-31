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

  const sendOTP = async (email: string): Promise<AuthResponse> => {
    return await auth.sendOTP(email);
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
    sendOTP,
    verifyOTP,
    logout,
    isAuthenticated: !!user,
  };
};
