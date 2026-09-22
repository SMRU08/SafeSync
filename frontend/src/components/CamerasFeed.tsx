import React from 'react';
import { CustomDesignFrame } from './CustomDesignFrame';
import { ActiveTab } from './Sidebar';

interface Props {
  onNavigate?: (tab: ActiveTab) => void;
}

export const CamerasFeed: React.FC<Props> = ({ onNavigate }) => {
  return (
    <CustomDesignFrame
      src="/html/cameras.html"
      title="RAKSHYA VISION - Cameras & Feed Health"
      onNavigate={onNavigate}
    />
  );
};

export default CamerasFeed;
