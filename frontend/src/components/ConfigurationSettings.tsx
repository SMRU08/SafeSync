import React from 'react';
import { CustomDesignFrame } from './CustomDesignFrame';
import { ActiveTab } from './Sidebar';

interface Props {
  onNavigate?: (tab: ActiveTab) => void;
}

export const ConfigurationSettings: React.FC<Props> = ({ onNavigate }) => {
  return (
    <CustomDesignFrame
      src="/html/configuration.html"
      title="RAKSHYA VISION - Configuration & System Settings"
      onNavigate={onNavigate}
    />
  );
};

export default ConfigurationSettings;
