import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import NavigationHeader from '../../Shared/NavigationHeader';
import './LessonPage.css';

const LessonPage = () => {
  const { lessonId } = useParams();
  const navigate = useNavigate();

  const lessons = {
    1: {
      title: "What is Astrology?",
      duration: "5 min read",
      level: "Beginner",
      content: `
        <h2>Introduction to Astrology</h2>
        <p>Astrology is an ancient practice that studies the correlation between celestial movements and human experiences. It's based on the belief that the positions and movements of celestial bodies can influence human affairs and natural phenomena.</p>
        
        <h3>Historical Background</h3>
        <p>Astrology has been practiced for thousands of years across different cultures:</p>
        <ul>
          <li><strong>Mesopotamian Origins:</strong> The earliest astrological records date back to ancient Babylon (2000 BCE)</li>
          <li><strong>Egyptian Influence:</strong> Egyptians developed the concept of decans and horoscopic astrology</li>
          <li><strong>Greek Development:</strong> Greeks systematized astrology and created the zodiac system we know today</li>
          <li><strong>Indian Tradition:</strong> Vedic astrology (Jyotish) developed independently with its own sophisticated system</li>
        </ul>

        <h3>Vedic vs Western Systems</h3>
        <div class="comparison-table">
          <div class="comparison-item">
            <h4>Vedic Astrology (Jyotish)</h4>
            <ul>
              <li>Uses sidereal zodiac (based on actual star positions)</li>
              <li>Includes lunar mansions (Nakshatras)</li>
              <li>Emphasizes karma and spiritual evolution</li>
              <li>Uses planetary periods (Dashas) for timing</li>
            </ul>
          </div>
          <div class="comparison-item">
            <h4>Western Astrology</h4>
            <ul>
              <li>Uses tropical zodiac (based on seasons)</li>
              <li>Focuses on psychological interpretation</li>
              <li>Emphasizes personality and relationships</li>
              <li>Uses transits and progressions for timing</li>
            </ul>
          </div>
        </div>

        <h3>Basic Principles</h3>
        <p>Astrology operates on several fundamental principles:</p>
        <ol>
          <li><strong>As Above, So Below:</strong> The macrocosm reflects in the microcosm</li>
          <li><strong>Synchronicity:</strong> Meaningful coincidences between celestial and earthly events</li>
          <li><strong>Cycles and Patterns:</strong> Planetary movements create recurring patterns</li>
          <li><strong>Symbolic Language:</strong> Planets, signs, and houses represent archetypal energies</li>
        </ol>
      `,
      nextLesson: 2
    },
    2: {
      title: "The Zodiac Signs",
      duration: "8 min read", 
      level: "Beginner",
      content: `
        <h2>Understanding the 12 Zodiac Signs</h2>
        <p>The zodiac is a belt of the heavens divided into 12 equal parts, each associated with specific characteristics and ruled by particular planets.</p>

        <h3>The Four Elements</h3>
        <div class="elements-grid">
          <div class="element fire">
            <h4>🔥 Fire Signs</h4>
            <p><strong>Aries, Leo, Sagittarius</strong></p>
            <p>Energetic, passionate, spontaneous, and action-oriented</p>
          </div>
          <div class="element earth">
            <h4>🌍 Earth Signs</h4>
            <p><strong>Taurus, Virgo, Capricorn</strong></p>
            <p>Practical, grounded, reliable, and material-focused</p>
          </div>
          <div class="element air">
            <h4>💨 Air Signs</h4>
            <p><strong>Gemini, Libra, Aquarius</strong></p>
            <p>Intellectual, communicative, social, and idea-focused</p>
          </div>
          <div class="element water">
            <h4>💧 Water Signs</h4>
            <p><strong>Cancer, Scorpio, Pisces</strong></p>
            <p>Emotional, intuitive, sensitive, and feeling-oriented</p>
          </div>
        </div>
      `,
      nextLesson: 3
    },
    7: {
      title: "Nakshatras (Lunar Mansions)",
      duration: "45 min read", 
      level: "Advanced",
      content: `
        <h2>Complete Mastery Guide to the 27 Nakshatras</h2>
        <p>Nakshatras are the 27 lunar mansions that form the backbone of Vedic astrology. Each spans exactly 13°20' and represents a complete archetypal energy pattern that influences personality, destiny, and spiritual evolution.</p>

        <h3>Understanding Nakshatra Components</h3>
        <div class="comparison-table">
          <div class="comparison-item">
            <h4>Essential Elements</h4>
            <ul>
              <li><strong>Ruling Deity:</strong> Divine consciousness governing the star</li>
              <li><strong>Planetary Lord:</strong> For Vimshottari Dasha calculations</li>
              <li><strong>Symbol:</strong> Core archetypal representation</li>
              <li><strong>Power (Shakti):</strong> Specific cosmic ability</li>
              <li><strong>Result:</strong> What the power achieves</li>
              <li><strong>Basis:</strong> Foundation of the power</li>
            </ul>
          </div>
          <div class="comparison-item">
            <h4>Classification System</h4>
            <ul>
              <li><strong>Guna:</strong> Sattva (harmony), Rajas (activity), Tamas (inertia)</li>
              <li><strong>Gana:</strong> Deva (divine), Manushya (human), Rakshasa (demonic)</li>
              <li><strong>Yoni:</strong> Animal nature and instinctive behavior</li>
              <li><strong>Caste:</strong> Brahmin, Kshatriya, Vaishya, Shudra</li>
              <li><strong>Direction:</strong> Spatial orientation and movement</li>
              <li><strong>Gender:</strong> Masculine, feminine, or neuter energy</li>
            </ul>
          </div>
        </div>

        <div class="nakshatra-list">
          <div class="nakshatra-item">
            <h4>1. Ashwini - The Horsemen (0°00' - 13°20' Aries)</h4>
            <p><strong>Symbol:</strong> Horse's head | <strong>Deity:</strong> Ashwini Kumaras (Divine physicians) | <strong>Lord:</strong> Ketu</p>
            <p><strong>Shakti:</strong> Shidhra Vyapani Shakti (power to quickly reach things) | <strong>Result:</strong> Healing and rejuvenation</p>
            <p><strong>Animal:</strong> Male Horse | <strong>Guna:</strong> Rajas | <strong>Gana:</strong> Deva | <strong>Caste:</strong> Vaishya</p>
            
            <p><strong>Deep Characteristics:</strong> Ashwini natives possess lightning-fast reflexes and an innate ability to initiate healing processes. They are the cosmic paramedics, always first to arrive at any crisis. Their horse-like nature makes them restless, always seeking new adventures and challenges. They have a childlike innocence combined with ancient wisdom about healing arts.</p>
            
            <p><strong>Psychological Profile:</strong> Impulsive decision-makers who trust their instincts completely. They have difficulty with patience and detailed planning but excel in emergency situations. Natural optimists who bounce back quickly from setbacks. Often appear younger than their age and maintain enthusiasm throughout life.</p>
            
            <p><strong>Spiritual Significance:</strong> Represents the beginning of the zodiacal journey - pure, untainted energy ready to manifest. They are here to learn about proper use of power and the responsibility that comes with healing abilities. Past life connections to healing traditions and emergency services.</p>
            
            <p><strong>Health Tendencies:</strong> Head injuries, accidents, blood pressure issues, eye problems. Strong recuperative powers but tendency toward accidents due to impulsiveness. Benefit from regular physical exercise and martial arts.</p>
            
            <p><strong>Career Mastery:</strong> Emergency medicine, paramedics, sports medicine, veterinary care, race car driving, aviation, pioneering research, startup businesses, adventure sports, military special forces.</p>
            
            <p><strong>Relationship Patterns:</strong> Fall in love quickly but may lose interest just as fast. Need partners who can match their energy and independence. Loyal once committed but require freedom. Best matches with other fire signs or air signs who appreciate their spontaneity.</p>
            
            <p><strong>Remedial Measures:</strong> Worship of Ganesha for removing obstacles. Chanting "Om Ashwini Kumarabhyam Namaha." Wearing gold or copper. Donating to medical causes. Practicing patience through meditation.</p>
          </div>

          <div class="nakshatra-item">
            <h4>2. Bharani - The Bearer (13°20' - 26°40' Aries)</h4>
            <p><strong>Symbol:</strong> Yoni (Vulva) | <strong>Deity:</strong> Yama (God of Death) | <strong>Lord:</strong> Venus</p>
            <p><strong>Shakti:</strong> Apabharani Shakti (power to take away) | <strong>Result:</strong> Cleansing and purification</p>
            <p><strong>Animal:</strong> Elephant | <strong>Guna:</strong> Rajas | <strong>Gana:</strong> Manushya | <strong>Caste:</strong> Kshatriya</p>
            
            <p><strong>Deep Characteristics:</strong> Bharani is the cosmic womb that bears the burden of creation and destruction. These natives have an innate understanding of life's cycles and can handle extreme situations with remarkable composure. They possess tremendous creative and procreative powers, often becoming the pillars of strength for their families and communities.</p>
            
            <p><strong>Psychological Profile:</strong> Extremely resilient with ability to endure hardships that would break others. They have a deep sense of moral responsibility and often sacrifice personal desires for greater good. Can be stubborn and inflexible when their values are challenged. Natural counselors who help others through difficult transitions.</p>
            
            <p><strong>Spiritual Significance:</strong> Represents the divine feminine principle of creation through destruction. They are here to learn about proper use of creative and sexual energy. Often have past life connections to roles involving birth, death, and transformation. May experience significant losses early in life to develop spiritual strength.</p>
            
            <p><strong>Health Tendencies:</strong> Reproductive system issues, diabetes, problems with elimination, headaches. Strong constitution but tendency to overwork. Benefit from regular detoxification and stress management practices.</p>
            
            <p><strong>Career Mastery:</strong> Obstetrics and gynecology, psychology, funeral services, waste management, recycling, agriculture, food production, entertainment industry, fashion design, jewelry making, banking and finance.</p>
            
            <p><strong>Relationship Patterns:</strong> Deeply loyal and committed partners who take relationships very seriously. May attract partners with problems they feel compelled to fix. Strong sexual nature but also capable of celibacy for spiritual reasons. Excellent parents who are protective of their children.</p>
            
            <p><strong>Remedial Measures:</strong> Worship of Divine Mother in her fierce forms (Durga, Kali). Chanting "Om Yamaya Namaha." Wearing diamonds or white sapphires. Donating to women's causes. Practicing forgiveness and letting go.</p>
          </div>

          <div class="nakshatra-item">
            <h4>3. Krittika - The Cutter (26°40' Aries - 10°00' Taurus)</h4>
            <p><strong>Symbol:</strong> Razor/Flame | <strong>Deity:</strong> Agni (Fire God) | <strong>Lord:</strong> Sun</p>
            <p><strong>Shakti:</strong> Dahana Shakti (power to burn) | <strong>Result:</strong> Purification through fire</p>
            <p><strong>Animal:</strong> Female Goat | <strong>Guna:</strong> Rajas | <strong>Gana:</strong> Rakshasa | <strong>Caste:</strong> Brahmin</p>
            
            <p><strong>Deep Characteristics:</strong> Krittika natives are the cosmic purifiers who cut through illusion with laser-like precision. They have an innate ability to see truth and expose falsehood, making them natural critics and reformers. Their fiery nature burns away impurities, both in themselves and others, though this process can be painful.</p>
            
            <p><strong>Psychological Profile:</strong> Perfectionist tendencies with high standards for themselves and others. Sharp intellect that can cut through complex problems quickly. May be perceived as harsh or critical, but their intentions are usually to help and improve. Strong leadership abilities but can be impatient with those who don't meet their standards.</p>
            
            <p><strong>Spiritual Significance:</strong> Represents the divine fire of discrimination (Viveka) that separates truth from falsehood. They are here to learn about constructive vs. destructive criticism. Often have past life connections to teaching, spiritual guidance, or roles requiring moral courage.</p>
            
            <p><strong>Health Tendencies:</strong> Digestive fire imbalances, skin problems, fever-related illnesses, eye strain. Strong constitution but tendency toward inflammatory conditions. Benefit from cooling foods and stress reduction techniques.</p>
            
            <p><strong>Career Mastery:</strong> Military leadership, law enforcement, legal profession, editing and publishing, food criticism, quality control, metallurgy, weapons manufacturing, spiritual teaching, fire-related industries, surgery.</p>
            
            <p><strong>Relationship Patterns:</strong> High standards in relationships may lead to disappointment. Need partners who can handle their direct communication style. Loyal and protective once committed. May struggle with expressing softer emotions but deeply caring underneath their tough exterior.</p>
            
            <p><strong>Remedial Measures:</strong> Worship of Agni or Sun god. Chanting "Om Agnaye Namaha." Wearing ruby or red coral. Fire ceremonies (Homas). Practicing compassion and gentleness in speech.</p>
          </div>

          <div class="nakshatra-item">
            <h4>4. Rohini - The Red One (10°00' - 23°20' Taurus)</h4>
            <p><strong>Symbol:</strong> Ox cart, Temple | <strong>Deity:</strong> Brahma (Creator) | <strong>Lord:</strong> Moon</p>
            <p><strong>Shakti:</strong> Rohana Shakti (power of growth) | <strong>Result:</strong> Creation and fertility</p>
            <p><strong>Animal:</strong> Male Serpent | <strong>Guna:</strong> Rajas | <strong>Gana:</strong> Manushya | <strong>Caste:</strong> Shudra</p>
            
            <p><strong>Deep Characteristics:</strong> Rohini is the beloved of the Moon, representing pure creative and procreative energy. These natives possess magnetic charm and natural beauty that attracts others effortlessly. They are the cosmic gardeners who make everything around them flourish and grow. Their presence brings abundance and fertility to any situation.</p>
            
            <p><strong>Psychological Profile:</strong> Naturally charismatic with strong aesthetic sense and love for luxury. They can be possessive and jealous in relationships due to their deep emotional nature. Excellent at accumulating wealth and resources. May struggle with materialism vs. spirituality. Strong nurturing instincts and protective of loved ones.</p>
            
            <p><strong>Spiritual Significance:</strong> Represents the divine creative principle and the power of manifestation through beauty and harmony. They are here to learn about proper use of material resources and the balance between earthly pleasures and spiritual growth. Often have past life connections to agriculture, arts, or roles involving beauty and creativity.</p>
            
            <p><strong>Health Tendencies:</strong> Throat problems, diabetes, weight gain, reproductive issues. Strong constitution but tendency toward indulgence. Benefit from moderate diet and regular exercise to maintain health and vitality.</p>
            
            <p><strong>Career Mastery:</strong> Fashion design, beauty industry, agriculture, horticulture, real estate, luxury goods, jewelry, music, dance, hospitality, food industry, banking, interior design.</p>
            
            <p><strong>Relationship Patterns:</strong> Deeply romantic and sensual, seeking beauty and harmony in relationships. May attract multiple suitors due to their charm. Can be possessive and need constant reassurance of love. Excellent homemakers who create beautiful, comfortable environments.</p>
            
            <p><strong>Remedial Measures:</strong> Worship of Brahma or Lakshmi. Chanting "Om Brahmane Namaha." Wearing pearl or moonstone. Offering white flowers to deities. Practicing gratitude and contentment.</p>
          </div>

          <div class="nakshatra-item">
            <h4>5. Mrigashira - The Deer's Head (23°20' Taurus - 6°40' Gemini)</h4>
            <p><strong>Symbol:</strong> Deer's head | <strong>Deity:</strong> Soma (Moon god) | <strong>Lord:</strong> Mars</p>
            <p><strong>Shakti:</strong> Prinana Shakti (power of giving fulfillment) | <strong>Result:</strong> Satisfaction through seeking</p>
            <p><strong>Animal:</strong> Female Serpent | <strong>Guna:</strong> Rajas | <strong>Gana:</strong> Deva | <strong>Caste:</strong> Kshatriya</p>
            
            <p><strong>Deep Characteristics:</strong> Mrigashira natives are eternal seekers, always searching for something just beyond their reach. Like deer, they are gentle, alert, and ready to flee at the first sign of danger. They possess an insatiable curiosity and desire to explore new territories, both physical and mental. Their quest often leads them to profound discoveries.</p>
            
            <p><strong>Psychological Profile:</strong> Restless minds that constantly seek new experiences and knowledge. They can be suspicious and cautious, especially in new situations. Natural researchers with excellent observation skills. May struggle with commitment due to their wandering nature. Gentle and compassionate but can be elusive when pressured.</p>
            
            <p><strong>Spiritual Significance:</strong> Represents the soul's eternal quest for truth and meaning. They are here to learn about the balance between seeking and finding, between curiosity and satisfaction. Often have past life connections to exploration, research, or spiritual seeking. May experience many false starts before finding their true path.</p>
            
            <p><strong>Health Tendencies:</strong> Nervous system disorders, anxiety, insomnia, digestive issues due to restlessness. Generally good health but tendency toward mental stress. Benefit from meditation, yoga, and grounding practices.</p>
            
            <p><strong>Career Mastery:</strong> Research and development, exploration, travel industry, writing, journalism, gemology, textiles, perfumes, forest products, detective work, archaeology, anthropology.</p>
            
            <p><strong>Relationship Patterns:</strong> Seek mental stimulation and variety in relationships. May have difficulty with long-term commitment until they find someone who shares their love of exploration. Need partners who give them space and freedom. Often attract partners from different cultures or backgrounds.</p>
            
            <p><strong>Remedial Measures:</strong> Worship of Soma or Chandra. Chanting "Om Somaya Namaha." Wearing emerald or green stones. Spending time in nature. Practicing mindfulness to reduce restlessness.</p>
          </div>

          <div class="nakshatra-item">
            <h4>6. Ardra - The Moist One (6°40' - 20°00' Gemini)</h4>
            <p><strong>Symbol:</strong> Teardrop, Diamond | <strong>Deity:</strong> Rudra (Storm god) | <strong>Lord:</strong> Rahu</p>
            <p><strong>Shakti:</strong> Yatna Shakti (power of effort) | <strong>Result:</strong> Transformation through struggle</p>
            <p><strong>Animal:</strong> Female Dog | <strong>Guna:</strong> Tamas | <strong>Gana:</strong> Manushya | <strong>Caste:</strong> Kshatriya</p>
            
            <p><strong>Deep Characteristics:</strong> Ardra natives are the cosmic storm-bringers who clear away stagnation through intense emotional and mental upheavals. They possess the power to destroy what is no longer needed to make way for new growth. Like lightning, they can illuminate truth in a flash but may also cause destruction in the process.</p>
            
            <p><strong>Psychological Profile:</strong> Highly intelligent with penetrating minds that can see through deception. Emotionally intense with tendency toward mood swings. They experience life in extremes - great joy or deep sorrow. Natural problem-solvers who thrive in crisis situations. May struggle with emotional regulation and need to learn balance.</p>
            
            <p><strong>Spiritual Significance:</strong> Represents the divine destroyer aspect that clears karma through intense experiences. They are here to learn about transformation through suffering and the power of renewal. Often experience significant losses or upheavals that lead to spiritual awakening. Past life connections to healing, transformation, or roles involving crisis management.</p>
            
            <p><strong>Health Tendencies:</strong> Nervous system disorders, mental health issues, heart problems, accidents. Strong recuperative powers but tendency toward stress-related illnesses. Benefit from stress management, therapy, and spiritual practices.</p>
            
            <p><strong>Career Mastery:</strong> Technology, electronics, software development, research, psychology, psychiatry, emergency services, crisis management, pharmaceuticals, chemicals, detective work.</p>
            
            <p><strong>Relationship Patterns:</strong> Intense and passionate in relationships but may experience emotional turbulence. Need partners who can handle their emotional depth and intensity. May go through several transformative relationships before finding stability. Loyal but demanding partners.</p>
            
            <p><strong>Remedial Measures:</strong> Worship of Rudra or Shiva. Chanting "Om Namah Shivaya." Wearing hessonite garnet. Regular meditation and pranayama. Practicing emotional regulation techniques.</p>
          </div>

          <div class="nakshatra-item">
            <h4>7. Punarvasu - The Return of Light (20°00' Gemini - 3°20' Cancer)</h4>
            <p><strong>Symbol:</strong> Bow and Quiver, House | <strong>Deity:</strong> Aditi (Mother of gods) | <strong>Lord:</strong> Jupiter</p>
            <p><strong>Shakti:</strong> Vasutva Prapana Shakti (power to gain wealth) | <strong>Result:</strong> Restoration and renewal</p>
            <p><strong>Animal:</strong> Female Cat | <strong>Guna:</strong> Rajas | <strong>Gana:</strong> Deva | <strong>Caste:</strong> Vaishya</p>
            
            <p><strong>Deep Characteristics:</strong> Punarvasu natives possess the remarkable ability to bounce back from any adversity, like the sun returning after an eclipse. They are the cosmic restorers who can rebuild what has been destroyed. Their optimistic nature and philosophical outlook help them find meaning in suffering and transform setbacks into comebacks.</p>
            
            <p><strong>Psychological Profile:</strong> Eternally optimistic with unshakeable faith in divine providence. They possess great mental resilience and ability to inspire hope in others. Natural teachers and philosophers who see the bigger picture. May be overly trusting or naive at times. Strong moral compass and desire to help others.</p>
            
            <p><strong>Spiritual Significance:</strong> Represents the return to divine grace after a period of darkness or difficulty. They are here to learn about faith, forgiveness, and the cyclical nature of existence. Often experience major comebacks after significant losses. Past life connections to teaching, healing, or spiritual guidance roles.</p>
            
            <p><strong>Health Tendencies:</strong> Generally good health with strong recuperative powers. May have issues with lungs, chest, or respiratory system. Benefit from positive thinking, spiritual practices, and maintaining optimistic outlook.</p>
            
            <p><strong>Career Mastery:</strong> Teaching, philosophy, religion, counseling, social work, hospitality, real estate, import-export, publishing, motivational speaking, rehabilitation services.</p>
            
            <p><strong>Relationship Patterns:</strong> Loyal and devoted partners who believe in the sanctity of relationships. May forgive too easily and give multiple chances. Seek partners who share their philosophical and spiritual interests. Excellent at rebuilding relationships after conflicts.</p>
            
            <p><strong>Remedial Measures:</strong> Worship of Jupiter or Vishnu. Chanting "Om Gurave Namaha." Wearing yellow sapphire or topaz. Donating to educational causes. Practicing gratitude and positive thinking.</p>
          </div>

          <div class="nakshatra-item">
            <h4>8. Pushya - The Nourisher (3°20' - 16°40' Cancer)</h4>
            <p><strong>Symbol:</strong> Cow's udder, Lotus, Arrow | <strong>Deity:</strong> Brihaspati (Jupiter) | <strong>Lord:</strong> Saturn</p>
            <p><strong>Shakti:</strong> Brahmavarchasa Shakti (power of spiritual energy) | <strong>Result:</strong> Spiritual illumination</p>
            <p><strong>Animal:</strong> Male Goat | <strong>Guna:</strong> Rajas | <strong>Gana:</strong> Deva | <strong>Caste:</strong> Kshatriya</p>
            
            <p><strong>Deep Characteristics:</strong> Pushya is considered the most auspicious nakshatra, representing divine nourishment and spiritual sustenance. These natives are natural nurturers who provide emotional, physical, and spiritual support to others. They possess the ability to make anything grow and flourish through their caring attention and disciplined approach.</p>
            
            <p><strong>Psychological Profile:</strong> Deeply caring and protective with strong sense of duty and responsibility. They are natural counselors who others turn to for guidance and support. Conservative in approach but progressive in thinking. May sacrifice their own needs for others. Strong spiritual inclinations and moral values.</p>
            
            <p><strong>Spiritual Significance:</strong> Represents the divine mother principle that nourishes all creation. They are here to learn about service, sacrifice, and the proper use of nurturing energy. Often chosen for important spiritual or healing roles. Past life connections to caregiving, spiritual teaching, or roles involving guidance and protection.</p>
            
            <p><strong>Health Tendencies:</strong> Generally robust health but may have issues with stomach, chest, or weight gain due to their nurturing nature. Benefit from balanced diet, regular exercise, and stress management.</p>
            
            <p><strong>Career Mastery:</strong> Counseling, psychology, nutrition, healthcare, agriculture, dairy industry, education, government service, spiritual teaching, social work, childcare.</p>
            
            <p><strong>Relationship Patterns:</strong> Extremely devoted and caring partners who put family first. May attract dependent partners who need their nurturing. Excellent parents who are protective and supportive. Seek stable, long-term relationships based on mutual respect and shared values.</p>
            
            <p><strong>Remedial Measures:</strong> Worship of Brihaspati or Ganesha. Chanting "Om Brihaspataye Namaha." Wearing blue sapphire or amethyst. Feeding the hungry and supporting charitable causes. Regular spiritual practices and meditation.</p>
          </div>

          <div class="nakshatra-item">
            <h4>9. Ashlesha - The Entwiner (16°40' - 30°00' Cancer)</h4>
            <p><strong>Symbol:</strong> Coiled Serpent, Wheel | <strong>Deity:</strong> Nagas (Serpent deities) | <strong>Lord:</strong> Mercury</p>
            <p><strong>Shakti:</strong> Visha Sleshana Shakti (power to inflict poison) | <strong>Result:</strong> Destruction of enemies</p>
            <p><strong>Animal:</strong> Male Cat | <strong>Guna:</strong> Rajas | <strong>Gana:</strong> Rakshasa | <strong>Caste:</strong> Kshatriya</p>
            
            <p><strong>Deep Characteristics:</strong> Ashlesha natives possess the serpent's wisdom - ancient, mysterious, and potentially dangerous. They have the ability to see through people's motivations and can be either healing or harmful depending on how they use their power. Like serpents, they can shed their skin and transform completely when necessary.</p>
            
            <p><strong>Psychological Profile:</strong> Highly intuitive with psychic abilities and deep understanding of human psychology. They can be manipulative and secretive but also profoundly wise and healing. Strong survival instincts and ability to regenerate after setbacks. May struggle with trust issues and tendency toward suspicion.</p>
            
            <p><strong>Spiritual Significance:</strong> Represents the kundalini energy and the power of transformation through wisdom. They are here to learn about the proper use of psychic and manipulative powers. Often have past life connections to occult practices, healing arts, or roles involving secrets and mysteries.</p>
            
            <p><strong>Health Tendencies:</strong> Digestive issues, food poisoning, allergies, mental health concerns. Strong constitution but sensitive to toxins. Benefit from detoxification practices, pure diet, and stress management.</p>
            
            <p><strong>Career Mastery:</strong> Psychology, psychiatry, occult sciences, astrology, medicine, politics, investigation, espionage, toxicology, pharmaceuticals, mysticism, hypnotherapy.</p>
            
            <p><strong>Relationship Patterns:</strong> Intense and possessive in relationships with tendency toward jealousy. May use emotional manipulation to control partners. Need partners who can handle their complexity and depth. Capable of profound intimacy but also destructive behavior.</p>
            
            <p><strong>Remedial Measures:</strong> Worship of Nagas or Ganesha. Chanting "Om Namo Narayanaya." Wearing emerald or cat's eye. Avoiding negative company. Practicing ethical behavior and using power responsibly.</p>
          </div>

          <div class="nakshatra-item">
            <h4>10. Magha - The Mighty One (0°00' - 13°20' Leo)</h4>
            <p><strong>Symbol:</strong> Royal Throne, Palanquin | <strong>Deity:</strong> Pitrs (Ancestors) | <strong>Lord:</strong> Ketu</p>
            <p><strong>Shakti:</strong> Tyaga Shepani Shakti (power to leave the body) | <strong>Result:</strong> Honoring ancestors</p>
            <p><strong>Animal:</strong> Male Rat | <strong>Guna:</strong> Rajas | <strong>Gana:</strong> Rakshasa | <strong>Caste:</strong> Kshatriya</p>
            
            <p><strong>Deep Characteristics:</strong> Magha natives carry the royal bloodline and ancestral power within them. They possess natural authority and command respect through their dignified presence. Like kings, they have both the privilege and responsibility of leadership. Their connection to ancestors gives them wisdom beyond their years and a sense of duty to family traditions.</p>
            
            <p><strong>Psychological Profile:</strong> Natural leaders with strong sense of pride and dignity. They expect respect and recognition for their contributions. May be authoritarian or domineering if power goes to their head. Strong family values and respect for tradition. Generous and protective of those under their care but can be demanding of loyalty.</p>
            
            <p><strong>Spiritual Significance:</strong> Represents the divine right of leadership and the responsibility that comes with power. They are here to learn about proper use of authority and the balance between personal desires and duty to others. Strong karmic connections to family lineage and ancestral patterns.</p>
            
            <p><strong>Health Tendencies:</strong> Heart problems, back issues, high blood pressure, stress-related disorders. Strong constitution but tendency toward pride-related health issues. Benefit from regular exercise, stress management, and maintaining humility.</p>
            
            <p><strong>Career Mastery:</strong> Government positions, politics, royal courts, archaeology, genealogy, museums, luxury industries, entertainment, leadership roles, family businesses, heritage preservation.</p>
            
            <p><strong>Relationship Patterns:</strong> Seek partners who respect their status and authority. May be attracted to those from good families or with social standing. Loyal and protective but expect devotion in return. Strong emphasis on family honor and reputation in relationships.</p>
            
            <p><strong>Remedial Measures:</strong> Ancestor worship and offerings. Chanting "Om Pitru Devaya Namaha." Wearing cat's eye or chrysoberyl. Maintaining family traditions. Practicing humility and service to others.</p>
          </div>

          <div class="nakshatra-item">
            <h4>11. Purva Phalguni - The Former Red One (13°20' - 26°40' Leo)</h4>
            <p><strong>Symbol:</strong> Front legs of bed, Hammock | <strong>Deity:</strong> Bhaga (God of delight) | <strong>Lord:</strong> Venus</p>
            <p><strong>Shakti:</strong> Prajanana Shakti (power of procreation) | <strong>Result:</strong> Creation through pleasure</p>
            <p><strong>Animal:</strong> Female Rat | <strong>Guna:</strong> Rajas | <strong>Gana:</strong> Manushya | <strong>Caste:</strong> Kshatriya</p>
            
            <p><strong>Deep Characteristics:</strong> Purva Phalguni natives are the cosmic pleasure-seekers who understand that joy and creativity are divine gifts to be celebrated. They possess natural charm and artistic abilities that bring beauty and happiness to the world. Their relaxed approach to life teaches others the importance of balance between work and play.</p>
            
            <p><strong>Psychological Profile:</strong> Naturally cheerful and optimistic with love for life's pleasures. They are generous and hospitable, always ready to share their good fortune. May struggle with discipline and long-term planning due to their focus on immediate gratification. Strong creative and artistic inclinations with natural performance abilities.</p>
            
            <p><strong>Spiritual Significance:</strong> Represents the divine principle of joy and the sacred nature of pleasure when properly channeled. They are here to learn about balance between indulgence and restraint, between personal pleasure and service to others. Often have past life connections to arts, entertainment, or roles involving bringing joy to others.</p>
            
            <p><strong>Health Tendencies:</strong> Heart problems, diabetes, issues related to overindulgence, reproductive system concerns. Generally good health but tendency toward excess. Benefit from moderation, regular exercise, and balanced lifestyle.</p>
            
            <p><strong>Career Mastery:</strong> Entertainment industry, music, dance, theater, hospitality, luxury goods, fashion, beauty industry, event planning, recreation, tourism, arts and crafts.</p>
            
            <p><strong>Relationship Patterns:</strong> Romantic and passionate with strong need for affection and appreciation. May have multiple relationships before settling down. Seek partners who can match their zest for life and appreciation of beauty. Generous and loving but may expect constant attention.</p>
            
            <p><strong>Remedial Measures:</strong> Worship of Venus or Lakshmi. Chanting "Om Shukraya Namaha." Wearing diamond or white sapphire. Practicing moderation and self-discipline. Channeling creativity into service.</p>
          </div>

          <div class="nakshatra-item">
            <h4>12. Uttara Phalguni - The Latter Red One (26°40' Leo - 10°00' Virgo)</h4>
            <p><strong>Symbol:</strong> Back legs of bed, Fig tree | <strong>Deity:</strong> Aryaman (God of contracts) | <strong>Lord:</strong> Sun</p>
            <p><strong>Shakti:</strong> Chayani Shakti (power of patronage) | <strong>Result:</strong> Prosperity through partnerships</p>
            <p><strong>Animal:</strong> Male Bull | <strong>Guna:</strong> Rajas | <strong>Gana:</strong> Manushya | <strong>Caste:</strong> Kshatriya</p>
            
            <p><strong>Deep Characteristics:</strong> Uttara Phalguni natives are the cosmic organizers who bring structure and stability to creative endeavors. They possess the ability to transform pleasure into productivity and dreams into reality. Their leadership style is based on service and cooperation rather than domination, making them natural team builders and partnership creators.</p>
            
            <p><strong>Psychological Profile:</strong> Reliable and responsible with strong organizational abilities. They are natural leaders who prefer to lead by example rather than force. Generous and helpful with strong sense of social responsibility. May be overly concerned with others' opinions and social status. Excellent at bringing people together for common causes.</p>
            
            <p><strong>Spiritual Significance:</strong> Represents the principle of dharmic leadership and the power of righteous partnerships. They are here to learn about service leadership and the balance between personal ambition and collective good. Often chosen for roles that require bringing people together and creating harmony.</p>
            
            <p><strong>Health Tendencies:</strong> Digestive issues, liver problems, stress-related disorders, back problems. Generally good health but tendency toward overwork. Benefit from regular rest, balanced diet, and stress management techniques.</p>
            
            <p><strong>Career Mastery:</strong> Management, administration, social work, unions, partnerships, contracts, healing professions, counseling, human resources, community organizing, public service.</p>
            
            <p><strong>Relationship Patterns:</strong> Seek stable, long-term partnerships based on mutual respect and shared goals. Excellent at maintaining relationships and resolving conflicts. May attract partners who need their organizational skills. Strong emphasis on fairness and equality in relationships.</p>
            
            <p><strong>Remedial Measures:</strong> Worship of Sun or Vishnu. Chanting "Om Suryaya Namaha." Wearing ruby or red coral. Serving community causes. Practicing leadership through service rather than domination.</p>
          </div>

          <div class="nakshatra-item">
            <h4>13. Hasta (10°00' - 23°20' Virgo)</h4>
            <p><strong>Symbol:</strong> Hand | <strong>Deity:</strong> Savitar | <strong>Lord:</strong> Moon</p>
            <p><strong>Characteristics:</strong> Skillful, hardworking, practical, clever. Excellent with detailed work.</p>
            <p><strong>Career:</strong> Crafts, manufacturing, healing, mechanics</p>
          </div>

          <div class="nakshatra-item">
            <h4>14. Chitra (23°20' Virgo - 6°40' Libra)</h4>
            <p><strong>Symbol:</strong> Bright jewel | <strong>Deity:</strong> Tvashtar | <strong>Lord:</strong> Mars</p>
            <p><strong>Characteristics:</strong> Artistic, beautiful, charismatic, perfectionist. Natural architects of beauty.</p>
            <p><strong>Career:</strong> Architecture, design, fashion, photography</p>
          </div>

          <div class="nakshatra-item">
            <h4>15. Swati (6°40' - 20°00' Libra)</h4>
            <p><strong>Symbol:</strong> Young shoot | <strong>Deity:</strong> Vayu | <strong>Lord:</strong> Rahu</p>
            <p><strong>Characteristics:</strong> Independent, flexible, diplomatic, business-minded. Strong desire for freedom.</p>
            <p><strong>Career:</strong> Business, trade, diplomacy, travel, aviation</p>
          </div>

          <div class="nakshatra-item">
            <h4>16. Vishakha (20°00' Libra - 3°20' Scorpio)</h4>
            <p><strong>Symbol:</strong> Triumphal arch | <strong>Deity:</strong> Indra-Agni | <strong>Lord:</strong> Jupiter</p>
            <p><strong>Characteristics:</strong> Determined, goal-oriented, ambitious, competitive. Natural achievers.</p>
            <p><strong>Career:</strong> Politics, law, military, sports, research</p>
          </div>

          <div class="nakshatra-item">
            <h4>17. Anuradha (3°20' - 16°40' Scorpio)</h4>
            <p><strong>Symbol:</strong> Lotus flower | <strong>Deity:</strong> Mitra | <strong>Lord:</strong> Saturn</p>
            <p><strong>Characteristics:</strong> Devoted, friendly, organized, balanced. Natural bridge-builders.</p>
            <p><strong>Career:</strong> Diplomacy, counseling, organization, travel</p>
          </div>

          <div class="nakshatra-item">
            <h4>18. Jyeshtha (16°40' - 30°00' Scorpio)</h4>
            <p><strong>Symbol:</strong> Circular amulet | <strong>Deity:</strong> Indra | <strong>Lord:</strong> Mercury</p>
            <p><strong>Characteristics:</strong> Protective, responsible, authoritative, generous. Natural protectors and leaders.</p>
            <p><strong>Career:</strong> Military, police, security, management</p>
          </div>

          <div class="nakshatra-item">
            <h4>19. Mula - The Root (0°00' - 13°20' Sagittarius)</h4>
            <div className="nakshatra-details">
              <p><strong>Deity:</strong> Nirriti (Goddess of destruction)<br/>
              <strong>Symbol:</strong> Bunch of roots<br/>
              <strong>Shakti:</strong> Barhana Shakti (power to break things apart)<br/>
              <strong>Ruling Planet:</strong> Ketu</p>
              
              <p><strong>Psychological Profile:</strong> Natural investigators who must get to the root of everything. They possess the ability to destroy what is false to make way for truth. Their probing nature serves as cosmic surgeons removing diseased elements.</p>
              
              <p><strong>Career Mastery:</strong> Research, investigation, archaeology, medicine, surgery, detective work, journalism, philosophy, law, politics.</p>
              
              <p><strong>Remedial Measures:</strong> Worship Ganesha, chant "Om Gam Ganapataye Namaha," wear cat's eye, practice patience.</p>
            </div>
          </div>

          <div class="nakshatra-item">
            <h4>20. Purva Ashadha - The Invincible One (13°20' - 26°40' Sagittarius)</h4>
            <div className="nakshatra-details">
              <p><strong>Deity:</strong> Apas (Water goddess)<br/>
              <strong>Symbol:</strong> Elephant tusk<br/>
              <strong>Shakti:</strong> Varchograhana Shakti (power of invigoration)<br/>
              <strong>Ruling Planet:</strong> Venus</p>
              
              <p><strong>Psychological Profile:</strong> Invincible in their convictions with ability to purify and invigorate others. Natural teachers and philosophers who inspire through unwavering faith and optimistic outlook.</p>
              
              <p><strong>Career Mastery:</strong> Teaching, preaching, counseling, water industries, shipping, philosophy, law, politics, motivational speaking.</p>
              
              <p><strong>Remedial Measures:</strong> Worship water deities, chant "Om Apah Devaya Namaha," wear diamond, practice humility.</p>
            </div>
          </div>

          <div class="nakshatra-item">
            <h4>21. Uttara Ashadha - The Universal Star (26°40' Sagittarius - 10°00' Capricorn)</h4>
            <div className="nakshatra-details">
              <p><strong>Deity:</strong> Vishvadevas (Universal gods)<br/>
              <strong>Symbol:</strong> Elephant tusk<br/>
              <strong>Shakti:</strong> Apradhrishya Shakti (power that cannot be conquered)<br/>
              <strong>Ruling Planet:</strong> Sun</p>
              
              <p><strong>Psychological Profile:</strong> Possess unshakeable determination and ability to achieve final victory through righteous means. Natural leaders who inspire through ethical approach and commitment to justice.</p>
              
              <p><strong>Career Mastery:</strong> Government service, administration, law enforcement, military, judiciary, social reform, international relations, ethics.</p>
              
              <p><strong>Remedial Measures:</strong> Worship Sun or Vishnu, chant "Om Suryaya Namaha," wear ruby, serve justice causes.</p>
            </div>
          </div>

          <div class="nakshatra-item">
            <h4>22. Shravana - The Listener (10°00' - 23°20' Capricorn)</h4>
            <div className="nakshatra-details">
              <p><strong>Deity:</strong> Vishnu (The preserver)<br/>
              <strong>Symbol:</strong> Ear<br/>
              <strong>Shakti:</strong> Samhanana Shakti (power to connect)<br/>
              <strong>Ruling Planet:</strong> Moon</p>
              
              <p><strong>Psychological Profile:</strong> Natural learners and teachers with exceptional listening abilities. Gift of connecting people and ideas, serving as bridges between different worlds of knowledge.</p>
              
              <p><strong>Career Mastery:</strong> Education, media, communication, music, radio, telecommunications, counseling, translation, library sciences.</p>
              
              <p><strong>Remedial Measures:</strong> Worship Vishnu, chant "Om Namo Narayanaya," wear pearl, practice active listening.</p>
            </div>
          </div>

          <div class="nakshatra-item">
            <h4>23. Dhanishtha - The Richest One (23°20' Capricorn - 6°40' Aquarius)</h4>
            <div className="nakshatra-details">
              <p><strong>Deity:</strong> Vasus (Eight elemental gods)<br/>
              <strong>Symbol:</strong> Drum<br/>
              <strong>Shakti:</strong> Khyapayitri Shakti (power to give fame)<br/>
              <strong>Ruling Planet:</strong> Mars</p>
              
              <p><strong>Psychological Profile:</strong> Possess natural rhythm and ability to accumulate wealth. Generous, musical, with excellent timing. Success comes through group efforts and harmonizing elements.</p>
              
              <p><strong>Career Mastery:</strong> Music, dance, entertainment, real estate, construction, engineering, group activities, sports, wealth management.</p>
              
              <p><strong>Remedial Measures:</strong> Worship Vasus, chant "Om Vasu Devaya Namaha," wear red coral, donate to artistic causes.</p>
            </div>
          </div>

          <div class="nakshatra-item">
            <h4>24. Shatabhisha - The Hundred Healers (6°40' - 20°00' Aquarius)</h4>
            <div className="nakshatra-details">
              <p><strong>Deity:</strong> Varuna (God of cosmic waters)<br/>
              <strong>Symbol:</strong> Empty circle<br/>
              <strong>Shakti:</strong> Bheshaja Shakti (power of healing)<br/>
              <strong>Ruling Planet:</strong> Rahu</p>
              
              <p><strong>Psychological Profile:</strong> Natural healers with mysterious and unconventional approaches. Ability to see beyond surface appearances and understand hidden connections in life.</p>
              
              <p><strong>Career Mastery:</strong> Medicine, alternative healing, research, astronomy, astrology, psychology, pharmaceuticals, water industries, innovation.</p>
              
              <p><strong>Remedial Measures:</strong> Worship Varuna, chant "Om Varunaya Namaha," wear hessonite garnet, engage in healing activities.</p>
            </div>
          </div>

          <div class="nakshatra-item">
            <h4>25. Purva Bhadrapada - The Burning Pair (20°00' Aquarius - 3°20' Pisces)</h4>
            <div className="nakshatra-details">
              <p><strong>Deity:</strong> Aja Ekapada (One-footed goat)<br/>
              <strong>Symbol:</strong> Swords<br/>
              <strong>Shakti:</strong> Yajamana Udyamana Shakti (power to elevate)<br/>
              <strong>Ruling Planet:</strong> Jupiter</p>
              
              <p><strong>Psychological Profile:</strong> Intense, passionate individuals who undergo significant transformations. Ability to burn away impurities through intense experiences and emerge stronger.</p>
              
              <p><strong>Career Mastery:</strong> Spirituality, occult sciences, research, philosophy, funeral services, transformation industries, psychology, mysticism.</p>
              
              <p><strong>Remedial Measures:</strong> Worship Shiva, chant "Om Namah Shivaya," wear yellow sapphire, practice moderation.</p>
            </div>
          </div>

          <div class="nakshatra-item">
            <h4>26. Uttara Bhadrapada - The Warrior Star (3°20' - 16°40' Pisces)</h4>
            <div className="nakshatra-details">
              <p><strong>Deity:</strong> Ahir Budhnya (Serpent of the deep)<br/>
              <strong>Symbol:</strong> Twin fish<br/>
              <strong>Shakti:</strong> Varshodyamana Shakti (power to bring rain)<br/>
              <strong>Ruling Planet:</strong> Saturn</p>
              
              <p><strong>Psychological Profile:</strong> Deep, contemplative individuals with access to profound wisdom and spiritual insights. Ability to bring spiritual nourishment to others like rain to parched earth.</p>
              
              <p><strong>Career Mastery:</strong> Spirituality, mysticism, counseling, charity work, social service, water industries, depth psychology, meditation teaching.</p>
              
              <p><strong>Remedial Measures:</strong> Worship Vishnu, chant "Om Namo Narayanaya," wear blue sapphire, engage in charitable activities.</p>
            </div>
          </div>

          <div class="nakshatra-item">
            <h4>27. Revati - The Wealthy One (16°40' - 30°00' Pisces)</h4>
            <div className="nakshatra-details">
              <p><strong>Deity:</strong> Pushan (Nourisher, protector of travelers)<br/>
              <strong>Symbol:</strong> Fish<br/>
              <strong>Shakti:</strong> Kshiradyapani Shakti (power to nourish)<br/>
              <strong>Ruling Planet:</strong> Mercury</p>
              
              <p><strong>Psychological Profile:</strong> Natural nurturers and protectors who bring completion and fulfillment. Ability to guide others safely through life's journeys and provide nourishment for growth.</p>
              
              <p><strong>Career Mastery:</strong> Hospitality, travel industry, shipping, transportation, nurturing professions, childcare, eldercare, guidance counseling.</p>
              
              <p><strong>Remedial Measures:</strong> Worship Vishnu or Lakshmi, chant "Om Pushne Namaha," wear emerald, serve travelers and those in need.</p>
            </div>
          </div>
        </div>
      `,
      nextLesson: 8
    }
  };

  const currentLesson = lessons[lessonId];

  if (!currentLesson) {
    return <div>Lesson not found</div>;
  }

  return (
    <div className="lesson-page">
      <NavigationHeader 
        onPeriodChange={() => {}}
        showZodiacSelector={false}
        zodiacSigns={[]}
        selectedZodiac={''}
        onZodiacChange={() => {}}
        user={null}
        onAdminClick={() => {}}
        onLogout={() => {}}
        onLogin={() => {}}
        showLoginButton={true}
      />
      <div className="container">
        <div className="back-button-container">
          <button className="back-btn" onClick={() => navigate('/beginners-guide')}>
            ← Back to Guide
          </button>
        </div>
        
        <div className="lesson-meta">
          <span className="lesson-number">Lesson {lessonId}</span>
          <span className="lesson-level">{currentLesson.level}</span>
          <span className="lesson-duration">{currentLesson.duration}</span>
        </div>

        <div className="lesson-content">
          <h1>{currentLesson.title}</h1>
          <div 
            className="lesson-body"
            dangerouslySetInnerHTML={{ __html: currentLesson.content }}
          />
        </div>

        <div className="lesson-navigation">
          {lessonId > 1 && (
            <button 
              className="nav-btn prev-btn"
              onClick={() => navigate(`/lesson/${parseInt(lessonId) - 1}`)}
            >
              ← Previous Lesson
            </button>
          )}
          {currentLesson.nextLesson && (
            <button 
              className="nav-btn next-btn"
              onClick={() => navigate(`/lesson/${currentLesson.nextLesson}`)}
            >
              Next Lesson →
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default LessonPage;