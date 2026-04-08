import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [wsNotification, setWsNotification] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem('user');
    const token = localStorage.getItem('auth_token');
    if (stored && token) {
      try { setUser(JSON.parse(stored)); } catch { /* ignore */ }
    }
    setLoading(false);
  }, []);

  const login = useCallback((userData) => {
    localStorage.setItem('auth_token', userData.token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  const updateUser = useCallback((userData) => {
    const merged = { ...JSON.parse(localStorage.getItem('user') || '{}'), ...userData };
    localStorage.setItem('user', JSON.stringify(merged));
    setUser(merged);
  }, []);

  const pushNotification = useCallback((message) => {
    setWsNotification({ message, id: Date.now() });
  }, []);

  const clearWsNotification = useCallback(() => setWsNotification(null), []);

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, updateUser, wsNotification, pushNotification, clearWsNotification }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}