import sqlite3

conn = sqlite3.connect('astrology.db')
cursor = conn.cursor()

# Complete detailed data for all 27 nakshatras
nakshatras = [
    {
        'name': 'Ashwini',
        'lord': 'Ketu',
        'deity': 'Ashwini Kumaras',
        'nature': 'Light/Swift',
        'guna': 'Rajas',
        'description': 'Ashwini nakshatra spans from 0°00\' to 13°20\' in Aries, ruled by Ketu with the Ashwini Kumaras as presiding deities. The symbol is a horse\'s head, representing speed, vitality, and healing power. This nakshatra embodies new beginnings, pioneering spirit, and the divine physicians\' healing energy.',
        'characteristics': 'Ashwini natives are natural pioneers with exceptional healing abilities and leadership qualities. They possess boundless energy, quick decision-making skills, and magnetic personalities that inspire others. Their restless nature drives constant exploration and innovation.',
        'positive_traits': 'Natural healing abilities, pioneering leadership, quick decision-making, high energy levels, entrepreneurial spirit, ability to inspire others, excellent problem-solving, natural counseling skills, strong sense of justice, works well under pressure.',
        'negative_traits': 'Impatience and restlessness, impulsive decisions, can appear aggressive, difficulty with long-term commitments, starts projects without finishing, overly critical of others\' pace, neglects relationships for work, prone to accidents from haste.',
        'careers': 'Medical professionals, emergency services, veterinarians, therapists, entrepreneurs, sports professionals, military services, transportation, pharmaceuticals, alternative healing, research and development.',
        'compatibility': 'Most compatible with Bharani, Krittika, Rohini. Good with Punarvasu, Pushya. Moderate with Ashlesha, Magha. Caution with Ardra, Swati.'
    },
    {
        'name': 'Bharani',
        'lord': 'Venus',
        'deity': 'Yama',
        'nature': 'Fierce/Ugra',
        'guna': 'Rajas',
        'description': 'Bharani nakshatra spans from 13°20\' to 26°40\' in Aries, ruled by Venus with Yama as deity. The symbol is the yoni, representing fertility, creativity, and life-death cycles. This nakshatra embodies bearing responsibility, transformation, and creative power.',
        'characteristics': 'Bharani natives possess extraordinary willpower and resilience. They understand life\'s cycles deeply and excel in creative fields. Natural sense of justice makes them excellent judges. Their nurturing nature combined with protective instincts creates magnetic personalities.',
        'positive_traits': 'Exceptional creative abilities, strong responsibility sense, natural leadership with protection, endures hardships well, excellent judgment skills, strong moral compass, nurturing family nature, transforms after setbacks, business acumen, intuitive abilities.',
        'negative_traits': 'Stubbornness and inflexibility, possessive and jealous, overly critical of others, mood swings and extremes, holds grudges and seeks revenge, manipulative when pursuing goals, struggles letting go, overindulges in pleasures, controlling in relationships.',
        'careers': 'Creative arts, entertainment, fashion and beauty, law and legal services, judiciary, psychology, gynecology, fertility health, agriculture, food industry, real estate, financial services.',
        'compatibility': 'Most compatible with Ashwini, Rohini, Mrigashira. Good with Krittika, Punarvasu. Moderate with Pushya, Ashlesha. Caution with Ardra, Jyeshtha.'
    },
    {
        'name': 'Krittika',
        'lord': 'Sun',
        'deity': 'Agni',
        'nature': 'Mixed',
        'guna': 'Rajas',
        'description': 'Krittika nakshatra spans from 26°40\' Aries to 10°00\' Taurus, ruled by the Sun with Agni as deity. The symbol is a sharp blade, representing purification and discernment. Associated with the Pleiades, it combines nurturing protection with fierce determination.',
        'characteristics': 'Krittika natives possess razor-sharp intellect and natural perfectionism. They are natural critics and analysts with strong leadership qualities. Their fiery nature makes them passionate about beliefs while maintaining protective instincts toward loved ones.',
        'positive_traits': 'Exceptional analytical abilities, strong leadership with authority, high standards and excellence pursuit, purifies and improves situations, protective family instincts, excellent teaching capabilities, inspires and motivates others, strong justice sense, sees through deception, organizational skills.',
        'negative_traits': 'Overly critical and harsh judgment, perfectionist to unrealistic levels, appears cold or insensitive, tendency toward anger, stubborn in opinions, overly controlling, holds others to impossible standards, impatient with underperformers, struggles accepting criticism.',
        'careers': 'Education and teaching, literary criticism, journalism, research and analysis, quality control, military services, law enforcement, culinary arts, art criticism, management, consulting, spiritual teaching.',
        'compatibility': 'Most compatible with Rohini, Mrigashira, Punarvasu. Good with Bharani, Pushya. Moderate with Ashwini, Ashlesha. Caution with Ardra, Swati.'
    },
    {
        'name': 'Rohini',
        'lord': 'Moon',
        'deity': 'Brahma',
        'nature': 'Fixed/Dhruva',
        'guna': 'Rajas',
        'description': 'Rohini nakshatra spans from 10°00\' to 23°20\' in Taurus, ruled by the Moon with Brahma as deity. The symbol is a chariot, representing material progress and fertility. This auspicious nakshatra embodies beauty, charm, and material abundance.',
        'characteristics': 'Rohini natives are blessed with natural beauty and magnetic charm. They possess strong artistic sensibilities and appreciation for luxury. Their nurturing nature and fixed determination help them achieve material prosperity while maintaining harmony.',
        'positive_traits': 'Natural beauty and charm, exceptional artistic abilities, strong nurturing instincts, attracts wealth and prosperity, excellent aesthetic taste, natural healing abilities, strong determination, creates relationship harmony, business sense for luxury, gardening abilities.',
        'negative_traits': 'Materialism and possession attachment, overindulgent in pleasures, possessive and jealous, stubborn and change-resistant, overly concerned with appearance, struggles letting go of relationships, lazy when comfortable, manipulative for desires, unrealistic expectations.',
        'careers': 'Fashion and beauty, jewelry and luxury goods, interior design, agriculture, food and culinary arts, entertainment, hospitality, real estate, banking, cosmetics, art dealing.',
        'compatibility': 'Most compatible with Mrigashira, Ardra, Punarvasu. Good with Krittika, Pushya. Moderate with Bharani, Ashlesha. Caution with Swati, Vishakha.'
    },
    {
        'name': 'Mrigashira',
        'lord': 'Mars',
        'deity': 'Soma',
        'nature': 'Soft/Mridu',
        'guna': 'Tamas',
        'description': 'Mrigashira nakshatra spans from 23°20\' Taurus to 6°40\' Gemini, ruled by Mars with Soma as deity. The symbol is a deer\'s head, representing gentleness and eternal seeking. This nakshatra embodies the quest for knowledge and new experiences.',
        'characteristics': 'Mrigashira natives possess insatiable curiosity and love for exploration. They combine gentle, refined nature with restless energy. Excellent communicators with natural adaptability, they maintain youthful appearance and demeanor throughout life.',
        'positive_traits': 'Exceptional curiosity and learning love, excellent communication skills, natural adaptability, gentle and refined nature, good analytical abilities, natural networking skills, youthful energy, sees multiple perspectives, travel and exploration instincts, teaching abilities.',
        'negative_traits': 'Restlessness and inability to settle, superficial in relationships, lacks focus and direction, indecisive and changeable, overly critical and fault-finding, struggles completing projects, suspicious and doubtful, overly talkative, difficulty with deep connections.',
        'careers': 'Travel and tourism, journalism, research, education, communication, sales and marketing, writing, translation, exploration sports, consulting, information technology.',
        'compatibility': 'Most compatible with Ardra, Punarvasu, Pushya. Good with Rohini, Ashlesha. Moderate with Krittika, Magha. Caution with Bharani, Jyeshtha.'
    },
    {
        'name': 'Ardra',
        'lord': 'Rahu',
        'deity': 'Rudra',
        'nature': 'Sharp/Tikshna',
        'guna': 'Tamas',
        'description': 'Ardra nakshatra spans from 6°40\' to 20°00\' in Gemini, ruled by Rahu with Rudra as deity. The symbol is a teardrop or diamond, representing transformation through destruction. This nakshatra embodies the storm that clears for new growth.',
        'characteristics': 'Ardra natives are intense, emotional individuals with transformative abilities. They possess sharp intellect and innovative thinking, often bringing revolutionary changes. They have the power to destroy old patterns and create new ones.',
        'positive_traits': 'Transformative abilities, sharp intellect, innovative thinking, brings positive change, strong research capabilities, natural healing abilities, sees through deception, strong intuitive powers, excellent problem-solving, helps others transform.',
        'negative_traits': 'Emotional instability, destructive tendencies, tendency toward extremes, overly critical nature, anger management issues, rebellious behavior, unpredictable nature, difficulty with authority, tendency toward depression.',
        'careers': 'Research and investigation, psychology, medicine and healing, technology innovation, environmental sciences, disaster management, transformation consulting, spiritual healing, alternative therapies, scientific research.',
        'compatibility': 'Most compatible with Punarvasu, Pushya, Ashlesha. Good with Mrigashira, Magha. Moderate with Rohini, Purva Phalguni. Caution with Krittika, Bharani.'
    },
    {
        'name': 'Punarvasu',
        'lord': 'Jupiter',
        'deity': 'Aditi',
        'nature': 'Movable/Chara',
        'guna': 'Rajas',
        'description': 'Punarvasu nakshatra spans from 20°00\' Gemini to 3°20\' Cancer, ruled by Jupiter with Aditi as deity. The symbol is a quiver of arrows or house, representing return to source and renewal. This nakshatra embodies restoration and renewal.',
        'characteristics': 'Punarvasu natives are optimistic, philosophical individuals with strong moral values. They possess the ability to bounce back from setbacks and help others do the same. Natural teachers and guides with wisdom beyond their years.',
        'positive_traits': 'Optimism and positive outlook, generosity and giving nature, wisdom and philosophical thinking, recovers from setbacks, natural teaching abilities, strong moral compass, inspires others, excellent counseling skills, spiritual inclinations, protective nature.',
        'negative_traits': 'Over-optimism leading to unrealistic expectations, tendency to be preachy, overly trusting nature, struggles with material ambitions, repeats past mistakes, overly generous to detriment, lacks practical approach, lives in idealistic world.',
        'careers': 'Teaching and education, counseling, spiritual services, philosophy, social work, publishing, travel and hospitality, healing and therapy, consulting, non-profit organizations.',
        'compatibility': 'Most compatible with Pushya, Ashlesha, Magha. Good with Ardra, Purva Phalguni. Moderate with Mrigashira, Uttara Phalguni. Caution with Swati, Vishakha.'
    },
    {
        'name': 'Pushya',
        'lord': 'Saturn',
        'deity': 'Brihaspati',
        'nature': 'Light/Laghu',
        'guna': 'Rajas',
        'description': 'Pushya nakshatra spans from 3°20\' to 16°40\' in Cancer, ruled by Saturn with Brihaspati as deity. The symbol is a cow\'s udder or lotus, representing nourishment and spiritual growth. This is one of the most auspicious nakshatras.',
        'characteristics': 'Pushya natives are nurturing, disciplined individuals with strong family values. They possess natural wisdom and ability to guide others spiritually. Patient, persistent, with strong organizational abilities and deep spiritual inclinations.',
        'positive_traits': 'Nurturing and caring nature, strong spiritual inclinations, excellent organizational abilities, natural wisdom and guidance, strong family values, provides emotional support, disciplined life approach, natural teaching abilities, creates harmony, strong moral foundation.',
        'negative_traits': 'Over-conservatism and change resistance, tendency to be controlling, overly rigid thinking, struggles with modern approaches, tendency toward pessimism, overly protective nature, difficulty expressing emotions, worries excessively.',
        'careers': 'Teaching and education, spiritual services, counseling and therapy, healthcare and nursing, social work, agriculture, food and nutrition, childcare, traditional healing, government service.',
        'compatibility': 'Most compatible with Ashlesha, Magha, Purva Phalguni. Good with Punarvasu, Uttara Phalguni. Moderate with Ardra, Hasta. Caution with Swati, Vishakha.'
    },
    {
        'name': 'Ashlesha',
        'lord': 'Mercury',
        'deity': 'Nagas',
        'nature': 'Sharp/Tikshna',
        'guna': 'Sattva',
        'description': 'Ashlesha nakshatra spans from 16°40\' to 30°00\' in Cancer, ruled by Mercury with Nagas as deities. The symbol is a coiled serpent, representing kundalini energy and transformation. This nakshatra embodies mystical wisdom and psychological insight.',
        'characteristics': 'Ashlesha natives are intuitive, mysterious individuals with deep psychological insight. They possess natural healing abilities and understanding of human psychology. Their penetrating mind can see through deceptions and hidden motives.',
        'positive_traits': 'Intuitive abilities, psychological insight, natural healing powers, sees through deception, excellent counseling skills, mystical wisdom, transformative abilities, protective instincts, research capabilities, spiritual healing powers.',
        'negative_traits': 'Manipulative tendencies, secretive nature, emotional instability, tendency toward revenge, overly suspicious, can be deceptive, struggles with trust, tendency toward isolation, mood swings, vindictive behavior.',
        'careers': 'Psychology and counseling, mystical and occult sciences, healing and therapy, research and investigation, medicine, spiritual guidance, detective work, psychiatry, alternative healing, esoteric studies.',
        'compatibility': 'Most compatible with Jyeshtha, Revati, Magha. Good with Pushya, Purva Phalguni. Moderate with Punarvasu, Uttara Phalguni. Caution with Mrigashira, Swati.'
    },
    {
        'name': 'Magha',
        'lord': 'Ketu',
        'deity': 'Pitrs',
        'nature': 'Fierce/Ugra',
        'guna': 'Tamas',
        'description': 'Magha nakshatra spans from 0°00\' to 13°20\' in Leo, ruled by Ketu with Pitrs as deities. The symbol is a royal throne, representing authority and ancestral power. This nakshatra embodies royal dignity and connection to ancestors.',
        'characteristics': 'Magha natives are authoritative, proud individuals with natural leadership qualities. They have deep respect for tradition and strong connection to ancestral lineage. Their regal bearing and dignity command respect from others.',
        'positive_traits': 'Natural leadership abilities, dignity and royal bearing, respect for tradition, strong ancestral connections, protective instincts, organizational skills, ability to command respect, generous nature, strong moral values, ceremonial abilities.',
        'negative_traits': 'Arrogance and superiority complex, domineering behavior, overly traditional thinking, resistance to change, tendency toward pride, can be authoritarian, struggles with equality, overly concerned with status, inflexible attitudes.',
        'careers': 'Politics and government, administration, ceremonial roles, traditional arts, genealogy, history, archaeology, royal services, luxury goods, heritage preservation, leadership positions.',
        'compatibility': 'Most compatible with Purva Phalguni, Uttara Phalguni, Hasta. Good with Pushya, Ashlesha. Moderate with Punarvasu, Chitra. Caution with Ardra, Swati.'
    },
    {
        'name': 'Purva Phalguni',
        'lord': 'Venus',
        'deity': 'Bhaga',
        'nature': 'Fierce/Ugra',
        'guna': 'Rajas',
        'description': 'Purva Phalguni nakshatra spans from 13°20\' to 26°40\' in Leo, ruled by Venus with Bhaga as deity. The symbol is a hammock or bed, representing relaxation and pleasure. This nakshatra embodies creativity, luxury, and enjoyment.',
        'characteristics': 'Purva Phalguni natives are creative, artistic individuals who love pleasure and luxury. They possess natural charm and generosity, often excelling in entertainment fields. Their love for beauty and comfort drives their life choices.',
        'positive_traits': 'Exceptional creativity and artistic abilities, natural charm and charisma, generous and giving nature, appreciation for beauty, entertainment talents, social skills, romantic nature, luxury appreciation, hospitality, creative problem-solving.',
        'negative_traits': 'Vanity and ego issues, laziness and complacency, overly indulgent lifestyle, tendency toward extravagance, can be superficial, avoids hard work, overly dependent on others, tendency toward procrastination, materialistic focus.',
        'careers': 'Entertainment industry, arts and creativity, fashion and beauty, hospitality, luxury goods, event management, interior design, music and dance, theater, recreational services.',
        'compatibility': 'Most compatible with Uttara Phalguni, Hasta, Chitra. Good with Magha, Swati. Moderate with Ashlesha, Vishakha. Caution with Ardra, Mula.'
    },
    {
        'name': 'Uttara Phalguni',
        'lord': 'Sun',
        'deity': 'Aryaman',
        'nature': 'Fixed/Dhruva',
        'guna': 'Rajas',
        'description': 'Uttara Phalguni nakshatra spans from 26°40\' Leo to 10°00\' Virgo, ruled by the Sun with Aryaman as deity. The symbol is a bed or hammock, representing support and partnership. This nakshatra embodies helpful service and beneficial relationships.',
        'characteristics': 'Uttara Phalguni natives are helpful, supportive individuals with excellent organizational skills. They excel in partnerships and collaborative efforts. Their generous nature and desire to help others makes them valuable team members.',
        'positive_traits': 'Helpful and supportive nature, excellent organizational skills, beneficial partnerships, generous and kind heart, natural counseling abilities, creates harmony, reliable and dependable, good team player, service-oriented, diplomatic skills.',
        'negative_traits': 'Overly dependent on others, difficulty making independent decisions, can be taken advantage of, tendency to be indecisive, avoids confrontation, may lack assertiveness, overly accommodating, struggles with leadership, dependent personality.',
        'careers': 'Service industries, counseling and support, partnership businesses, organizational roles, human resources, social services, healthcare support, administrative roles, diplomatic services, collaborative projects.',
        'compatibility': 'Most compatible with Hasta, Chitra, Swati. Good with Purva Phalguni, Vishakha. Moderate with Magha, Anuradha. Caution with Ashlesha, Mula.'
    },
    {
        'name': 'Hasta',
        'lord': 'Moon',
        'deity': 'Savitar',
        'nature': 'Light/Laghu',
        'guna': 'Rajas',
        'description': 'Hasta nakshatra spans from 10°00\' to 23°20\' in Virgo, ruled by the Moon with Savitar as deity. The symbol is a hand, representing skill and craftsmanship. This nakshatra embodies dexterity, healing touch, and practical abilities.',
        'characteristics': 'Hasta natives are skillful, hardworking individuals with exceptional practical intelligence. They possess healing hands and natural craftsmanship abilities. Their attention to detail and perfectionist nature leads to excellence in chosen fields.',
        'positive_traits': 'Exceptional skills and craftsmanship, hardworking nature, practical intelligence, healing touch abilities, attention to detail, perfectionist approach, natural healing abilities, excellent hand-eye coordination, problem-solving skills, reliable work ethic.',
        'negative_traits': 'Perfectionism to fault, overly critical nature, too focused on details, can be nitpicky, tendency toward worry, overly cautious approach, struggles with big picture, can be inflexible, tendency toward anxiety, overly self-critical.',
        'careers': 'Craftsmanship and skilled trades, medical and healing professions, surgery, massage therapy, artisan work, precision manufacturing, quality control, detailed analysis, handicrafts, technical skills.',
        'compatibility': 'Most compatible with Chitra, Swati, Vishakha. Good with Uttara Phalguni, Anuradha. Moderate with Purva Phalguni, Jyeshtha. Caution with Magha, Mula.'
    },
    {
        'name': 'Chitra',
        'lord': 'Mars',
        'deity': 'Vishvakarma',
        'nature': 'Soft/Mridu',
        'guna': 'Tamas',
        'description': 'Chitra nakshatra spans from 23°20\' Virgo to 6°40\' Libra, ruled by Mars with Vishvakarma as deity. The symbol is a bright jewel or pearl, representing beauty and craftsmanship. This nakshatra embodies artistic creation and aesthetic perfection.',
        'characteristics': 'Chitra natives are creative, artistic individuals with exceptional aesthetic sense. They possess natural charisma and ability to create beautiful things. Their eye for detail and artistic vision makes them excellent designers and creators.',
        'positive_traits': 'Exceptional creativity and artistic abilities, natural charisma and charm, aesthetic sense and eye for beauty, craftsmanship abilities, innovative thinking, attention to visual details, natural design sense, ability to inspire others, creative problem-solving, artistic vision.',
        'negative_traits': 'Vanity and ego about appearance, superficiality in relationships, overly concerned with looks, can be materialistic, tendency toward showing off, may lack depth, overly focused on external beauty, can be manipulative, tendency toward jealousy.',
        'careers': 'Design and architecture, fashion industry, jewelry design, visual arts, photography, interior decoration, cosmetics, beauty industry, creative advertising, artistic crafts.',
        'compatibility': 'Most compatible with Swati, Vishakha, Anuradha. Good with Hasta, Jyeshtha. Moderate with Uttara Phalguni, Mula. Caution with Purva Phalguni, Purva Ashadha.'
    },
    {
        'name': 'Swati',
        'lord': 'Rahu',
        'deity': 'Vayu',
        'nature': 'Movable/Chara',
        'guna': 'Tamas',
        'description': 'Swati nakshatra spans from 6°40\' to 20°00\' in Libra, ruled by Rahu with Vayu as deity. The symbol is a young shoot blown by wind, representing independence and flexibility. This nakshatra embodies freedom, movement, and adaptability.',
        'characteristics': 'Swati natives are independent, flexible individuals with strong diplomatic skills. They value freedom above all and possess natural business acumen. Their adaptable nature helps them succeed in various environments and situations.',
        'positive_traits': 'Independence and self-reliance, diplomatic skills and tact, business acumen and trade abilities, flexibility and adaptability, natural negotiation skills, ability to maintain balance, social networking abilities, communication skills, entrepreneurial spirit, peaceful nature.',
        'negative_traits': 'Restlessness and inability to settle, indecisiveness and changeability, superficial relationships, tendency to be scattered, avoids deep commitments, can be opportunistic, lacks consistency, tendency toward materialism, may be unreliable.',
        'careers': 'Business and trade, diplomacy and international relations, communication services, travel industry, sales and marketing, negotiation services, import-export, consulting, mediation, networking businesses.',
        'compatibility': 'Most compatible with Vishakha, Anuradha, Jyeshtha. Good with Chitra, Mula. Moderate with Hasta, Purva Ashadha. Caution with Ashwini, Magha.'
    },
    {
        'name': 'Vishakha',
        'lord': 'Jupiter',
        'deity': 'Indragni',
        'nature': 'Mixed',
        'guna': 'Rajas',
        'description': 'Vishakha nakshatra spans from 20°00\' Libra to 3°20\' Scorpio, ruled by Jupiter with Indra-Agni as deities. The symbol is a triumphal arch or forked branch, representing achievement and determination. This nakshatra embodies goal-oriented success.',
        'characteristics': 'Vishakha natives are determined, goal-oriented individuals with strong ambition. They possess natural leadership abilities and unwavering focus on objectives. Their competitive spirit and persistence lead to eventual success in chosen fields.',
        'positive_traits': 'Strong determination and goal focus, natural leadership abilities, competitive spirit and drive, ability to achieve objectives, persistent nature, inspirational qualities, strategic thinking, ability to overcome obstacles, ambitious nature, motivational skills.',
        'negative_traits': 'Over-ambition leading to ruthlessness, impatience with slow progress, can be overly competitive, tendency to be aggressive, may ignore others\' needs, single-minded focus, can be manipulative, tendency toward jealousy, workaholic tendencies.',
        'careers': 'Leadership positions, competitive sports, business management, politics, military services, project management, goal-oriented consulting, achievement coaching, strategic planning, executive roles.',
        'compatibility': 'Most compatible with Anuradha, Jyeshtha, Mula. Good with Swati, Purva Ashadha. Moderate with Chitra, Uttara Ashadha. Caution with Hasta, Rohini.'
    },
    {
        'name': 'Anuradha',
        'lord': 'Saturn',
        'deity': 'Mitra',
        'nature': 'Soft/Mridu',
        'guna': 'Tamas',
        'description': 'Anuradha nakshatra spans from 3°20\' to 16°40\' in Scorpio, ruled by Saturn with Mitra as deity. The symbol is a lotus flower or triumphal archway, representing devotion and success through friendship. This nakshatra embodies loyal friendship and devotion.',
        'characteristics': 'Anuradha natives are devoted, friendly individuals who achieve success through relationships. They possess excellent diplomatic skills and organizational abilities. Their loyal nature and ability to build lasting friendships opens many doors.',
        'positive_traits': 'Devotion and loyalty, excellent diplomatic skills, organizational abilities, ability to build lasting friendships, success through relationships, natural counseling abilities, harmonious nature, ability to bring people together, supportive nature, spiritual inclinations.',
        'negative_traits': 'Over-dependence on others, overly accommodating nature, too trusting of others, difficulty saying no, can be taken advantage of, avoids confrontation, may lack assertiveness, tendency to sacrifice own needs, dependent personality.',
        'careers': 'Counseling and mediation, diplomatic services, organizational roles, human resources, social work, relationship counseling, team building, collaborative projects, spiritual guidance, community services.',
        'compatibility': 'Most compatible with Jyeshtha, Mula, Purva Ashadha. Good with Vishakha, Uttara Ashadha. Moderate with Swati, Shravana. Caution with Chitra, Hasta.'
    },
    {
        'name': 'Jyeshtha',
        'lord': 'Mercury',
        'deity': 'Indra',
        'nature': 'Sharp/Tikshna',
        'guna': 'Sattva',
        'description': 'Jyeshtha nakshatra spans from 16°40\' to 30°00\' in Scorpio, ruled by Mercury with Indra as deity. The symbol is a circular amulet or earring, representing protection and seniority. This nakshatra embodies protective authority and elder wisdom.',
        'characteristics': 'Jyeshtha natives are protective, authoritative individuals with strong sense of responsibility. They naturally take on elder roles and possess wisdom beyond their years. Their protective instincts and leadership abilities make them natural guardians.',
        'positive_traits': 'Protective nature and strong responsibility, natural leadership abilities, elder wisdom and maturity, ability to take charge, strong organizational skills, natural authority, ability to guide others, protective instincts, sense of duty, administrative abilities.',
        'negative_traits': 'Overly controlling behavior, authoritarian tendencies, too critical of others, can be domineering, tendency toward pride, may be inflexible, struggles with delegation, overly protective, can be judgmental, tendency toward superiority.',
        'careers': 'Administration and management, protective services, elder care, government positions, security services, supervisory roles, organizational leadership, protective industries, authority positions, guidance counseling.',
        'compatibility': 'Most compatible with Mula, Purva Ashadha, Uttara Ashadha. Good with Anuradha, Shravana. Moderate with Vishakha, Dhanishta. Caution with Bharani, Mrigashira.'
    },
    {
        'name': 'Mula',
        'lord': 'Ketu',
        'deity': 'Nirriti',
        'nature': 'Sharp/Tikshna',
        'guna': 'Tamas',
        'description': 'Mula nakshatra spans from 0°00\' to 13°20\' in Sagittarius, ruled by Ketu with Nirriti as deity. The symbol is a bunch of roots or lion\'s tail, representing foundation and investigation. This nakshatra embodies getting to root causes and transformation.',
        'characteristics': 'Mula natives are investigative, research-oriented individuals with philosophical nature. They possess ability to get to root causes of problems and bring transformative changes. Their deep thinking and analytical abilities reveal hidden truths.',
        'positive_traits': 'Investigative abilities and research skills, philosophical nature and deep thinking, transformative power and change ability, ability to find root causes, analytical and logical thinking, spiritual inclinations, ability to destroy negativity, healing abilities, truth-seeking nature.',
        'negative_traits': 'Destructive tendencies when upset, restlessness and dissatisfaction, overly critical nature, tendency toward extremes, can be ruthless in pursuit of truth, may be too blunt, struggles with superficial relationships, tendency toward isolation.',
        'careers': 'Research and investigation, philosophy and spirituality, detective work, root cause analysis, transformational consulting, spiritual healing, archaeological work, deep analysis, investigative journalism, therapeutic work.',
        'compatibility': 'Most compatible with Purva Ashadha, Uttara Ashadha, Shravana. Good with Jyeshtha, Dhanishta. Moderate with Anuradha, Shatabhisha. Caution with Purva Phalguni, Chitra.'
    },
    {
        'name': 'Purva Ashadha',
        'lord': 'Venus',
        'deity': 'Apas',
        'nature': 'Fierce/Ugra',
        'guna': 'Rajas',
        'description': 'Purva Ashadha nakshatra spans from 13°20\' to 26°40\' in Sagittarius, ruled by Venus with Apas as deity. The symbol is a fan or winnowing basket, representing purification and invincibility. This nakshatra embodies invincible spirit and purifying power.',
        'characteristics': 'Purva Ashadha natives are invincible, purifying individuals with strong influential nature. They possess ability to purify situations and people around them. Their invincible spirit and determination help overcome any obstacles in their path.',
        'positive_traits': 'Invincible spirit and determination, purifying abilities and influence, natural leadership and influence, ability to inspire others, strong conviction and beliefs, persuasive abilities, ability to overcome obstacles, influential nature, strong willpower, transformative abilities.',
        'negative_traits': 'Excessive pride and ego, stubbornness and inflexibility, overly argumentative nature, tendency to be domineering, can be overly aggressive, may be intolerant of others, tendency toward fanaticism, can be overly critical, inflexible thinking.',
        'careers': 'Leadership and influence roles, purification industries, water treatment, cleansing services, influential positions, motivational speaking, transformational work, spiritual purification, debate and argumentation, influential writing.',
        'compatibility': 'Most compatible with Uttara Ashadha, Shravana, Dhanishta. Good with Mula, Shatabhisha. Moderate with Jyeshtha, Purva Bhadrapada. Caution with Chitra, Hasta.'
    },
    {
        'name': 'Uttara Ashadha',
        'lord': 'Sun',
        'deity': 'Vishvedevas',
        'nature': 'Fixed/Dhruva',
        'guna': 'Rajas',
        'description': 'Uttara Ashadha nakshatra spans from 26°40\' Sagittarius to 10°00\' Capricorn, ruled by the Sun with Vishvadevas as deities. The symbol is an elephant\'s tusk or planks of bed, representing strength and support. This nakshatra embodies victory and ethical leadership.',
        'characteristics': 'Uttara Ashadha natives are victorious, righteous individuals with strong leadership qualities. They possess unwavering determination and ethical approach to life. Their ability to achieve long-term goals through persistent effort is remarkable.',
        'positive_traits': 'Strong determination and persistence, ethical nature and moral values, natural leadership abilities, ability to achieve long-term goals, righteous approach to life, ability to provide support, strong organizational skills, reliable and dependable, inspirational qualities, victory-oriented mindset.',
        'negative_traits': 'Stubbornness and inflexibility, overly serious nature, tendency to be rigid, may be too focused on goals, can be overly demanding, tendency toward workaholism, may neglect personal relationships, overly critical of others, inflexible thinking.',
        'careers': 'Leadership positions, ethical consulting, long-term planning, government services, administrative roles, project management, organizational leadership, ethical guidance, strategic planning, victory-oriented fields.',
        'compatibility': 'Most compatible with Shravana, Dhanishta, Shatabhisha. Good with Purva Ashadha, Purva Bhadrapada. Moderate with Mula, Uttara Bhadrapada. Caution with Vishakha, Swati.'
    },
    {
        'name': 'Shravana',
        'lord': 'Moon',
        'deity': 'Vishnu',
        'nature': 'Movable/Chara',
        'guna': 'Rajas',
        'description': 'Shravana nakshatra spans from 10°00\' to 23°20\' in Capricorn, ruled by the Moon with Vishnu as deity. The symbol is three footprints or an ear, representing learning and listening. This nakshatra embodies knowledge acquisition and communication.',
        'characteristics': 'Shravana natives are excellent listeners with remarkable learning abilities. They possess natural wisdom and communication skills that make them effective teachers and knowledge preservers. Their scholarly nature and ability to absorb information is exceptional.',
        'positive_traits': 'Excellent listening abilities, scholarly nature and love of learning, natural communication skills, ability to preserve knowledge, teaching abilities, wisdom and intelligence, ability to connect with others, good memory and retention, natural counseling skills, spiritual inclinations.',
        'negative_traits': 'Overly talkative nature, tendency toward gossip, too focused on information gathering, can be superficial in knowledge, may lack practical application, tendency to be preachy, can be overly curious, may spread rumors, information overload.',
        'careers': 'Education and teaching, communication services, media and journalism, knowledge preservation, library sciences, research and documentation, counseling, information technology, broadcasting, scholarly pursuits.',
        'compatibility': 'Most compatible with Dhanishta, Shatabhisha, Purva Bhadrapada. Good with Uttara Ashadha, Uttara Bhadrapada. Moderate with Purva Ashadha, Revati. Caution with Anuradha, Mula.'
    },
    {
        'name': 'Dhanishta',
        'lord': 'Mars',
        'deity': 'Vasus',
        'nature': 'Movable/Chara',
        'guna': 'Tamas',
        'description': 'Dhanishta nakshatra spans from 23°20\' Capricorn to 6°40\' Aquarius, ruled by Mars with Vasus as deities. The symbol is a drum or flute, representing rhythm and music. This nakshatra embodies wealth, music, and group activities.',
        'characteristics': 'Dhanishta natives are sociable, adaptable individuals with vibrant personalities. They possess natural musical talents and ability to work well in groups. Their rhythmic nature and social skills make them excellent team players and performers.',
        'positive_traits': 'Sociability and group working abilities, adaptability and flexibility, vibrant and energetic personality, musical and rhythmic talents, natural performance abilities, ability to create wealth, good networking skills, team player mentality, entertaining nature, organizational abilities.',
        'negative_traits': 'Easy susceptibility to influence, tendency toward aggression, materialistic focus, can be overly social, may lack individual identity, tendency toward showing off, can be superficial, overly concerned with wealth, may be unreliable.',
        'careers': 'Performing arts and music, entertainment industry, group activities and team sports, event management, social networking, wealth management, rhythmic arts, group leadership, musical instruments, performance coaching.',
        'compatibility': 'Most compatible with Shatabhisha, Purva Bhadrapada, Uttara Bhadrapada. Good with Shravana, Revati. Moderate with Uttara Ashadha, Ashwini. Caution with Jyeshtha, Purva Ashadha.'
    },
    {
        'name': 'Shatabhisha',
        'lord': 'Rahu',
        'deity': 'Varuna',
        'nature': 'Movable/Chara',
        'guna': 'Tamas',
        'description': 'Shatabhisha nakshatra spans from 6°40\' to 20°00\' in Aquarius, ruled by Rahu with Varuna as deity. The symbol is an empty circle or hundred healers, representing healing and mystery. This nakshatra embodies healing abilities and unconventional approaches.',
        'characteristics': 'Shatabhisha natives possess natural healing abilities and are independent, mysterious individuals. They have unconventional approaches to life and strong research inclinations. Their healing powers and mysterious nature make them unique personalities.',
        'positive_traits': 'Natural healing abilities, independent nature and self-reliance, research skills and investigative abilities, unconventional thinking and approaches, mysterious and intriguing personality, ability to work alone, innovative solutions, spiritual healing powers, unique perspectives, transformative abilities.',
        'negative_traits': 'Overly secretive nature, stubborn and inflexible thinking, too unconventional for others, tendency toward isolation, can be rebellious, may be too independent, struggles with authority, tendency toward eccentricity, can be unpredictable.',
        'careers': 'Healing and alternative medicine, research and investigation, unconventional fields, independent consulting, spiritual healing, innovative technologies, unique approaches, mystery solving, transformational work, independent research.',
        'compatibility': 'Most compatible with Purva Bhadrapada, Uttara Bhadrapada, Revati. Good with Dhanishta, Ashwini. Moderate with Shravana, Bharani. Caution with Uttara Ashadha, Mula.'
    },
    {
        'name': 'Purva Bhadrapada',
        'lord': 'Jupiter',
        'deity': 'Aja Ekapada',
        'nature': 'Fierce/Ugra',
        'guna': 'Rajas',
        'description': 'Purva Bhadrapada nakshatra spans from 20°00\' Aquarius to 3°20\' Pisces, ruled by Jupiter with Aja Ekapada as deity. The symbol is a sword or two front legs of bed, representing transformation and spiritual fire. This nakshatra embodies intense spiritual transformation.',
        'characteristics': 'Purva Bhadrapada natives are transformative, spiritual individuals with intense personalities. They possess deep philosophical nature and ability to undergo profound transformations. Their spiritual fire and intensity can inspire or intimidate others.',
        'positive_traits': 'Transformative abilities and spiritual power, philosophical nature and deep thinking, intense spiritual fire, ability to inspire transformation in others, strong convictions and beliefs, natural spiritual teaching abilities, ability to see deeper truths, transformational healing, spiritual wisdom, mystical inclinations.',
        'negative_traits': 'Tendency toward extremes, unpredictable behavior patterns, overly intense nature, can be fanatical, tendency toward spiritual pride, may be too serious, struggles with mundane matters, can be judgmental, tendency toward isolation.',
        'careers': 'Spiritual teaching and guidance, transformational work, philosophy and mysticism, spiritual healing, intense counseling, transformational consulting, spiritual writing, mystical practices, deep therapy, spiritual leadership.',
        'compatibility': 'Most compatible with Uttara Bhadrapada, Revati, Ashwini. Good with Shatabhisha, Bharani. Moderate with Dhanishta, Krittika. Caution with Purva Ashadha, Uttara Ashadha.'
    },
    {
        'name': 'Uttara Bhadrapada',
        'lord': 'Saturn',
        'deity': 'Ahir Budhnya',
        'nature': 'Fixed/Dhruva',
        'guna': 'Tamas',
        'description': 'Uttara Bhadrapada nakshatra spans from 3°20\' to 16°40\' in Pisces, ruled by Saturn with Ahir Budhnya as deity. The symbol is back legs of bed or a serpent in water, representing depth and stability. This nakshatra embodies deep wisdom and foundational strength.',
        'characteristics': 'Uttara Bhadrapada natives are deep, stable individuals with profound wisdom. They possess ability to provide strong foundations and support to others. Their depth of understanding and stable nature makes them reliable guides and counselors.',
        'positive_traits': 'Depth and profound wisdom, stability and reliable nature, ability to provide strong foundations, deep understanding of life, natural counseling abilities, spiritual depth, ability to support others, patient and persistent nature, philosophical thinking, transformative wisdom.',
        'negative_traits': 'Overly serious and somber nature, pessimistic outlook on life, too slow to take action, tendency toward depression, can be overly cautious, may lack spontaneity, tendency toward isolation, overly philosophical, can be rigid in thinking.',
        'careers': 'Deep counseling and therapy, foundational work, spiritual guidance, philosophical pursuits, depth psychology, foundational planning, stable support services, wisdom teaching, deep research, transformational depth work.',
        'compatibility': 'Most compatible with Revati, Ashwini, Bharani. Good with Purva Bhadrapada, Krittika. Moderate with Shatabhisha, Rohini. Caution with Shravana, Uttara Ashadha.'
    },
    {
        'name': 'Revati',
        'lord': 'Mercury',
        'deity': 'Pushan',
        'nature': 'Soft/Mridu',
        'guna': 'Sattva',
        'description': 'Revati nakshatra spans from 16°40\' to 30°00\' in Pisces, ruled by Mercury with Pushan as deity. The symbol is a fish or drum, representing nourishment and completion. This nakshatra embodies nourishing care and completion of cycles.',
        'characteristics': 'Revati natives are nourishing, prosperous individuals with protective instincts. They possess natural ability to complete projects and cycles. Their caring nature and prosperity consciousness makes them excellent providers and nurturers.',
        'positive_traits': 'Nourishing and caring nature, prosperity consciousness, protective instincts toward others, ability to complete projects, natural nurturing abilities, generous and giving nature, ability to provide for others, completion-oriented mindset, spiritual nourishment, healing through care.',
        'negative_traits': 'Overly protective nature, possessive tendencies, too giving to own detriment, can be overly emotional, tendency to be taken advantage of, may neglect own needs, overly nurturing, can be clingy, tendency toward worry.',
        'careers': 'Nourishment and care industries, completion services, protective services, nurturing professions, childcare and family services, food and nutrition, travel and journey completion, prosperity consulting, caring professions, completion-oriented work.',
        'compatibility': 'Most compatible with Ashwini, Bharani, Krittika. Good with Uttara Bhadrapada, Rohini. Moderate with Purva Bhadrapada, Mrigashira. Caution with Dhanishta, Shravana.'
    }
]

# Insert all nakshatras
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

print(f"Successfully populated all {count} detailed nakshatras in the database!")