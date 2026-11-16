import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react';
import { authApi, errorMessage, getToken, setToken } from '../services/api';
import type { User } from '../types';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => {
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const onUnauthorized = () => setUser(null);
    window.addEventListener('apa:unauthorized', onUnauthorized);
    return () => window.removeEventListener('apa:unauthorized', onUnauthorized);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const data = await authApi.login(email, password);
      setToken(data.access_token);
      setUser(data.user);
    } catch (error) {
      throw new Error(errorMessage(error));
    }
  }, []);

  const register = useCallback(async (email: string, password: string, name: string) => {
    try {
      const data = await authApi.register(email, password, name);
      setToken(data.access_token);
      setUser(data.user);
    } catch (error) {
      throw new Error(errorMessage(error));
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
