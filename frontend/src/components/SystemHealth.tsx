import React from 'react';
import { CustomDesignFrame } from './CustomDesignFrame';
import { ActiveTab } from './Sidebar';

interface Props {
  onNavigate?: (tab: ActiveTab) => void;
}

export const SystemHealth: React.FC<Props> = ({ onNavigate }) => {
  return (
    <CustomDesignFrame
      src="/html/system-health.html"
      title="RAKSHYA VISION - System Health & Edge Diagnostics"
      onNavigate={onNavigate}
    />
  );
};

export default SystemHealth;
