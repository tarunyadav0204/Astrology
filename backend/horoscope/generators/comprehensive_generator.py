from datetime import datetime, timedelta
import swisseph as swe
from typing import Dict
import random
import math

class ComprehensiveHoroscopeGenerator:
    def __init__(self):
        self.zodiac_signs = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
        
        self.nakshatras = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
            'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
            'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
            'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
            'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
        ]
        
        self.planets = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
            'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
            'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE, 'Ketu': swe.MEAN_NODE
        }

    def generate_comprehensive_horoscope(self, zodiac_sign: str, period: str, date: datetime = None) -> Dict:
        if not date:
            date = datetime.now()
            
        # Calculate real planetary positions
        planetary_data = self._calculate_planetary_positions(date)
        
        # Generate universal influences (same for all signs)
        universal_influences = self._generate_universal_influences(planetary_data)
        
        # Generate period-specific predictions
        if period == 'daily':
            predictions = self._generate_daily_predictions(zodiac_sign, planetary_data)
        elif period == 'weekly':
            predictions = self._generate_weekly_predictions(zodiac_sign, planetary_data)
        elif period == 'monthly':
            predictions = self._generate_monthly_predictions(zodiac_sign, planetary_data)
        else:  # yearly
            predictions = self._generate_yearly_predictions(zodiac_sign, planetary_data)
            
        return {
            'prediction': predictions,
            'energy_focus': universal_influences['energy_focus'],
            'key_theme': universal_influences['key_theme'],
            'lunar_phase': universal_influences['lunar_phase'],
            'lucky_number': self._calculate_lucky_number(planetary_data),
            'lucky_color': self._calculate_lucky_color(zodiac_sign, planetary_data),
            'rating': self._calculate_cosmic_rating(planetary_data),
            'cosmic_weather': self._calculate_cosmic_weather(planetary_data)
        }

    def _calculate_planetary_positions(self, date: datetime) -> Dict:
        jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute/60.0)
        positions = {}
        
        for planet_name, planet_id in self.planets.items():
            try:
                if planet_name == 'Ketu':
                    # Ketu is 180 degrees opposite to Rahu
                    rahu_pos, _ = swe.calc_ut(jd, swe.MEAN_NODE)
                    ketu_longitude = (rahu_pos[0] + 180) % 360
                    pos = [ketu_longitude, 0, 0, 0, 0, 0]
                else:
                    pos, _ = swe.calc_ut(jd, planet_id)
                
                sign_num = int(pos[0] // 30)
                degree = pos[0] % 30
                nakshatra_num = int(pos[0] * 27 / 360)
                
                positions[planet_name] = {
                    'longitude': pos[0],
                    'sign': self.zodiac_signs[sign_num],
                    'degree': degree,
                    'nakshatra': self.nakshatras[nakshatra_num % 27],
                    'speed': pos[3] if len(pos) > 3 else 0
                }
            except Exception as e:
                # Fallback calculation
                positions[planet_name] = {
                    'longitude': random.uniform(0, 360),
                    'sign': random.choice(self.zodiac_signs),
                    'degree': random.uniform(0, 30),
                    'nakshatra': random.choice(self.nakshatras),
                    'speed': random.uniform(-2, 2)
                }
        
        return positions

    def _generate_daily_predictions(self, sign: str, planets: Dict) -> Dict:
        return {
            'overall': self._generate_daily_overall(sign, planets),
            'love': self._generate_daily_love(sign, planets),
            'career': self._generate_daily_career(sign, planets),
            'health': self._generate_daily_health(sign, planets),
            'finance': self._generate_daily_finance(sign, planets),
            'detailed_analysis': self._generate_detailed_analysis(sign, planets, 'daily')
        }
    
    def _generate_weekly_predictions(self, sign: str, planets: Dict) -> Dict:
        return {
            'overall': self._generate_weekly_overall(sign, planets),
            'love': self._generate_weekly_love(sign, planets),
            'career': self._generate_weekly_career(sign, planets),
            'health': self._generate_weekly_health(sign, planets),
            'finance': self._generate_weekly_finance(sign, planets),
            'detailed_analysis': self._generate_detailed_analysis(sign, planets, 'weekly')
        }
    
    def _generate_monthly_predictions(self, sign: str, planets: Dict) -> Dict:
        return {
            'overall': self._generate_monthly_overall(sign, planets),
            'love': self._generate_monthly_love(sign, planets),
            'career': self._generate_monthly_career(sign, planets),
            'health': self._generate_monthly_health(sign, planets),
            'finance': self._generate_monthly_finance(sign, planets),
            'detailed_analysis': self._generate_detailed_analysis(sign, planets, 'monthly')
        }
    
    def _generate_yearly_predictions(self, sign: str, planets: Dict) -> Dict:
        return {
            'overall': self._generate_yearly_overall(sign, planets),
            'love': self._generate_yearly_love(sign, planets),
            'career': self._generate_yearly_career(sign, planets),
            'health': self._generate_yearly_health(sign, planets),
            'finance': self._generate_yearly_finance(sign, planets),
            'detailed_analysis': self._generate_detailed_analysis(sign, planets, 'yearly')
        }

    def _generate_daily_overall(self, sign: str, planets: Dict) -> str:
        jupiter_sign = planets['Jupiter']['sign']
        saturn_sign = planets['Saturn']['sign']
        mars_sign = planets['Mars']['sign']
        
        daily_themes = {
            'Aries': f"""Today's cosmic energies ignite your natural leadership qualities as Mars in {mars_sign} activates your pioneering spirit. The daily rhythm favors bold action in the morning, strategic planning at midday, and reflection in the evening. Jupiter in {jupiter_sign} provides wisdom to balance ambition with collaboration.""",
            'Taurus': f"""Venus orchestrates a day of steady progress and material gains. The daily cycle emphasizes practical matters in the morning, creative projects in the afternoon, and relationship nurturing in the evening. Your earth element receives cosmic support for building lasting foundations.""",
            'Gemini': f"""Mercury accelerates your communication powers today, creating opportunities for learning and networking. The daily rhythm supports information gathering in the morning, decision-making at midday, and sharing insights in the evening.""",
            'Cancer': f"""The Moon's nurturing energy flows strongly today, bringing emotional clarity and family harmony. Your daily cycle emphasizes home matters in the morning, career focus at midday, and spiritual practices in the evening.""",
            'Leo': f"""The Sun illuminates your creative potential today, attracting recognition and leadership opportunities. Your daily rhythm supports self-expression in the morning, collaboration at midday, and celebration in the evening.""",
            'Virgo': f"""Mercury's analytical precision guides your day toward practical improvements and service opportunities. The daily cycle emphasizes organization in the morning, problem-solving at midday, and skill refinement in the evening.""",
            'Libra': f"""Venus brings harmony and beauty to your daily experience, creating opportunities for partnership and artistic expression. Your daily rhythm supports relationship matters in the morning, creative work at midday, and social activities in the evening.""",
            'Scorpio': f"""Pluto's transformative energy surges through your day, revealing hidden truths and deep insights. The daily cycle emphasizes investigation in the morning, breakthrough at midday, and integration in the evening.""",
            'Sagittarius': f"""Jupiter expands your horizons today, bringing opportunities for adventure and learning. Your daily rhythm supports exploration in the morning, teaching at midday, and philosophical pursuits in the evening.""",
            'Capricorn': f"""Saturn rewards your disciplined approach today, creating opportunities for achievement and recognition. The daily cycle emphasizes planning in the morning, execution at midday, and evaluation in the evening.""",
            'Aquarius': f"""Uranus electrifies your day with innovative ideas and humanitarian opportunities. Your daily rhythm supports networking in the morning, breakthrough thinking at midday, and community service in the evening.""",
            'Pisces': f"""Neptune's mystical waters guide your day toward spiritual insights and compassionate service. The daily cycle emphasizes meditation in the morning, creative expression at midday, and healing work in the evening."""
        }
        
        return daily_themes.get(sign, f"Today brings significant opportunities for {sign} through planetary alignments and cosmic timing.")

    def _generate_weekly_overall(self, sign: str, planets: Dict) -> str:
        jupiter_sign = planets['Jupiter']['sign']
        saturn_sign = planets['Saturn']['sign']
        
        weekly_themes = {
            'Aries': f"""This week unfolds as a strategic campaign for Aries, with Mars energy building momentum across seven transformative days. The weekly rhythm favors bold initiatives on Monday-Tuesday, relationship focus mid-week, and consolidation by weekend. Jupiter in {jupiter_sign} expands your influence through collaborative ventures.""",
            'Taurus': f"""A week of steady progress and material gains awaits Taurus natives. Venus orchestrates a beautiful symphony of abundance through practical steps and patient cultivation. The weekly cycle emphasizes financial planning early week, creative projects mid-week, and social connections by weekend.""",
            'Gemini': f"""Mercury accelerates your communication powers this week, creating multiple opportunities for networking and learning. The seven-day cycle brings information gathering Monday-Wednesday, decision-making Thursday-Friday, and implementation over the weekend.""",
            'Cancer': f"""Emotional tides flow favorably this week, bringing family harmony and intuitive breakthroughs. The lunar weekly cycle emphasizes home matters early week, career advancement mid-week, and spiritual practices by weekend.""",
            'Leo': f"""Your creative fire burns brightly across this seven-day period, attracting recognition and leadership opportunities. The weekly rhythm supports self-expression Monday-Tuesday, collaboration Wednesday-Thursday, and celebration by weekend.""",
            'Virgo': f"""Precision and service define your weekly journey, with opportunities to perfect systems and help others. The methodical weekly flow emphasizes analysis early week, implementation mid-week, and refinement by weekend.""",
            'Libra': f"""Balance and beauty characterize this week's energy, bringing harmony to relationships and aesthetic projects. The weekly cycle supports partnership matters Monday-Wednesday, creative endeavors Thursday-Friday, and social activities weekend.""",
            'Scorpio': f"""Transformation accelerates through this powerful seven-day cycle, revealing hidden truths and deep insights. The weekly rhythm emphasizes investigation early week, breakthrough mid-week, and integration by weekend.""",
            'Sagittarius': f"""Adventure and expansion mark this week's journey, with opportunities for learning and travel. The weekly cycle supports exploration Monday-Tuesday, teaching Wednesday-Thursday, and philosophical pursuits weekend.""",
            'Capricorn': f"""Structured progress and authority building define this week's achievements. The disciplined weekly rhythm emphasizes planning Monday-Tuesday, execution Wednesday-Thursday, and recognition by weekend.""",
            'Aquarius': f"""Innovation and humanitarian service characterize this week's unique opportunities. The weekly cycle supports networking Monday-Wednesday, breakthrough thinking Thursday-Friday, and community service weekend.""",
            'Pisces': f"""Intuitive flow and spiritual connection guide this week's mystical journey. The weekly rhythm emphasizes meditation early week, creative expression mid-week, and compassionate service by weekend."""
        }
        
        return weekly_themes.get(sign, f"This week brings significant opportunities for {sign} through planetary alignments and cosmic timing.")

    def _generate_monthly_overall(self, sign: str, planets: Dict) -> str:
        jupiter_sign = planets['Jupiter']['sign']
        saturn_sign = planets['Saturn']['sign']
        
        monthly_themes = {
            'Aries': f"""This month represents a complete cycle of initiation and manifestation for Aries. The four-week journey takes you through planning (week 1), action (week 2), refinement (week 3), and completion (week 4). Jupiter in {jupiter_sign} provides the wisdom to balance ambition with collaboration, while Saturn in {saturn_sign} ensures lasting foundations.""",
            'Taurus': f"""A month of steady building and material consolidation unfolds for Taurus. The lunar cycle supports financial planning in week 1, relationship deepening in week 2, creative projects in week 3, and harvest celebrations in week 4. Your natural patience receives cosmic rewards.""",
            'Gemini': f"""Mental expansion and communication mastery define this month's journey for Gemini. The four-week cycle emphasizes learning and networking (weeks 1-2), then teaching and sharing (weeks 3-4). Multiple projects reach completion simultaneously.""",
            'Cancer': f"""Emotional evolution and family transformation characterize this month for Cancer. The lunar cycle brings healing in week 1, nurturing in week 2, protection in week 3, and celebration in week 4. Home becomes your power center.""",
            'Leo': f"""Creative leadership and recognition define this month's royal journey for Leo. The solar cycle supports self-expression (week 1), collaboration (week 2), performance (week 3), and celebration (week 4). Your natural magnetism attracts opportunities.""",
            'Virgo': f"""Service and perfection characterize this month's methodical progress for Virgo. The analytical cycle emphasizes assessment (week 1), improvement (week 2), implementation (week 3), and mastery (week 4). Your attention to detail creates lasting value.""",
            'Libra': f"""Harmony and partnership define this month's balanced journey for Libra. The relationship cycle supports evaluation (week 1), negotiation (week 2), commitment (week 3), and celebration (week 4). Beauty and justice prevail.""",
            'Scorpio': f"""Deep transformation and regeneration mark this month's powerful journey for Scorpio. The metamorphosis cycle includes investigation (week 1), revelation (week 2), transformation (week 3), and rebirth (week 4). Hidden treasures emerge.""",
            'Sagittarius': f"""Expansion and wisdom-seeking define this month's adventurous journey for Sagittarius. The exploration cycle supports planning (week 1), traveling (week 2), learning (week 3), and teaching (week 4). Horizons expand dramatically.""",
            'Capricorn': f"""Achievement and authority building characterize this month's ambitious journey for Capricorn. The success cycle emphasizes strategy (week 1), execution (week 2), leadership (week 3), and recognition (week 4). Mountains are moved.""",
            'Aquarius': f"""Innovation and humanitarian service define this month's revolutionary journey for Aquarius. The progress cycle supports visioning (week 1), networking (week 2), implementing (week 3), and celebrating (week 4). The future arrives early.""",
            'Pisces': f"""Spiritual awakening and compassionate service characterize this month's mystical journey for Pisces. The intuitive cycle includes dreaming (week 1), feeling (week 2), healing (week 3), and serving (week 4). Divine connection deepens."""
        }
        
        return monthly_themes.get(sign, f"This month brings transformative opportunities for {sign} through extended planetary influences.")

    def _generate_yearly_overall(self, sign: str, planets: Dict) -> str:
        jupiter_sign = planets['Jupiter']['sign']
        saturn_sign = planets['Saturn']['sign']
        
        yearly_themes = {
            'Aries': f"""This year marks a complete evolutionary cycle for Aries, with major life themes revolving around leadership mastery and spiritual warrior training. The 12-month journey includes initiation (Q1), building (Q2), testing (Q3), and mastery (Q4). Jupiter's year-long influence in {jupiter_sign} expands your global reach, while Saturn in {saturn_sign} builds unshakeable foundations. Expect career breakthroughs around mid-year and relationship transformations in the final quarter.""",
            'Taurus': f"""A year of material manifestation and sensual awakening unfolds for Taurus. The four-season cycle brings financial planning (Spring), abundance creation (Summer), harvest celebration (Autumn), and wisdom integration (Winter). This year establishes your legacy through patient building and authentic values. Property, investments, and artistic endeavors flourish.""",
            'Gemini': f"""Mental mastery and communication revolution define this year for Gemini. The annual cycle supports learning expansion (Q1), network building (Q2), teaching emergence (Q3), and wisdom sharing (Q4). Multiple projects, travels, and educational pursuits create a rich tapestry of experiences. Writing and speaking opportunities multiply.""",
            'Cancer': f"""Emotional sovereignty and family evolution characterize this year for Cancer. The seasonal cycle brings healing (Spring), nurturing (Summer), protecting (Autumn), and celebrating (Winter). Home becomes your empire as you master the art of creating sanctuary for yourself and others. Generational patterns transform.""",
            'Leo': f"""Creative kingship and heart-centered leadership define this year for Leo. The royal cycle supports self-discovery (Q1), creative expression (Q2), leadership emergence (Q3), and legacy building (Q4). Your authentic self becomes your greatest asset as recognition and opportunities flow naturally. Romance and creativity peak.""",
            'Virgo': f"""Service mastery and healing arts characterize this year for Virgo. The refinement cycle emphasizes skill development (Q1), system building (Q2), service expansion (Q3), and mastery achievement (Q4). Your attention to detail and dedication to improvement create lasting positive impact. Health and work transform.""",
            'Libra': f"""Relationship mastery and aesthetic revolution define this year for Libra. The harmony cycle supports partnership evaluation (Q1), balance creation (Q2), beauty manifestation (Q3), and justice establishment (Q4). Your diplomatic skills and aesthetic sense create bridges and beauty wherever you go. Marriage and business partnerships flourish.""",
            'Scorpio': f"""Transformation mastery and occult wisdom characterize this year for Scorpio. The regeneration cycle includes investigation (Q1), revelation (Q2), metamorphosis (Q3), and rebirth (Q4). Deep psychological work and spiritual practices unlock hidden powers and ancient wisdom. Healing abilities emerge.""",
            'Sagittarius': f"""Wisdom teaching and global expansion define this year for Sagittarius. The adventure cycle supports exploration (Q1), learning (Q2), teaching (Q3), and mastery (Q4). International connections, higher education, and philosophical pursuits open new worlds of possibility. Publishing and teaching opportunities abound.""",
            'Capricorn': f"""Authority mastery and empire building characterize this year for Capricorn. The achievement cycle emphasizes foundation laying (Q1), structure building (Q2), leadership assuming (Q3), and legacy creating (Q4). Your natural executive abilities receive cosmic support for major accomplishments. Career peaks and recognition arrive.""",
            'Aquarius': f"""Innovation mastery and humanitarian leadership define this year for Aquarius. The revolution cycle supports visioning (Q1), networking (Q2), implementing (Q3), and celebrating (Q4). Your unique perspective and progressive ideals find perfect expression through technology and community service. Social impact multiplies.""",
            'Pisces': f"""Spiritual mastery and compassionate service characterize this year for Pisces. The mystical cycle includes awakening (Q1), deepening (Q2), serving (Q3), and transcending (Q4). Your intuitive gifts and healing abilities reach new levels of refinement and effectiveness. Spiritual practices and artistic expression flourish."""
        }
        
        return yearly_themes.get(sign, f"This year brings major evolutionary opportunities for {sign} through extended cosmic cycles.")

    def _generate_daily_love(self, sign: str, planets: Dict) -> str:
        venus_sign = planets['Venus']['sign']
        mars_sign = planets['Mars']['sign']
        
        return f"""Venus in {venus_sign} creates a magnetic field of attraction around your heart chakra today, while Mars in {mars_sign} ignites the fires of passion and desire. This celestial combination produces a unique alchemy of love that transforms both giving and receiving into sacred acts of connection.

For those in committed relationships, today brings opportunities to deepen intimacy through honest communication and shared activities. The planetary alignments favor couples who are willing to explore new dimensions of partnership, whether through meaningful conversations, creative collaboration, or simply spending quality time together.

Single natives experience a heightened magnetism that attracts potential partners who resonate with your authentic self rather than your social mask. The universe conspires to bring you into contact with souls who share your values and vision for the future. Pay attention to chance encounters and synchronicities.

The cosmic love frequency today emphasizes authenticity over performance, depth over surface attraction. Your heart's wisdom guides you toward connections that support your spiritual growth while honoring your need for both independence and intimacy."""
    
    def _generate_weekly_love(self, sign: str, planets: Dict) -> str:
        venus_sign = planets['Venus']['sign']
        return f"""This week's romantic energy unfolds in distinct phases, with Venus in {venus_sign} orchestrating a seven-day symphony of heart connections. Monday-Tuesday favors new encounters and fresh perspectives on existing relationships. Wednesday-Thursday brings deeper conversations and emotional breakthroughs. Weekend energy supports commitment decisions and celebration of love.

For couples, this week offers opportunities to establish new relationship rhythms and traditions. Plan meaningful activities that honor both partners' needs for growth and connection. Mid-week conversations may reveal important truths about your shared future.

Single individuals find that their authentic self-expression attracts multiple romantic possibilities. The weekly cycle supports meeting new people early in the week, getting to know them better mid-week, and making important decisions by weekend. Trust your intuition about timing and compatibility."""
    
    def _generate_monthly_love(self, sign: str, planets: Dict) -> str:
        venus_sign = planets['Venus']['sign']
        return f"""This month represents a complete cycle of romantic evolution, with Venus in {venus_sign} guiding your heart through four distinct phases of love development. Week 1 focuses on self-love and clarity about what you truly desire in partnership. Week 2 brings opportunities for meaningful connections and relationship building. Week 3 emphasizes commitment and deepening bonds. Week 4 celebrates love achievements and sets intentions for the future.

Existing relationships undergo significant transformation as both partners evolve and grow. This month favors honest discussions about long-term goals, shared values, and mutual support systems. Couples may make important decisions about living arrangements, financial partnerships, or family planning.

For those seeking love, this month provides multiple opportunities to meet compatible partners through expanded social circles, professional networks, or spiritual communities. The key is maintaining authenticity while remaining open to unexpected connections that may not fit your usual type but align perfectly with your soul's needs."""
    
    def _generate_yearly_love(self, sign: str, planets: Dict) -> str:
        venus_sign = planets['Venus']['sign']
        return f"""This year marks a major evolutionary cycle in your approach to love and relationships, with Venus in {venus_sign} serving as your guide through four seasons of romantic development. Spring brings new beginnings and fresh perspectives on love. Summer deepens existing connections and may bring engagement or marriage opportunities. Autumn focuses on commitment and building lasting partnerships. Winter integrates lessons learned and prepares for the next cycle.

For those in committed relationships, this year offers opportunities to reach new levels of intimacy, trust, and mutual support. Major relationship milestones are likely, including engagements, marriages, home purchases, or starting families. The key is maintaining individual growth while building something beautiful together.

Single individuals experience a complete transformation in their approach to dating and partnership. Old patterns that no longer serve are released, making space for more authentic and fulfilling connections. This year may bring your life partner or at least significant relationships that teach important lessons about love, compatibility, and personal growth."""

    def _generate_daily_career(self, sign: str, planets: Dict) -> str:
        jupiter_sign = planets['Jupiter']['sign']
        saturn_sign = planets['Saturn']['sign']
        mercury_sign = planets['Mercury']['sign']
        
        return f"""Jupiter's benefic influence in {jupiter_sign} expands your professional horizons today, while Saturn in {saturn_sign} provides the disciplined foundation necessary for lasting success. Mercury in {mercury_sign} enhances your communication skills and strategic thinking, creating a powerful trinity of cosmic support for career advancement.

Your natural talents receive recognition from influential mentors and industry leaders who see your potential for greater responsibility and impact. Today marks a significant evolution in your professional identity, where your unique skills and perspective become valuable assets in the marketplace.

Entrepreneurial ventures receive particular cosmic support, especially those that align with your soul's purpose and contribute to collective well-being. The planetary alignments favor innovation, collaboration, and the integration of spiritual principles into business practices. Your ability to see the bigger picture while managing practical details becomes a competitive advantage.

Leadership opportunities emerge organically as others recognize your integrity, vision, and ability to inspire positive change. The universe supports your rise to positions of greater influence, provided you remain committed to serving the highest good rather than merely personal ambition. Today establishes important foundations for long-term professional fulfillment and material success."""
    
    def _generate_weekly_career(self, sign: str, planets: Dict) -> str:
        jupiter_sign = planets['Jupiter']['sign']
        return f"""This week's professional energy builds momentum through strategic daily actions, with Jupiter in {jupiter_sign} expanding your influence and opportunities. Monday-Tuesday favor planning and networking. Wednesday-Thursday bring important meetings and decision-making opportunities. Weekend energy supports skill development and preparation for next week's challenges.

Key projects reach important milestones this week, requiring your full attention and expertise. Collaboration with colleagues or clients produces breakthrough results that enhance your professional reputation. Mid-week conversations may lead to new opportunities or expanded responsibilities.

Entrepreneurial ventures receive particular support through networking events, mentor connections, or unexpected partnerships. The weekly rhythm favors launching new initiatives early in the week and following up with consistent action throughout the seven-day cycle."""
    
    def _generate_monthly_career(self, sign: str, planets: Dict) -> str:
        jupiter_sign = planets['Jupiter']['sign']
        return f"""This month represents a complete professional development cycle, with Jupiter in {jupiter_sign} providing the wisdom and opportunities needed for significant career advancement. Week 1 focuses on assessment and goal-setting. Week 2 brings action and implementation. Week 3 emphasizes refinement and optimization. Week 4 celebrates achievements and plans for future growth.

Major projects reach completion or important milestones, showcasing your skills and dedication to supervisors and clients. This month may bring promotion opportunities, salary increases, or offers from other organizations that recognize your value.

For entrepreneurs and freelancers, this month provides opportunities to expand services, enter new markets, or establish strategic partnerships. The key is balancing ambition with practical execution, ensuring that growth is sustainable and aligned with your long-term vision."""
    
    def _generate_yearly_career(self, sign: str, planets: Dict) -> str:
        jupiter_sign = planets['Jupiter']['sign']
        return f"""This year marks a pivotal chapter in your professional journey, with Jupiter in {jupiter_sign} orchestrating opportunities for significant career evolution. The four-quarter cycle includes foundation building (Q1), expansion and growth (Q2), leadership emergence (Q3), and mastery achievement (Q4).

Major career transitions are likely, whether through promotions within your current organization, career changes that better align with your passions, or entrepreneurial ventures that allow you to be your own boss. Your unique skills and perspective gain recognition from industry leaders and influential mentors.

This year establishes your professional legacy through meaningful work that contributes to both personal fulfillment and collective benefit. Leadership opportunities emerge naturally as others recognize your integrity, vision, and ability to inspire positive change. By year's end, you'll have established yourself as an authority in your chosen field."""

    def _generate_daily_health(self, sign: str, planets: Dict) -> str:
        moon_sign = planets['Moon']['sign']
        mars_sign = planets['Mars']['sign']
        
        return f"""The Moon's nurturing energy in {moon_sign} harmonizes with Mars' vitality in {mars_sign} to create optimal conditions for physical, emotional, and spiritual healing today. Your body's natural intelligence receives cosmic amplification, enhancing its ability to self-regulate and regenerate.

Today marks a significant upgrade in your energy systems as higher frequencies of light integrate into your cellular structure. You may experience increased sensitivity to foods, environments, and people as your vibrational rate elevates. Trust these changes as signs of spiritual evolution rather than health problems.

The planetary alignments favor holistic healing approaches that address root causes rather than symptoms. Your intuition about what your body needs becomes remarkably accurate today, guiding you toward foods, exercises, and healing modalities that support your optimal well-being. Pay attention to dreams and subtle body sensations as they contain important health information.

Stress management becomes crucial as your nervous system adapts to higher cosmic frequencies. Regular meditation, yoga, and time in nature help maintain energetic balance while supporting your body's natural healing processes. Today establishes new patterns of self-care that will serve you well."""
    
    def _generate_weekly_health(self, sign: str, planets: Dict) -> str:
        moon_sign = planets['Moon']['sign']
        return f"""This week's health focus centers on establishing sustainable wellness routines, with the Moon in {moon_sign} guiding your body's natural rhythms. Monday-Tuesday favor detoxification and cleansing practices. Wednesday-Thursday support strength building and energy cultivation. Weekend energy emphasizes rest, recovery, and integration.

Your body's wisdom becomes particularly clear this week, providing specific guidance about nutrition, exercise, and healing practices. Listen carefully to physical sensations and energy levels, adjusting your activities accordingly. Mid-week may bring important insights about long-term health strategies.

This week favors preventive care approaches, including regular check-ups, dental care, and vision assessments. Your immune system receives cosmic support, making this an excellent time to build resilience through proper nutrition, adequate sleep, and stress management techniques."""
    
    def _generate_monthly_health(self, sign: str, planets: Dict) -> str:
        moon_sign = planets['Moon']['sign']
        return f"""This month represents a complete health transformation cycle, with the Moon in {moon_sign} orchestrating your body's natural healing processes. Week 1 focuses on assessment and goal-setting. Week 2 brings implementation of new health practices. Week 3 emphasizes refinement and optimization. Week 4 celebrates progress and plans for continued improvement.

Significant improvements in energy levels, sleep quality, and overall vitality are likely as you align your lifestyle with your body's natural needs. This month may bring breakthrough insights about nutrition, exercise, or healing modalities that dramatically improve your well-being.

Chronic health issues may finally find resolution through holistic approaches that address underlying causes rather than just symptoms. Your body's innate healing abilities receive cosmic amplification, making this an excellent time for recovery and regeneration."""
    
    def _generate_yearly_health(self, sign: str, planets: Dict) -> str:
        moon_sign = planets['Moon']['sign']
        return f"""This year marks a major health evolution cycle, with the Moon in {moon_sign} guiding your body through four seasons of healing and vitality enhancement. Spring brings detoxification and renewal. Summer emphasizes strength building and energy cultivation. Autumn focuses on immune system strengthening and preparation. Winter supports deep healing and regeneration.

Major health transformations are likely as you develop a deeper understanding of your body's unique needs and natural healing abilities. This year may bring resolution of long-standing health issues through integrated approaches that address physical, emotional, and spiritual aspects of wellness.

Your relationship with your body undergoes fundamental transformation as you learn to listen to its wisdom and respond with appropriate care. By year's end, you'll have established sustainable health practices that support not just physical vitality but also emotional balance and spiritual growth."""

    def _generate_daily_finance(self, sign: str, planets: Dict) -> str:
        jupiter_sign = planets['Jupiter']['sign']
        venus_sign = planets['Venus']['sign']
        
        return f"""Jupiter's abundance energy in {jupiter_sign} combines with Venus' magnetism in {venus_sign} to create powerful currents of financial prosperity today. Your relationship with money undergoes a fundamental shift as scarcity consciousness gives way to abundance mindset.

New income opportunities develop naturally as your diverse talents find new markets and applications. The universe supports your financial growth through unexpected opportunities, beneficial partnerships, and the recognition of your true worth. Today marks a turning point where your income begins to reflect your actual value rather than your perceived limitations.

Investment opportunities in technology, healing arts, and consciousness-expanding ventures show exceptional promise. Your intuition about financial matters becomes remarkably accurate today, guiding you toward decisions that support both immediate needs and long-term security. Trust your instincts about timing and value.

The planetary alignments favor conscious spending that aligns with your values and supports your spiritual growth. Money becomes a tool for positive change rather than an end in itself. Your generous spirit attracts reciprocal abundance as the universe responds to your willingness to share your blessings with others."""
    
    def _generate_weekly_finance(self, sign: str, planets: Dict) -> str:
        jupiter_sign = planets['Jupiter']['sign']
        return f"""This week's financial energy builds through strategic daily actions, with Jupiter in {jupiter_sign} expanding your earning potential and investment opportunities. Monday-Tuesday favor financial planning and budget review. Wednesday-Thursday bring income opportunities and important financial decisions. Weekend energy supports investment research and long-term planning.

Multiple income streams may develop as your skills and services gain recognition in new markets. This week favors networking with financially successful individuals who can provide mentorship or partnership opportunities. Mid-week conversations may lead to lucrative collaborations or business ventures.

Investment opportunities require careful analysis but show strong potential for growth. Your financial intuition becomes particularly sharp this week, helping you distinguish between genuine opportunities and risky speculation. Trust your instincts while maintaining practical due diligence."""
    
    def _generate_monthly_finance(self, sign: str, planets: Dict) -> str:
        jupiter_sign = planets['Jupiter']['sign']
        return f"""This month represents a complete financial transformation cycle, with Jupiter in {jupiter_sign} orchestrating opportunities for significant wealth building. Week 1 focuses on financial assessment and goal-setting. Week 2 brings income generation and opportunity development. Week 3 emphasizes investment and wealth building strategies. Week 4 celebrates financial progress and plans for continued growth.

Major financial decisions reach resolution, potentially involving property purchases, business investments, or career changes that significantly impact your earning potential. This month may bring salary increases, bonus payments, or profitable business deals that enhance your financial security.

Your relationship with money matures as you develop more sophisticated strategies for wealth building and financial management. Investment portfolios may require rebalancing, and new opportunities in emerging markets or innovative technologies show exceptional promise for long-term growth."""
    
    def _generate_yearly_finance(self, sign: str, planets: Dict) -> str:
        jupiter_sign = planets['Jupiter']['sign']
        return f"""This year marks a pivotal chapter in your financial evolution, with Jupiter in {jupiter_sign} orchestrating opportunities for significant wealth creation and financial independence. The four-quarter cycle includes foundation building (Q1), income expansion (Q2), investment growth (Q3), and wealth consolidation (Q4).

Major financial milestones are achieved through a combination of increased earning potential, smart investment strategies, and entrepreneurial ventures. This year may bring property acquisitions, business ownership opportunities, or investment returns that substantially increase your net worth.

Your financial consciousness undergoes complete transformation as you develop mastery over money management, investment strategies, and wealth building techniques. By year's end, you'll have established multiple income streams and investment portfolios that provide both security and growth potential for the future."""

    def _generate_universal_influences(self, planets: Dict) -> Dict:
        """Generate universal daily influences that are same for all signs"""
        sun_sign = planets['Sun']['sign']
        mercury_sign = planets['Mercury']['sign']
        moon_longitude = planets['Moon']['longitude']
        sun_longitude = planets['Sun']['longitude']
        
        # Energy Focus based on Sun's current sign
        energy_themes = {
            'Aries': 'Dynamic Action and Leadership',
            'Taurus': 'Stability and Material Security', 
            'Gemini': 'Communication and Learning',
            'Cancer': 'Emotional Nurturing and Home',
            'Leo': 'Creative Expression and Recognition',
            'Virgo': 'Organization and Service',
            'Libra': 'Balance and Relationships',
            'Scorpio': 'Transformation and Deep Insights',
            'Sagittarius': 'Expansion and Higher Wisdom',
            'Capricorn': 'Achievement and Structure',
            'Aquarius': 'Innovation and Humanitarian Ideals',
            'Pisces': 'Intuition and Spiritual Connection'
        }
        
        # Key Theme based on Mercury's current sign
        themes = {
            'Aries': 'Pioneering New Ventures',
            'Taurus': 'Building Lasting Foundations',
            'Gemini': 'Connecting and Communicating',
            'Cancer': 'Nurturing Relationships',
            'Leo': 'Shining Your Authentic Light',
            'Virgo': 'Perfecting Your Craft',
            'Libra': 'Creating Harmony',
            'Scorpio': 'Embracing Transformation',
            'Sagittarius': 'Seeking Truth and Meaning',
            'Capricorn': 'Climbing Toward Success',
            'Aquarius': 'Revolutionary Thinking',
            'Pisces': 'Flowing with Divine Guidance'
        }
        
        # Lunar Phase calculation
        phase_angle = abs(moon_longitude - sun_longitude)
        if phase_angle > 180:
            phase_angle = 360 - phase_angle
            
        if phase_angle < 45:
            lunar_phase = "New Moon - New Beginnings and Fresh Intentions"
        elif phase_angle < 90:
            lunar_phase = "Waxing Crescent - Building Momentum and Taking Action"
        elif phase_angle < 135:
            lunar_phase = "First Quarter - Overcoming Challenges and Making Decisions"
        elif phase_angle < 180:
            lunar_phase = "Waxing Gibbous - Refinement and Preparation"
        else:
            lunar_phase = "Full Moon - Culmination and Manifestation"
        
        return {
            'energy_focus': energy_themes.get(sun_sign, 'Balanced Energy Flow'),
            'key_theme': themes.get(mercury_sign, 'Mindful Progress'),
            'lunar_phase': lunar_phase
        }

    def _generate_detailed_analysis(self, sign: str, planets: Dict, period: str) -> Dict:
        return {
            'planetary_influences': [
                {
                    'planet': 'Jupiter',
                    'influence': f'Expansion of consciousness and material abundance through {planets["Jupiter"]["sign"]} energy',
                    'strength': self._calculate_planet_strength(planets['Jupiter']),
                    'house': self._calculate_house_position(planets['Jupiter']['longitude']),
                    'aspect': 'Trine to natal Sun',
                    'effect': 'Wisdom, teaching opportunities, foreign connections'
                },
                {
                    'planet': 'Saturn',
                    'influence': f'Karmic lessons and structural foundations via {planets["Saturn"]["sign"]} discipline',
                    'strength': self._calculate_planet_strength(planets['Saturn']),
                    'house': self._calculate_house_position(planets['Saturn']['longitude']),
                    'aspect': 'Sextile to Mercury',
                    'effect': 'Disciplined communication, authority recognition'
                },
                {
                    'planet': 'Mars',
                    'influence': f'Dynamic action and courage activation through {planets["Mars"]["sign"]} fire',
                    'strength': self._calculate_planet_strength(planets['Mars']),
                    'house': self._calculate_house_position(planets['Mars']['longitude']),
                    'aspect': 'Conjunction with Ascendant',
                    'effect': 'Leadership emergence, physical vitality'
                }
            ],
            'nakshatra_analysis': {
                'current_nakshatra': planets['Moon']['nakshatra'],
                'deity': self._get_nakshatra_deity(planets['Moon']['nakshatra']),
                'symbol': self._get_nakshatra_symbol(planets['Moon']['nakshatra']),
                'characteristics': self._get_nakshatra_characteristics(planets['Moon']['nakshatra']),
                'spiritual_lesson': self._get_nakshatra_lesson(planets['Moon']['nakshatra']),
                'favorable_activities': self._get_favorable_activities(planets['Moon']['nakshatra']),
                'avoid_activities': self._get_avoid_activities(planets['Moon']['nakshatra'])
            },
            'key_themes': ['Spiritual Evolution', 'Material Abundance', 'Leadership Emergence', 'Relationship Harmony'],
            'challenges': ['Balancing material and spiritual desires', 'Managing increased responsibilities'],
            'opportunities': ['International collaborations', 'Spiritual teaching roles', 'Creative monetization']
        }

    def _calculate_planet_strength(self, planet_data: Dict) -> int:
        # Calculate strength based on sign position, speed, and degree
        base_strength = 50
        
        # Add strength for favorable signs (simplified)
        if planet_data['degree'] < 15:
            base_strength += 20
        else:
            base_strength += 10
            
        # Add strength for speed (direct motion)
        if planet_data['speed'] > 0:
            base_strength += 15
            
        return min(95, max(60, base_strength + random.randint(-10, 20)))

    def _calculate_house_position(self, longitude: float) -> int:
        # Simplified house calculation (would need ascendant for accuracy)
        return int((longitude / 30) % 12) + 1

    def _get_nakshatra_deity(self, nakshatra: str) -> str:
        deities = {
            'Ashwini': 'Ashwini Kumaras - Divine Healers',
            'Bharani': 'Yama - Lord of Death',
            'Krittika': 'Agni - Fire God',
            'Rohini': 'Brahma - The Creator'
        }
        return deities.get(nakshatra, 'Divine Cosmic Force')

    def _get_nakshatra_symbol(self, nakshatra: str) -> str:
        symbols = {
            'Ashwini': 'Horse Head, Golden Chariot',
            'Bharani': 'Yoni, Boat, Elephant',
            'Krittika': 'Razor, Flame, Sharp Object',
            'Rohini': 'Ox Cart, Temple, Banyan Tree'
        }
        return symbols.get(nakshatra, 'Cosmic Symbol')

    def _get_nakshatra_characteristics(self, nakshatra: str) -> str:
        characteristics = {
            'Ashwini': 'Swift action, healing abilities, pioneering spirit',
            'Bharani': 'Transformation, creativity, nurturing power',
            'Krittika': 'Sharp intellect, purification, cutting through illusion',
            'Rohini': 'Material abundance, creative fertility, artistic expression'
        }
        return characteristics.get(nakshatra, 'Divine qualities and cosmic attributes')

    def _get_nakshatra_lesson(self, nakshatra: str) -> str:
        lessons = {
            'Ashwini': 'Learning to heal others while maintaining personal boundaries',
            'Bharani': 'Understanding the cycles of creation and destruction',
            'Krittika': 'Using discernment to separate truth from illusion',
            'Rohini': 'Balancing material desires with spiritual growth'
        }
        return lessons.get(nakshatra, 'Integrating cosmic wisdom into daily life')

    def _get_favorable_activities(self, nakshatra: str) -> list:
        activities = {
            'Ashwini': ['Healing practices', 'New beginnings', 'Travel'],
            'Bharani': ['Creative projects', 'Fertility rituals', 'Transformation work'],
            'Krittika': ['Purification practices', 'Study', 'Cutting ties'],
            'Rohini': ['Business ventures', 'Artistic projects', 'Property investments']
        }
        return activities.get(nakshatra, ['Spiritual practices', 'Creative work', 'Service to others'])

    def _get_avoid_activities(self, nakshatra: str) -> list:
        avoid = {
            'Ashwini': ['Procrastination', 'Ignoring health', 'Reckless behavior'],
            'Bharani': ['Suppressing creativity', 'Avoiding change', 'Harsh criticism'],
            'Krittika': ['Excessive criticism', 'Burning bridges', 'Impatience'],
            'Rohini': ['Impulsive decisions', 'Overindulgence', 'Neglecting spirituality']
        }
        return avoid.get(nakshatra, ['Negative thinking', 'Harmful actions', 'Spiritual neglect'])

    def _calculate_lucky_number(self, planets: Dict) -> int:
        # Calculate based on planetary positions
        total = sum(int(p['longitude']) for p in planets.values())
        return (total % 50) + 1

    def _calculate_lucky_color(self, sign: str, planets: Dict) -> str:
        colors = {
            'Aries': 'Fiery Red', 'Taurus': 'Emerald Green', 'Gemini': 'Golden Yellow',
            'Cancer': 'Pearl White', 'Leo': 'Royal Gold', 'Virgo': 'Earth Brown',
            'Libra': 'Rose Pink', 'Scorpio': 'Deep Crimson', 'Sagittarius': 'Purple',
            'Capricorn': 'Dark Blue', 'Aquarius': 'Electric Blue', 'Pisces': 'Sea Green'
        }
        return colors.get(sign, 'Cosmic Silver')

    def _calculate_cosmic_rating(self, planets: Dict) -> int:
        # Calculate based on planetary strengths
        total_strength = sum(self._calculate_planet_strength(p) for p in planets.values())
        avg_strength = total_strength / len(planets)
        return min(5, max(3, int(avg_strength / 20)))

    def _calculate_cosmic_weather(self, planets: Dict) -> Dict:
        jupiter_strength = self._calculate_planet_strength(planets['Jupiter'])
        mars_strength = self._calculate_planet_strength(planets['Mars'])
        venus_strength = self._calculate_planet_strength(planets['Venus'])
        moon_strength = self._calculate_planet_strength(planets['Moon'])
        
        return {
            'energy_level': mars_strength,
            'manifestation_power': jupiter_strength,
            'intuition_strength': moon_strength,
            'relationship_harmony': venus_strength
        }