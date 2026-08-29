import React from 'react';
import UniversalAIInsights from '../Shared/UniversalAIInsights';
import { HealthReportPDF } from '../PDF/HealthReportPDF';
import HealthBodyZonePreview from '../Health/HealthBodyZonePreview';
import './AIInsightsTab.css';

const AIInsightsTab = ({ chartData, birthDetails, bodyZoneMap, bodyZoneLoading }) => {
  return (
    <div className="health-insights-stack">
      <HealthBodyZonePreview data={bodyZoneMap} loading={bodyZoneLoading} />
      <UniversalAIInsights
        analysisType="health"
        chartData={chartData}
        birthDetails={birthDetails}
        PDFComponent={HealthReportPDF}
      />
    </div>
  );
};

export default AIInsightsTab;