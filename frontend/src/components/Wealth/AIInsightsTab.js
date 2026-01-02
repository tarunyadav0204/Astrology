import React from 'react';
import UniversalAIInsights from '../Shared/UniversalAIInsights';
import { WealthReportPDF } from '../PDF/WealthReportPDF';

const AIInsightsTab = ({ chartData, birthDetails }) => {
  return (
    <UniversalAIInsights
      analysisType="wealth"
      chartData={chartData}
      birthDetails={birthDetails}
      PDFComponent={WealthReportPDF}
    />
  );
};

export default AIInsightsTab;