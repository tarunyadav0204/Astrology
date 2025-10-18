import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/apiService';
import { useAstrology } from '../../context/AstrologyContext';
import { 
  getHouseLordship, getFriendship, ownSigns, exaltationSigns, debilitationSigns,
  houseLords, getPlanetStatus, getPlanetDignity, getStatusColor, getNakshatraLord
} from '../../utils/planetAnalyzer';

const HouseAnalysisModal = ({ 
  isOpen, 
  onClose, 
  houseNumber, 
  signName, 
  chartData, 
  getPlanetsInHouse,
  getRashiForHouse 
}) => {
  const { birthData } = useAstrology();
  const [yogiData, setYogiData] = useState(chartData.yogiData);
  
  useEffect(() => {
    const fetchYogiData = async () => {
      if (!yogiData && birthData) {
        try {
          const data = await apiService.calculateYogi(birthData);
          setYogiData(data);
        } catch (error) {
          console.error('Failed to fetch Yogi data:', error);
        }
      }
    };
    
    fetchYogiData();
  }, [yogiData, birthData]);
  
  if (!isOpen) return null;

  const houseIndex = houseNumber - 1;
  const rashiIndex = getRashiForHouse(houseIndex);
  const houseLords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
  const houseLord = houseLords[rashiIndex];
  const planetsInHouse = getPlanetsInHouse(houseIndex);
  const lordData = chartData.planets?.[houseLord];
  const lordHouse = lordData ? (() => {
    const lordSign = lordData.sign;
    const ascendantSign = chartData.houses?.[0]?.sign || 0;
    return ((lordSign - ascendantSign + 12) % 12) + 1;
  })() : null;
  
  const ascendantSign = chartData.houses?.[0]?.sign || 0;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 10000,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      backdropFilter: 'blur(8px)'
    }} onClick={onClose}>
      <div style={{
        background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
        borderRadius: '20px', padding: '0', maxWidth: '600px', width: '95%',
        maxHeight: '85vh', overflow: 'hidden',
        boxShadow: '0 25px 50px rgba(0,0,0,0.25), 0 0 0 1px rgba(255,255,255,0.2)',
        border: '1px solid rgba(233, 30, 99, 0.1)'
      }} onClick={e => e.stopPropagation()}>
        <div style={{
          background: 'linear-gradient(135deg, #e91e63 0%, #ff6f00 100%)',
          padding: '20px', color: 'white', borderRadius: '20px 20px 0 0'
        }}>
          <h2 style={{ margin: 0, fontSize: '24px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '10px' }}>
            🏠 House {houseNumber} Analysis
            <span style={{ fontSize: '16px', opacity: 0.9 }}>({signName})</span>
          </h2>
        </div>
        <div style={{ padding: '25px', maxHeight: '60vh', overflowY: 'auto' }}>
          
          <div style={{
            background: 'linear-gradient(135deg, rgba(233, 30, 99, 0.1) 0%, rgba(255, 111, 0, 0.1) 100%)',
            borderRadius: '12px', padding: '15px', marginBottom: '20px',
            border: '1px solid rgba(233, 30, 99, 0.2)'
          }}>
            <h4 style={{ color: '#e91e63', margin: '0 0 12px 0', fontSize: '16px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
              👥 Occupants Analysis
            </h4>
            {planetsInHouse.length > 0 ? planetsInHouse.map(planet => {
              const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet.name);
              const isNaturalMalefic = ['Mars', 'Saturn', 'Sun', 'Rahu', 'Ketu'].includes(planet.name);
              const lordships = getHouseLordship(planet.name, ascendantSign);
              const isInOwnSign = ownSigns[planet.name]?.includes(rashiIndex);
              const status = getPlanetStatus(planet.name, rashiIndex, lordships);
              
              return (
                <div key={planet.name} style={{
                  fontSize: '13px', padding: '8px 12px', marginBottom: '6px',
                  background: 'rgba(255,255,255,0.7)', borderRadius: '8px',
                  border: '1px solid rgba(0,0,0,0.1)'
                }}>
                  <strong>{planet.name}</strong>: {isNaturalBenefic ? 'Benefic' : isNaturalMalefic ? 'Malefic' : 'Neutral'}
                  {lordships.length > 0 && <span style={{ color: '#666' }}> • Lord of {lordships.join(', ')}</span>}
                  {isInOwnSign && <span style={{ color: '#4caf50' }}> • Own Sign</span>}
                  <div style={{ marginTop: '4px' }}>
                    <span style={{
                      color: getStatusColor(status),
                      fontWeight: '600', fontSize: '12px'
                    }}>● {status}</span>
                  </div>
                </div>
              );
            }) : <div style={{ fontSize: '13px', color: '#666', fontStyle: 'italic', padding: '8px 0' }}>Empty house</div>}
          </div>
          
          <div style={{
            background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(139, 195, 74, 0.1) 100%)',
            borderRadius: '12px', padding: '15px', marginBottom: '20px',
            border: '1px solid rgba(76, 175, 80, 0.2)'
          }}>
            <h4 style={{ color: '#4caf50', margin: '0 0 12px 0', fontSize: '16px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
              🤝 Friendship Analysis
            </h4>
            {planetsInHouse.map(planet => {
              const friendship = getFriendship(planet.name, houseLord);
              const isInOwnSign = ownSigns[planet.name]?.includes(rashiIndex);
              
              const planetData = chartData.planets?.[planet.name];
              const nakshatraLord = planetData ? getNakshatraLord(planetData.longitude) : 'Unknown';
              const nakshatraFriendship = getFriendship(planet.name, nakshatraLord);
              
              const getColoredText = (text) => {
                if (text.includes('Positive')) return <span style={{ color: '#4caf50' }}>{text}</span>;
                if (text.includes('Negative')) return <span style={{ color: '#f44336' }}>{text}</span>;
                return <span style={{ color: '#666' }}>{text}</span>;
              };
              
              let signStatus = isInOwnSign ? 'Own Sign - Positive' : 
                             friendship === 'Friend' ? 'Friend\'s Sign - Positive' : 
                             friendship === 'Enemy' ? 'Enemy\'s Sign - Negative' : 'Neutral Sign';
              
              let nakshatraStatus = nakshatraFriendship === 'Friend' ? 'Friend\'s Nakshatra - Positive' :
                                   nakshatraFriendship === 'Enemy' ? 'Enemy\'s Nakshatra - Negative' : 'Neutral Nakshatra';
              
              return (
                <div key={planet.name} style={{
                  fontSize: '13px', padding: '8px 12px', marginBottom: '6px',
                  background: 'rgba(255,255,255,0.7)', borderRadius: '8px',
                  border: '1px solid rgba(0,0,0,0.1)'
                }}>
                  <strong>{planet.name}</strong>: {getColoredText(signStatus)}
                  <div style={{ marginTop: '4px', fontSize: '12px' }}>
                    Nakshatra: {getColoredText(nakshatraStatus)} (Lord: {nakshatraLord})
                  </div>
                </div>
              );
            })}
          </div>
          
          <div style={{
            background: 'linear-gradient(135deg, rgba(156, 39, 176, 0.1) 0%, rgba(103, 58, 183, 0.1) 100%)',
            borderRadius: '12px', padding: '15px', marginBottom: '20px',
            border: '1px solid rgba(156, 39, 176, 0.2)'
          }}>
            <h4 style={{ color: '#9c27b0', margin: '0 0 12px 0', fontSize: '16px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
              👑 House Lord Analysis
            </h4>
            <div style={{
              fontSize: '14px', padding: '8px 12px', marginBottom: '8px',
              background: 'rgba(255,255,255,0.7)', borderRadius: '8px',
              border: '1px solid rgba(0,0,0,0.1)'
            }}>
              <strong>{houseLord}</strong> (Lord of House {houseNumber})
              {lordData && (() => {
                const nakshatraLords = [
                  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
                  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
                  'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
                ];
                const nakshatraIndex = Math.floor(lordData.longitude / 13.333333);
                const nakshatraLord = nakshatraLords[nakshatraIndex];
                const nakshatraFriendship = getFriendship(houseLord, nakshatraLord);
                
                const getColoredText = (text) => {
                  if (text.includes('Positive')) return <span style={{ color: '#4caf50' }}>{text}</span>;
                  if (text.includes('Negative')) return <span style={{ color: '#f44336' }}>{text}</span>;
                  return <span style={{ color: '#666' }}>{text}</span>;
                };
                
                let signStatus = exaltationSigns[houseLord] === lordData.sign ? 'Exalted - Positive' :
                               debilitationSigns[houseLord] === lordData.sign ? 'Debilitated - Negative' :
                               ownSigns[houseLord]?.includes(lordData.sign) ? 'Own Sign - Positive' :
                               getFriendship(houseLord, houseLords[lordData.sign]) === 'Friend' ? 'Friend\'s Sign - Positive' :
                               getFriendship(houseLord, houseLords[lordData.sign]) === 'Enemy' ? 'Enemy\'s Sign - Negative' : 'Neutral';
                
                let nakshatraStatus = nakshatraFriendship === 'Friend' ? 'Friend\'s Nakshatra - Positive' :
                                     nakshatraFriendship === 'Enemy' ? 'Enemy\'s Nakshatra - Negative' : 'Neutral Nakshatra';
                
                return (
                  <div style={{ marginTop: '8px', fontSize: '13px' }}>
                    <div>Currently in House {lordHouse}</div>
                    <div>Sign Status: {getColoredText(signStatus)}</div>
                    <div>Nakshatra: {getColoredText(nakshatraStatus)} (Lord: {nakshatraLord})</div>
                  </div>
                );
              })()}
            </div>
          </div>
          
          <div style={{
            background: 'linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, rgba(255, 193, 7, 0.1) 100%)',
            borderRadius: '12px', padding: '15px', marginBottom: '20px',
            border: '1px solid rgba(255, 152, 0, 0.2)'
          }}>
            <h4 style={{ color: '#ff9800', margin: '0 0 12px 0', fontSize: '16px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
              🎯 Aspects Analysis
            </h4>
            {(() => {
              const aspectingPlanets = [];
              Object.entries(chartData.planets || {}).forEach(([name, data]) => {
                const planetSign = data.sign;
                const ascendantSign = chartData.houses?.[0]?.sign || 0;
                const planetHouse = ((planetSign - ascendantSign + 12) % 12) + 1;
                let aspects = [];
                
                if (!['Rahu', 'Ketu'].includes(name)) {
                  const seventhHouse = (planetHouse + 6) % 12 || 12;
                  if (seventhHouse === houseNumber) aspects.push('7th');
                }
                
                if (['Rahu', 'Ketu'].includes(name)) {
                  const rahuKetuAspects = [(planetHouse + 2) % 12 || 12, (planetHouse + 10) % 12 || 12];
                  if (rahuKetuAspects.includes(houseNumber)) {
                    aspects.push(houseNumber === rahuKetuAspects[0] ? '3rd' : '11th');
                  }
                }
                
                if (name === 'Mars') {
                  const marsAspects = [(planetHouse + 3) % 12 || 12, (planetHouse + 7) % 12 || 12];
                  if (marsAspects.includes(houseNumber)) {
                    aspects.push(houseNumber === marsAspects[0] ? '4th' : '8th');
                  }
                }
                
                if (name === 'Jupiter') {
                  const jupiterAspects = [(planetHouse + 4) % 12 || 12, (planetHouse + 8) % 12 || 12];
                  if (jupiterAspects.includes(houseNumber)) {
                    aspects.push(houseNumber === jupiterAspects[0] ? '5th' : '9th');
                  }
                }
                
                if (name === 'Saturn') {
                  const saturnAspects = [(planetHouse + 2) % 12 || 12, (planetHouse + 9) % 12 || 12];
                  if (saturnAspects.includes(houseNumber)) {
                    aspects.push(houseNumber === saturnAspects[0] ? '3rd' : '10th');
                  }
                }
                
                if (aspects.length > 0) {
                  const lordships = getHouseLordship(name);
                  const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(name);
                  const isMaleficLord = lordships.some(h => [6, 8, 12].includes(h));
                  
                  let aspectNature = isNaturalBenefic && !isMaleficLord ? 'Positive' : 
                                   !isNaturalBenefic || isMaleficLord ? 'Negative' : 'Mixed';
                  
                  aspectingPlanets.push({ name, aspects, nature: aspectNature, lordships });
                }
              });
              
              return aspectingPlanets.length > 0 ? aspectingPlanets.map(planet => (
                <div key={planet.name} style={{
                  fontSize: '13px', padding: '8px 12px', marginBottom: '6px',
                  background: 'rgba(255,255,255,0.7)', borderRadius: '8px',
                  border: '1px solid rgba(0,0,0,0.1)'
                }}>
                  <strong>{planet.name}</strong> {planet.aspects.join(', ')} aspect
                  {planet.lordships.length > 0 && <span style={{ color: '#666' }}> • Lord of {planet.lordships.join(', ')}</span>}
                  <div style={{ marginTop: '4px' }}>
                    <span style={{
                      color: planet.nature === 'Positive' ? '#4caf50' : planet.nature === 'Negative' ? '#f44336' : '#ff9800',
                      fontWeight: '600', fontSize: '12px'
                    }}>● {planet.nature}</span>
                  </div>
                </div>
              )) : <div style={{ fontSize: '13px', color: '#666', fontStyle: 'italic', padding: '8px 0' }}>No planetary aspects</div>;
            })()}
          </div>
          
          <div style={{
            background: 'linear-gradient(135deg, rgba(63, 81, 181, 0.1) 0%, rgba(33, 150, 243, 0.1) 100%)',
            borderRadius: '12px', padding: '15px', marginBottom: '20px',
            border: '1px solid rgba(63, 81, 181, 0.2)'
          }}>
            <h4 style={{ color: '#3f51b5', margin: '0 0 12px 0', fontSize: '16px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
              ✨ Special Conditions
            </h4>
            <div style={{ fontSize: '13px' }}>
              <div style={{ padding: '8px 12px', marginBottom: '6px', background: 'rgba(255,255,255,0.7)', borderRadius: '8px', border: '1px solid rgba(0,0,0,0.1)' }}>
                <strong>Dagdha Rashi:</strong> {(() => {
                  const currentYogiData = yogiData || chartData.yogiData;
                  if (currentYogiData?.dagdha_rashi) {
                    return currentYogiData.dagdha_rashi.sign === rashiIndex ? 
                      <span style={{ color: '#f44336', fontWeight: '600' }}>Yes - Negative</span> : 
                      <span style={{ color: '#4caf50' }}>No</span>;
                  }
                  return <span style={{ color: '#ff9800' }}>Loading...</span>;
                })()}
              </div>
              <div style={{ padding: '8px 12px', marginBottom: '6px', background: 'rgba(255,255,255,0.7)', borderRadius: '8px', border: '1px solid rgba(0,0,0,0.1)' }}>
                <strong>Tithi Shunya:</strong> {(() => {
                  const currentYogiData = yogiData || chartData.yogiData;
                  if (currentYogiData?.tithi_shunya_rashi) {
                    return currentYogiData.tithi_shunya_rashi.sign === rashiIndex ? 
                      <span style={{ color: '#f44336', fontWeight: '600' }}>Yes - Negative</span> : 
                      <span style={{ color: '#4caf50' }}>No</span>;
                  }
                  return <span style={{ color: '#ff9800' }}>Loading...</span>;
                })()}
              </div>
              <div style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.7)', borderRadius: '8px', border: '1px solid rgba(0,0,0,0.1)' }}>
                <strong>Yogi Point:</strong> {(() => {
                  const currentYogiData = yogiData || chartData.yogiData;
                  if (currentYogiData?.yogi && currentYogiData.yogi.sign === rashiIndex) 
                    return <span style={{ color: '#4caf50', fontWeight: '600' }}>Yogi Point here - Very Positive</span>;
                  if (currentYogiData?.avayogi && currentYogiData.avayogi.sign === rashiIndex) 
                    return <span style={{ color: '#f44336', fontWeight: '600' }}>Avayogi Point here - Very Negative</span>;
                  return currentYogiData ? 
                    <span style={{ color: '#666' }}>No special Yogi influence</span> : 
                    <span style={{ color: '#ff9800' }}>Loading...</span>;
                })()}
              </div>
            </div>
          </div>
          
          <div style={{
            background: 'linear-gradient(135deg, rgba(96, 125, 139, 0.1) 0%, rgba(69, 90, 100, 0.1) 100%)',
            borderRadius: '12px', padding: '15px', marginBottom: '20px',
            border: '1px solid rgba(96, 125, 139, 0.2)'
          }}>
            <h4 style={{ color: '#607d8b', margin: '0 0 12px 0', fontSize: '16px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
              📊 Overall Assessment
            </h4>
            {(() => {
              let positiveFactors = 0;
              let negativeFactors = 0;
              let neutralFactors = 0;
              
              // Count occupants
              planetsInHouse.forEach(planet => {
                const lordships = getHouseLordship(planet.name);
                const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planet.name);
                const isNaturalMalefic = ['Mars', 'Saturn', 'Sun', 'Rahu', 'Ketu'].includes(planet.name);
                const hasTrikonaLordship = lordships.some(h => [1, 5, 9].includes(h));
                const hasKendraLordship = lordships.some(h => [1, 4, 7, 10].includes(h));
                
                if (lordships.includes(6) || lordships.includes(8)) {
                  negativeFactors++;
                } else if (isNaturalBenefic && (hasTrikonaLordship || hasKendraLordship)) {
                  positiveFactors++;
                } else if (isNaturalMalefic) {
                  negativeFactors++;
                } else {
                  neutralFactors++;
                }
              });
              
              // Count aspects
              Object.entries(chartData.planets || {}).forEach(([name, data]) => {
                const planetSign = data.sign;
                const ascendantSign = chartData.houses?.[0]?.sign || 0;
                const planetHouse = ((planetSign - ascendantSign + 12) % 12) + 1;
                let hasAspect = false;
                
                if (!['Rahu', 'Ketu'].includes(name)) {
                  const seventhHouse = (planetHouse + 6) % 12 || 12;
                  if (seventhHouse === houseNumber) hasAspect = true;
                }
                
                if (['Rahu', 'Ketu', 'Mars', 'Jupiter', 'Saturn'].includes(name)) {
                  // Check special aspects
                  let specialAspects = [];
                  if (['Rahu', 'Ketu'].includes(name)) {
                    specialAspects = [(planetHouse + 2) % 12 || 12, (planetHouse + 10) % 12 || 12];
                  } else if (name === 'Mars') {
                    specialAspects = [(planetHouse + 3) % 12 || 12, (planetHouse + 7) % 12 || 12];
                  } else if (name === 'Jupiter') {
                    specialAspects = [(planetHouse + 4) % 12 || 12, (planetHouse + 8) % 12 || 12];
                  } else if (name === 'Saturn') {
                    specialAspects = [(planetHouse + 2) % 12 || 12, (planetHouse + 9) % 12 || 12];
                  }
                  if (specialAspects.includes(houseNumber)) hasAspect = true;
                }
                
                if (hasAspect) {
                  const lordships = getHouseLordship(name);
                  const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(name);
                  const isMaleficLord = lordships.some(h => [6, 8, 12].includes(h));
                  
                  if (isNaturalBenefic && !isMaleficLord) {
                    positiveFactors++;
                  } else if (!isNaturalBenefic || isMaleficLord) {
                    negativeFactors++;
                  } else {
                    neutralFactors++;
                  }
                }
              });
              
              // Check special conditions
              const currentYogiData = yogiData || chartData.yogiData;
              if (currentYogiData?.dagdha_rashi?.sign === rashiIndex) negativeFactors++;
              if (currentYogiData?.tithi_shunya_rashi?.sign === rashiIndex) negativeFactors++;
              if (currentYogiData?.yogi?.sign === rashiIndex) positiveFactors++;
              if (currentYogiData?.avayogi?.sign === rashiIndex) negativeFactors++;
              
              const totalFactors = positiveFactors + negativeFactors + neutralFactors;
              let overallStatus = 'Neutral';
              let statusColor = '#ff9800';
              
              if (positiveFactors > negativeFactors) {
                overallStatus = 'Favorable';
                statusColor = '#4caf50';
              } else if (negativeFactors > positiveFactors) {
                overallStatus = 'Challenging';
                statusColor = '#f44336';
              }
              
              return (
                <div style={{ fontSize: '13px' }}>
                  <div style={{ padding: '8px 12px', marginBottom: '8px', background: 'rgba(255,255,255,0.7)', borderRadius: '8px', border: '1px solid rgba(0,0,0,0.1)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong>House Status:</strong>
                      <span style={{ color: statusColor, fontWeight: '600' }}>{overallStatus}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', fontSize: '12px' }}>
                    <div style={{ flex: 1, textAlign: 'center', padding: '6px', background: 'rgba(76, 175, 80, 0.1)', borderRadius: '6px' }}>
                      <div style={{ color: '#4caf50', fontWeight: '600' }}>{positiveFactors}</div>
                      <div>Positive</div>
                    </div>
                    <div style={{ flex: 1, textAlign: 'center', padding: '6px', background: 'rgba(255, 152, 0, 0.1)', borderRadius: '6px' }}>
                      <div style={{ color: '#ff9800', fontWeight: '600' }}>{neutralFactors}</div>
                      <div>Neutral</div>
                    </div>
                    <div style={{ flex: 1, textAlign: 'center', padding: '6px', background: 'rgba(244, 67, 54, 0.1)', borderRadius: '6px' }}>
                      <div style={{ color: '#f44336', fontWeight: '600' }}>{negativeFactors}</div>
                      <div>Negative</div>
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
        <div style={{ padding: '20px', borderTop: '1px solid rgba(0,0,0,0.1)', textAlign: 'center' }}>
          <button onClick={onClose} style={{
            background: 'linear-gradient(135deg, #e91e63 0%, #ff6f00 100%)',
            color: 'white', border: 'none', borderRadius: '25px',
            padding: '12px 30px', fontSize: '14px', fontWeight: '600',
            cursor: 'pointer', transition: 'all 0.3s ease',
            boxShadow: '0 4px 15px rgba(233, 30, 99, 0.3)'
          }}>Close Analysis</button>
        </div>
      </div>
    </div>
  );
};

export default HouseAnalysisModal;