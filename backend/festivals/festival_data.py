"""
Comprehensive Hindu Festivals and Vrats Database
"""

HINDU_FESTIVALS = {
    # Major Festivals
    "diwali": {
        "name": "Diwali",
        "type": "major_festival",
        "lunar_day": "amavasya",
        "month": "kartik",
        "duration": 5,
        "description": "Festival of lights celebrating victory of light over darkness",
        "significance": "Worship of Lakshmi, prosperity and wealth",
        "rituals": ["lighting diyas", "rangoli", "fireworks", "sweets distribution"]
    },
    "holi": {
        "name": "Holi",
        "type": "major_festival", 
        "lunar_day": "purnima",
        "month": "phalguna",
        "duration": 2,
        "description": "Festival of colors celebrating spring and love",
        "significance": "Victory of good over evil, Radha-Krishna love",
        "rituals": ["holika dahan", "color play", "gujiya", "thandai"]
    },
    "dussehra": {
        "name": "Dussehra/Vijayadashami",
        "type": "major_festival",
        "lunar_day": "dashami",
        "month": "ashwin",
        "duration": 1,
        "description": "Victory of Rama over Ravana",
        "significance": "Triumph of good over evil",
        "rituals": ["ravana effigy burning", "durga visarjan", "weapon worship"]
    },
    "navratri": {
        "name": "Navratri",
        "type": "major_festival",
        "lunar_day": "pratipada",
        "month": "ashwin",
        "duration": 9,
        "description": "Nine nights dedicated to Goddess Durga",
        "significance": "Divine feminine power worship",
        "rituals": ["fasting", "garba dance", "durga puja", "kanya puja"]
    },
    
    # Krishna Festivals
    "janmashtami": {
        "name": "Krishna Janmashtami",
        "type": "major_festival",
        "lunar_day": "ashtami",
        "month": "bhadrapada",
        "duration": 1,
        "description": "Birth of Lord Krishna",
        "significance": "Divine incarnation celebration",
        "rituals": ["midnight celebration", "dahi handi", "jhula", "bhajans"]
    },
    "govardhan_puja": {
        "name": "Govardhan Puja",
        "type": "festival",
        "lunar_day": "pratipada",
        "month": "kartik",
        "duration": 1,
        "description": "Krishna lifting Govardhan mountain",
        "significance": "Protection and devotion",
        "rituals": ["annakut", "govardhan parikrama", "cow worship"]
    },
    
    # Ganesha Festivals
    "ganesh_chaturthi": {
        "name": "Ganesh Chaturthi",
        "type": "major_festival",
        "lunar_day": "chaturthi",
        "month": "bhadrapada",
        "duration": 11,
        "description": "Birth of Lord Ganesha",
        "significance": "Remover of obstacles",
        "rituals": ["ganesha installation", "modak offering", "visarjan"]
    },
    
    # Shiva Festivals
    "maha_shivratri": {
        "name": "Maha Shivratri",
        "type": "major_festival",
        "lunar_day": "chaturdashi",
        "month": "magha",
        "duration": 1,
        "description": "Great night of Lord Shiva",
        "significance": "Shiva-Parvati marriage, cosmic dance",
        "rituals": ["night vigil", "shiva linga worship", "fasting", "rudra abhishek"]
    },
    
    # Rama Festivals
    "ram_navami": {
        "name": "Ram Navami",
        "type": "major_festival",
        "lunar_day": "navami",
        "month": "chaitra",
        "duration": 1,
        "description": "Birth of Lord Rama",
        "significance": "Ideal king and dharma",
        "rituals": ["rama katha", "bhajans", "processions", "charitable acts"]
    },
    
    # Hanuman Festivals
    "hanuman_jayanti": {
        "name": "Hanuman Jayanti",
        "type": "festival",
        "lunar_day": "purnima",
        "month": "chaitra",
        "duration": 1,
        "description": "Birth of Lord Hanuman",
        "significance": "Devotion and strength",
        "rituals": ["hanuman chalisa", "sindoor offering", "strength prayers"]
    },
    
    # Karva Chauth and Women's Vrats
    "karva_chauth": {
        "name": "Karva Chauth",
        "type": "vrat",
        "lunar_day": "chaturthi",
        "month": "kartik",
        "duration": 1,
        "description": "Married women's fast for husband's longevity",
        "significance": "Marital devotion and love",
        "rituals": ["nirjala fast", "moon worship", "mehendi", "sargi"]
    },
    "teej": {
        "name": "Hariyali Teej",
        "type": "vrat",
        "lunar_day": "tritiya",
        "month": "sravana",
        "duration": 1,
        "description": "Women's festival for marital bliss",
        "significance": "Parvati-Shiva union",
        "rituals": ["fasting", "swing decoration", "green clothes", "mehendi"]
    },
    
    # Ekadashi Vrats - Specific Names
    "devutthana_ekadashi": {
        "name": "Devutthana Ekadashi",
        "type": "vrat",
        "lunar_day": "ekadashi",
        "month": "kartik",
        "duration": 1,
        "description": "Awakening of Lord Vishnu from cosmic sleep",
        "significance": "End of Chaturmas, beginning of wedding season",
        "rituals": ["fasting", "vishnu worship", "tulsi vivah", "charity"]
    },
    "utpanna_ekadashi": {
        "name": "Utpanna Ekadashi",
        "type": "vrat",
        "lunar_day": "ekadashi",
        "month": "margashirsha",
        "duration": 1,
        "description": "Krishna paksha Ekadashi in Margashirsha",
        "significance": "Spiritual purification and Vishnu worship",
        "rituals": ["fasting", "vishnu worship", "charity"]
    },
    
    # November 2025 Specific Festivals
    "kansa_vadh": {
        "name": "Kansa Vadh",
        "type": "festival",
        "lunar_day": "ekadashi",
        "month": "kartik",
        "duration": 1,
        "description": "Killing of demon Kansa by Krishna",
        "significance": "Victory of good over evil",
        "rituals": ["krishna worship", "bhajans", "charity"]
    },
    "tulasi_vivah": {
        "name": "Tulasi Vivah",
        "type": "festival",
        "lunar_day": "dvadashi",
        "month": "kartik",
        "duration": 1,
        "description": "Marriage ceremony of Tulasi with Vishnu",
        "significance": "Sacred plant worship, marital bliss",
        "rituals": ["tulasi decoration", "marriage ceremony", "prasad distribution"]
    },
    "dev_diwali": {
        "name": "Dev Diwali",
        "type": "major_festival",
        "lunar_day": "purnima",
        "month": "kartik",
        "duration": 1,
        "description": "Festival of lights for gods",
        "significance": "Celebration by devas, Ganga aarti",
        "rituals": ["ganga aarti", "diyas lighting", "holy bath"]
    },
    "kalabhairav_jayanti": {
        "name": "Kalabhairav Jayanti",
        "type": "festival",
        "lunar_day": "ashtami",
        "month": "margashirsha",
        "duration": 1,
        "description": "Birth of Kalabhairav (Shiva's fierce form)",
        "significance": "Protection from negative forces",
        "rituals": ["kalabhairav worship", "black sesame offering", "night vigil"]
    },
    # Seasonal Festivals
    "makar_sankranti": {
        "name": "Makar Sankranti",
        "type": "seasonal_festival",
        "solar_date": "january_14",
        "duration": 1,
        "description": "Sun's transition to Capricorn",
        "significance": "Harvest festival, solar worship",
        "rituals": ["kite flying", "til-gud", "holy bath", "charity"]
    },
    "baisakhi": {
        "name": "Baisakhi",
        "type": "seasonal_festival",
        "solar_date": "april_13",
        "duration": 1,
        "description": "Harvest festival of North India",
        "significance": "New year, prosperity",
        "rituals": ["bhangra", "gurdwara visit", "feast", "thanksgiving"]
    },
    
    # Pitra Paksha
    "pitra_paksha": {
        "name": "Pitra Paksha",
        "type": "ancestral_period",
        "lunar_day": "purnima_to_amavasya",
        "month": "bhadrapada",
        "duration": 15,
        "description": "Fortnight for ancestor worship",
        "significance": "Honoring departed souls",
        "rituals": ["shraddha", "tarpan", "pind daan", "brahmin feeding"]
    },
    
    # Regional Festivals
    "onam": {
        "name": "Onam",
        "type": "regional_festival",
        "lunar_day": "thiruvonam",
        "month": "chingam",
        "duration": 10,
        "description": "Kerala harvest festival",
        "significance": "King Mahabali's return",
        "rituals": ["pookalam", "onasadya", "kathakali", "boat race"]
    },
    "durga_puja": {
        "name": "Durga Puja",
        "type": "regional_festival",
        "lunar_day": "saptami_to_dashami",
        "month": "ashwin",
        "duration": 4,
        "description": "Bengali goddess worship",
        "significance": "Durga's victory over Mahishasura",
        "rituals": ["pandal hopping", "dhunuchi dance", "sindoor khela", "visarjan"]
    },
    
    # Guru and Saint Festivals
    "guru_purnima": {
        "name": "Guru Purnima",
        "type": "spiritual_festival",
        "lunar_day": "purnima",
        "month": "ashadha",
        "duration": 1,
        "description": "Honoring spiritual teachers",
        "significance": "Guru-disciple tradition",
        "rituals": ["guru worship", "pada puja", "dakshina", "satsang"]
    },
    
    # Fasting Days
    "pradosh_vrat": {
        "name": "Pradosh Vrat",
        "type": "vrat",
        "lunar_day": "trayodashi",
        "month": "all",
        "duration": 1,
        "description": "Bi-monthly Shiva worship",
        "significance": "Shiva's blessing for prosperity",
        "rituals": ["evening worship", "shiva stories", "fasting", "abhishek"]
    },
    "sankashti_chaturthi": {
        "name": "Sankashti Chaturthi",
        "type": "vrat",
        "lunar_day": "chaturthi",
        "month": "all",
        "duration": 1,
        "description": "Monthly Ganesha fast",
        "significance": "Obstacle removal",
        "rituals": ["moonrise worship", "modak offering", "ganesha mantras"]
    },
    
    # Astrological Festivals
    "kumbh_mela": {
        "name": "Kumbh Mela",
        "type": "astrological_festival",
        "cycle": "12_years",
        "description": "Largest spiritual gathering",
        "significance": "Planetary alignment bathing",
        "rituals": ["holy dip", "satsang", "charity", "spiritual discourse"]
    }
}

# Monthly Vrat Calendar
MONTHLY_VRATS = {
    "ekadashi": {
        "name": "Ekadashi",
        "frequency": "twice_monthly",
        "days": [11, 26],  # Shukla and Krishna paksha
        "deity": "Vishnu",
        "benefits": "Spiritual purification, moksha"
    },
    "pradosh": {
        "name": "Pradosh Vrat",
        "frequency": "twice_monthly", 
        "days": [13, 28],  # Trayodashi
        "deity": "Shiva",
        "benefits": "Prosperity, obstacle removal"
    },
    "sankashti": {
        "name": "Sankashti Chaturthi",
        "frequency": "monthly",
        "days": [19],  # Krishna paksha chaturthi
        "deity": "Ganesha", 
        "benefits": "Obstacle removal, success"
    },
    "shivaratri": {
        "name": "Masik Shivaratri",
        "frequency": "monthly",
        "days": [14],  # Krishna paksha chaturdashi
        "deity": "Shiva",
        "benefits": "Spiritual growth, liberation"
    }
}

# Festival Categories
FESTIVAL_CATEGORIES = {
    "major_festivals": ["diwali", "holi", "dussehra", "navratri", "janmashtami"],
    "vrats": ["karva_chauth", "teej", "ekadashi_vrat", "pradosh_vrat"],
    "seasonal": ["makar_sankranti", "baisakhi"],
    "regional": ["onam", "durga_puja"],
    "spiritual": ["guru_purnima", "maha_shivratri"],
    "monthly_observances": ["ekadashi", "pradosh", "sankashti", "shivaratri"]
}