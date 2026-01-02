import React from 'react';
import UniversalAIInsights from '../Shared/UniversalAIInsights';
import { EducationReportPDF } from '../PDF/EducationReportPDF';

const AIQuestionsTab = ({ chartData, birthDetails }) => {
  return (
    <UniversalAIInsights
      analysisType="education"
      chartData={chartData}
      birthDetails={birthDetails}
      PDFComponent={EducationReportPDF}
    />
  );
};

export default AIQuestionsTab;