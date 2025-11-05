import React from 'react';
import { useAnalytics } from '../../hooks/useAnalytics';

const AnalyticsWrapper = ({ children }) => {
  useAnalytics();
  return children;
};

export default AnalyticsWrapper;