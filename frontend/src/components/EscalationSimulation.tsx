import React from 'react';
import { CustomDesignFrame } from './CustomDesignFrame';
import { ActiveTab } from './Sidebar';

interface Props {
  onNavigate?: (tab: ActiveTab) => void;
}

export const EscalationSimulation: React.FC<Props> = ({ onNavigate }) => {
  return (
    <CustomDesignFrame
      src="/html/simulation.html"
      title="RAKSHYA VISION - Tier 1 Escalation Live Test Simulation"
      onNavigate={onNavigate}
    />
  );
};

export default EscalationSimulation;
