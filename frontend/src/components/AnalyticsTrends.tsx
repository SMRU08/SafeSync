import React from 'react';
import { CustomDesignFrame } from './CustomDesignFrame';
import { ActiveTab } from './Sidebar';

interface Props {
  onNavigate?: (tab: ActiveTab) => void;
}

export const AnalyticsTrends: React.FC<Props> = ({ onNavigate }) => {
  return (
    <CustomDesignFrame
      src="/html/analytics.html"
      title="RAKSHYA VISION - Analytics & Compliance Trends"
      onNavigate={onNavigate}
    />
  );
};

export default AnalyticsTrends;
