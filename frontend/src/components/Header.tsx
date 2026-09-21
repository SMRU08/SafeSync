/**
 * Header.tsx — RAKSHYA VISION Phase 8
 * Industrial SOC top navigation bar with live status telemetry and UTC clock.
 */

import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Server,
  Database,
  Cpu,
  Radio,
  Clock,
  RotateCw,
  Eye,
  Video,
  Users,
  Flame,
  Bell,
  BarChart3,
  Sliders,
} from 'lucide-react';
import { NavigationTab } from '../types';
import { SystemStatusState } from '../hooks/useSafetyData';
import { WebSocketStatus } from '../hooks/useWebSocket';

interface HeaderProps {
  currentTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
  systemStatus: SystemStatusState;
  wsStatus: WebSocketStatus;
  activeAlertsCount: number;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onTabChange,
  systemStatus,
  wsStatus,
  activeAlertsCount,
  onRefresh,
  isRefreshing,
}) => {
  const [utcTime, setUtcTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().replace('GMT', 'UTC'));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const navItems: { id: NavigationTab; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: 'overview', label: 'Overview', icon: <Eye size={16} /> },
    { id: 'cameras', label: 'Live Cameras', icon: <Video size={16} /> },
    { id: 'workers', label: 'Workers & PPE', icon: <Users size={16} /> },
    { id: 'hazards', label: 'Fire & Smoke', icon: <Flame size={16} /> },
    {
      id: 'alerts',
      label: 'Alerts & Incidents',
      icon: <Bell size={16} />,
      badge: activeAlertsCount > 0 ? activeAlertsCount : undefined,
    },
    { id: 'analytics', label: 'Analytics', icon: <BarChart3 size={16} /> },
    { id: 'settings', label: 'System Config', icon: <Sliders size={16} /> },
  ];

  return (
    <header className="soc-header">
      <div className="soc-header-top">
        {/* Branding */}
        <div className="brand-group">
          <div className="brand-logo">
            <ShieldAlert size={26} className="brand-icon" />
          </div>
          <div className="brand-text">
            <div className="brand-title-row">
              <span className="brand-name">RAKSHYA VISION</span>
              <span className="brand-tag">SOC MONITOR</span>
              <span className="brand-version">v1.0-P8</span>
            </div>
            <p className="brand-subtext">AI Vision-Based Safety & Hazard Monitoring System</p>
          </div>
        </div>

        {/* Telemetry Status Pills */}
        <div className="telemetry-bar">
          {/* Backend */}
          <div className={`status-pill pill-${systemStatus.backend}`}>
            <Server size={14} />
            <span className="pill-label">API</span>
            <span className="pill-value">{systemStatus.backend.toUpperCase()}</span>
          </div>

          {/* AI Engine */}
          <div className="status-pill pill-ai">
            <Cpu size={14} />
            <span className="pill-label">AI</span>
            <span className="pill-value">{systemStatus.aiEngine.toUpperCase()}</span>
          </div>

          {/* Database */}
          <div className={`status-pill pill-${systemStatus.database}`}>
            <Database size={14} />
            <span className="pill-label">DB</span>
            <span className="pill-value">{systemStatus.database.toUpperCase()}</span>
          </div>

          {/* WebSocket */}
          <div className={`status-pill pill-ws pill-${wsStatus.toLowerCase()}`}>
            <Radio size={14} className={wsStatus === 'CONNECTED' ? 'animate-pulse' : ''} />
            <span className="pill-label">WS</span>
            <span className="pill-value">{wsStatus}</span>
          </div>

          {/* UTC Clock */}
          <div className="status-pill pill-clock">
            <Clock size={14} />
            <span className="pill-value clock-text">{utcTime || 'UTC --:--:--'}</span>
          </div>

          {/* Refresh Button */}
          <button
            className={`header-refresh-btn ${isRefreshing ? 'spinning' : ''}`}
            onClick={onRefresh}
            title="Refresh telemetry"
          >
            <RotateCw size={14} />
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="soc-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-tab-btn ${currentTab === item.id ? 'active' : ''}`}
            onClick={() => onTabChange(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
            {item.badge !== undefined && (
              <span className="nav-badge pulse-badge">{item.badge}</span>
            )}
          </button>
        ))}
      </nav>
    </header>
  );
};
