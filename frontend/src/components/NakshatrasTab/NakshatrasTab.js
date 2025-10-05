import React, { useState } from 'react';

const NakshatrasTab = ({ chartData, birthData }) => {
  const [selectedNakshatra, setSelectedNakshatra] = useState(null);
  
  const nakshatras = [
    { 
      name: 'Ashwini', lord: 'Ketu', deity: 'Ashwini Kumaras', nature: 'Light/Swift', guna: 'Rajas',
      description: 'Ashwini nakshatra is the first among the twenty-seven nakshatras and comes under the domain of planet Ketu. Ashwini nakshatra is symbolized by the head of a horse. The presiding deities of this nakshatra are Ashwini Kumaras, the twin sons of Surya and Sanjna. They are considered the physicians of the gods and are known for their healing powers. The shakti of Ashwini is "Shidhra Vyapani Shakti" which gives the power to quickly reach things. This nakshatra spans from 0°00 to 13°20 in Mesha Rashi (Aries).',
      characteristics: 'People born under Ashwini nakshatra are known for their pioneering spirit and dynamic nature. They possess natural healing abilities and are often drawn to medicine and healthcare. These natives are quick in their actions and decisions, often acting on impulse. They have a strong desire to help others and possess leadership qualities. Ashwini natives are adventurous, independent, and have a youthful appearance throughout their lives. They are blessed with good health and vitality.',
      behavioral: 'Ashwini natives exhibit swift and decisive behavior. They are natural leaders who prefer to take initiative rather than follow others. Their impulsive nature sometimes leads them to make hasty decisions. They are compassionate healers who cannot see others in pain. These individuals are honest, straightforward, and have a childlike innocence. They possess strong willpower and determination to achieve their goals.',
      positiveTraits: 'The positive traits of Ashwini natives include their healing abilities, leadership qualities, pioneering spirit, and helpful nature. They are quick learners, adaptable, and possess natural charisma. Their optimistic outlook and energetic personality inspire others. They have strong intuitive powers and can sense the needs of others. Ashwini natives are blessed with good fortune and often succeed in their endeavors through their own efforts.',
      negativeTraits: 'The negative traits include impatience, impulsiveness, and tendency to be overly aggressive. They may lack persistence and give up on projects midway. Their straightforward nature sometimes hurts others feelings. They can be stubborn and refuse to listen to advice. Ashwini natives may also suffer from headaches and injuries to the head due to their impulsive nature.',
      careers: 'Ashwini natives excel in careers related to healing and medicine such as doctors, nurses, veterinarians, and alternative healers. They also do well in emergency services, military, police, and rescue operations. Transportation, automobile industry, sports, and adventure-related careers suit them well. They can succeed as entrepreneurs, pioneers in new fields, and in leadership positions. Counseling, therapy, and social work are also suitable career options.',
      compatibility: 'Ashwini is most compatible with Bharani and Krittika nakshatras. The animal symbol of Ashwini is male horse, which is compatible with female horse (Shatabhisha). However, they may face challenges with nakshatras like Jyeshtha and Anuradha. In terms of marriage compatibility, Ashwini natives should avoid partners from Magha, Purva Phalguni, and Uttara Phalguni nakshatras as per traditional Vedic astrology principles.'
    },
    { 
      name: 'Bharani', lord: 'Venus', deity: 'Yama', nature: 'Fierce/Ugra', guna: 'Rajas',
      description: 'Bharani nakshatra is the second nakshatra in Vedic astrology, ruled by Venus and presided over by Yama, the god of death and dharma. The symbol of Bharani is the yoni (female reproductive organ), representing creativity, fertility, and the power of transformation. This nakshatra spans from 13°20 to 26°40 in Mesha Rashi (Aries). The shakti of Bharani is "Apabharani Shakti" - the power to take away or remove. Bharani represents the cosmic womb from which all creation emerges and to which it returns.',
      characteristics: 'Bharani natives are known for their strong willpower, determination, and ability to bear responsibilities. They possess natural leadership qualities and are not afraid to take on challenges. These individuals have a deep understanding of life and death cycles and often work in fields related to transformation. They are creative, artistic, and have a strong sense of justice. Bharani natives are passionate, intense, and have magnetic personalities that attract others.',
      behavioral: 'People born under Bharani nakshatra exhibit fierce determination and unwavering resolve. They are natural judges who can distinguish between right and wrong. Their behavior is marked by intensity and passion in whatever they undertake. They have a protective nature and will go to great lengths to defend their loved ones. These natives are not easily influenced by others and prefer to make their own decisions.',
      positiveTraits: 'The positive traits of Bharani natives include their strong sense of responsibility, creative abilities, and natural leadership skills. They are loyal, trustworthy, and have the courage to face difficult situations. Their artistic talents and aesthetic sense are well-developed. They possess good judgment and can make fair decisions. Bharani natives are also known for their fertility and ability to nurture growth in various aspects of life.',
      negativeTraits: 'The negative traits include stubbornness, jealousy, and tendency to be overly critical. They may become too controlling and possessive in relationships. Their intense nature can sometimes lead to conflicts with others. Bharani natives may also struggle with anger management and can be vengeful when wronged. They might face challenges related to reproductive health.',
      careers: 'Bharani natives excel in careers related to law, justice, and administration. They make excellent judges, lawyers, and law enforcement officers. Creative fields such as arts, music, dance, and entertainment are also suitable. They can succeed in businesses related to women and children, fertility clinics, and healthcare. Publishing, writing, and media are other favorable career options. They also do well in fields involving transformation and change management.',
      compatibility: 'Bharani is most compatible with Ashwini and Rohini nakshatras. The elephant is the animal symbol of Bharani, which shares a friendly relationship with horse (Ashwini) and serpent (Rohini). However, they may face challenges with lion-represented nakshatras like Dhanishta and Purva Bhadrapada. Marriage compatibility should be carefully analyzed, especially avoiding partnerships with Magha, Purva Phalguni, and Uttara Phalguni nakshatras.'
    },
    { 
      name: 'Krittika', lord: 'Sun', deity: 'Agni', nature: 'Mixed', guna: 'Rajas',
      description: 'Krittika nakshatra is the third nakshatra in Vedic astrology, ruled by the Sun and presided over by Agni, the fire god. The symbol of Krittika is a sharp razor or flame, representing the power to cut through illusion and burn away impurities. This nakshatra spans from 26°40 in Mesha (Aries) to 10°00 in Vrishabha (Taurus). Krittika is known as the "Star of Fire" and represents purification, transformation, and spiritual awakening. The shakti of Krittika is "Dahana Shakti" - the power to burn and purify.',
      characteristics: 'Krittika natives are known for their sharp intellect, determination, and ability to see through deception. They possess natural leadership qualities and are not afraid to speak the truth, even if it hurts others. These individuals have a strong sense of justice and will fight against injustice wherever they see it. They are perfectionists who pay attention to details and have high standards for themselves and others. Krittika natives are also known for their spiritual inclination and desire for self-improvement.',
      behavioral: 'People born under Krittika nakshatra exhibit sharp, direct, and sometimes cutting behavior. They are natural critics who can identify flaws and weaknesses in systems, people, and situations. Their approach to life is methodical and they prefer to work independently. They have strong willpower and determination to achieve their goals. These natives are protective of their loved ones and will defend them fiercely when needed.',
      positiveTraits: 'The positive traits of Krittika natives include their sharp intellect, leadership abilities, and strong sense of justice. They are excellent at identifying problems and finding solutions. Their perfectionist nature ensures high-quality work and attention to detail. They possess natural teaching abilities and can guide others effectively. Krittika natives are also known for their courage, determination, and ability to purify and transform situations.',
      negativeTraits: 'The negative traits include being overly critical, harsh in speech, and sometimes cruel in their judgments. They may become too demanding and expect perfection from others. Their sharp tongue can hurt people unnecessarily. Krittika natives may also be prone to anger and impatience when things don\'t go according to their expectations. They might struggle with being too rigid and inflexible in their approach.',
      careers: 'Krittika natives excel in careers that require sharp intellect and analytical abilities. They make excellent teachers, critics, editors, and researchers. Military, police, and law enforcement are suitable fields. They can succeed in engineering, technology, and scientific research. Spiritual guidance, counseling, and healing arts are also favorable. They do well in careers involving fire, metals, and sharp instruments. Leadership positions in various fields suit their natural commanding abilities.',
      compatibility: 'Krittika is most compatible with Rohini and Mrigashira nakshatras. The sheep is the animal symbol of Krittika, which has natural compatibility with serpent (Rohini) and deer (Mrigashira). However, they may face challenges with nakshatras represented by natural predators. In marriage, Krittika natives should be careful about their sharp nature and learn to be more gentle and understanding with their partners.'
    },
    { 
      name: 'Rohini', lord: 'Moon', deity: 'Brahma', nature: 'Fixed/Dhruva', guna: 'Rajas',
      description: 'Rohini nakshatra is the fourth nakshatra in Vedic astrology, ruled by the Moon and presided over by Brahma, the creator god. The symbol of Rohini is an ox cart or chariot, representing material progress and fertility. This nakshatra spans from 10°00 to 23°20 in Vrishabha Rashi (Taurus). Rohini is considered one of the most auspicious nakshatras and is often called the "beloved of the Moon" as the Moon is said to spend most of its time here. The shakti of Rohini is "Rohana Shakti" - the power of growth and creation.',
      characteristics: 'Rohini natives are blessed with natural beauty, charm, and magnetic personalities. They possess artistic talents and have a refined taste for beautiful things. These individuals are stable, reliable, and have a strong desire for material comforts and security. They are nurturing by nature and make excellent parents and caregivers. Rohini natives have a romantic disposition and are often successful in attracting wealth and prosperity.',
      behavioral: 'People born under Rohini nakshatra exhibit calm, steady, and reliable behavior. They prefer stability and security over adventure and risk-taking. Their approach to life is practical and methodical. They have a natural ability to attract resources and people towards them. These natives are patient, persistent, and work steadily towards their goals. They value relationships and are loyal to their loved ones.',
      positiveTraits: 'The positive traits of Rohini natives include their natural beauty, artistic abilities, and magnetic charm. They are reliable, trustworthy, and have excellent nurturing qualities. Their ability to create wealth and attract prosperity is remarkable. They possess good taste, refinement, and appreciation for arts and culture. Rohini natives are also known for their fertility, both literally and metaphorically, bringing growth and abundance wherever they go.',
      negativeTraits: 'The negative traits include materialism, possessiveness, and tendency to be overly attached to physical comforts. They may become lazy and complacent when things are going well. Their desire for luxury can sometimes lead to extravagance. Rohini natives may also be stubborn and resistant to change. They might struggle with jealousy and can be overly critical of others who they perceive as threats.',
      careers: 'Rohini natives excel in careers related to arts, beauty, and luxury goods. They make successful artists, designers, musicians, and performers. Fashion industry, cosmetics, jewelry, and luxury retail are favorable fields. Agriculture, horticulture, and food industry also suit them well. They can succeed in banking, finance, and real estate. Entertainment industry, hospitality, and tourism are other suitable career options. They also do well in businesses related to women and children.',
      compatibility: 'Rohini is most compatible with Mrigashira and Ardra nakshatras. The serpent is the animal symbol of Rohini, which has natural compatibility with deer (Mrigashira) and dog (Ardra). However, they may face challenges with mongoose-represented nakshatras. In marriage, Rohini natives should be careful about compatibility with nakshatras like Jyeshtha, Mula, and Ashlesha, as these combinations may create challenges in relationships.'
    },
    { 
      name: 'Mrigashira', lord: 'Mars', deity: 'Soma', nature: 'Soft/Mridu', guna: 'Tamas',
      description: 'Mrigashira nakshatra is the fifth nakshatra in Vedic astrology, ruled by Mars and presided over by Soma, the Moon god. The symbol of Mrigashira is the head of a deer, representing the eternal search for knowledge, truth, and spiritual fulfillment. This nakshatra spans from 23°20 in Vrishabha (Taurus) to 6°40 in Mithuna (Gemini). Mrigashira is known as the "Searching Star" and represents curiosity, exploration, and the quest for higher knowledge. The shakti of Mrigashira is "Prinana Shakti" - the power to give fulfillment.',
      characteristics: 'Mrigashira natives are known for their curious nature, love for exploration, and constant search for knowledge. They possess excellent communication skills and are natural storytellers. These individuals are gentle, sensitive, and have a refined aesthetic sense. They love beauty, art, and culture. Mrigashira natives are also known for their restless nature and desire to travel and explore new places. They have a youthful appearance and maintain their curiosity throughout life.',
      behavioral: 'People born under Mrigashira nakshatra exhibit gentle, curious, and exploratory behavior. They are natural seekers who are always looking for new experiences and knowledge. Their approach to life is soft and diplomatic, preferring harmony over conflict. They have excellent social skills and can adapt to different environments easily. These natives are also known for their romantic nature and appreciation of beauty in all forms.',
      positiveTraits: 'The positive traits of Mrigashira natives include their curiosity, communication skills, and gentle nature. They are excellent learners and teachers who can absorb and share knowledge effectively. Their diplomatic skills help them navigate social situations smoothly. They possess natural artistic abilities and good taste. Mrigashira natives are also known for their adaptability, flexibility, and ability to find beauty in simple things.',
      negativeTraits: 'The negative traits include restlessness, indecisiveness, and tendency to be superficial in their pursuits. They may start many projects but fail to complete them due to their wandering nature. Their constant search for something better can make them dissatisfied with what they have. Mrigashira natives may also be prone to gossip and can be easily influenced by others. They might struggle with commitment and consistency.',
      careers: 'Mrigashira natives excel in careers related to communication, travel, and exploration. They make excellent writers, journalists, teachers, and researchers. Travel and tourism industry suits them well. They can succeed in arts, music, and entertainment fields. Sales, marketing, and public relations are favorable career options. They also do well in fields involving beauty, fashion, and luxury goods. Research, exploration, and adventure-related careers are also suitable.',
      compatibility: 'Mrigashira is most compatible with Ardra and Punarvasu nakshatras. The deer is the animal symbol of Mrigashira, which has natural compatibility with dog (Ardra) and cat (Punarvasu). However, they may face challenges with predatory animals. In marriage, Mrigashira natives need partners who can understand their need for freedom and exploration while providing emotional stability.'
    },
    { 
      name: 'Ardra', lord: 'Rahu', deity: 'Rudra', nature: 'Sharp/Tikshna', guna: 'Tamas',
      description: 'Ardra nakshatra is the sixth nakshatra in Vedic astrology, ruled by Rahu and presided over by Rudra, the fierce form of Lord Shiva. The symbol of Ardra is a teardrop or a human head, representing sorrow, destruction, and transformation. This nakshatra spans from 6°40 to 20°00 in Mithuna Rashi (Gemini). Ardra is known as the "Star of Sorrow" and represents the destructive aspect of nature that clears the way for new growth. The shakti of Ardra is "Yatna Shakti" - the power of effort and achievement through struggle.',
      characteristics: 'Ardra natives are intense, emotional, and transformative individuals. They possess sharp intellect and excellent research abilities. These people are naturally inclined towards innovation and breaking conventional boundaries. They have healing abilities and can help others through their own experiences of pain and transformation. Ardra natives are also known for their ability to see through illusions and get to the core of matters.',
      behavioral: 'People born under Ardra nakshatra exhibit intense, passionate, and sometimes unpredictable behavior. They are natural rebels who question authority and conventional wisdom. Their approach to life involves constant transformation and renewal. They have a tendency to experience emotional extremes and can be both destructive and creative. These natives are also known for their ability to bounce back from difficulties stronger than before.',
      positiveTraits: 'The positive traits of Ardra natives include their transformative abilities, sharp intellect, and innovative thinking. They are excellent researchers who can uncover hidden truths. Their healing abilities help them assist others in overcoming difficulties. They possess strong willpower and determination to overcome obstacles. Ardra natives are also known for their ability to adapt to changing circumstances and their capacity for deep emotional understanding.',
      negativeTraits: 'The negative traits include emotional instability, destructive tendencies, and tendency towards extremes. They may be prone to anger, jealousy, and vindictive behavior. Their intense nature can sometimes overwhelm others. Ardra natives may also struggle with depression and mood swings. They might have difficulty maintaining stable relationships due to their unpredictable nature and tendency to create storms in calm situations.',
      careers: 'Ardra natives excel in careers involving research, investigation, and transformation. They make excellent scientists, researchers, psychologists, and psychiatrists. Medical field, especially surgery and emergency medicine, suits them well. They can succeed in technology, innovation, and cutting-edge fields. Occult sciences, astrology, and healing arts are favorable. They also do well in crisis management, disaster relief, and fields involving radical change or transformation.',
      compatibility: 'Ardra is most compatible with Punarvasu and Pushya nakshatras. The dog is the animal symbol of Ardra, which has natural compatibility with cat (Punarvasu) and sheep (Pushya). However, they may face challenges with nakshatras represented by natural enemies. In marriage, Ardra natives need partners who can handle their intense nature and provide emotional stability during their transformative phases.'
    },
    { 
      name: 'Punarvasu', lord: 'Jupiter', deity: 'Aditi', nature: 'Movable/Chara', guna: 'Rajas',
      description: 'Punarvasu nakshatra is the seventh nakshatra in Vedic astrology, ruled by Jupiter and presided over by Aditi, the mother of gods. The symbol of Punarvasu is a quiver of arrows or a house, representing renewal, restoration, and return to prosperity. This nakshatra spans from 20°00 in Mithuna (Gemini) to 3°20 in Karka (Cancer). Punarvasu is known as the "Star of Renewal" and represents the return of light after darkness, hope after despair. The shakti of Punarvasu is "Vasutva Prapana Shakti" - the power to gain wealth and abundance.',
      characteristics: 'Punarvasu natives are optimistic, philosophical, and generous individuals. They possess natural wisdom and have a protective, nurturing nature. These people are blessed with good fortune and have the ability to bounce back from setbacks. They are spiritually inclined and often serve as guides and teachers to others. Punarvasu natives are also known for their ability to create harmony and bring people together.',
      behavioral: 'People born under Punarvasu nakshatra exhibit optimistic, generous, and philosophical behavior. They are natural teachers and guides who inspire others with their wisdom. Their approach to life is positive and hopeful, even in difficult circumstances. They have excellent communication skills and can adapt to different situations easily. These natives are also known for their loyalty, honesty, and strong moral principles.',
      positiveTraits: 'The positive traits of Punarvasu natives include their optimism, generosity, and wisdom. They are excellent teachers and counselors who can guide others effectively. Their ability to recover from setbacks and help others do the same is remarkable. They possess strong moral values and integrity. Punarvasu natives are also known for their protective nature, good fortune, and ability to create abundance and prosperity.',
      negativeTraits: 'The negative traits include over-optimism, tendency to be preachy, and sometimes naive trust in others. They may be too generous for their own good and can be taken advantage of by others. Their philosophical nature might make them impractical at times. Punarvasu natives may also struggle with being overly protective and interfering in others\' lives. They might have difficulty saying no to requests for help.',
      careers: 'Punarvasu natives excel in careers related to teaching, counseling, and guidance. They make excellent teachers, professors, philosophers, and spiritual guides. Publishing, writing, and media are favorable fields. They can succeed in social work, charity, and humanitarian causes. Real estate, hospitality, and travel industry suit them well. They also do well in fields involving restoration, renovation, and renewal. Healing arts and alternative medicine are other suitable career options.',
      compatibility: 'Punarvasu is most compatible with Pushya and Ashlesha nakshatras. The cat is the animal symbol of Punarvasu, which has natural compatibility with sheep (Pushya) and serpent (Ashlesha). However, they may face challenges with dog-represented nakshatras. In marriage, Punarvasu natives make loyal and supportive partners who bring optimism and wisdom to relationships.'
    },
    { 
      name: 'Pushya', lord: 'Saturn', deity: 'Brihaspati', nature: 'Light/Laghu', guna: 'Rajas',
      description: 'Pushya nakshatra is the eighth nakshatra in Vedic astrology, ruled by Saturn and presided over by Brihaspati, the guru of gods. The symbol of Pushya is the udder of a cow or a lotus flower, representing nourishment, prosperity, and spiritual growth. This nakshatra spans from 3°20 to 16°40 in Karka Rashi (Cancer). Pushya is considered one of the most auspicious nakshatras and is known as the "Star of Nourishment." The shakti of Pushya is "Brahmavarchasa Shakti" - the power of spiritual energy and divine radiance.',
      characteristics: 'Pushya natives are nurturing, disciplined, and spiritually inclined individuals. They possess natural leadership abilities and have a strong sense of duty and responsibility. These people are blessed with wisdom, patience, and the ability to provide guidance to others. They are conservative in their approach and prefer traditional values. Pushya natives are also known for their ability to accumulate wealth and resources through steady effort.',
      behavioral: 'People born under Pushya nakshatra exhibit calm, steady, and responsible behavior. They are natural caregivers who put others\' needs before their own. Their approach to life is methodical and disciplined. They have excellent organizational skills and can manage resources effectively. These natives are also known for their loyalty, reliability, and strong moral principles. They prefer stability and security over adventure and risk-taking.',
      positiveTraits: 'The positive traits of Pushya natives include their nurturing nature, discipline, and spiritual wisdom. They are excellent providers and protectors who ensure the well-being of their family and community. Their ability to accumulate wealth and resources through honest means is remarkable. They possess strong moral values and integrity. Pushya natives are also known for their patience, perseverance, and ability to guide others on the right path.',
      negativeTraits: 'The negative traits include over-conservatism, rigidity, and tendency to be controlling. They may be too focused on material security and miss out on emotional fulfillment. Their disciplined nature might make them appear cold or distant. Pushya natives may also struggle with being overly critical and judgmental of others. They might have difficulty adapting to change and can be stubborn in their beliefs.',
      careers: 'Pushya natives excel in careers related to nourishment, care, and guidance. They make excellent teachers, counselors, nutritionists, and healthcare professionals. Government service, administration, and management are favorable fields. They can succeed in agriculture, food industry, and hospitality. Banking, finance, and insurance suit them well. They also do well in religious and spiritual organizations. Traditional businesses and family enterprises are other suitable career options.',
      compatibility: 'Pushya is most compatible with Ashlesha and Magha nakshatras. The sheep is the animal symbol of Pushya, which has natural compatibility with serpent (Ashlesha) and rat (Magha). However, they may face challenges with predatory animals. In marriage, Pushya natives make devoted and caring partners who prioritize family welfare and stability.'
    },
    { 
      name: 'Ashlesha', lord: 'Mercury', deity: 'Nagas', nature: 'Sharp/Tikshna', guna: 'Sattva',
      description: 'Ashlesha nakshatra is the ninth nakshatra in Vedic astrology, ruled by Mercury and presided over by the Nagas (serpent deities). The symbol of Ashlesha is a coiled serpent, representing kundalini energy, wisdom, and transformation. This nakshatra spans from 16°40 to 30°00 in Karka Rashi (Cancer). Ashlesha is known as the "Clinging Star" and represents the power of penetration and hypnotic influence. The shakti of Ashlesha is "Visha Sleshana Shakti" - the power to inflict poison or remove poison.',
      characteristics: 'Ashlesha natives are intuitive, mysterious, and possess deep psychological insight. They have natural healing abilities and can understand the hidden motivations of others. These people are emotionally complex and often struggle with inner conflicts. They possess hypnotic charm and can influence others easily. Ashlesha natives are also known for their ability to transform themselves and others through their penetrating wisdom.',
      behavioral: 'People born under Ashlesha nakshatra exhibit mysterious, intuitive, and sometimes manipulative behavior. They are natural psychologists who can read people easily. Their approach to life involves deep emotional exploration and transformation. They have a tendency to be secretive and may not reveal their true intentions easily. These natives are also known for their ability to adapt to different situations like a serpent changing its skin.',
      positiveTraits: 'The positive traits of Ashlesha natives include their intuitive abilities, psychological insight, and healing powers. They are excellent counselors and therapists who can help others overcome deep-seated issues. Their ability to transform negative situations into positive ones is remarkable. They possess natural wisdom and can see through deceptions. Ashlesha natives are also known for their loyalty to those they care about and their protective nature.',
      negativeTraits: 'The negative traits include manipulative tendencies, secretiveness, and emotional instability. They may use their psychological insight to control or deceive others. Their complex emotional nature can make them difficult to understand. Ashlesha natives may also struggle with jealousy, possessiveness, and vindictive behavior. They might have difficulty trusting others and can be overly suspicious.',
      careers: 'Ashlesha natives excel in careers involving psychology, healing, and transformation. They make excellent psychologists, psychiatrists, therapists, and counselors. Occult sciences, astrology, and mystical studies suit them well. They can succeed in research, investigation, and detective work. Medicine, especially alternative healing, is favorable. They also do well in fields involving secrets, intelligence, and behind-the-scenes work. Writing, especially mystery or psychological genres, is another suitable option.',
      compatibility: 'Ashlesha is most compatible with Jyeshtha and Revati nakshatras. The serpent is the animal symbol of Ashlesha, which has natural compatibility with mongoose (Jyeshtha) and elephant (Revati). However, they may face challenges with eagle-represented nakshatras. In marriage, Ashlesha natives need partners who can understand their complex emotional nature and provide stability.'
    },
    { 
      name: 'Magha', lord: 'Ketu', deity: 'Pitrs', nature: 'Fierce/Ugra', guna: 'Tamas',
      description: 'Magha nakshatra is the tenth nakshatra in Vedic astrology, ruled by Ketu and presided over by the Pitrs (ancestral spirits). The symbol of Magha is a throne or a palanquin, representing royal authority, ancestral pride, and leadership. This nakshatra spans from 0°00 to 13°20 in Simha Rashi (Leo). Magha is known as the "Star of Power" and represents connection with ancestors and inherited authority. The shakti of Magha is "Tyaga Shepani Shakti" - the power to leave the body and unite with the ancestors.',
      characteristics: 'Magha natives are authoritative, proud, and possess natural leadership qualities. They have deep respect for tradition, ancestry, and established customs. These people are born leaders who command respect and authority. They possess royal bearing and dignity in their demeanor. Magha natives are also known for their generosity, especially towards family and those they consider worthy of their patronage.',
      behavioral: 'People born under Magha nakshatra exhibit regal, authoritative, and traditional behavior. They are natural leaders who expect respect and recognition for their position. Their approach to life involves maintaining dignity and upholding family honor. They have strong connections with their roots and ancestry. These natives are also known for their ceremonial nature and love for rituals and traditions.',
      positiveTraits: 'The positive traits of Magha natives include their leadership abilities, dignity, and respect for tradition. They are generous patrons who support worthy causes and individuals. Their ability to command respect and maintain authority is remarkable. They possess strong family values and ancestral connections. Magha natives are also known for their loyalty, honor, and ability to inspire others through their example.',
      negativeTraits: 'The negative traits include arrogance, superiority complex, and tendency to be domineering. They may be overly concerned with status and recognition. Their pride might make them inflexible and resistant to change. Magha natives may also struggle with accepting criticism and can be vindictive towards those who challenge their authority. They might have difficulty relating to people from different social backgrounds.',
      careers: 'Magha natives excel in careers involving leadership, authority, and tradition. They make excellent politicians, government officials, and administrators. Royal courts, aristocracy, and high-profile positions suit them well. They can succeed in archaeology, genealogy, and historical research. Traditional arts, cultural preservation, and ceremonial roles are favorable. They also do well in positions of power and influence in various fields.',
      compatibility: 'Magha is most compatible with Purva Phalguni and Uttara Phalguni nakshatras. The rat is the animal symbol of Magha, which has natural compatibility with cow (Purva Phalguni and Uttara Phalguni). However, they may face challenges with cat-represented nakshatras. In marriage, Magha natives need partners who respect their need for dignity and status while providing emotional warmth.'
    },
    { 
      name: 'Purva Phalguni', lord: 'Venus', deity: 'Bhaga', nature: 'Fierce/Ugra', guna: 'Rajas',
      description: 'Purva Phalguni nakshatra is the eleventh nakshatra in Vedic astrology, ruled by Venus and presided over by Bhaga, the god of fortune and prosperity. The symbol of Purva Phalguni is a bed, hammock, or the front legs of a cot, representing rest, relaxation, and pleasure. This nakshatra spans from 13°20 to 26°40 in Simha Rashi (Leo). Purva Phalguni is known as the "Star of Fortune" and represents enjoyment, creativity, and procreation. The shakti of Purva Phalguni is "Prajanana Shakti" - the power of procreation and creation.',
      characteristics: 'Purva Phalguni natives are creative, artistic, and pleasure-loving individuals. They possess natural charm, charisma, and magnetic personalities. These people love luxury, comfort, and beautiful things. They are generous, hospitable, and enjoy entertaining others. Purva Phalguni natives are also known for their romantic nature and strong desire for companionship and partnership.',
      behavioral: 'People born under Purva Phalguni nakshatra exhibit charming, pleasure-seeking, and sociable behavior. They are natural entertainers who love to be the center of attention. Their approach to life involves seeking joy, beauty, and comfort. They have excellent social skills and can make friends easily. These natives are also known for their generous nature and willingness to share their good fortune with others.',
      positiveTraits: 'The positive traits of Purva Phalguni natives include their creativity, charm, and generous nature. They are excellent entertainers and hosts who can make others feel comfortable and happy. Their artistic abilities and aesthetic sense are remarkable. They possess natural magnetism and can attract wealth and opportunities. Purva Phalguni natives are also known for their loyalty in relationships and their ability to bring joy to others.',
      negativeTraits: 'The negative traits include vanity, laziness, and tendency to be overly indulgent. They may be too focused on pleasure and comfort, neglecting responsibilities. Their desire for luxury can lead to extravagance and financial problems. Purva Phalguni natives may also struggle with commitment issues and can be superficial in their relationships. They might have difficulty dealing with hardships and challenges.',
      careers: 'Purva Phalguni natives excel in careers related to entertainment, arts, and luxury. They make excellent actors, musicians, artists, and performers. Fashion industry, beauty, and cosmetics suit them well. They can succeed in hospitality, tourism, and event management. Luxury goods, jewelry, and high-end retail are favorable fields. They also do well in careers involving creativity, design, and aesthetics.',
      compatibility: 'Purva Phalguni is most compatible with Uttara Phalguni and Hasta nakshatras. The rat is the animal symbol of Purva Phalguni, which has natural compatibility with cow (Uttara Phalguni) and buffalo (Hasta). However, they may face challenges with cat-represented nakshatras. In marriage, Purva Phalguni natives are romantic and devoted partners who seek harmony and pleasure in relationships.'
    },
    { 
      name: 'Uttara Phalguni', lord: 'Sun', deity: 'Aryaman', nature: 'Fixed/Dhruva', guna: 'Rajas',
      description: 'Uttara Phalguni nakshatra is the twelfth nakshatra in Vedic astrology, ruled by the Sun and presided over by Aryaman, the god of patronage and contracts. The symbol of Uttara Phalguni is a bed or the back legs of a cot, representing support, patronage, and friendship. This nakshatra spans from 26°40 in Simha (Leo) to 10°00 in Kanya (Virgo). Uttara Phalguni is known as the "Star of Patronage" and represents helpful nature, support, and beneficial partnerships. The shakti of Uttara Phalguni is "Chayani Shakti" - the power of giving prosperity through union and partnership.',
      characteristics: 'Uttara Phalguni natives are helpful, supportive, and organized individuals. They possess natural leadership qualities and have a strong sense of duty towards others. These people are excellent organizers and can bring people together for common causes. They value friendship and are known for their loyalty and reliability. Uttara Phalguni natives are also blessed with the ability to gain support from others and create beneficial partnerships.',
      behavioral: 'People born under Uttara Phalguni nakshatra exhibit helpful, organized, and responsible behavior. They are natural supporters who put others\' needs before their own. Their approach to life involves creating harmony and building beneficial relationships. They have excellent organizational skills and can manage people and resources effectively. These natives are also known for their diplomatic nature and ability to resolve conflicts.',
      positiveTraits: 'The positive traits of Uttara Phalguni natives include their helpful nature, organizational skills, and ability to create beneficial partnerships. They are excellent leaders who inspire others through service. Their loyalty and reliability make them trusted friends and advisors. They possess strong moral values and integrity. Uttara Phalguni natives are also known for their ability to gain patronage and support from influential people.',
      negativeTraits: 'The negative traits include tendency to be overly dependent on others, difficulty in making independent decisions, and sometimes being too accommodating. They may sacrifice their own needs for others to their detriment. Their desire for harmony might make them avoid necessary confrontations. Uttara Phalguni natives may also struggle with being overly critical of themselves and others.',
      careers: 'Uttara Phalguni natives excel in careers involving service, organization, and support. They make excellent social workers, counselors, and human resource professionals. Management, administration, and organizational roles suit them well. They can succeed in public service, government, and non-profit organizations. Healing arts, therapy, and supportive services are favorable fields. They also do well in careers involving partnerships and collaborations.',
      compatibility: 'Uttara Phalguni is most compatible with Hasta and Chitra nakshatras. The cow is the animal symbol of Uttara Phalguni, which has natural compatibility with buffalo (Hasta) and tiger (Chitra). However, they may face challenges with mongoose-represented nakshatras. In marriage, Uttara Phalguni natives are supportive and caring partners who prioritize harmony and mutual growth.'
    },
    { 
      name: 'Hasta', lord: 'Moon', deity: 'Savitar', nature: 'Light/Laghu', guna: 'Rajas',
      description: 'Hasta nakshatra is the thirteenth nakshatra in Vedic astrology, ruled by the Moon and presided over by Savitar, the creative aspect of the Sun god. The symbol of Hasta is a hand or closed fist, representing skill, dexterity, and the power of creation through hands. This nakshatra spans from 10°00 to 23°20 in Kanya Rashi (Virgo). Hasta is known as the "Star of the Hand" and represents craftsmanship, skill, and the ability to manifest ideas into reality. The shakti of Hasta is "Hasta Sthapaniya Agama Shakti" - the power to gain what one seeks and place it in their hands.',
      characteristics: 'Hasta natives are skillful, hardworking, and practical individuals. They possess excellent manual dexterity and can create beautiful things with their hands. These people are intelligent, witty, and have a good sense of humor. They are detail-oriented and perfectionist in their approach. Hasta natives are also known for their ability to heal others through touch and their practical problem-solving abilities.',
      behavioral: 'People born under Hasta nakshatra exhibit skillful, practical, and hardworking behavior. They are natural craftspeople who take pride in their work. Their approach to life is methodical and detail-oriented. They have excellent hand-eye coordination and can excel in activities requiring precision. These natives are also known for their helpful nature and willingness to use their skills to benefit others.',
      positiveTraits: 'The positive traits of Hasta natives include their exceptional skills, hardworking nature, and practical intelligence. They are excellent craftspeople and healers who can create and repair things with their hands. Their attention to detail and perfectionist approach ensure high-quality work. They possess good humor and can lighten tense situations. Hasta natives are also known for their reliability, honesty, and helpful nature.',
      negativeTraits: 'The negative traits include perfectionism that can lead to procrastination, tendency to be overly critical, and sometimes being too focused on details at the expense of the bigger picture. They may be impatient with those who don\'t share their standards. Their practical nature might make them appear materialistic. Hasta natives may also struggle with expressing emotions and can be overly reserved.',
      careers: 'Hasta natives excel in careers requiring skill, precision, and manual dexterity. They make excellent craftspeople, artisans, and skilled workers. Medical field, especially surgery and healing arts, suits them well. They can succeed in manufacturing, engineering, and technical fields. Fine arts, sculpture, and detailed artistic work are favorable. They also do well in massage therapy, physiotherapy, and hands-on healing modalities.',
      compatibility: 'Hasta is most compatible with Chitra and Swati nakshatras. The buffalo is the animal symbol of Hasta, which has natural compatibility with tiger (Chitra) and buffalo (Swati). However, they may face challenges with elephant-represented nakshatras. In marriage, Hasta natives are practical and caring partners who express love through service and creating comfort for their loved ones.'
    },
    { 
      name: 'Chitra', lord: 'Mars', deity: 'Vishvakarma', nature: 'Soft/Mridu', guna: 'Tamas',
      description: 'Chitra nakshatra is the fourteenth nakshatra in Vedic astrology, ruled by Mars and presided over by Vishvakarma, the celestial architect. The symbol of Chitra is a bright jewel, pearl, or shining light, representing beauty, craftsmanship, and artistic creation. This nakshatra spans from 23°20 in Kanya (Virgo) to 6°40 in Tula (Libra). Chitra is known as the "Star of Opportunity" and represents the power to create beauty and manifest artistic visions. The shakti of Chitra is "Punya Chayani Shakti" - the power to accumulate merit and create beautiful forms.',
      characteristics: 'Chitra natives are creative, artistic, and possess exceptional aesthetic sense. They have natural charisma and attractive personalities that draw others to them. These people are perfectionists who pay attention to every detail in their creations. They possess good taste and can appreciate and create beauty in various forms. Chitra natives are also known for their ability to see opportunities where others see obstacles.',
      behavioral: 'People born under Chitra nakshatra exhibit creative, charismatic, and perfectionist behavior. They are natural artists who express themselves through various creative mediums. Their approach to life involves creating beauty and harmony in their surroundings. They have excellent taste and can spot quality and authenticity easily. These natives are also known for their diplomatic nature and ability to present things in an attractive manner.',
      positiveTraits: 'The positive traits of Chitra natives include their creativity, artistic abilities, and natural charisma. They are excellent designers and creators who can manifest beautiful things. Their perfectionist approach ensures high-quality work. They possess good social skills and can present ideas attractively. Chitra natives are also known for their ability to see potential in people and situations and their talent for bringing out the best in others.',
      negativeTraits: 'The negative traits include vanity, superficiality, and tendency to be overly concerned with appearances. They may be too focused on external beauty and neglect inner development. Their perfectionist nature can lead to procrastination and dissatisfaction. Chitra natives may also struggle with being overly critical of others and can be manipulative in their pursuit of beauty and perfection.',
      careers: 'Chitra natives excel in careers related to design, arts, and beauty. They make excellent architects, designers, artists, and photographers. Fashion industry, jewelry design, and luxury goods suit them well. They can succeed in media, advertising, and visual arts. Interior design, landscaping, and aesthetic enhancement are favorable fields. They also do well in careers involving presentation, styling, and image consulting.',
      compatibility: 'Chitra is most compatible with Swati and Vishakha nakshatras. The tiger is the animal symbol of Chitra, which has natural compatibility with buffalo (Swati) and tiger (Vishakha). However, they may face challenges with deer-represented nakshatras. In marriage, Chitra natives are romantic and aesthetic partners who create beauty and harmony in relationships.'
    },
    { 
      name: 'Swati', lord: 'Rahu', deity: 'Vayu', nature: 'Movable/Chara', guna: 'Tamas',
      description: 'Swati nakshatra is the fifteenth nakshatra in Vedic astrology, ruled by Rahu and presided over by Vayu, the wind god. The symbol of Swati is a young shoot blown by the wind or a coral, representing flexibility, independence, and growth. This nakshatra spans from 6°40 to 20°00 in Tula Rashi (Libra). Swati is known as the "Star of Independence" and represents the power of movement, change, and adaptation. The shakti of Swati is "Pradhvamsa Shakti" - the power to scatter and disperse.',
      characteristics: 'Swati natives are independent, flexible, and diplomatic individuals. They possess excellent business acumen and adaptability to changing circumstances. These people love freedom and dislike being controlled or restricted. They are natural diplomats who can navigate complex social situations with ease. Swati natives are also known for their ability to influence others and their talent for communication and negotiation.',
      behavioral: 'People born under Swati nakshatra exhibit independent, flexible, and diplomatic behavior. They are natural negotiators who can find common ground between opposing parties. Their approach to life involves maintaining freedom while building beneficial relationships. They have excellent communication skills and can adapt their style to different audiences. These natives are also known for their restless nature and desire for constant movement and change.',
      positiveTraits: 'The positive traits of Swati natives include their independence, diplomatic skills, and business acumen. They are excellent negotiators and mediators who can resolve conflicts effectively. Their adaptability and flexibility help them succeed in various environments. They possess strong communication skills and can influence others positively. Swati natives are also known for their fair-mindedness, balance, and ability to see multiple perspectives.',
      negativeTraits: 'The negative traits include restlessness, indecisiveness, and tendency to be superficial in relationships. They may struggle with commitment and can be unreliable when it comes to long-term obligations. Their desire for freedom might make them appear selfish or uncommitted. Swati natives may also be prone to changing their minds frequently and can be influenced by others too easily.',
      careers: 'Swati natives excel in careers involving communication, negotiation, and business. They make excellent diplomats, mediators, and international business professionals. Sales, marketing, and public relations suit them well. They can succeed in travel, transportation, and logistics. Trade, commerce, and entrepreneurship are favorable fields. They also do well in careers involving movement, change, and adaptation.',
      compatibility: 'Swati is most compatible with Vishakha and Anuradha nakshatras. The buffalo is the animal symbol of Swati, which has natural compatibility with tiger (Vishakha) and deer (Anuradha). However, they may face challenges with lion-represented nakshatras. In marriage, Swati natives need partners who respect their independence while providing emotional stability.'
    },
    { 
      name: 'Vishakha', lord: 'Jupiter', deity: 'Indragni', nature: 'Mixed', guna: 'Rajas',
      description: 'Vishakha nakshatra is the sixteenth nakshatra in Vedic astrology, ruled by Jupiter and presided over by Indra-Agni, representing the combined power of leadership and fire. The symbol of Vishakha is a triumphal arch or a potter\'s wheel, representing achievement, determination, and the power to shape destiny. This nakshatra spans from 20°00 in Tula (Libra) to 3°20 in Vrishchika (Scorpio). Vishakha is known as the "Star of Purpose" and represents focused determination and the ability to achieve goals. The shakti of Vishakha is "Vyapana Shakti" - the power to achieve many fruits in life.',
      characteristics: 'Vishakha natives are determined, goal-oriented, and ambitious individuals. They possess strong leadership qualities and competitive spirit. These people have the ability to focus intensely on their objectives and work persistently towards achieving them. They are natural leaders who can inspire others to follow their vision. Vishakha natives are also known for their ability to transform challenges into opportunities.',
      behavioral: 'People born under Vishakha nakshatra exhibit determined, ambitious, and competitive behavior. They are natural achievers who set high goals for themselves. Their approach to life involves focused effort and persistent action towards their objectives. They have strong willpower and can overcome obstacles through sheer determination. These natives are also known for their leadership abilities and capacity to motivate others.',
      positiveTraits: 'The positive traits of Vishakha natives include their determination, leadership abilities, and goal-oriented nature. They are excellent achievers who can turn their visions into reality. Their competitive spirit drives them to excel in their chosen fields. They possess strong willpower and persistence. Vishakha natives are also known for their ability to inspire others and their capacity for transformation and growth.',
      negativeTraits: 'The negative traits include over-ambition, impatience, and tendency to be ruthless in pursuit of goals. They may become so focused on achievements that they neglect relationships and personal well-being. Their competitive nature might make them appear aggressive or dominating. Vishakha natives may also struggle with jealousy and can be overly critical of those who don\'t share their drive.',
      careers: 'Vishakha natives excel in careers requiring leadership, determination, and goal achievement. They make excellent executives, managers, and entrepreneurs. Politics, competitive sports, and achievement-oriented fields suit them well. They can succeed in business, sales, and target-driven professions. Military, law enforcement, and positions of authority are favorable. They also do well in fields involving transformation, motivation, and inspiring others to achieve.',
      compatibility: 'Vishakha is most compatible with Anuradha and Jyeshtha nakshatras. The tiger is the animal symbol of Vishakha, which has natural compatibility with deer (Anuradha) and mongoose (Jyeshtha). However, they may face challenges with buffalo-represented nakshatras. In marriage, Vishakha natives are passionate and determined partners who bring focus and ambition to relationships.'
    },
    { 
      name: 'Anuradha', lord: 'Saturn', deity: 'Mitra', nature: 'Soft/Mridu', guna: 'Tamas',
      description: 'Anuradha nakshatra is the seventeenth nakshatra in Vedic astrology, ruled by Saturn and presided over by Mitra, the god of friendship and partnership. The symbol of Anuradha is a lotus flower or a triumphal archway, representing success, devotion, and the power of friendship. This nakshatra spans from 3°20 to 16°40 in Vrishchika Rashi (Scorpio). Anuradha is known as the "Star of Success" and represents the power of devotion, friendship, and organized effort. The shakti of Anuradha is "Radhana Shakti" - the power of worship and devotion.',
      characteristics: 'Anuradha natives are devoted, friendly, and successful individuals. They possess excellent organizational abilities and diplomatic skills. These people are naturally inclined towards building strong friendships and partnerships. They have deep spiritual inclinations and often achieve success through devotion and persistent effort. Anuradha natives are also known for their ability to bring people together and create harmonious environments.',
      behavioral: 'People born under Anuradha nakshatra exhibit devoted, diplomatic, and organized behavior. They are natural bridge-builders who can connect different groups and individuals. Their approach to life involves creating harmony and building lasting relationships. They have excellent social skills and can work effectively in teams. These natives are also known for their spiritual nature and dedication to higher causes.',
      positiveTraits: 'The positive traits of Anuradha natives include their devotion, diplomatic skills, and organizational abilities. They are excellent team players who can achieve success through collaboration. Their friendly nature helps them build strong networks and partnerships. They possess deep spiritual wisdom and can guide others on the path of devotion. Anuradha natives are also known for their loyalty, reliability, and ability to create lasting success.',
      negativeTraits: 'The negative traits include over-dependence on others, tendency to be overly accommodating, and sometimes being too trusting. They may sacrifice their own needs for the sake of maintaining harmony. Their desire for approval might make them compromise their principles. Anuradha natives may also struggle with being overly emotional and can be hurt easily by betrayal or rejection.',
      careers: 'Anuradha natives excel in careers involving counseling, diplomacy, and organization. They make excellent counselors, therapists, and human relations professionals. International relations, diplomacy, and cross-cultural work suit them well. They can succeed in spiritual organizations, religious institutions, and charitable work. Event management, hospitality, and team-building are favorable fields. They also do well in careers involving partnerships and collaborative efforts.',
      compatibility: 'Anuradha is most compatible with Jyeshtha and Mula nakshatras. The deer is the animal symbol of Anuradha, which has natural compatibility with mongoose (Jyeshtha) and dog (Mula). However, they may face challenges with tiger-represented nakshatras. In marriage, Anuradha natives are devoted and harmonious partners who prioritize relationship building and mutual success.'
    },
    { 
      name: 'Jyeshtha', lord: 'Mercury', deity: 'Indra', nature: 'Sharp/Tikshna', guna: 'Sattva',
      description: 'Jyeshtha nakshatra is the eighteenth nakshatra in Vedic astrology, ruled by Mercury and presided over by Indra, the king of gods. The symbol of Jyeshtha is an earring, umbrella, or talisman, representing protection, authority, and seniority. This nakshatra spans from 16°40 to 30°00 in Vrishchika Rashi (Scorpio). Jyeshtha is known as the "Star of Seniority" and represents the power of protection, responsibility, and elder wisdom. The shakti of Jyeshtha is "Arohana Shakti" - the power to rise and conquer.',
      characteristics: 'Jyeshtha natives are protective, authoritative, and responsible individuals. They possess natural leadership qualities and a strong sense of duty towards others. These people often take on the role of protector and guide for their family and community. They have excellent administrative abilities and can handle positions of authority effectively. Jyeshtha natives are also known for their generosity and willingness to help those in need.',
      behavioral: 'People born under Jyeshtha nakshatra exhibit protective, responsible, and authoritative behavior. They are natural leaders who take charge in difficult situations. Their approach to life involves taking responsibility for others and ensuring their welfare. They have strong moral principles and can make tough decisions when necessary. These natives are also known for their ability to provide guidance and protection to those under their care.',
      positiveTraits: 'The positive traits of Jyeshtha natives include their protective nature, leadership abilities, and sense of responsibility. They are excellent administrators and managers who can handle complex situations effectively. Their generosity and willingness to help others is remarkable. They possess strong moral courage and can stand up for what is right. Jyeshtha natives are also known for their wisdom, maturity, and ability to guide others.',
      negativeTraits: 'The negative traits include tendency to be overly controlling, authoritarian behavior, and sometimes being too critical of others. They may become possessive and jealous in relationships. Their strong sense of responsibility might make them interfere in others\' lives unnecessarily. Jyeshtha natives may also struggle with pride and can be vindictive towards those who challenge their authority.',
      careers: 'Jyeshtha natives excel in careers involving administration, management, and protection. They make excellent government officials, military officers, and law enforcement professionals. Management, supervision, and executive positions suit them well. They can succeed in fields involving authority, responsibility, and decision-making. Security services, insurance, and protective industries are favorable. They also do well in careers involving guidance, counseling, and elder care.',
      compatibility: 'Jyeshtha is most compatible with Mula and Purva Ashadha nakshatras. The mongoose is the animal symbol of Jyeshtha, which has natural compatibility with dog (Mula) and monkey (Purva Ashadha). However, they may face challenges with deer-represented nakshatras. In marriage, Jyeshtha natives are protective and responsible partners who take their commitments seriously.'
    },
    { 
      name: 'Mula', lord: 'Ketu', deity: 'Nirriti', nature: 'Sharp/Tikshna', guna: 'Tamas',
      description: 'Mula nakshatra is the nineteenth nakshatra in Vedic astrology, ruled by Ketu and presided over by Nirriti, the goddess of destruction and dissolution. The symbol of Mula is a bunch of roots tied together or a lion\'s tail, representing foundation, investigation, and the power to uproot. This nakshatra spans from 0°00 to 13°20 in Dhanus Rashi (Sagittarius). Mula is known as the "Star of Foundation" and represents the power to investigate, research, and get to the root of matters. The shakti of Mula is "Barhana Shakti" - the power to break things apart and destroy.',
      characteristics: 'Mula natives are investigative, research-oriented, and philosophical individuals. They possess a deep desire to understand the fundamental nature of existence. These people are natural researchers who can dig deep to uncover hidden truths. They have transformative abilities and often go through significant life changes. Mula natives are also known for their spiritual seeking nature and ability to help others through difficult transitions.',
      behavioral: 'People born under Mula nakshatra exhibit investigative, philosophical, and transformative behavior. They are natural seekers who question everything and seek deeper understanding. Their approach to life involves getting to the root of problems and finding fundamental solutions. They have a tendency to destroy old patterns to create new ones. These natives are also known for their ability to handle crises and help others through transformative experiences.',
      positiveTraits: 'The positive traits of Mula natives include their investigative abilities, philosophical nature, and transformative power. They are excellent researchers who can uncover hidden knowledge and truths. Their ability to handle crises and help others through difficult times is remarkable. They possess deep spiritual wisdom and can guide others on the path of self-discovery. Mula natives are also known for their courage, determination, and ability to start fresh.',
      negativeTraits: 'The negative traits include destructive tendencies, restlessness, and tendency to be overly critical. They may be prone to creating upheavals in stable situations. Their questioning nature might make them appear skeptical or negative. Mula natives may also struggle with maintaining long-term relationships due to their transformative nature. They might have difficulty accepting conventional wisdom and can be rebellious.',
      careers: 'Mula natives excel in careers involving research, investigation, and transformation. They make excellent researchers, investigators, and detectives. Philosophy, spirituality, and occult sciences suit them well. They can succeed in medicine, psychology, and healing arts. Crisis management, disaster relief, and emergency services are favorable fields. They also do well in careers involving fundamental research, archaeology, and uncovering hidden knowledge.',
      compatibility: 'Mula is most compatible with Purva Ashadha and Uttara Ashadha nakshatras. The dog is the animal symbol of Mula, which has natural compatibility with monkey (Purva Ashadha) and mongoose (Uttara Ashadha). However, they may face challenges with serpent-represented nakshatras. In marriage, Mula natives need partners who can handle their transformative nature and support their spiritual journey.'
    },
    { 
      name: 'Purva Ashadha', lord: 'Venus', deity: 'Apas', nature: 'Fierce/Ugra', guna: 'Rajas',
      description: 'Purva Ashadha nakshatra is the twentieth nakshatra in Vedic astrology, ruled by Venus and presided over by Apas, the water deities. The symbol of Purva Ashadha is a fan, winnowing basket, or elephant tusk, representing purification, invincibility, and the power to cleanse. This nakshatra spans from 13°20 to 26°40 in Dhanus Rashi (Sagittarius). Purva Ashadha is known as the "Star of Invincibility" and represents the power of purification and the ability to remain unconquered. The shakti of Purva Ashadha is "Varchograhana Shakti" - the power to energize and invigorate.',
      characteristics: 'Purva Ashadha natives are invincible, purifying, and influential individuals. They possess natural pride and ambition that drives them to achieve great heights. These people have excellent debating skills and can influence others through their words. They are natural purifiers who can cleanse negative situations and environments. Purva Ashadha natives are also known for their ability to remain unconquered in the face of challenges.',
      behavioral: 'People born under Purva Ashadha nakshatra exhibit proud, ambitious, and influential behavior. They are natural leaders who can inspire others through their conviction and determination. Their approach to life involves purifying and improving whatever they encounter. They have excellent communication skills and can be very persuasive. These natives are also known for their ability to bounce back from setbacks stronger than before.',
      positiveTraits: 'The positive traits of Purva Ashadha natives include their invincible spirit, purifying abilities, and influential nature. They are excellent speakers and debaters who can convince others effectively. Their ability to cleanse and purify negative situations is remarkable. They possess strong willpower and determination. Purva Ashadha natives are also known for their pride in their achievements and their ability to inspire others to reach higher standards.',
      negativeTraits: 'The negative traits include excessive pride, stubbornness, and tendency to be overly argumentative. They may be too focused on winning debates rather than finding truth. Their purifying nature might make them appear critical or judgmental. Purva Ashadha natives may also struggle with accepting defeat and can be vindictive towards opponents. They might have difficulty compromising or seeing other perspectives.',
      careers: 'Purva Ashadha natives excel in careers involving debate, law, and influence. They make excellent lawyers, politicians, and public speakers. Water-related industries, purification systems, and environmental work suit them well. They can succeed in fields involving cleansing, healing, and improvement. Media, journalism, and influence-based careers are favorable. They also do well in positions where they can use their persuasive abilities and fighting spirit.',
      compatibility: 'Purva Ashadha is most compatible with Uttara Ashadha and Shravana nakshatras. The monkey is the animal symbol of Purva Ashadha, which has natural compatibility with mongoose (Uttara Ashadha) and monkey (Shravana). However, they may face challenges with rat-represented nakshatras. In marriage, Purva Ashadha natives are passionate and proud partners who bring energy and purification to relationships.'
    },
    { 
      name: 'Uttara Ashadha', lord: 'Sun', deity: 'Vishvedevas', nature: 'Fixed/Dhruva', guna: 'Rajas',
      description: 'Uttara Ashadha nakshatra is the twenty-first nakshatra in Vedic astrology, ruled by the Sun and presided over by the Vishvadevas, the universal gods. The symbol of Uttara Ashadha is an elephant tusk or a small bed, representing final victory, achievement, and unshakeable determination. This nakshatra spans from 26°40 in Dhanus (Sagittarius) to 10°00 in Makara (Capricorn). Uttara Ashadha is known as the "Star of Victory" and represents the power of final achievement and lasting success. The shakti of Uttara Ashadha is "Apradhrishya Shakti" - the power that cannot be conquered.',
      characteristics: 'Uttara Ashadha natives are victorious, righteous, and possess strong leadership qualities. They have unwavering determination and ethical principles that guide their actions. These people are natural achievers who work steadily towards their goals with patience and persistence. They possess strong moral courage and can stand up for justice and righteousness. Uttara Ashadha natives are also known for their ability to achieve lasting success and create permanent positive changes.',
      behavioral: 'People born under Uttara Ashadha nakshatra exhibit determined, ethical, and goal-oriented behavior. They are natural leaders who inspire others through their integrity and persistence. Their approach to life involves steady progress towards meaningful goals. They have strong moral principles and can make difficult decisions based on what is right. These natives are also known for their ability to remain calm and focused under pressure.',
      positiveTraits: 'The positive traits of Uttara Ashadha natives include their determination, ethical nature, and leadership abilities. They are excellent achievers who can create lasting success through honest means. Their moral courage and integrity inspire others to follow their example. They possess strong willpower and can overcome any obstacle through persistence. Uttara Ashadha natives are also known for their reliability, responsibility, and ability to bring projects to successful completion.',
      negativeTraits: 'The negative traits include stubbornness, inflexibility, and tendency to be overly serious. They may be too rigid in their approach and resistant to change. Their strong moral principles might make them appear judgmental or self-righteous. Uttara Ashadha natives may also struggle with being overly demanding of themselves and others. They might have difficulty relaxing and enjoying life due to their focus on achievements.',
      careers: 'Uttara Ashadha natives excel in careers involving leadership, ethics, and long-term achievement. They make excellent government officials, judges, and ethical leaders. Law, justice, and social causes suit them well. They can succeed in fields requiring persistence, determination, and moral courage. Corporate leadership, project management, and goal-oriented professions are favorable. They also do well in careers involving permanent achievements and lasting contributions to society.',
      compatibility: 'Uttara Ashadha is most compatible with Shravana and Dhanishta nakshatras. The mongoose is the animal symbol of Uttara Ashadha, which has natural compatibility with monkey (Shravana) and lion (Dhanishta). However, they may face challenges with cow-represented nakshatras. In marriage, Uttara Ashadha natives are committed and reliable partners who bring stability and achievement-oriented focus to relationships.'
    },
    { 
      name: 'Shravana', lord: 'Moon', deity: 'Vishnu', nature: 'Movable/Chara', guna: 'Rajas',
      description: 'Shravana nakshatra is the twenty-second nakshatra in Vedic astrology, ruled by the Moon and presided over by Vishnu, the preserver god. The symbol of Shravana is an ear or three footprints, representing listening, learning, and the path of knowledge. This nakshatra spans from 10°00 to 23°20 in Makara Rashi (Capricorn). Shravana is known as the "Star of Learning" and represents the power of listening, acquiring knowledge, and preserving wisdom. The shakti of Shravana is "Samhanana Shakti" - the power to connect and link things together.',
      characteristics: 'Shravana natives are excellent listeners, knowledgeable, and wise individuals. They possess natural scholarly abilities and have a deep respect for learning and tradition. These people are excellent communicators who can preserve and transmit knowledge effectively. They have good memory and can absorb information quickly. Shravana natives are also known for their ability to connect different pieces of information and create meaningful understanding.',
      behavioral: 'People born under Shravana nakshatra exhibit attentive, scholarly, and communicative behavior. They are natural students and teachers who value knowledge and wisdom. Their approach to life involves continuous learning and sharing of information. They have excellent listening skills and can understand others deeply. These natives are also known for their respect for tradition and their ability to preserve cultural knowledge.',
      positiveTraits: 'The positive traits of Shravana natives include their listening abilities, scholarly nature, and communication skills. They are excellent learners who can acquire and retain vast amounts of knowledge. Their ability to connect different concepts and create understanding is remarkable. They possess good memory and can preserve important information. Shravana natives are also known for their wisdom, patience, and ability to guide others through their knowledge.',
      negativeTraits: 'The negative traits include tendency to be overly talkative, gossipy nature, and sometimes being too focused on gathering information without practical application. They may be prone to spreading rumors or sharing confidential information. Their scholarly nature might make them appear pedantic or overly intellectual. Shravana natives may also struggle with being overly dependent on others for validation of their knowledge.',
      careers: 'Shravana natives excel in careers involving education, communication, and knowledge preservation. They make excellent teachers, professors, and educational administrators. Media, journalism, and information technology suit them well. They can succeed in counseling, therapy, and advisory roles. Library science, research, and traditional knowledge preservation are favorable fields. They also do well in careers involving listening, learning, and transmitting information.',
      compatibility: 'Shravana is most compatible with Dhanishta and Shatabhisha nakshatras. The monkey is the animal symbol of Shravana, which has natural compatibility with lion (Dhanishta) and horse (Shatabhisha). However, they may face challenges with tiger-represented nakshatras. In marriage, Shravana natives are attentive and communicative partners who value intellectual connection and shared learning.'
    },
    { 
      name: 'Dhanishta', lord: 'Mars', deity: 'Vasus', nature: 'Movable/Chara', guna: 'Tamas',
      description: 'The general characteristics of Dhanishta nakshatra derives its potency from the eight deities or "Vasus" governing it. Thus the nakshatra combines and epitomizes the general characteristics of the respective Vasus. Ruled by Apah, Dhruva, Dhara, Anila, Anala, Pratyusa, Pravasha and Soma; the nakshatra stands for ability in music dance, confidence, stability, dependability, hard work, energy, exceptional sharpness, commercial skills and benevolence. The dolphin like constellation endowed with the mystical "Khyapayitri shakti", bestows upon its native fame, success and prosperity in abundance.',
      characteristics: 'Exhibiting a wide variety in its personality traits, natives of Dhanishta nakshatra are well known for their sociability and adaptability. With their captivating smile and endearing ways, they are exceptionally fine tuned in striking a comfort zone with the given surrounding. Manifesting vivacity, confidence and constancy of purpose, personality traits of such natives are geared to luxury and good life. Being one of the most vibrant nakshatras the natives born with Dhanishta in ascendance are equally charitable and wise.',
      behavioral: 'With its instinctive sociability and expressive ways, behavioral characteristics of such natives are oriented towards group centric activities. In spite of being motivated by a constancy of purpose, natives born under the influence of Dhanishta Nakshatra are extremely adjustable or adaptable to changing needs of the environment. Marked by sharpness, generosity and frank joviality, the natives are usually outgoing and luxury prone in their behavioral characteristics.',
      positiveTraits: 'Positive traits geared to warmly vibrant mannerisms, frankness and easy adaptability characterize the natives born with Dhanishta in ascendance. Ability to shine in lines related to performing arts such as music and dance also counts amongst their multi dimensional positive traits. Striking a bond of geniality and harmony with the immediate surroundings is a uniquely laudable trait of these natives. Revealing the positive facets of hopefulness, joy and sympathy; natives of the mentioned nakshatra are given to much success and achievements.',
      negativeTraits: 'Their charmingly sociable mannerisms may prove to be a curse for them on account of their easy susceptibility to the influences of society. Being spurred on by negatives, they may manifest subsequent negativity in their behavioral traits. Apart from their easy susceptibility to influence, the other negative traits include aggression, talkativeness, materialistic ways, covetousness, lust for success and susceptibility to select incompatible life partners.',
      careers: 'Besides doing fine in careers related to performing arts, natives of Dhanishta nakshatra can curve exceptional niche in managerial positions and ones catering to group activities. Thus career opportunities based on management and entrepreneurship are also suitable for them. They are found to be equally prosperous in medical profession; particularly in specialized branch of surgery. Equally successful they may turn out to be in career opportunities revolving around military bands, real estate and scientific research.',
      compatibility: 'Going by the norms of Veda Dosha or principles of stellar obstruction; Mrigashirsha and Chitra are incompatible to Dhanishta nakshatra. Keeping in mind the concept of instinctive compatibility or "yoni kuta", Dhanishta nakshatra is most compatible to Purva Bhadrapada Nakshatra represented by a masculine lion. Taking into account elephants phallic incompatibility to lion; both the birth stars represented by elephant ie., Bharani & Revati are non compatible to Dhanishta nakshatra. Likewise following lions neutrality with monkey, and mongoose- the stars such as Shravana, Purvashadha, Uttarashada, may be partially compatible to it.'
    },
    { 
      name: 'Shatabhisha', lord: 'Rahu', deity: 'Varuna', nature: 'Movable/Chara', guna: 'Tamas',
      description: 'Shatabhisha nakshatra is the twenty-fourth nakshatra in Vedic astrology, ruled by Rahu and presided over by Varuna, the god of cosmic waters and healing. The symbol of Shatabhisha is an empty circle or a hundred healers, representing healing, medicine, and the power of emptiness. This nakshatra spans from 6°40 to 20°00 in Kumbha Rashi (Aquarius). Shatabhisha is known as the "Star of Healing" and represents the power of healing, research, and unconventional approaches. The shakti of Shatabhisha is "Bheshaja Shakti" - the power of healing and medicine.',
      characteristics: 'Shatabhisha natives possess natural healing abilities and are independent, mysterious individuals. They have a strong inclination towards research and unconventional approaches to problems. These people are natural healers who can understand the root causes of ailments and provide effective remedies. They prefer to work independently and often have unique perspectives on life. Shatabhisha natives are also known for their ability to see beyond conventional boundaries and explore new frontiers.',
      behavioral: 'People born under Shatabhisha nakshatra exhibit independent, mysterious, and research-oriented behavior. They are natural healers who approach problems from unique angles. Their approach to life involves exploring unconventional methods and challenging established norms. They have excellent analytical abilities and can see patterns that others miss. These natives are also known for their preference for solitude and their ability to work effectively alone.',
      positiveTraits: 'The positive traits of Shatabhisha natives include their healing abilities, independent nature, and research skills. They are excellent healers who can provide innovative solutions to health problems. Their ability to think outside conventional boundaries is remarkable. They possess strong analytical skills and can conduct thorough research. Shatabhisha natives are also known for their honesty, directness, and ability to see truth clearly.',
      negativeTraits: 'The negative traits include tendency to be overly secretive, stubborn nature, and sometimes being too unconventional for practical purposes. They may be prone to isolation and can appear aloof or detached. Their independent nature might make them resistant to teamwork. Shatabhisha natives may also struggle with being overly critical of conventional methods and can be dismissive of others\' approaches.',
      careers: 'Shatabhisha natives excel in careers involving healing, research, and unconventional fields. They make excellent doctors, researchers, and alternative healers. Astronomy, astrology, and occult sciences suit them well. They can succeed in fields involving innovation, technology, and breakthrough discoveries. Medical research, pharmaceutical development, and healing arts are favorable. They also do well in careers involving independence, analysis, and unconventional approaches.',
      compatibility: 'Shatabhisha is most compatible with Purva Bhadrapada and Uttara Bhadrapada nakshatras. The horse is the animal symbol of Shatabhisha, which has natural compatibility with lion (Purva Bhadrapada) and cow (Uttara Bhadrapada). However, they may face challenges with tiger-represented nakshatras. In marriage, Shatabhisha natives need partners who respect their independence and support their unconventional approaches.'
    },
    { 
      name: 'Purva Bhadrapada', lord: 'Jupiter', deity: 'Aja Ekapada', nature: 'Fierce/Ugra', guna: 'Rajas',
      description: 'Purva Bhadrapada nakshatra is the twenty-fifth nakshatra in Vedic astrology, ruled by Jupiter and presided over by Aja Ekapada, the one-footed goat representing the unborn and eternal fire. The symbol of Purva Bhadrapada is a sword, two front legs of a bed, or a man with two faces, representing transformation, duality, and the power of spiritual fire. This nakshatra spans from 20°00 in Kumbha (Aquarius) to 3°20 in Meena (Pisces). Purva Bhadrapada is known as the "Star of Burning" and represents the power of transformation through spiritual fire. The shakti of Purva Bhadrapada is "Yajamana Udyamana Shakti" - the power to elevate through spiritual practices.',
      characteristics: 'Purva Bhadrapada natives are transformative, spiritual, and intense individuals. They possess deep philosophical inclinations and often experience significant life transformations. These people have a dual nature and can see both sides of any situation. They are passionate about spiritual growth and often undergo intense experiences that lead to wisdom. Purva Bhadrapada natives are also known for their ability to help others through transformative processes.',
      behavioral: 'People born under Purva Bhadrapada nakshatra exhibit intense, philosophical, and transformative behavior. They are natural seekers who are drawn to deep spiritual and philosophical questions. Their approach to life involves constant transformation and growth. They have a tendency to experience extremes and can be both passionate and detached. These natives are also known for their ability to see the deeper meaning in life experiences.',
      positiveTraits: 'The positive traits of Purva Bhadrapada natives include their transformative abilities, spiritual wisdom, and philosophical nature. They are excellent guides who can help others through difficult transitions. Their ability to see both sides of situations makes them good counselors. They possess deep spiritual insight and can access higher wisdom. Purva Bhadrapada natives are also known for their passion, intensity, and ability to inspire others towards spiritual growth.',
      negativeTraits: 'The negative traits include tendency towards extremes, unpredictable behavior, and sometimes being overly intense. They may be prone to mood swings and can be difficult to understand. Their transformative nature might make them appear unstable or unreliable. Purva Bhadrapada natives may also struggle with being overly critical of materialistic pursuits and can be judgmental of others\' spiritual progress.',
      careers: 'Purva Bhadrapada natives excel in careers involving spirituality, philosophy, and transformation. They make excellent spiritual teachers, philosophers, and transformational coaches. Occult sciences, mysticism, and esoteric studies suit them well. They can succeed in fields involving intense research, psychology, and healing. Funeral services, crisis counseling, and transformational work are favorable. They also do well in careers involving fire, energy, and spiritual practices.',
      compatibility: 'Purva Bhadrapada is most compatible with Uttara Bhadrapada and Revati nakshatras. The lion is the animal symbol of Purva Bhadrapada, which has natural compatibility with cow (Uttara Bhadrapada) and elephant (Revati). However, they may face challenges with deer-represented nakshatras. In marriage, Purva Bhadrapada natives are intense and transformative partners who bring spiritual depth to relationships.'
    },
    { 
      name: 'Uttara Bhadrapada', lord: 'Saturn', deity: 'Ahir Budhnya', nature: 'Fixed/Dhruva', guna: 'Tamas',
      description: 'Uttara Bhadrapada nakshatra is the twenty-sixth nakshatra in Vedic astrology, ruled by Saturn and presided over by Ahir Budhnya, the serpent of the deep sea representing the depths of cosmic consciousness. The symbol of Uttara Bhadrapada is the back legs of a bed, a twin man, or a serpent in water, representing depth, stability, and the power of the unconscious. This nakshatra spans from 3°20 to 16°40 in Meena Rashi (Pisces). Uttara Bhadrapada is known as the "Star of Foundation" and represents the power of depth, stability, and cosmic consciousness. The shakti of Uttara Bhadrapada is "Varshodyamana Shakti" - the power to bring rain and cosmic blessings.',
      characteristics: 'Uttara Bhadrapada natives are deep, stable, and wise individuals. They possess profound spiritual wisdom and have access to the depths of cosmic consciousness. These people are excellent planners who can see the long-term implications of actions. They have a mysterious quality and often possess psychic or intuitive abilities. Uttara Bhadrapada natives are also known for their patience, stability, and ability to provide strong foundations for others.',
      behavioral: 'People born under Uttara Bhadrapada nakshatra exhibit deep, stable, and mysterious behavior. They are natural planners who think carefully before taking action. Their approach to life involves building strong foundations and working towards long-term goals. They have excellent patience and can wait for the right time to act. These natives are also known for their spiritual depth and ability to access higher wisdom.',
      positiveTraits: 'The positive traits of Uttara Bhadrapada natives include their depth, stability, and wisdom. They are excellent planners and strategists who can create lasting foundations. Their spiritual insight and intuitive abilities are remarkable. They possess great patience and can handle long-term projects effectively. Uttara Bhadrapada natives are also known for their reliability, loyalty, and ability to provide emotional and spiritual support to others.',
      negativeTraits: 'The negative traits include tendency to be overly serious, pessimistic outlook, and sometimes being too slow to act. They may be prone to depression and can become withdrawn or isolated. Their deep nature might make them appear aloof or unapproachable. Uttara Bhadrapada natives may also struggle with being overly cautious and can miss opportunities due to over-analysis.',
      careers: 'Uttara Bhadrapada natives excel in careers involving planning, spirituality, and depth work. They make excellent counselors, therapists, and spiritual advisors. Long-term planning, strategy, and foundation work suit them well. They can succeed in fields involving water, depth research, and unconscious exploration. Psychology, psychiatry, and deep healing are favorable. They also do well in careers involving stability, patience, and long-term commitment.',
      compatibility: 'Uttara Bhadrapada is most compatible with Revati and Ashwini nakshatras. The cow is the animal symbol of Uttara Bhadrapada, which has natural compatibility with elephant (Revati) and horse (Ashwini). However, they may face challenges with sheep-represented nakshatras. In marriage, Uttara Bhadrapada natives are stable and deeply committed partners who provide emotional and spiritual foundation to relationships.'
    },
    { 
      name: 'Revati', lord: 'Mercury', deity: 'Pushan', nature: 'Soft/Mridu', guna: 'Sattva',
      description: 'Revati nakshatra is the twenty-seventh and final nakshatra in Vedic astrology, ruled by Mercury and presided over by Pushan, the nourisher and protector deity. The symbol of Revati is a fish swimming in the sea or a drum, representing nourishment, prosperity, and the completion of the cosmic cycle. This nakshatra spans from 16°40 to 30°00 in Meena Rashi (Pisces). Revati is known as the "Star of Wealth" and represents the power of nourishment, protection, and completion. The shakti of Revati is "Kshiradyapani Shakti" - the power to nourish and foster growth.',
      characteristics: 'Revati natives are nourishing, prosperous, and protective individuals. They possess natural kindness and have a strong desire to help and protect others. These people are blessed with wealth and prosperity, both material and spiritual. They are excellent travelers and can adapt to different environments easily. Revati natives are also known for their ability to complete projects and bring things to successful conclusion.',
      behavioral: 'People born under Revati nakshatra exhibit nourishing, protective, and kind behavior. They are natural caregivers who put others\' welfare before their own. Their approach to life involves creating prosperity and abundance for themselves and others. They have excellent social skills and can make others feel comfortable and cared for. These natives are also known for their ability to bring projects to completion and their talent for finishing what others start.',
      positiveTraits: 'The positive traits of Revati natives include their nourishing nature, prosperity consciousness, and protective instincts. They are excellent caregivers who can provide both material and emotional support to others. Their ability to create wealth and abundance is remarkable. They possess natural kindness and compassion. Revati natives are also known for their completion abilities, travel skills, and talent for bringing harmony and prosperity wherever they go.',
      negativeTraits: 'The negative traits include tendency to be overly protective, possessive nature, and sometimes being too giving for their own good. They may be prone to spoiling others and can be taken advantage of due to their generous nature. Their protective instincts might make them interfere in others\' lives unnecessarily. Revati natives may also struggle with being overly emotional and can be hurt easily by ingratitude.',
      careers: 'Revati natives excel in careers involving nourishment, travel, and completion work. They make excellent hospitality professionals, travel agents, and tourism operators. Food industry, nutrition, and catering suit them well. They can succeed in fields involving protection, security, and care services. Completion work, project finishing, and final stages of development are favorable. They also do well in careers involving prosperity creation, wealth management, and abundance work.',
      compatibility: 'Revati is most compatible with Ashwini and Bharani nakshatras. The elephant is the animal symbol of Revati, which has natural compatibility with horse (Ashwini) and elephant (Bharani). However, they may face challenges with deer-represented nakshatras. In marriage, Revati natives are nourishing and protective partners who create prosperity and completion in relationships.'
    }
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
      const nakshatraData = nakshatras[nakshatra.index];
      
      return {
        planet: name,
        longitude: data.longitude.toFixed(2),
        nakshatra: nakshatraData?.name || 'Unknown',
        pada: nakshatra.pada,
        lord: nakshatraData?.lord || 'Unknown',
        deity: nakshatraData?.deity || 'Unknown',
        nature: nakshatraData?.nature || 'Unknown',
        guna: nakshatraData?.guna || 'Unknown'
      };
    });
  };

  const planetaryPositions = getPlanetaryPositions();

  return (
    <div style={{ 
      display: 'grid', 
      gridTemplateColumns: window.innerWidth <= 768 
        ? '1fr' 
        : selectedNakshatra ? '300px 1fr' : '1fr 1fr', 
      gap: '1rem', 
      height: '100%' 
    }}>
      {/* Left side - Planetary Positions */}
      <div>
        <h3 style={{ color: '#e91e63', marginBottom: '1rem', fontSize: '1.1rem' }}>
          🌟 Planetary Positions in Nakshatras
        </h3>
        <div style={{ 
          maxHeight: window.innerWidth <= 768 
            ? selectedNakshatra ? '30vh' : '25vh'
            : selectedNakshatra ? '25vh' : '20vh', 
          overflowY: 'auto',
          overflowX: 'auto',
          border: '1px solid #e91e63',
          borderRadius: '8px',
          WebkitOverflowScrolling: 'touch'
        }}>
          <table style={{ 
            width: '100%', 
            fontSize: window.innerWidth <= 768 ? '0.7rem' : '0.8rem',
            minWidth: window.innerWidth <= 768 ? '280px' : 'auto'
          }}>
            <thead style={{ background: '#e91e63', color: 'white', position: 'sticky', top: 0 }}>
              <tr>
                <th style={{ padding: window.innerWidth <= 768 ? '0.3rem' : '0.5rem', textAlign: 'left' }}>Planet</th>
                <th style={{ padding: window.innerWidth <= 768 ? '0.3rem' : '0.5rem', textAlign: 'left' }}>Nakshatra</th>
                <th style={{ padding: window.innerWidth <= 768 ? '0.3rem' : '0.5rem', textAlign: 'center' }}>Pada</th>
                <th style={{ padding: window.innerWidth <= 768 ? '0.3rem' : '0.5rem', textAlign: 'left' }}>Lord</th>
              </tr>
            </thead>
            <tbody>
              {planetaryPositions.map((pos, index) => (
                <tr key={pos.planet} style={{ 
                  background: index % 2 === 0 ? '#f9f9f9' : 'white',
                  borderBottom: '1px solid #eee',
                  cursor: 'pointer'
                }}
                onClick={() => setSelectedNakshatra(nakshatras.find(n => n.name === pos.nakshatra))}>
                  <td style={{ padding: window.innerWidth <= 768 ? '0.3rem' : '0.4rem', fontWeight: '600', color: '#e91e63' }}>
                    {pos.planet}
                  </td>
                  <td style={{ padding: window.innerWidth <= 768 ? '0.3rem' : '0.4rem', color: '#0066cc', textDecoration: 'underline' }}>{pos.nakshatra}</td>
                  <td style={{ padding: window.innerWidth <= 768 ? '0.3rem' : '0.4rem', textAlign: 'center', fontWeight: '600' }}>
                    {pos.pada}
                  </td>
                  <td style={{ padding: window.innerWidth <= 768 ? '0.3rem' : '0.4rem', color: '#666' }}>{pos.lord}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {!selectedNakshatra && (
          <div style={{ marginTop: '1rem' }}>
            <h4 style={{ color: '#ff6f00', fontSize: '0.9rem', marginBottom: '0.5rem' }}>📚 All Nakshatras</h4>
            <div style={{ 
              maxHeight: '25vh', 
              overflowY: 'auto',
              border: '1px solid #ff6f00',
              borderRadius: '8px'
            }}>
              <div style={{ padding: '0.5rem' }}>
                {nakshatras.map((nak, index) => (
                  <div key={nak.name} 
                       onClick={() => setSelectedNakshatra(nak)}
                       style={{ 
                         padding: '0.3rem 0.5rem',
                         cursor: 'pointer',
                         borderRadius: '4px',
                         marginBottom: '0.2rem',
                         background: index % 2 === 0 ? '#fff8f0' : 'white',
                         border: '1px solid #eee',
                         fontSize: '0.8rem',
                         color: '#0066cc',
                         textDecoration: 'underline'
                       }}>
                    {index + 1}. {nak.name} - {nak.lord}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Right side - Detailed Nakshatra Information */}
      <div>
        {selectedNakshatra ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ color: '#e91e63', fontSize: '1.2rem', margin: 0 }}>
                🌟 {selectedNakshatra.name} Nakshatra
              </h3>
              <button 
                onClick={() => setSelectedNakshatra(null)}
                style={{
                  marginLeft: '1rem',
                  padding: '0.3rem 0.6rem',
                  background: '#e91e63',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.7rem'
                }}
              >
                ← Back
              </button>
            </div>
            
            <div style={{ 
              maxHeight: window.innerWidth <= 768 ? '50vh' : '60vh', 
              overflowY: 'auto',
              border: '1px solid #e91e63',
              borderRadius: '8px',
              padding: window.innerWidth <= 768 ? '0.5rem' : '1rem',
              background: 'white',
              WebkitOverflowScrolling: 'touch'
            }}>
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: window.innerWidth <= 768 ? '1fr' : '1fr 1fr', 
                  gap: window.innerWidth <= 768 ? '0.5rem' : '1rem', 
                  marginBottom: '1rem' 
                }}>
                  <div><strong>Lord:</strong> {selectedNakshatra.lord}</div>
                  <div><strong>Deity:</strong> {selectedNakshatra.deity}</div>
                  <div><strong>Nature:</strong> {selectedNakshatra.nature}</div>
                  <div><strong>Guna:</strong> {selectedNakshatra.guna}</div>
                </div>
              </div>
              
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ color: '#ff6f00', fontSize: window.innerWidth <= 768 ? '0.9rem' : '1rem', marginBottom: '0.5rem' }}>📖 Basic Information</h4>
                <p style={{ fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem', lineHeight: '1.5', color: '#333', textAlign: 'justify' }}>
                  {selectedNakshatra.description}
                </p>
              </div>
              
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ color: '#ff6f00', fontSize: window.innerWidth <= 768 ? '0.9rem' : '1rem', marginBottom: '0.5rem' }}>✨ General Characteristics</h4>
                <p style={{ fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem', lineHeight: '1.5', color: '#333', textAlign: 'justify' }}>
                  {selectedNakshatra.characteristics}
                </p>
              </div>
              
              {selectedNakshatra.behavioral && (
                <div style={{ marginBottom: '1rem' }}>
                  <h4 style={{ color: '#ff6f00', fontSize: window.innerWidth <= 768 ? '0.9rem' : '1rem', marginBottom: '0.5rem' }}>🎭 Behavioral Characteristics</h4>
                  <p style={{ fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem', lineHeight: '1.5', color: '#333', textAlign: 'justify' }}>
                    {selectedNakshatra.behavioral}
                  </p>
                </div>
              )}
              
              {selectedNakshatra.positiveTraits && (
                <div style={{ marginBottom: '1rem' }}>
                  <h4 style={{ color: '#22c55e', fontSize: window.innerWidth <= 768 ? '0.9rem' : '1rem', marginBottom: '0.5rem' }}>✅ Positive Traits</h4>
                  <p style={{ fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem', lineHeight: '1.5', color: '#333', textAlign: 'justify' }}>
                    {selectedNakshatra.positiveTraits}
                  </p>
                </div>
              )}
              
              {selectedNakshatra.negativeTraits && (
                <div style={{ marginBottom: '1rem' }}>
                  <h4 style={{ color: '#ef4444', fontSize: window.innerWidth <= 768 ? '0.9rem' : '1rem', marginBottom: '0.5rem' }}>⚠️ Negative Traits</h4>
                  <p style={{ fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem', lineHeight: '1.5', color: '#333', textAlign: 'justify' }}>
                    {selectedNakshatra.negativeTraits}
                  </p>
                </div>
              )}
              
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ color: '#ff6f00', fontSize: window.innerWidth <= 768 ? '0.9rem' : '1rem', marginBottom: '0.5rem' }}>💼 Career Options</h4>
                <p style={{ fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem', lineHeight: '1.5', color: '#333', textAlign: 'justify' }}>
                  {selectedNakshatra.careers}
                </p>
              </div>
              
              <div>
                <h4 style={{ color: '#ff6f00', fontSize: window.innerWidth <= 768 ? '0.9rem' : '1rem', marginBottom: '0.5rem' }}>🤝 Compatibility and Incompatibility</h4>
                <p style={{ fontSize: window.innerWidth <= 768 ? '0.8rem' : '0.9rem', lineHeight: '1.5', color: '#333', textAlign: 'justify' }}>
                  {selectedNakshatra.compatibility}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div>
            <h3 style={{ color: '#e91e63', marginBottom: '1rem', fontSize: '1.1rem' }}>
              📚 Click any Nakshatra for detailed information
            </h3>
            <div style={{ 
              padding: '2rem',
              textAlign: 'center',
              border: '2px dashed #e91e63',
              borderRadius: '8px',
              color: '#666'
            }}>
              <p>Select a nakshatra from the planetary positions table or the list on the left to view detailed characteristics, career options, compatibility, and more comprehensive information.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NakshatrasTab;