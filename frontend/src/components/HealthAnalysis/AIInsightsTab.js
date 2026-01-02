import React from 'react';
import UniversalAIInsights from '../Shared/UniversalAIInsights';
import { HealthReportPDF } from '../PDF/HealthReportPDF';

const AIInsightsTab = ({ chartData, birthDetails }) => {
  return (
    <UniversalAIInsights
      analysisType="health"
      chartData={chartData}
      birthDetails={birthDetails}
      PDFComponent={HealthReportPDF}
    />
  );
};

export default AIInsightsTab;