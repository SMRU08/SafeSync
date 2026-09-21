/**
 * MetricCard.tsx — RAKSHYA VISION Phase 8
 * High-visibility metric card with cyber-industrial styling and status variants.
 */

import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  variant?: 'default' | 'critical' | 'high' | 'warning' | 'success' | 'info';
  badge?: string;
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  variant = 'default',
  badge,
  onClick,
}) => {
  return (
    <div
      className={`metric-card card-${variant} ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
    >
      <div className="metric-header">
        <span className="metric-title">{title}</span>
        <div className="metric-icon-wrap">{icon}</div>
      </div>
      <div className="metric-body">
        <div className="metric-value-row">
          <span className="metric-value">{value}</span>
          {badge && <span className={`metric-badge badge-${variant}`}>{badge}</span>}
        </div>
        {subtitle && <span className="metric-subtitle">{subtitle}</span>}
      </div>
    </div>
  );
};
