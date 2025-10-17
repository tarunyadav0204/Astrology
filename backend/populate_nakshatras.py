import sqlite3

# Initialize database connection
conn = sqlite3.connect('astrology.db')
cursor = conn.cursor()

# Nakshatra data
nakshatras = [
    {
        'name': 'Ashwini',
        'lord': 'Ketu',
        'deity': 'Ashwini Kumaras',
        'nature': 'Light/Swift',
        'guna': 'Rajas',
        'description': 'Ashwini nakshatra, the first among the 27 nakshatras, spans from 0°00\' to 13°20\' in Aries. Ruled by Ketu and presided over by the Ashwini Kumaras (divine physicians), this nakshatra embodies the energy of new beginnings, healing, and swift action. The symbol of Ashwini is a horse\'s head, representing speed, vitality, and the power to traverse great distances quickly. People born under this nakshatra are natural pioneers who possess an innate ability to initiate projects and lead others into uncharted territories.',
        'characteristics': 'Ashwini natives are characterized by their remarkable energy, enthusiasm, and pioneering spirit. They possess a natural inclination towards healing and helping others, often drawn to medical or therapeutic professions. These individuals are quick thinkers and fast actors, rarely hesitating when opportunities arise. They have a magnetic personality that attracts others and natural leadership qualities that inspire confidence. Their restless nature drives them to constantly seek new experiences and challenges. They are independent, self-reliant, and prefer to carve their own path rather than follow conventional routes.',
        'positive_traits': 'Natural healers with intuitive medical knowledge, excellent leadership and pioneering abilities, quick decision-making skills, high energy levels and enthusiasm, strong initiative and entrepreneurial spirit, ability to inspire and motivate others, excellent problem-solving capabilities, natural counselors and advisors, strong sense of justice and fairness, ability to work well under pressure.',
        'negative_traits': 'Tendency towards impatience and restlessness, can be impulsive in decision-making, may appear aggressive or pushy to others, difficulty in maintaining long-term commitments, tendency to start many projects but not complete them, can be overly critical of others\' pace, may neglect personal relationships due to work focus, prone to accidents due to haste, can be stubborn and inflexible at times.',
        'careers': 'Medical professionals (doctors, surgeons, nurses), emergency services personnel, veterinarians, therapists and counselors, entrepreneurs and business leaders, sports professionals and coaches, military and defense services, transportation industry, pharmaceutical industry, alternative healing practitioners, research and development fields.',
        'compatibility': 'Most compatible with Bharani, Krittika, and Rohini nakshatras. Good compatibility with Punarvasu and Pushya. Moderate compatibility with Ashlesha and Magha. Should exercise caution with Ardra and Swati nakshatras.'
    },
    {
        'name': 'Bharani',
        'lord': 'Venus',
        'deity': 'Yama',
        'nature': 'Fierce/Ugra',
        'guna': 'Rajas',
        'description': 'Bharani nakshatra spans from 13°20\' to 26°40\' in Aries and is ruled by Venus with Yama (the god of death and dharma) as its presiding deity. The symbol of Bharani is the yoni (female reproductive organ), representing fertility, creativity, and the power of transformation. This nakshatra embodies the energy of bearing, nurturing, and the cycle of life and death. Bharani represents the womb of creation where ideas, projects, and life itself are conceived and nurtured before birth. It signifies the power to bear responsibility and carry burdens with grace.',
        'characteristics': 'Bharani natives possess extraordinary willpower and the ability to endure hardships with remarkable resilience. They have a deep understanding of life\'s cycles and are naturally drawn to transformative experiences. These individuals are highly creative and possess strong artistic inclinations, often excelling in fields that require imagination and aesthetic sense. They have a natural sense of justice and fairness, making them excellent judges of character and situations. Their nurturing nature makes them protective of their loved ones, and they often take on responsibilities that others might find overwhelming. They possess a magnetic charm and sensuality that attracts others.',
        'positive_traits': 'Exceptional creative and artistic abilities, strong sense of responsibility and duty, natural leadership qualities with protective instincts, ability to endure hardships and overcome obstacles, excellent judgment and decision-making skills, strong moral compass and ethical standards, nurturing and caring nature towards family, ability to transform and regenerate after setbacks, natural business acumen and financial wisdom, strong intuitive and psychic abilities.',
        'negative_traits': 'Tendency towards stubbornness and inflexibility, can be overly possessive and jealous in relationships, may become overly critical and judgmental of others, prone to mood swings and emotional extremes, tendency to hold grudges and seek revenge, can be manipulative when pursuing goals, may struggle with letting go of past hurts, tendency to overindulge in sensual pleasures, can be overly controlling in relationships.',
        'careers': 'Creative arts (music, dance, painting, sculpture), entertainment industry, fashion and beauty industry, law and legal services, judiciary and court systems, psychology and counseling, gynecology and obstetrics, fertility and reproductive health, agriculture and horticulture, food and hospitality industry, real estate and property development, financial services and banking.',
        'compatibility': 'Most compatible with Ashwini, Rohini, and Mrigashira nakshatras. Good compatibility with Krittika and Punarvasu. Moderate compatibility with Pushya and Ashlesha. Should be cautious with Ardra and Jyeshtha nakshatras.'
    },
    {
        'name': 'Krittika',
        'lord': 'Sun',
        'deity': 'Agni',
        'nature': 'Mixed',
        'guna': 'Rajas',
        'description': 'Krittika nakshatra spans from 26°40\' Aries to 10°00\' Taurus, making it unique as it bridges two zodiac signs. Ruled by the Sun and presided over by Agni (the fire god), this nakshatra embodies the power of purification, transformation, and sharp discernment. The symbol of Krittika is a sharp blade or razor, representing the ability to cut through illusion and reveal truth. This nakshatra is associated with the Pleiades star cluster, also known as the Seven Sisters, representing nurturing and protection combined with fierce determination.',
        'characteristics': 'Krittika natives possess razor-sharp intellect and an innate ability to discern truth from falsehood. They have a natural inclination towards perfectionism and high standards in all aspects of life. These individuals are natural critics and analysts, capable of identifying flaws and suggesting improvements with remarkable precision. They possess strong leadership qualities and are not afraid to take charge when situations demand it. Their fiery nature makes them passionate about their beliefs and causes. They have a protective instinct towards those they care about and will fight fiercely to defend their loved ones.',
        'positive_traits': 'Exceptional analytical and critical thinking abilities, strong leadership qualities with natural authority, high standards and pursuit of excellence, ability to purify and improve situations, strong protective instincts towards family and friends, excellent teaching and mentoring capabilities, natural ability to inspire and motivate others, strong sense of justice and fairness, ability to cut through deception and see truth, excellent organizational and management skills.',
        'negative_traits': 'Tendency to be overly critical and harsh in judgment, can be perfectionist to the point of being unrealistic, may appear cold or insensitive to others\' feelings, tendency towards anger and aggressive behavior, can be stubborn and inflexible in opinions, may become overly controlling or dominating, tendency to hold others to impossibly high standards, can be impatient with those who don\'t meet expectations, may struggle with accepting criticism from others.',
        'careers': 'Education and teaching professions, literary criticism and editing, journalism and media, research and analysis, quality control and inspection, military and defense services, law enforcement and security, culinary arts and food criticism, art and design criticism, management and administration, consulting and advisory services, spiritual teaching and guidance.',
        'compatibility': 'Most compatible with Rohini, Mrigashira, and Punarvasu nakshatras. Good compatibility with Bharani and Pushya. Moderate compatibility with Ashwini and Ashlesha. Should exercise caution with Ardra and Swati nakshatras.'
    },
    {
        'name': 'Rohini',
        'lord': 'Moon',
        'deity': 'Brahma',
        'nature': 'Fixed/Dhruva',
        'guna': 'Rajas',
        'description': 'Rohini nakshatra is ruled by the Moon and presided over by Brahma, the creator god.',
        'characteristics': 'Rohini natives are blessed with natural beauty and charm.',
        'positive_traits': 'Natural beauty, artistic abilities, magnetic charm.',
        'negative_traits': 'Materialism, possessiveness, attachment to comforts.',
        'careers': 'Arts, beauty, luxury goods, fashion.',
        'compatibility': 'Most compatible with Mrigashira and Ardra nakshatras.'
    },
    {
        'name': 'Mrigashira',
        'lord': 'Mars',
        'deity': 'Soma',
        'nature': 'Soft/Mridu',
        'guna': 'Tamas',
        'description': 'Mrigashira nakshatra is ruled by Mars and presided over by Soma.',
        'characteristics': 'Mrigashira natives are known for their curious nature and love for exploration.',
        'positive_traits': 'Curiosity, communication skills, gentle nature.',
        'negative_traits': 'Restlessness, indecisiveness, superficial pursuits.',
        'careers': 'Communication, travel, exploration, writing.',
        'compatibility': 'Most compatible with Ardra and Punarvasu nakshatras.'
    },
    {
        'name': 'Ardra',
        'lord': 'Rahu',
        'deity': 'Rudra',
        'nature': 'Sharp/Tikshna',
        'guna': 'Tamas',
        'description': 'Ardra nakshatra is ruled by Rahu and presided over by Rudra.',
        'characteristics': 'Ardra natives are intense, emotional, and transformative individuals.',
        'positive_traits': 'Transformative abilities, sharp intellect, innovative thinking.',
        'negative_traits': 'Emotional instability, destructive tendencies, extremes.',
        'careers': 'Research, investigation, transformation, science.',
        'compatibility': 'Most compatible with Punarvasu and Pushya nakshatras.'
    },
    {
        'name': 'Punarvasu',
        'lord': 'Jupiter',
        'deity': 'Aditi',
        'nature': 'Movable/Chara',
        'guna': 'Rajas',
        'description': 'Punarvasu nakshatra is ruled by Jupiter and presided over by Aditi.',
        'characteristics': 'Punarvasu natives are optimistic, philosophical, and generous.',
        'positive_traits': 'Optimism, generosity, wisdom.',
        'negative_traits': 'Over-optimism, tendency to be preachy.',
        'careers': 'Teaching, counseling, guidance.',
        'compatibility': 'Most compatible with Pushya and Ashlesha nakshatras.'
    },
    {
        'name': 'Pushya',
        'lord': 'Saturn',
        'deity': 'Brihaspati',
        'nature': 'Light/Laghu',
        'guna': 'Rajas',
        'description': 'Pushya nakshatra is ruled by Saturn and presided over by Brihaspati.',
        'characteristics': 'Pushya natives are nurturing, disciplined, and spiritually inclined.',
        'positive_traits': 'Nurturing nature, discipline, spiritual wisdom.',
        'negative_traits': 'Over-conservatism, rigidity, controlling.',
        'careers': 'Teaching, counseling, healthcare.',
        'compatibility': 'Most compatible with Ashlesha and Magha nakshatras.'
    },
    {
        'name': 'Ashlesha',
        'lord': 'Mercury',
        'deity': 'Nagas',
        'nature': 'Sharp/Tikshna',
        'guna': 'Sattva',
        'description': 'Ashlesha nakshatra is ruled by Mercury and presided over by the Nagas.',
        'characteristics': 'Ashlesha natives are intuitive, mysterious, and possess deep psychological insight.',
        'positive_traits': 'Intuitive abilities, psychological insight, healing powers.',
        'negative_traits': 'Manipulative tendencies, secretiveness, emotional instability.',
        'careers': 'Psychology, healing, transformation.',
        'compatibility': 'Most compatible with Jyeshtha and Revati nakshatras.'
    },
    {
        'name': 'Magha',
        'lord': 'Ketu',
        'deity': 'Pitrs',
        'nature': 'Fierce/Ugra',
        'guna': 'Tamas',
        'description': 'Magha nakshatra is ruled by Ketu and presided over by the Pitrs.',
        'characteristics': 'Magha natives are authoritative, proud, and possess natural leadership qualities.',
        'positive_traits': 'Leadership abilities, dignity, respect for tradition.',
        'negative_traits': 'Arrogance, superiority complex, domineering.',
        'careers': 'Politics, government, administration.',
        'compatibility': 'Most compatible with Purva Phalguni and Uttara Phalguni nakshatras.'
    },
    {
        'name': 'Purva Phalguni',
        'lord': 'Venus',
        'deity': 'Bhaga',
        'nature': 'Fierce/Ugra',
        'guna': 'Rajas',
        'description': 'Purva Phalguni nakshatra is ruled by Venus and presided over by Bhaga.',
        'characteristics': 'Purva Phalguni natives are creative, artistic, and pleasure-loving.',
        'positive_traits': 'Creativity, charm, generous nature.',
        'negative_traits': 'Vanity, laziness, overly indulgent.',
        'careers': 'Entertainment, arts, luxury.',
        'compatibility': 'Most compatible with Uttara Phalguni and Hasta nakshatras.'
    },
    {
        'name': 'Uttara Phalguni',
        'lord': 'Sun',
        'deity': 'Aryaman',
        'nature': 'Fixed/Dhruva',
        'guna': 'Rajas',
        'description': 'Uttara Phalguni nakshatra is ruled by the Sun and presided over by Aryaman.',
        'characteristics': 'Uttara Phalguni natives are helpful, supportive, and organized.',
        'positive_traits': 'Helpful nature, organizational skills, beneficial partnerships.',
        'negative_traits': 'Overly dependent on others, difficulty in making independent decisions.',
        'careers': 'Service, organization, support.',
        'compatibility': 'Most compatible with Hasta and Chitra nakshatras.'
    },
    {
        'name': 'Hasta',
        'lord': 'Moon',
        'deity': 'Savitar',
        'nature': 'Light/Laghu',
        'guna': 'Rajas',
        'description': 'Hasta nakshatra is ruled by the Moon and presided over by Savitar.',
        'characteristics': 'Hasta natives are skillful, hardworking, and practical.',
        'positive_traits': 'Exceptional skills, hardworking nature, practical intelligence.',
        'negative_traits': 'Perfectionism, overly critical, too focused on details.',
        'careers': 'Craftsmanship, medical field, skilled work.',
        'compatibility': 'Most compatible with Chitra and Swati nakshatras.'
    },
    {
        'name': 'Chitra',
        'lord': 'Mars',
        'deity': 'Vishvakarma',
        'nature': 'Soft/Mridu',
        'guna': 'Tamas',
        'description': 'Chitra nakshatra is ruled by Mars and presided over by Vishvakarma.',
        'characteristics': 'Chitra natives are creative, artistic, and possess exceptional aesthetic sense.',
        'positive_traits': 'Creativity, artistic abilities, natural charisma.',
        'negative_traits': 'Vanity, superficiality, overly concerned with appearances.',
        'careers': 'Design, arts, beauty.',
        'compatibility': 'Most compatible with Swati and Vishakha nakshatras.'
    },
    {
        'name': 'Swati',
        'lord': 'Rahu',
        'deity': 'Vayu',
        'nature': 'Movable/Chara',
        'guna': 'Tamas',
        'description': 'Swati nakshatra is ruled by Rahu and presided over by Vayu.',
        'characteristics': 'Swati natives are independent, flexible, and diplomatic.',
        'positive_traits': 'Independence, diplomatic skills, business acumen.',
        'negative_traits': 'Restlessness, indecisiveness, superficial relationships.',
        'careers': 'Communication, negotiation, business.',
        'compatibility': 'Most compatible with Vishakha and Anuradha nakshatras.'
    },
    {
        'name': 'Vishakha',
        'lord': 'Jupiter',
        'deity': 'Indragni',
        'nature': 'Mixed',
        'guna': 'Rajas',
        'description': 'Vishakha nakshatra is ruled by Jupiter and presided over by Indra-Agni.',
        'characteristics': 'Vishakha natives are determined, goal-oriented, and ambitious.',
        'positive_traits': 'Determination, leadership abilities, goal-oriented nature.',
        'negative_traits': 'Over-ambition, impatience, ruthless in pursuit of goals.',
        'careers': 'Leadership, determination, goal achievement.',
        'compatibility': 'Most compatible with Anuradha and Jyeshtha nakshatras.'
    },
    {
        'name': 'Anuradha',
        'lord': 'Saturn',
        'deity': 'Mitra',
        'nature': 'Soft/Mridu',
        'guna': 'Tamas',
        'description': 'Anuradha nakshatra is ruled by Saturn and presided over by Mitra.',
        'characteristics': 'Anuradha natives are devoted, friendly, and successful.',
        'positive_traits': 'Devotion, diplomatic skills, organizational abilities.',
        'negative_traits': 'Over-dependence on others, overly accommodating, too trusting.',
        'careers': 'Counseling, diplomacy, organization.',
        'compatibility': 'Most compatible with Jyeshtha and Mula nakshatras.'
    },
    {
        'name': 'Jyeshtha',
        'lord': 'Mercury',
        'deity': 'Indra',
        'nature': 'Sharp/Tikshna',
        'guna': 'Sattva',
        'description': 'Jyeshtha nakshatra is ruled by Mercury and presided over by Indra.',
        'characteristics': 'Jyeshtha natives are protective, authoritative, and responsible.',
        'positive_traits': 'Protective nature, leadership abilities, sense of responsibility.',
        'negative_traits': 'Overly controlling, authoritarian behavior, too critical.',
        'careers': 'Administration, management, protection.',
        'compatibility': 'Most compatible with Mula and Purva Ashadha nakshatras.'
    },
    {
        'name': 'Mula',
        'lord': 'Ketu',
        'deity': 'Nirriti',
        'nature': 'Sharp/Tikshna',
        'guna': 'Tamas',
        'description': 'Mula nakshatra is ruled by Ketu and presided over by Nirriti.',
        'characteristics': 'Mula natives are investigative, research-oriented, and philosophical.',
        'positive_traits': 'Investigative abilities, philosophical nature, transformative power.',
        'negative_traits': 'Destructive tendencies, restlessness, overly critical.',
        'careers': 'Research, investigation, transformation.',
        'compatibility': 'Most compatible with Purva Ashadha and Uttara Ashadha nakshatras.'
    },
    {
        'name': 'Purva Ashadha',
        'lord': 'Venus',
        'deity': 'Apas',
        'nature': 'Fierce/Ugra',
        'guna': 'Rajas',
        'description': 'Purva Ashadha nakshatra is ruled by Venus and presided over by Apas.',
        'characteristics': 'Purva Ashadha natives are invincible, purifying, and influential.',
        'positive_traits': 'Invincible spirit, purifying abilities, influential nature.',
        'negative_traits': 'Excessive pride, stubbornness, overly argumentative.',
        'careers': 'Debate, law, influence.',
        'compatibility': 'Most compatible with Uttara Ashadha and Shravana nakshatras.'
    },
    {
        'name': 'Uttara Ashadha',
        'lord': 'Sun',
        'deity': 'Vishvedevas',
        'nature': 'Fixed/Dhruva',
        'guna': 'Rajas',
        'description': 'Uttara Ashadha nakshatra is ruled by the Sun and presided over by the Vishvadevas.',
        'characteristics': 'Uttara Ashadha natives are victorious, righteous, and possess strong leadership qualities.',
        'positive_traits': 'Determination, ethical nature, leadership abilities.',
        'negative_traits': 'Stubbornness, inflexibility, overly serious.',
        'careers': 'Leadership, ethics, long-term achievement.',
        'compatibility': 'Most compatible with Shravana and Dhanishta nakshatras.'
    },
    {
        'name': 'Shravana',
        'lord': 'Moon',
        'deity': 'Vishnu',
        'nature': 'Movable/Chara',
        'guna': 'Rajas',
        'description': 'Shravana nakshatra is ruled by the Moon and presided over by Vishnu.',
        'characteristics': 'Shravana natives are excellent listeners, knowledgeable, and wise.',
        'positive_traits': 'Listening abilities, scholarly nature, communication skills.',
        'negative_traits': 'Overly talkative, gossipy nature, too focused on information.',
        'careers': 'Education, communication, knowledge preservation.',
        'compatibility': 'Most compatible with Dhanishta and Shatabhisha nakshatras.'
    },
    {
        'name': 'Dhanishta',
        'lord': 'Mars',
        'deity': 'Vasus',
        'nature': 'Movable/Chara',
        'guna': 'Tamas',
        'description': 'Dhanishta nakshatra is ruled by Mars and presided over by the Vasus.',
        'characteristics': 'Dhanishta natives are sociable, adaptable, and vibrant.',
        'positive_traits': 'Sociability, adaptability, vibrant personality.',
        'negative_traits': 'Easy susceptibility to influence, aggression, materialism.',
        'careers': 'Performing arts, management, entrepreneurship.',
        'compatibility': 'Most compatible with Shatabhisha and Purva Bhadrapada nakshatras.'
    },
    {
        'name': 'Shatabhisha',
        'lord': 'Rahu',
        'deity': 'Varuna',
        'nature': 'Movable/Chara',
        'guna': 'Tamas',
        'description': 'Shatabhisha nakshatra is ruled by Rahu and presided over by Varuna.',
        'characteristics': 'Shatabhisha natives possess natural healing abilities and are independent, mysterious individuals.',
        'positive_traits': 'Healing abilities, independent nature, research skills.',
        'negative_traits': 'Overly secretive, stubborn nature, too unconventional.',
        'careers': 'Healing, research, unconventional fields.',
        'compatibility': 'Most compatible with Purva Bhadrapada and Uttara Bhadrapada nakshatras.'
    },
    {
        'name': 'Purva Bhadrapada',
        'lord': 'Jupiter',
        'deity': 'Aja Ekapada',
        'nature': 'Fierce/Ugra',
        'guna': 'Rajas',
        'description': 'Purva Bhadrapada nakshatra is ruled by Jupiter and presided over by Aja Ekapada.',
        'characteristics': 'Purva Bhadrapada natives are transformative, spiritual, and intense individuals.',
        'positive_traits': 'Transformative abilities, spiritual wisdom, philosophical nature.',
        'negative_traits': 'Tendency towards extremes, unpredictable behavior, overly intense.',
        'careers': 'Spirituality, philosophy, transformation.',
        'compatibility': 'Most compatible with Uttara Bhadrapada and Revati nakshatras.'
    },
    {
        'name': 'Uttara Bhadrapada',
        'lord': 'Saturn',
        'deity': 'Ahir Budhnya',
        'nature': 'Fixed/Dhruva',
        'guna': 'Tamas',
        'description': 'Uttara Bhadrapada nakshatra is ruled by Saturn and presided over by Ahir Budhnya.',
        'characteristics': 'Uttara Bhadrapada natives are deep, stable, and wise individuals.',
        'positive_traits': 'Depth, stability, wisdom.',
        'negative_traits': 'Overly serious, pessimistic outlook, too slow to act.',
        'careers': 'Planning, spirituality, depth work.',
        'compatibility': 'Most compatible with Revati and Ashwini nakshatras.'
    },
    {
        'name': 'Revati',
        'lord': 'Mercury',
        'deity': 'Pushan',
        'nature': 'Soft/Mridu',
        'guna': 'Sattva',
        'description': 'Revati nakshatra is ruled by Mercury and presided over by Pushan.',
        'characteristics': 'Revati natives are nourishing, prosperous, and protective individuals.',
        'positive_traits': 'Nourishing nature, prosperity consciousness, protective instincts.',
        'negative_traits': 'Overly protective, possessive nature, too giving.',
        'careers': 'Nourishment, travel, completion work.',
        'compatibility': 'Most compatible with Ashwini and Bharani nakshatras.'
    }
]

# Insert nakshatras into database
count = 0
for nakshatra in nakshatras:
    cursor.execute('''
        INSERT OR REPLACE INTO nakshatras 
        (name, lord, deity, nature, guna, description, characteristics, 
         positive_traits, negative_traits, careers, compatibility)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        nakshatra['name'], nakshatra['lord'], nakshatra['deity'],
        nakshatra['nature'], nakshatra['guna'], nakshatra['description'],
        nakshatra['characteristics'], nakshatra['positive_traits'],
        nakshatra['negative_traits'], nakshatra['careers'],
        nakshatra['compatibility']
    ))
    count += 1

conn.commit()
conn.close()

print(f"Successfully populated {count} nakshatras in the database!")