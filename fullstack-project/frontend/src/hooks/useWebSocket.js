import { useEffect, useRef } from 'react';

function getWsUrl(userId, token) {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host = window.location.port === '5173'
    ? `${window.location.hostname}:8000`
    : window.location.host;
  return `${protocol}://${host}/ws/${userId}?token=${encodeURIComponent(token)}`;
}

export function useWebSocket(userId, onMessage) {
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    if (!userId) return;
    const token = localStorage.getItem('auth_token');
    if (!token) return;

    const ws = new WebSocket(getWsUrl(userId, token));
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessageRef.current(data.message || String(event.data));
      } catch {
        onMessageRef.current(String(event.data));
      }
    };
    ws.onerror = () => {};

    return () => { ws.close(); };
  }, [userId]);
}