import React from 'react';
import { CustomDesignFrame } from './CustomDesignFrame';
import { ActiveTab } from './Sidebar';

interface Props {
  onNavigate?: (tab: ActiveTab) => void;
}

export const SocOverview: React.FC<Props> = ({ onNavigate }) => {
  return (
    <CustomDesignFrame
      src="/html/overview.html"
      title="RAKSHYA VISION - Industrial Safety SOC Overview"
      onNavigate={onNavigate}
    />
  );
};

export default SocOverview;
