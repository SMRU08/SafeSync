import React from 'react';
import { CustomDesignFrame } from './CustomDesignFrame';
import { ActiveTab } from './Sidebar';

interface Props {
  onNavigate?: (tab: ActiveTab) => void;
}

export const AlertsTriage: React.FC<Props> = ({ onNavigate }) => {
  return (
    <CustomDesignFrame
      src="/html/alerts.html"
      title="RAKSHYA VISION - Alerts & Incidents Triage"
      onNavigate={onNavigate}
    />
  );
};

export default AlertsTriage;
