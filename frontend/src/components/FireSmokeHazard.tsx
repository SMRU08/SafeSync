import React from 'react';
import { CustomDesignFrame } from './CustomDesignFrame';
import { ActiveTab } from './Sidebar';

interface Props {
  onNavigate?: (tab: ActiveTab) => void;
}

export const FireSmokeHazard: React.FC<Props> = ({ onNavigate }) => {
  return (
    <CustomDesignFrame
      src="/html/hazards.html"
      title="RAKSHYA VISION - Fire & Smoke Hazard Monitoring"
      onNavigate={onNavigate}
    />
  );
};

export default FireSmokeHazard;
