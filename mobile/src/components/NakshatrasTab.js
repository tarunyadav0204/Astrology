import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { apiService } from '../services/apiService';

const PlanetarySignificance = ({ planet, nakshatra, house }) => {
  const [interpretation, setInterpretation] = useState('Loading interpretation...');
  
  useEffect(() => {
    loadInterpretation();
  }, [planet, nakshatra, house]);
  
  const loadInterpretation = async () => {
    const result = await getPlanetNakshatraSignificance(planet, nakshatra, house);
    setInterpretation(result);
  };
  
  return <Text style={styles.sectionText}>{interpretation}</Text>;
};

const getPlanetNakshatraSignificance = async (planet, nakshatra, house) => {
  try {
    const interpretation = await apiService.getPlanetNakshatraInterpretation(planet, nakshatra, house);
    if (interpretation) {
      return interpretation;
    }
  } catch (error) {
    console.error('Failed to fetch interpretation:', error);
  }
  
  // Fallback to base interpretation without house context
  return `Classical texts describe ${planet} in ${nakshatra} as bringing specific influences. This combination creates unique karmic patterns and life experiences that manifest according to the native's overall chart strength and planetary periods.`;
};



export default function NakshatrasTab({ chartData, birthData }) {
  const [selectedNakshatra, setSelectedNakshatra] = useState(null);
  const [selectedPlanetPosition, setSelectedPlanetPosition] = useState(null);
  
  const nakshatras = [
    { name: 'Ashwini', lord: 'Ketu', deity: 'Ashwini Kumaras', nature: 'Light/Swift', guna: 'Rajas', description: 'Ashwini nakshatra is the first among the twenty-seven nakshatras and comes under the domain of planet Ketu.', characteristics: 'People born under Ashwini nakshatra are known for their pioneering spirit and dynamic nature.', positiveTraits: 'Healing abilities, leadership qualities, pioneering spirit.', negativeTraits: 'Impatience, impulsiveness, overly aggressive.', careers: 'Medicine, healing arts, emergency services.', compatibility: 'Most compatible with Bharani and Krittika nakshatras.' },
    { name: 'Bharani', lord: 'Venus', deity: 'Yama', nature: 'Fierce/Ugra', guna: 'Rajas', description: 'Bharani nakshatra is ruled by Venus and presided over by Yama, the god of death and dharma.', characteristics: 'Bharani natives are known for their strong willpower and determination.', positiveTraits: 'Strong responsibility, creative abilities, natural leadership.', negativeTraits: 'Stubbornness, jealousy, overly critical nature.', careers: 'Law, justice, administration, creative arts.', compatibility: 'Most compatible with Ashwini and Rohini nakshatras.' },
    { name: 'Krittika', lord: 'Sun', deity: 'Agni', nature: 'Mixed', guna: 'Rajas', description: 'Krittika nakshatra is ruled by the Sun and presided over by Agni, the fire god.', characteristics: 'Krittika natives are known for their sharp intellect and determination.', positiveTraits: 'Sharp intellect, leadership abilities, strong justice sense.', negativeTraits: 'Overly critical, harsh speech, cruel judgments.', careers: 'Teaching, criticism, editing, research.', compatibility: 'Most compatible with Rohini and Mrigashira nakshatras.' },
    { name: 'Rohini', lord: 'Moon', deity: 'Brahma', nature: 'Fixed/Dhruva', guna: 'Rajas', description: 'Rohini nakshatra is ruled by the Moon and presided over by Brahma, the creator god.', characteristics: 'Rohini natives are blessed with natural beauty and charm.', positiveTraits: 'Natural beauty, artistic abilities, magnetic charm.', negativeTraits: 'Materialism, possessiveness, attachment to comforts.', careers: 'Arts, beauty, luxury goods, fashion.', compatibility: 'Most compatible with Mrigashira and Ardra nakshatras.' },
    { name: 'Mrigashira', lord: 'Mars', deity: 'Soma', nature: 'Soft/Mridu', guna: 'Tamas', description: 'Mrigashira nakshatra is ruled by Mars and presided over by Soma.', characteristics: 'Mrigashira natives are known for their curious nature and love for exploration.', positiveTraits: 'Curiosity, communication skills, gentle nature.', negativeTraits: 'Restlessness, indecisiveness, superficial pursuits.', careers: 'Communication, travel, exploration, writing.', compatibility: 'Most compatible with Ardra and Punarvasu nakshatras.' },
    { name: 'Ardra', lord: 'Rahu', deity: 'Rudra', nature: 'Sharp/Tikshna', guna: 'Tamas', description: 'Ardra nakshatra is ruled by Rahu and presided over by Rudra.', characteristics: 'Ardra natives are intense, emotional, and transformative individuals.', positiveTraits: 'Transformative abilities, sharp intellect, innovative thinking.', negativeTraits: 'Emotional instability, destructive tendencies, extremes.', careers: 'Research, investigation, transformation, science.', compatibility: 'Most compatible with Punarvasu and Pushya nakshatras.' },
    { name: 'Punarvasu', lord: 'Jupiter', deity: 'Aditi', nature: 'Movable/Chara', guna: 'Rajas', description: 'Punarvasu nakshatra is ruled by Jupiter and presided over by Aditi.', characteristics: 'Punarvasu natives are optimistic, philosophical, and generous.', positiveTraits: 'Optimism, generosity, wisdom.', negativeTraits: 'Over-optimism, tendency to be preachy.', careers: 'Teaching, counseling, guidance.', compatibility: 'Most compatible with Pushya and Ashlesha nakshatras.' },
    { name: 'Pushya', lord: 'Saturn', deity: 'Brihaspati', nature: 'Light/Laghu', guna: 'Rajas', description: 'Pushya nakshatra is ruled by Saturn and presided over by Brihaspati.', characteristics: 'Pushya natives are nurturing, disciplined, and spiritually inclined.', positiveTraits: 'Nurturing nature, discipline, spiritual wisdom.', negativeTraits: 'Over-conservatism, rigidity, controlling.', careers: 'Teaching, counseling, healthcare.', compatibility: 'Most compatible with Ashlesha and Magha nakshatras.' },
    { name: 'Ashlesha', lord: 'Mercury', deity: 'Nagas', nature: 'Sharp/Tikshna', guna: 'Sattva', description: 'Ashlesha nakshatra is ruled by Mercury and presided over by the Nagas.', characteristics: 'Ashlesha natives are intuitive, mysterious, and possess deep psychological insight.', positiveTraits: 'Intuitive abilities, psychological insight, healing powers.', negativeTraits: 'Manipulative tendencies, secretiveness, emotional instability.', careers: 'Psychology, healing, transformation.', compatibility: 'Most compatible with Jyeshtha and Revati nakshatras.' },
    { name: 'Magha', lord: 'Ketu', deity: 'Pitrs', nature: 'Fierce/Ugra', guna: 'Tamas', description: 'Magha nakshatra is ruled by Ketu and presided over by the Pitrs.', characteristics: 'Magha natives are authoritative, proud, and possess natural leadership qualities.', positiveTraits: 'Leadership abilities, dignity, respect for tradition.', negativeTraits: 'Arrogance, superiority complex, domineering.', careers: 'Politics, government, administration.', compatibility: 'Most compatible with Purva Phalguni and Uttara Phalguni nakshatras.' },
    { name: 'Purva Phalguni', lord: 'Venus', deity: 'Bhaga', nature: 'Fierce/Ugra', guna: 'Rajas', description: 'Purva Phalguni nakshatra is ruled by Venus and presided over by Bhaga.', characteristics: 'Purva Phalguni natives are creative, artistic, and pleasure-loving.', positiveTraits: 'Creativity, charm, generous nature.', negativeTraits: 'Vanity, laziness, overly indulgent.', careers: 'Entertainment, arts, luxury.', compatibility: 'Most compatible with Uttara Phalguni and Hasta nakshatras.' },
    { name: 'Uttara Phalguni', lord: 'Sun', deity: 'Aryaman', nature: 'Fixed/Dhruva', guna: 'Rajas', description: 'Uttara Phalguni nakshatra is ruled by the Sun and presided over by Aryaman.', characteristics: 'Uttara Phalguni natives are helpful, supportive, and organized.', positiveTraits: 'Helpful nature, organizational skills, beneficial partnerships.', negativeTraits: 'Overly dependent on others, difficulty in making independent decisions.', careers: 'Service, organization, support.', compatibility: 'Most compatible with Hasta and Chitra nakshatras.' },
    { name: 'Hasta', lord: 'Moon', deity: 'Savitar', nature: 'Light/Laghu', guna: 'Rajas', description: 'Hasta nakshatra is ruled by the Moon and presided over by Savitar.', characteristics: 'Hasta natives are skillful, hardworking, and practical.', positiveTraits: 'Exceptional skills, hardworking nature, practical intelligence.', negativeTraits: 'Perfectionism, overly critical, too focused on details.', careers: 'Craftsmanship, medical field, skilled work.', compatibility: 'Most compatible with Chitra and Swati nakshatras.' },
    { name: 'Chitra', lord: 'Mars', deity: 'Vishvakarma', nature: 'Soft/Mridu', guna: 'Tamas', description: 'Chitra nakshatra is ruled by Mars and presided over by Vishvakarma.', characteristics: 'Chitra natives are creative, artistic, and possess exceptional aesthetic sense.', positiveTraits: 'Creativity, artistic abilities, natural charisma.', negativeTraits: 'Vanity, superficiality, overly concerned with appearances.', careers: 'Design, arts, beauty.', compatibility: 'Most compatible with Swati and Vishakha nakshatras.' },
    { name: 'Swati', lord: 'Rahu', deity: 'Vayu', nature: 'Movable/Chara', guna: 'Tamas', description: 'Swati nakshatra is ruled by Rahu and presided over by Vayu.', characteristics: 'Swati natives are independent, flexible, and diplomatic.', positiveTraits: 'Independence, diplomatic skills, business acumen.', negativeTraits: 'Restlessness, indecisiveness, superficial relationships.', careers: 'Communication, negotiation, business.', compatibility: 'Most compatible with Vishakha and Anuradha nakshatras.' },
    { name: 'Vishakha', lord: 'Jupiter', deity: 'Indragni', nature: 'Mixed', guna: 'Rajas', description: 'Vishakha nakshatra is ruled by Jupiter and presided over by Indra-Agni.', characteristics: 'Vishakha natives are determined, goal-oriented, and ambitious.', positiveTraits: 'Determination, leadership abilities, goal-oriented nature.', negativeTraits: 'Over-ambition, impatience, ruthless in pursuit of goals.', careers: 'Leadership, determination, goal achievement.', compatibility: 'Most compatible with Anuradha and Jyeshtha nakshatras.' },
    { name: 'Anuradha', lord: 'Saturn', deity: 'Mitra', nature: 'Soft/Mridu', guna: 'Tamas', description: 'Anuradha nakshatra is ruled by Saturn and presided over by Mitra.', characteristics: 'Anuradha natives are devoted, friendly, and successful.', positiveTraits: 'Devotion, diplomatic skills, organizational abilities.', negativeTraits: 'Over-dependence on others, overly accommodating, too trusting.', careers: 'Counseling, diplomacy, organization.', compatibility: 'Most compatible with Jyeshtha and Mula nakshatras.' },
    { name: 'Jyeshtha', lord: 'Mercury', deity: 'Indra', nature: 'Sharp/Tikshna', guna: 'Sattva', description: 'Jyeshtha nakshatra is ruled by Mercury and presided over by Indra.', characteristics: 'Jyeshtha natives are protective, authoritative, and responsible.', positiveTraits: 'Protective nature, leadership abilities, sense of responsibility.', negativeTraits: 'Overly controlling, authoritarian behavior, too critical.', careers: 'Administration, management, protection.', compatibility: 'Most compatible with Mula and Purva Ashadha nakshatras.' },
    { name: 'Mula', lord: 'Ketu', deity: 'Nirriti', nature: 'Sharp/Tikshna', guna: 'Tamas', description: 'Mula nakshatra is ruled by Ketu and presided over by Nirriti.', characteristics: 'Mula natives are investigative, research-oriented, and philosophical.', positiveTraits: 'Investigative abilities, philosophical nature, transformative power.', negativeTraits: 'Destructive tendencies, restlessness, overly critical.', careers: 'Research, investigation, transformation.', compatibility: 'Most compatible with Purva Ashadha and Uttara Ashadha nakshatras.' },
    { name: 'Purva Ashadha', lord: 'Venus', deity: 'Apas', nature: 'Fierce/Ugra', guna: 'Rajas', description: 'Purva Ashadha nakshatra is ruled by Venus and presided over by Apas.', characteristics: 'Purva Ashadha natives are invincible, purifying, and influential.', positiveTraits: 'Invincible spirit, purifying abilities, influential nature.', negativeTraits: 'Excessive pride, stubbornness, overly argumentative.', careers: 'Debate, law, influence.', compatibility: 'Most compatible with Uttara Ashadha and Shravana nakshatras.' },
    { name: 'Uttara Ashadha', lord: 'Sun', deity: 'Vishvedevas', nature: 'Fixed/Dhruva', guna: 'Rajas', description: 'Uttara Ashadha nakshatra is ruled by the Sun and presided over by the Vishvadevas.', characteristics: 'Uttara Ashadha natives are victorious, righteous, and possess strong leadership qualities.', positiveTraits: 'Determination, ethical nature, leadership abilities.', negativeTraits: 'Stubbornness, inflexibility, overly serious.', careers: 'Leadership, ethics, long-term achievement.', compatibility: 'Most compatible with Shravana and Dhanishta nakshatras.' },
    { name: 'Shravana', lord: 'Moon', deity: 'Vishnu', nature: 'Movable/Chara', guna: 'Rajas', description: 'Shravana nakshatra is ruled by the Moon and presided over by Vishnu.', characteristics: 'Shravana natives are excellent listeners, knowledgeable, and wise.', positiveTraits: 'Listening abilities, scholarly nature, communication skills.', negativeTraits: 'Overly talkative, gossipy nature, too focused on information.', careers: 'Education, communication, knowledge preservation.', compatibility: 'Most compatible with Dhanishta and Shatabhisha nakshatras.' },
    { name: 'Dhanishta', lord: 'Mars', deity: 'Vasus', nature: 'Movable/Chara', guna: 'Tamas', description: 'Dhanishta nakshatra is ruled by Mars and presided over by the Vasus.', characteristics: 'Dhanishta natives are sociable, adaptable, and vibrant.', positiveTraits: 'Sociability, adaptability, vibrant personality.', negativeTraits: 'Easy susceptibility to influence, aggression, materialism.', careers: 'Performing arts, management, entrepreneurship.', compatibility: 'Most compatible with Shatabhisha and Purva Bhadrapada nakshatras.' },
    { name: 'Shatabhisha', lord: 'Rahu', deity: 'Varuna', nature: 'Movable/Chara', guna: 'Tamas', description: 'Shatabhisha nakshatra is ruled by Rahu and presided over by Varuna.', characteristics: 'Shatabhisha natives possess natural healing abilities and are independent, mysterious individuals.', positiveTraits: 'Healing abilities, independent nature, research skills.', negativeTraits: 'Overly secretive, stubborn nature, too unconventional.', careers: 'Healing, research, unconventional fields.', compatibility: 'Most compatible with Purva Bhadrapada and Uttara Bhadrapada nakshatras.' },
    { name: 'Purva Bhadrapada', lord: 'Jupiter', deity: 'Aja Ekapada', nature: 'Fierce/Ugra', guna: 'Rajas', description: 'Purva Bhadrapada nakshatra is ruled by Jupiter and presided over by Aja Ekapada.', characteristics: 'Purva Bhadrapada natives are transformative, spiritual, and intense individuals.', positiveTraits: 'Transformative abilities, spiritual wisdom, philosophical nature.', negativeTraits: 'Tendency towards extremes, unpredictable behavior, overly intense.', careers: 'Spirituality, philosophy, transformation.', compatibility: 'Most compatible with Uttara Bhadrapada and Revati nakshatras.' },
    { name: 'Uttara Bhadrapada', lord: 'Saturn', deity: 'Ahir Budhnya', nature: 'Fixed/Dhruva', guna: 'Tamas', description: 'Uttara Bhadrapada nakshatra is ruled by Saturn and presided over by Ahir Budhnya.', characteristics: 'Uttara Bhadrapada natives are deep, stable, and wise individuals.', positiveTraits: 'Depth, stability, wisdom.', negativeTraits: 'Overly serious, pessimistic outlook, too slow to act.', careers: 'Planning, spirituality, depth work.', compatibility: 'Most compatible with Revati and Ashwini nakshatras.' },
    { name: 'Revati', lord: 'Mercury', deity: 'Pushan', nature: 'Soft/Mridu', guna: 'Sattva', description: 'Revati nakshatra is ruled by Mercury and presided over by Pushan.', characteristics: 'Revati natives are nourishing, prosperous, and protective individuals.', positiveTraits: 'Nourishing nature, prosperity consciousness, protective instincts.', negativeTraits: 'Overly protective, possessive nature, too giving.', careers: 'Nourishment, travel, completion work.', compatibility: 'Most compatible with Ashwini and Bharani nakshatras.' }
  ];

  const getNakshatra = (longitude) => {
    const nakshatraIndex = Math.floor(longitude / 13.333333);
    const pada = Math.floor((longitude % 13.333333) / 3.333333) + 1;
    return { index: nakshatraIndex, pada };
  };

  const getPlanetaryPositions = () => {
    if (!chartData?.planets) return [];
    
    return Object.entries(chartData.planets).map(([name, data]) => {
      const nakshatra = getNakshatra(data.longitude);
      const nakshatraData = nakshatras[nakshatra.index] || nakshatras[0];
      
      return {
        planet: name,
        longitude: data.longitude.toFixed(2),
        nakshatra: nakshatraData.name,
        pada: nakshatra.pada,
        lord: nakshatraData.lord,
        deity: nakshatraData.deity,
        nature: nakshatraData.nature,
        guna: nakshatraData.guna,
        house: data.house || 1
      };
    });
  };

  const planetaryPositions = getPlanetaryPositions();

  if (selectedPlanetPosition) {
    return (
      <ScrollView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity 
            onPress={() => setSelectedPlanetPosition(null)}
            style={styles.backButton}
          >
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.selectedTitle}>🪐 {selectedPlanetPosition.planet} in {selectedPlanetPosition.nakshatra}</Text>
        </View>
        
        <View style={styles.scrollContent}>
          <View style={styles.detailCard}>
            <View style={styles.basicInfo}>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Planet:</Text>
                <Text style={styles.infoValue}>{selectedPlanetPosition.planet}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Nakshatra:</Text>
                <Text style={styles.infoValue}>{selectedPlanetPosition.nakshatra}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Pada:</Text>
                <Text style={styles.infoValue}>{selectedPlanetPosition.pada}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Nakshatra Lord:</Text>
                <Text style={styles.infoValue}>{selectedPlanetPosition.lord}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>House:</Text>
                <Text style={styles.infoValue}>{selectedPlanetPosition.house}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Longitude:</Text>
                <Text style={styles.infoValue}>{selectedPlanetPosition.longitude}°</Text>
              </View>
            </View>
            
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>🌟 Planetary Significance</Text>
              <PlanetarySignificance 
                planet={selectedPlanetPosition.planet}
                nakshatra={selectedPlanetPosition.nakshatra}
                house={selectedPlanetPosition.house}
              />
            </View>
            
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>📖 Nakshatra Overview</Text>
              <Text style={styles.sectionText}>
                {nakshatras.find(n => n.name === selectedPlanetPosition.nakshatra)?.description}
              </Text>
            </View>
            
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>🎯 Key Influences</Text>
              <Text style={styles.sectionText}>
                • Nakshatra Lord: {selectedPlanetPosition.lord} influences this placement{'\n'}
                • Pada {selectedPlanetPosition.pada}: Specific sub-division effects{'\n'}
                • Planetary combination creates unique life experiences{'\n'}
                • This placement affects personality, career, and relationships
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    );
  }

  if (selectedNakshatra) {
    return (
      <ScrollView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity 
            onPress={() => setSelectedNakshatra(null)}
            style={styles.backButton}
          >
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.selectedTitle}>🌟 {selectedNakshatra.name}</Text>
        </View>
        
        <View style={styles.scrollContent}>
          <View style={styles.detailCard}>
            <View style={styles.basicInfo}>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Lord:</Text>
                <Text style={styles.infoValue}>{selectedNakshatra.lord}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Deity:</Text>
                <Text style={styles.infoValue}>{selectedNakshatra.deity}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Nature:</Text>
                <Text style={styles.infoValue}>{selectedNakshatra.nature}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Guna:</Text>
                <Text style={styles.infoValue}>{selectedNakshatra.guna}</Text>
              </View>
            </View>
            
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>📖 Description</Text>
              <Text style={styles.sectionText}>{selectedNakshatra.description}</Text>
            </View>
            
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>✨ Characteristics</Text>
              <Text style={styles.sectionText}>{selectedNakshatra.characteristics}</Text>
            </View>
            
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, {color: '#22c55e'}]}>✅ Positive Traits</Text>
              <Text style={styles.sectionText}>{selectedNakshatra.positiveTraits}</Text>
            </View>
            
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, {color: '#ef4444'}]}>⚠️ Negative Traits</Text>
              <Text style={styles.sectionText}>{selectedNakshatra.negativeTraits}</Text>
            </View>
            
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>💼 Career Options</Text>
              <Text style={styles.sectionText}>{selectedNakshatra.careers}</Text>
            </View>
            
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>🤝 Compatibility</Text>
              <Text style={styles.sectionText}>{selectedNakshatra.compatibility}</Text>
            </View>
          </View>
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>🌟 Nakshatra Analysis</Text>
        {planetaryPositions.length > 0 && (
          <View style={styles.planetarySection}>
            <Text style={styles.sectionTitle}>🪐 Planetary Positions</Text>
            {planetaryPositions.map((pos, index) => (
              <TouchableOpacity 
                key={pos.planet} 
                style={styles.planetCard}
                onPress={() => setSelectedPlanetPosition(pos)}
              >
                <View style={styles.planetInfo}>
                  <Text style={styles.planetName}>{pos.planet}</Text>
                  <Text style={styles.planetDetails}>{pos.nakshatra} - Pada {pos.pada}</Text>
                  <Text style={styles.planetLord}>Lord: {pos.lord}</Text>
                </View>
                <Text style={styles.arrow}>→</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
        
        <View style={styles.nakshatraGrid}>
          <Text style={styles.sectionTitle}>📚 All Nakshatras</Text>
          {nakshatras.map((nakshatra, index) => (
            <TouchableOpacity 
              key={index} 
              style={styles.nakshatraCard}
              onPress={() => setSelectedNakshatra(nakshatra)}
            >
              <View style={styles.nakshatraHeader}>
                <Text style={styles.nakshatraName}>{index + 1}. {nakshatra.name}</Text>
                <Text style={styles.nakshatraLord}>{nakshatra.lord}</Text>
              </View>
              <Text style={styles.nakshatraRange}>
                {(index * 13.33).toFixed(1)}° - {((index + 1) * 13.33).toFixed(1)}°
              </Text>
              <Text style={styles.nakshatraDeity}>Deity: {nakshatra.deity}</Text>
            </TouchableOpacity>
          ))}
        </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#e91e63',
    textAlign: 'center',
    marginBottom: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  backButton: {
    backgroundColor: '#e91e63',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginRight: 12,
  },
  backButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  selectedTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#e91e63',
    flex: 1,
  },
  detailCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  basicInfo: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  infoLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#e91e63',
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ff6f00',
    marginBottom: 8,
  },
  sectionText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#333',
    textAlign: 'justify',
  },
  planetarySection: {
    marginBottom: 24,
    marginTop: 8,
  },
  planetCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    borderLeftWidth: 4,
    borderLeftColor: '#e91e63',
  },
  planetInfo: {
    flex: 1,
  },
  planetName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#e91e63',
    marginBottom: 2,
  },
  planetDetails: {
    fontSize: 14,
    color: '#0066cc',
    marginBottom: 2,
  },
  planetLord: {
    fontSize: 12,
    color: '#666',
  },
  arrow: {
    fontSize: 18,
    color: '#e91e63',
    fontWeight: 'bold',
  },
  nakshatraGrid: {
    marginTop: 8,
  },
  nakshatraCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 14,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 3,
    borderLeftWidth: 4,
    borderLeftColor: '#ff6f00',
  },
  nakshatraHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  nakshatraName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#e91e63',
    flex: 1,
  },
  nakshatraLord: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ff6f00',
    backgroundColor: '#fff8e1',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  nakshatraRange: {
    fontSize: 13,
    color: '#666',
    marginBottom: 4,
  },
  nakshatraDeity: {
    fontSize: 12,
    color: '#0066cc',
    fontStyle: 'italic',
  },
});