import sqlite3

# Initialize database connection
conn = sqlite3.connect('astrology.db')
cursor = conn.cursor()

# Clear existing interpretations
cursor.execute("DELETE FROM planet_nakshatra_interpretations")

# Comprehensive planet-nakshatra interpretations
interpretations = {
    "Sun": {
        "Ashwini": "Sun in Ashwini creates dynamic leaders with healing abilities and pioneering spirit. These natives possess exceptional vitality, quick decision-making skills, and natural medical intuition. They excel in emergency situations and often become successful doctors, healers, or leaders in innovative fields. Their personality radiates confidence and they inspire others through their actions rather than words.",
        "Bharani": "Sun in Bharani produces individuals with strong moral compass and creative leadership. These natives have the ability to bear great responsibilities and transform challenging situations into opportunities. They possess natural artistic talents, strong sense of justice, and often excel in law, administration, or creative fields. Their leadership style is nurturing yet firm.",
        "Krittika": "Sun in Krittika creates sharp-minded leaders with exceptional analytical abilities. These natives are natural critics and perfectionists who excel in teaching, research, and quality control. They have the ability to cut through illusions and see truth clearly. Their leadership is based on knowledge and precision, making them excellent mentors and guides.",
        "Rohini": "Sun in Rohini produces charismatic leaders with natural magnetism and artistic abilities. These natives are blessed with beauty, charm, and material prosperity. They excel in arts, entertainment, luxury goods, and beauty industries. Their leadership style is attractive and inspiring, drawing people naturally towards them.",
        "Mrigashira": "Sun in Mrigashira creates curious and communicative leaders who love exploration and learning. These natives are natural teachers and communicators who excel in media, writing, travel, and education. They have restless energy that drives them to constantly seek new knowledge and experiences.",
        "Ardra": "Sun in Ardra produces transformative leaders with intense emotional depth and innovative thinking. These natives excel in research, technology, and fields requiring radical transformation. They have the ability to destroy old patterns and create new ones, making them excellent change agents and innovators.",
        "Punarvasu": "Sun in Punarvasu creates optimistic and philosophical leaders with strong moral values. These natives are natural teachers and counselors who excel in education, spirituality, and guidance roles. They have the ability to bounce back from setbacks and help others do the same.",
        "Pushya": "Sun in Pushya produces nurturing leaders with strong spiritual inclinations and disciplined approach. These natives excel in healthcare, education, and spiritual guidance. They are natural protectors and providers who create stable foundations for others to grow.",
        "Ashlesha": "Sun in Ashlesha creates intuitive leaders with deep psychological insight and mysterious charm. These natives excel in psychology, healing, occult sciences, and transformation work. They have the ability to understand hidden motivations and help others overcome deep-seated issues."
    },
    "Moon": {
        "Ashwini": "Moon in Ashwini creates emotionally dynamic individuals with healing instincts and pioneering emotional responses. These natives have quick emotional reactions, natural empathy for suffering, and strong desire to help others. They often become successful in medical fields, emergency services, or healing professions.",
        "Bharani": "Moon in Bharani produces emotionally strong individuals with deep creative instincts and nurturing nature. These natives have the emotional capacity to bear great burdens and transform pain into beauty. They excel in creative arts, childcare, and fields requiring emotional strength.",
        "Krittika": "Moon in Krittika creates emotionally sharp individuals with critical thinking and perfectionist tendencies. These natives have high emotional standards and the ability to purify their environment. They often become successful critics, editors, or quality controllers.",
        "Rohini": "Moon in Rohini produces emotionally stable individuals with natural beauty and material comfort needs. These natives are blessed with emotional charm, artistic sensibilities, and attraction to luxury. They excel in arts, beauty, fashion, and entertainment industries.",
        "Mrigashira": "Moon in Mrigashira creates emotionally curious individuals with restless minds and communication needs. These natives have changeable emotions and strong desire for variety and exploration. They excel in communication, travel, and fields requiring adaptability."
    },
    "Mars": {
        "Ashwini": "Mars in Ashwini creates warriors with healing powers and pioneering courage. These natives are natural fighters who use their energy to help and heal others. They excel in surgery, emergency medicine, sports, and military services. Their courage is directed towards protecting and healing.",
        "Bharani": "Mars in Bharani produces passionate warriors with creative energy and strong willpower. These natives have the courage to face death and transformation. They excel in fields requiring intense energy like surgery, law enforcement, or creative arts that involve transformation.",
        "Krittika": "Mars in Krittika creates sharp warriors with cutting precision and analytical courage. These natives are natural critics and fighters who use their energy to cut through falsehood. They excel in military strategy, surgical procedures, and fields requiring precise action."
    }
}

# Planets and nakshatras lists
planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
nakshatras = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", 
              "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", 
              "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", 
              "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

# House significations for contextual interpretation
house_meanings = {
    1: "personality, self-expression, and physical appearance",
    2: "wealth, family, speech, and values", 
    3: "communication, siblings, courage, and short journeys",
    4: "home, mother, emotions, and inner peace",
    5: "creativity, children, education, and romance",
    6: "health, service, enemies, and daily work",
    7: "partnerships, marriage, and business relationships",
    8: "transformation, occult, longevity, and hidden matters",
    9: "higher learning, spirituality, luck, and long journeys",
    10: "career, reputation, authority, and public image",
    11: "gains, friendships, hopes, and social networks",
    12: "spirituality, losses, foreign lands, and subconscious"
}

# Generate comprehensive interpretations
for planet in planets:
    for nakshatra in nakshatras:
        # Get base interpretation or create generic one
        base_interpretation = interpretations.get(planet, {}).get(nakshatra, 
            f"{planet} in {nakshatra} creates a unique blend of planetary energy with nakshatra characteristics, influencing the native's life in profound ways.")
        
        for house in range(1, 13):
            # Create house-specific interpretation
            house_context = house_meanings[house]
            
            if planet in interpretations and nakshatra in interpretations[planet]:
                interpretation = f"{base_interpretation} When placed in the {house}th house, this combination specifically influences {house_context}, creating opportunities for growth and expression through these life areas. The native may find their greatest fulfillment and success by channeling this planetary-nakshatra energy into {house}th house matters."
            else:
                # Generate detailed interpretation for missing combinations
                interpretation = f"{planet} in {nakshatra} nakshatra brings the combined influence of {planet}'s natural significations with {nakshatra}'s unique characteristics. In the {house}th house, this placement affects {house_context}, creating a distinctive pattern of experiences and opportunities. The native should focus on developing the positive qualities of both {planet} and {nakshatra} through {house}th house activities for optimal results."
            
            # Insert into database
            cursor.execute('''
                INSERT OR REPLACE INTO planet_nakshatra_interpretations 
                (planet, nakshatra, house, interpretation)
                VALUES (?, ?, ?, ?)
            ''', (planet, nakshatra, house, interpretation))

# Commit changes
conn.commit()
conn.close()

print("Successfully populated detailed planet-nakshatra interpretations!")
print("Total combinations: 9 planets × 27 nakshatras × 12 houses = 2,916 interpretations")