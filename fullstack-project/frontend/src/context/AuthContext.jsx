import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [wsNotification, setWsNotification] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    const stored = localStorage.getItem('user');
    const token = localStorage.getItem('auth_token');
    if (stored && token) {
      try { setUser(JSON.parse(stored)); } catch { /* ignore */ }
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (!user) {
      wsRef.current?.close();
      wsRef.current = null;
      return;
    }
    const token = localStorage.getItem('auth_token');
    if (!token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.host;
    const wsUrl = `${protocol}://${host}/ws/${user.user_id}?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setWsNotification({ message: data.message || String(event.data), id: Date.now() });
      } catch {
        setWsNotification({ message: String(event.data), id: Date.now() });
      }
    };
    ws.onerror = () => { };
    ws.onclose = () => { wsRef.current = null; };
    wsRef.current = ws;

    return () => { ws.close(); wsRef.current = null; };
  }, [user?.user_id]);

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
    const merged = { ...user, ...userData };
    localStorage.setItem('user', JSON.stringify(merged));
    setUser(merged);
  }, [user]);

  const clearWsNotification = useCallback(() => setWsNotification(null), []);

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, updateUser, wsNotification, clearWsNotification }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}