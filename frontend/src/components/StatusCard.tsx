import React from 'react';

interface StatusCardProps {
  title: string;
  status: string;
  variant: 'success' | 'warning' | 'error' | 'neutral' | 'pending';
  detail?: string;
}

export const StatusCard: React.FC<StatusCardProps> = ({ title, status, variant, detail }) => {
  return (
    <div className={`status-card status-${variant}`}>
      <div className="card-header">
        <span className="card-title">{title}</span>
        <span className={`status-badge badge-${variant}`}>{status}</span>
      </div>
      {detail && <div className="card-detail">{detail}</div>}
    </div>
  );
};
