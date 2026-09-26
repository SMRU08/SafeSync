/**
 * useWebSocket.ts — SafeSync Phase 8
 * Resilient WebSocket hook for real-time safety alert broadcasts.
 * Features automatic reconnection, heartbeat pings, and connection state management.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { API_BASE_URL } from '../utils/constants';
import { WebSocketMessage } from '../types';

export type WebSocketStatus = 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED';

export interface UseWebSocketReturn {
  status: WebSocketStatus;
  lastMessage: WebSocketMessage | null;
  activeConnections: number;
  sendPing: () => void;
  reconnect: () => void;
}

export function useWebSocket(onEvent?: (message: WebSocketMessage) => void): UseWebSocketReturn {
  const [status, setStatus] = useState<WebSocketStatus>('CONNECTING');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [activeConnections, setActiveConnections] = useState<number>(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const pingIntervalRef = useRef<number | null>(null);
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  const connect = useCallback(() => {
    // Clean up previous socket if exists
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const wsUrl = `${API_BASE_URL.replace(/^http/, 'ws')}/ws/alerts`;
    setStatus('CONNECTING');

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('CONNECTED');
        // Start heartbeat ping
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 15000);
      };

      ws.onmessage = (event) => {
        try {
          const parsed: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(parsed);

          if (parsed.type === 'connected' && typeof parsed.active_connections === 'number') {
            setActiveConnections(parsed.active_connections);
          }

          if (onEventRef.current) {
            onEventRef.current(parsed);
          }
        } catch {
          // Non-JSON frame ignored
        }
      };

      ws.onclose = () => {
        setStatus('DISCONNECTED');
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
        // Attempt reconnect after 3 seconds
        if (!reconnectTimeoutRef.current) {
          reconnectTimeoutRef.current = window.setTimeout(() => {
            reconnectTimeoutRef.current = null;
            connect();
          }, 3000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      setStatus('DISCONNECTED');
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendPing = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
    }
  }, []);

  const reconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    connect();
  }, [connect]);

  return {
    status,
    lastMessage,
    activeConnections,
    sendPing,
    reconnect,
  };
}
