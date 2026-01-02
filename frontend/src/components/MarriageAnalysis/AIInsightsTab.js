import React from 'react';
import UniversalAIInsights from '../Shared/UniversalAIInsights';
import { MarriageReportPDF } from '../PDF/MarriageReportPDF';

const AIInsightsTab = ({ chartData, birthDetails }) => {
  return (
    <UniversalAIInsights
      analysisType="marriage"
      chartData={chartData}
      birthDetails={birthDetails}
      PDFComponent={MarriageReportPDF}
    />
  );
};

export default AIInsightsTab;