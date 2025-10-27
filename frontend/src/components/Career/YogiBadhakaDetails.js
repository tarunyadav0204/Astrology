// Helper function to render Yogi/Badhaka details
export const renderYogiBadhakaDetails = (analysisType, detailType, completeAnalysisData) => {
  const data = completeAnalysisData[analysisType];
  if (!data) return <div>No data available</div>;

  if (detailType === 'yogi') {
    let yogiData = null;
    if (analysisType === 'tenth-lord') {
      yogiData = data.yogi_significance;
    } else if (analysisType === 'tenth-house') {
      yogiData = data.yogi_analysis;
    } else if (analysisType === 'saturn-karaka') {
      yogiData = data.saturn_yogi_significance;
    } else if (analysisType === 'saturn-tenth') {
      yogiData = data.saturn_tenth_yogi_analysis;
    } else if (analysisType === 'amatyakaraka') {
      yogiData = data.amk_yogi_significance;
    }

    if (!yogiData) {
      return <div className="section-details">No Yogi analysis available</div>;
    }

    return (
      <div className="section-details">
        <div className="detail-row">
          <span>Yogi Status:</span>
          <span>{yogiData.has_impact || yogiData.lord_significance?.has_impact || yogiData.saturn_significance?.has_impact || yogiData.amk_significance?.has_impact || yogiData.house_impact?.total_impact > 0 ? 'Active' : 'Inactive'}</span>
        </div>
        <div className="detail-row">
          <span>Impact Level:</span>
          <span>{yogiData.house_impact?.total_impact || yogiData.career_impact?.total_impact || 'Moderate'}</span>
        </div>
        <div className="detail-row">
          <span>Special Status:</span>
          <span>{yogiData.lord_significance?.special_status || yogiData.saturn_significance?.special_status || yogiData.amk_significance?.special_status || 'Neutral'}</span>
        </div>
        <div className="detail-row">
          <span>Career Benefit:</span>
          <span>Enhanced spiritual and material success through righteous actions</span>
        </div>
      </div>
    );
  }

  if (detailType === 'badhaka') {
    let badhakaData = null;
    if (analysisType === 'tenth-lord') {
      badhakaData = data.badhaka_impact;
    } else if (analysisType === 'tenth-house') {
      badhakaData = data.badhaka_analysis;
    } else if (analysisType === 'saturn-karaka') {
      badhakaData = data.saturn_badhaka_impact;
    } else if (analysisType === 'saturn-tenth') {
      badhakaData = data.saturn_tenth_badhaka_analysis;
    } else if (analysisType === 'amatyakaraka') {
      badhakaData = data.amk_badhaka_impact;
    }

    if (!badhakaData) {
      return <div className="section-details">No Badhaka analysis available</div>;
    }

    return (
      <div className="section-details">
        <div className="detail-row">
          <span>Badhaka Status:</span>
          <span>{badhakaData.has_impact || badhakaData.lord_impact?.has_impact || badhakaData.badhaka_impact?.has_impact || badhakaData.house_impact?.has_impact || badhakaData.career_impact?.has_impact ? 'Active' : 'Inactive'}</span>
        </div>
        <div className="detail-row">
          <span>Impact Score:</span>
          <span>{badhakaData.house_impact?.impact_score || badhakaData.career_impact?.impact_score || badhakaData.badhaka_impact?.impact_score || 0}</span>
        </div>
        <div className="detail-row">
          <span>Is Badhaka Lord:</span>
          <span>{badhakaData.lord_impact?.is_badhaka_lord || badhakaData.badhaka_impact?.is_badhaka_lord ? 'Yes' : 'No'}</span>
        </div>
        <div className="detail-row">
          <span>Career Challenge:</span>
          <span>Obstacles that ultimately lead to growth and transformation</span>
        </div>
      </div>
    );
  }

  return <div>Analysis type not supported</div>;
};