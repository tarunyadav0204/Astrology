import sqlite3

# Initialize database connection
conn = sqlite3.connect('astrology.db')
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS planet_nakshatra_interpretations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        planet TEXT NOT NULL,
        nakshatra TEXT NOT NULL,
        house INTEGER NOT NULL,
        interpretation TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(planet, nakshatra, house)
    )
''')
conn.commit()

planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
nakshatras = ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati']

house_meanings = {
    1: "personality and self-expression",
    2: "wealth, family, and speech", 
    3: "communication, siblings, and courage",
    4: "home, mother, and emotional foundation",
    5: "creativity, children, and intelligence",
    6: "health, service, and daily work",
    7: "partnerships and marriage",
    8: "transformation and hidden matters",
    9: "higher learning and spiritual beliefs",
    10: "career and public reputation",
    11: "gains, friendships, and aspirations",
    12: "spirituality, losses, and foreign connections"
}

# Base interpretations for each planet-nakshatra combination
base_interpretations = {
    ('Sun', 'Ashwini'): "creates natural healers and pioneers with exceptional leadership in medical fields",
    ('Sun', 'Bharani'): "gives tremendous willpower to bear life's burdens and transform through suffering",
    ('Sun', 'Krittika'): "creates sharp, penetrating intelligence with purifying abilities",
    ('Sun', 'Rohini'): "gives natural magnetism and material prosperity through charm",
    ('Sun', 'Mrigashira'): "creates eternal seekers of knowledge with restless energy",
    ('Sun', 'Ardra'): "gives transformative leadership through storms and upheavals",
    ('Sun', 'Punarvasu'): "creates optimistic leaders who can restore and renew",
    ('Sun', 'Pushya'): "gives nurturing leadership and spiritual authority",
    ('Sun', 'Ashlesha'): "creates mysterious leaders with hypnotic influence",
    ('Sun', 'Magha'): "gives royal authority and ancestral pride",
    ('Sun', 'Purva Phalguni'): "creates charismatic leaders in entertainment and luxury",
    ('Sun', 'Uttara Phalguni'): "gives supportive leadership and helpful nature",
    ('Sun', 'Hasta'): "creates skillful leaders with healing hands",
    ('Sun', 'Chitra'): "gives artistic leadership and creative authority",
    ('Sun', 'Swati'): "creates independent leaders who value freedom",
    ('Sun', 'Vishakha'): "gives determined leadership focused on goals",
    ('Sun', 'Anuradha'): "creates devoted leaders who build lasting friendships",
    ('Sun', 'Jyeshtha'): "gives protective leadership and elder wisdom",
    ('Sun', 'Mula'): "creates investigative leaders who get to root causes",
    ('Sun', 'Purva Ashadha'): "gives invincible leadership and purifying authority",
    ('Sun', 'Uttara Ashadha'): "creates ethical leaders with lasting achievements",
    ('Sun', 'Shravana'): "gives learned leadership and communication skills",
    ('Sun', 'Dhanishta'): "creates wealthy leaders with musical talents",
    ('Sun', 'Shatabhisha'): "gives healing leadership and research abilities",
    ('Sun', 'Purva Bhadrapada'): "creates transformative leaders with spiritual fire",
    ('Sun', 'Uttara Bhadrapada'): "gives deep leadership and foundational wisdom",
    ('Sun', 'Revati'): "creates nourishing leaders who complete cycles",
    
    ('Moon', 'Ashwini'): "gives emotional healing abilities and swift intuition",
    ('Moon', 'Bharani'): "creates deep emotional strength and creative fertility",
    ('Moon', 'Krittika'): "gives sharp emotional intelligence and purifying intuition",
    ('Moon', 'Rohini'): "creates beautiful, magnetic personalities with material comforts",
    ('Moon', 'Mrigashira'): "gives restless emotions and constant search for fulfillment",
    ('Moon', 'Ardra'): "creates emotional storms and transformative feelings",
    ('Moon', 'Punarvasu'): "gives optimistic emotions and renewable hope",
    ('Moon', 'Pushya'): "creates nurturing, protective emotions with spiritual inclination",
    ('Moon', 'Ashlesha'): "gives mysterious, penetrating emotions with hypnotic influence",
    ('Moon', 'Magha'): "creates proud, royal emotions with ancestral connections",
    ('Moon', 'Purva Phalguni'): "gives pleasure-seeking emotions and creative feelings",
    ('Moon', 'Uttara Phalguni'): "creates helpful, supportive emotions with partnership focus",
    ('Moon', 'Hasta'): "gives skillful emotions and healing touch",
    ('Moon', 'Chitra'): "creates artistic emotions and aesthetic feelings",
    ('Moon', 'Swati'): "gives independent emotions and balanced feelings",
    ('Moon', 'Vishakha'): "creates determined emotions focused on goals",
    ('Moon', 'Anuradha'): "gives devoted emotions and friendship-focused feelings",
    ('Moon', 'Jyeshtha'): "creates protective emotions and elder-like feelings",
    ('Moon', 'Mula'): "gives investigative emotions and root-seeking feelings",
    ('Moon', 'Purva Ashadha'): "creates invincible emotions and purifying feelings",
    ('Moon', 'Uttara Ashadha'): "gives stable emotions and achievement-focused feelings",
    ('Moon', 'Shravana'): "creates listening emotions and learning-focused feelings",
    ('Moon', 'Dhanishta'): "gives musical emotions and group-focused feelings",
    ('Moon', 'Shatabhisha'): "creates healing emotions and research-focused feelings",
    ('Moon', 'Purva Bhadrapada'): "gives intense emotions and spiritually transformative feelings",
    ('Moon', 'Uttara Bhadrapada'): "creates deep emotions and foundational feelings",
    ('Moon', 'Revati'): "gives nourishing emotions and completion-focused feelings",
    
    ('Mars', 'Ashwini'): "creates dynamic healers and emergency responders with explosive healing energy",
    ('Mars', 'Bharani'): "gives tremendous energy to bear burdens and transform through struggle",
    ('Mars', 'Krittika'): "creates sharp, cutting energy with purifying power",
    ('Mars', 'Rohini'): "gives passionate energy directed toward beauty and material pleasures",
    ('Mars', 'Mrigashira'): "creates restless energy and constant search for new challenges",
    ('Mars', 'Ardra'): "gives destructive energy that clears the way for new growth",
    ('Mars', 'Punarvasu'): "creates renewable energy and optimistic action",
    ('Mars', 'Pushya'): "gives protective energy and nurturing action",
    ('Mars', 'Ashlesha'): "creates penetrating energy and strategic action",
    ('Mars', 'Magha'): "gives royal warrior energy and ancestral pride",
    ('Mars', 'Purva Phalguni'): "creates creative energy and pleasure-seeking action",
    ('Mars', 'Uttara Phalguni'): "gives helpful energy and supportive action",
    ('Mars', 'Hasta'): "creates skillful energy and healing action",
    ('Mars', 'Chitra'): "gives artistic energy and creative action",
    ('Mars', 'Swati'): "creates independent energy and balanced action",
    ('Mars', 'Vishakha'): "gives determined energy focused on goals",
    ('Mars', 'Anuradha'): "creates devoted energy and friendship-focused action",
    ('Mars', 'Jyeshtha'): "gives protective energy and elder-like action",
    ('Mars', 'Mula'): "creates investigative energy and root-destroying action",
    ('Mars', 'Purva Ashadha'): "gives invincible energy and purifying action",
    ('Mars', 'Uttara Ashadha'): "creates ethical energy and achievement-focused action",
    ('Mars', 'Shravana'): "gives learning energy and communication-focused action",
    ('Mars', 'Dhanishta'): "creates musical energy and group-focused action",
    ('Mars', 'Shatabhisha'): "gives healing energy and research-focused action",
    ('Mars', 'Purva Bhadrapada'): "creates intense energy and spiritually transformative action",
    ('Mars', 'Uttara Bhadrapada'): "gives deep energy and foundational action",
    ('Mars', 'Revati'): "creates nourishing energy and completion-focused action"
}

# Generate interpretations for all combinations
count = 0
for planet in planets:
    for nakshatra in nakshatras:
        for house in range(1, 13):
            # Get base interpretation or create generic one
            base = base_interpretations.get((planet, nakshatra), f"{planet} in {nakshatra} brings unique planetary energy through this nakshatra's influence")
            
            # Create house-specific interpretation
            house_meaning = house_meanings[house]
            interpretation = f"{base}. This manifests in your {house_meaning}, creating a unique blend of {planet}'s energy through {nakshatra}'s influence in your {house}th house."
            
            # Insert into database
            cursor.execute(
                "INSERT OR REPLACE INTO planet_nakshatra_interpretations (planet, nakshatra, house, interpretation) VALUES (?, ?, ?, ?)",
                (planet, nakshatra, house, interpretation)
            )
            count += 1

conn.commit()
conn.close()

print(f"Successfully populated {count} interpretations in the database!")