import React from 'react';
import { CustomDesignFrame } from './CustomDesignFrame';
import { ActiveTab } from './Sidebar';

interface Props {
  onNavigate?: (tab: ActiveTab) => void;
}

export const WorkersMonitoring: React.FC<Props> = ({ onNavigate }) => {
  return (
    <CustomDesignFrame
      src="/html/workers.html"
      title="RAKSHYA VISION - Workers & PPE Monitoring"
      onNavigate={onNavigate}
    />
  );
};

export default WorkersMonitoring;
