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
        "description": "The most celebrated Hindu festival, Diwali marks the triumph of light over darkness, good over evil, and knowledge over ignorance. Celebrated over five days, it honors the return of Lord Rama to Ayodhya and the worship of Goddess Lakshmi for prosperity.",
        "significance": "Celebrates Lord Rama's return from exile, Goddess Lakshmi's blessings for wealth and prosperity, and the victory of dharma. Each day has special meaning: Dhanteras (wealth), Naraka Chaturdashi (victory over demon), Lakshmi Puja (prosperity), Govardhan Puja (gratitude), and Bhai Dooj (sibling love).",
        "rituals": ["lighting oil lamps and candles", "creating colorful rangoli patterns", "Lakshmi and Ganesha worship", "exchanging sweets and gifts", "fireworks and celebrations", "cleaning and decorating homes", "wearing new clothes", "charitable giving"]
    },
    "holi": {
        "name": "Holi",
        "type": "major_festival", 
        "lunar_day": "purnima",
        "month": "phalguna",
        "duration": 2,
        "description": "The vibrant festival of colors celebrating the arrival of spring, the triumph of good over evil, and the divine love between Radha and Krishna. Known as the 'Festival of Love' and 'Festival of Colors', it brings people together in joyous celebration.",
        "significance": "Commemorates the burning of demoness Holika and salvation of Prahlad, celebrates the eternal love of Radha-Krishna, marks the end of winter and arrival of spring, promotes unity and forgiveness among people, and represents the victory of devotion over evil.",
        "rituals": ["Holika Dahan bonfire ceremony", "playing with colored powders and water", "preparing traditional sweets like gujiya and malpua", "drinking thandai and bhang", "singing Holi songs and dancing", "visiting friends and family", "seeking forgiveness and renewing relationships"]
    },
    "dussehra": {
        "name": "Dussehra/Vijayadashami",
        "type": "major_festival",
        "lunar_day": "dashami",
        "month": "ashwin",
        "duration": 1,
        "description": "Celebrated as the victory of Lord Rama over the ten-headed demon king Ravana, Dussehra symbolizes the triumph of righteousness over evil. It marks the end of Navratri and celebrates the divine feminine power's victory over demonic forces.",
        "significance": "Represents the eternal victory of dharma (righteousness) over adharma (evil), celebrates Lord Rama's victory over Ravana, honors Goddess Durga's triumph over Mahishasura, and marks the beginning of preparations for Diwali. It's considered auspicious for new beginnings.",
        "rituals": ["burning effigies of Ravana, Meghnad, and Kumbhakarna", "Durga idol immersion (Visarjan)", "weapon worship (Shastra Puja)", "Ram Lila performances", "reading Ramayana", "seeking blessings for new ventures", "charitable acts and feeding the poor"]
    },
    "navratri": {
        "name": "Navratri",
        "type": "major_festival",
        "lunar_day": "pratipada",
        "month": "ashwin",
        "duration": 9,
        "description": "Nine sacred nights dedicated to the worship of Goddess Durga and her nine divine forms (Navadurga). Each night honors a different aspect of the Divine Mother, culminating in the celebration of feminine power and spiritual transformation.",
        "significance": "Celebrates the divine feminine energy (Shakti), honors the nine forms of Goddess Durga, represents the victory of good over evil through the goddess's triumph over demons, promotes spiritual purification and inner transformation, and strengthens devotion to the Divine Mother.",
        "rituals": ["nine days of fasting and prayer", "Garba and Dandiya Raas dancing", "daily Durga Puja and aarti", "Kanya Puja (worshipping young girls)", "reciting Durga Saptashati", "maintaining ritual purity", "offering flowers and sweets to the goddess", "community celebrations and cultural programs"]
    },
    
    # Krishna Festivals
    "janmashtami": {
        "name": "Krishna Janmashtami",
        "type": "major_festival",
        "lunar_day": "ashtami",
        "month": "bhadrapada",
        "duration": 1,
        "description": "The joyous celebration of Lord Krishna's birth at midnight in Mathura. This festival commemorates the divine incarnation who came to restore dharma and guide humanity through his teachings in the Bhagavad Gita.",
        "significance": "Celebrates the birth of the eighth avatar of Vishnu, represents the victory of good over evil through Krishna's life, honors divine love and devotion, teaches the importance of dharma and righteous living, and brings joy and spiritual upliftment to devotees.",
        "rituals": ["midnight celebration marking Krishna's birth time", "Dahi Handi (pot breaking) competitions", "decorating Krishna's cradle (Jhula)", "singing bhajans and kirtans", "fasting until midnight", "offering butter, milk, and sweets", "dramatic enactments of Krishna's childhood", "temple decorations and processions"]
    },
    "govardhan_puja": {
        "name": "Govardhan Puja",
        "type": "festival",
        "lunar_day": "pratipada",
        "month": "kartik",
        "duration": 1,
        "description": "Commemorates Lord Krishna's lifting of Govardhan mountain to protect the people of Vrindavan from Indra's wrath. Also known as Annakut, it celebrates the abundance of nature and Krishna's protective power.",
        "significance": "Honors Krishna's divine protection and strength, celebrates the importance of nature and environment, teaches humility over pride (Indra's lesson), represents the bond between humans and nature, and emphasizes community unity and sharing.",
        "rituals": ["Annakut (mountain of food) offering", "Govardhan Parikrama (circumambulation)", "cow worship and feeding", "creating Govardhan mountain replicas with food", "community feasting and sharing", "environmental awareness activities", "Krishna bhajans and stories"]
    },
    
    # Ganesha Festivals
    "ganesh_chaturthi": {
        "name": "Ganesh Chaturthi",
        "type": "major_festival",
        "lunar_day": "chaturthi",
        "month": "bhadrapada",
        "duration": 11,
        "description": "The grand celebration of Lord Ganesha's birth, marked by installing clay idols in homes and public pandals. The festival culminates with the immersion ceremony (Visarjan), symbolizing the cycle of creation and dissolution.",
        "significance": "Honors the remover of obstacles and lord of beginnings, promotes community unity and cultural preservation, teaches environmental consciousness through clay idols, represents the impermanence of material forms, and brings prosperity and wisdom to devotees.",
        "rituals": ["installing Ganesha idols in homes and pandals", "daily prayers and aarti ceremonies", "offering modaks (sweet dumplings)", "cultural programs and competitions", "community processions with music and dance", "Visarjan (immersion) ceremony", "chanting Ganesha mantras", "seeking blessings for new ventures"]
    },
    
    # Shiva Festivals
    "maha_shivratri": {
        "name": "Maha Shivratri",
        "type": "major_festival",
        "lunar_day": "chaturdashi",
        "month": "magha",
        "duration": 1,
        "description": "The most sacred night dedicated to Lord Shiva, celebrating his cosmic dance and the divine union with Goddess Parvati. Devotees observe night-long vigils, fasting, and intensive worship to receive Shiva's blessings for spiritual liberation.",
        "significance": "Commemorates the marriage of Shiva and Parvati, celebrates Shiva's cosmic dance (Tandava) that maintains universal rhythm, marks the night when Shiva drank poison to save the world, represents the triumph of consciousness over ignorance, and offers the opportunity for spiritual transformation and moksha.",
        "rituals": ["all-night vigil (jagran) with prayers", "Shiva Linga worship with milk, honey, and water", "fasting and meditation", "Rudra Abhishek (sacred bathing ceremony)", "chanting Om Namah Shivaya", "offering bel leaves and flowers", "visiting Shiva temples", "reading Shiva Purana and singing bhajans"]
    },
    
    # Rama Festivals
    "ram_navami": {
        "name": "Ram Navami",
        "type": "major_festival",
        "lunar_day": "navami",
        "month": "chaitra",
        "duration": 1,
        "description": "The celebration of Lord Rama's birth, honoring the seventh avatar of Vishnu who exemplified dharma, righteousness, and ideal kingship. The festival promotes the values of truth, duty, and moral conduct in personal and social life.",
        "significance": "Celebrates the birth of the ideal king and perfect human being, promotes the values of dharma and righteous living, honors the victory of good over evil as depicted in Ramayana, teaches devotion, duty, and moral conduct, and brings blessings for family harmony and social justice.",
        "rituals": ["reciting Ramayana and Ram Katha", "singing Ram bhajans and kirtans", "organizing processions with Ram's idol", "charitable acts and feeding the poor", "visiting Ram temples", "fasting and prayer", "community celebrations and cultural programs", "reading about Rama's life and teachings"]
    },
    
    # Hanuman Festivals
    "hanuman_jayanti": {
        "name": "Hanuman Jayanti",
        "type": "festival",
        "lunar_day": "purnima",
        "month": "chaitra",
        "duration": 1,
        "description": "The birth celebration of Lord Hanuman, the devoted follower of Rama known for his immense strength, courage, and unwavering devotion. This festival inspires devotees to cultivate similar qualities of service, strength, and spiritual dedication.",
        "significance": "Honors the epitome of devotion and selfless service, celebrates physical and mental strength, promotes courage and fearlessness, teaches the power of faith and surrender, and provides protection from negative forces and obstacles.",
        "rituals": ["reciting Hanuman Chalisa and Bajrang Baan", "offering sindoor (vermillion) and oil", "prayers for strength and protection", "visiting Hanuman temples", "organizing strength competitions", "feeding monkeys and the needy", "reading Hanuman's stories from Ramayana", "chanting Jai Hanuman mantras"]
    },
    
    # Karva Chauth and Women's Vrats
    "karva_chauth": {
        "name": "Karva Chauth",
        "type": "vrat",
        "lunar_day": "chaturthi",
        "month": "kartik",
        "duration": 1,
        "description": "A sacred fast observed by married women for the longevity, prosperity, and well-being of their husbands. The fast is broken only after sighting the moon and performing the traditional rituals, symbolizing the deep bond of marriage.",
        "significance": "Celebrates marital devotion and the sacred bond between husband and wife, ensures the husband's long life and prosperity, strengthens family relationships, promotes the tradition of sacrifice and love in marriage, and brings blessings for a happy married life.",
        "rituals": ["nirjala fast (without water) from sunrise to moonrise", "moon worship and offering water", "applying mehendi (henna) on hands", "receiving sargi (pre-dawn meal) from mother-in-law", "dressing in bridal attire", "listening to Karva Chauth story", "exchanging gifts with other married women", "breaking fast after seeing husband's face through a sieve"]
    },
    "teej": {
        "name": "Hariyali Teej",
        "type": "vrat",
        "lunar_day": "tritiya",
        "month": "sravana",
        "duration": 1,
        "description": "A joyous festival celebrated by women during the monsoon season, honoring the reunion of Lord Shiva and Goddess Parvati. It celebrates marital bliss, fertility, and the beauty of nature during the rainy season.",
        "significance": "Commemorates the divine marriage of Shiva and Parvati, celebrates the monsoon season and fertility, promotes marital happiness and harmony, honors the feminine divine energy, and brings prosperity to families.",
        "rituals": ["fasting for marital bliss", "decorating swings with flowers and greenery", "wearing green clothes and jewelry", "applying mehendi and singing folk songs", "worshipping Shiva and Parvati", "enjoying swings in gardens", "preparing traditional sweets", "community celebrations with dance and music"]
    },
    
    # Ekadashi Vrats - Specific Names
    "shukla_ekadashi": {
        "name": "Shukla Ekadashi",
        "type": "vrat",
        "lunar_day": "ekadashi",
        "paksha": "shukla",
        "month": "all",
        "duration": 1,
        "description": "The sacred fast observed on the 11th day of the bright fortnight (Shukla Paksha) every month, dedicated to Lord Vishnu. This bi-monthly observance is considered one of the most important spiritual practices in Hinduism for achieving moksha and spiritual purification.",
        "significance": "Grants liberation from sins and negative karma, promotes spiritual advancement and consciousness, ensures material and spiritual prosperity, provides protection from negative forces, brings Vishnu's divine blessings, and helps achieve moksha (liberation from the cycle of birth and death).",
        "rituals": ["complete fasting from grains, beans, and cereals", "intensive Vishnu worship and meditation", "chanting Vishnu Sahasranama and mantras", "reading Bhagavad Gita and Vishnu Purana", "charitable acts and feeding the poor", "staying awake in devotion and prayer", "visiting Vishnu temples", "breaking fast on Dwadashi after sunrise with proper rituals"]
    },
    "krishna_ekadashi": {
        "name": "Krishna Ekadashi",
        "type": "vrat",
        "lunar_day": "ekadashi",
        "paksha": "krishna",
        "month": "all",
        "duration": 1,
        "description": "The sacred fast observed on the 11th day of the dark fortnight (Krishna Paksha) every month, dedicated to Lord Vishnu. This powerful vrat is believed to destroy sins and grant spiritual merit equal to performing elaborate yajnas and pilgrimages.",
        "significance": "Destroys accumulated sins and negative karma, grants spiritual purification and divine grace, ensures protection from evil influences, promotes devotion and surrender to Vishnu, brings peace and prosperity, and helps in achieving spiritual liberation.",
        "rituals": ["strict fasting from all grains and pulses", "Vishnu worship with flowers and tulsi leaves", "reciting Vishnu mantras and bhajans", "meditation and spiritual contemplation", "charitable giving and serving the needy", "night-long vigil in prayer", "temple visits and darshan", "proper fast-breaking ceremony on Dwadashi"]
    },
    "devutthana_ekadashi": {
        "name": "Devutthana Ekadashi",
        "type": "vrat",
        "lunar_day": "ekadashi",
        "month": "kartik",
        "duration": 1,
        "description": "Also known as Prabodhini Ekadashi, this marks the awakening of Lord Vishnu from his four-month cosmic sleep (Yoga Nidra). It signals the end of Chaturmas and the beginning of the auspicious period for weddings and religious ceremonies.",
        "significance": "Celebrates Vishnu's awakening from cosmic sleep, marks the end of the four-month Chaturmas period, begins the auspicious wedding season, promotes spiritual awakening and consciousness, and brings divine blessings for new beginnings.",
        "rituals": ["observing strict fast and prayers", "Vishnu worship with special offerings", "Tulsi Vivah (marriage of Tulsi plant)", "charitable giving and feeding the poor", "staying awake all night in devotion", "reading Vishnu Sahasranama", "lighting lamps and decorating temples", "community celebrations and religious discourses"]
    },
    "utpanna_ekadashi": {
        "name": "Utpanna Ekadashi",
        "type": "vrat",
        "lunar_day": "ekadashi",
        "month": "margashirsha",
        "duration": 1,
        "description": "The Krishna Paksha Ekadashi of Margashirsha month, believed to be the day when Ekadashi Devi manifested to destroy demons. This powerful vrat purifies the soul and grants liberation from sins and negative karma.",
        "significance": "Commemorates the manifestation of Ekadashi Devi, provides spiritual purification and liberation from sins, grants protection from negative forces, promotes devotion to Lord Vishnu, and helps achieve moksha (liberation).",
        "rituals": ["complete fasting from grains and beans", "intensive Vishnu worship and meditation", "chanting Vishnu mantras and bhajans", "charitable acts and donations", "reading Ekadashi Mahatmya", "staying awake in prayer and devotion", "visiting Vishnu temples", "breaking fast on Dwadashi with proper rituals"]
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
    
    # Regional New Year Festivals
    "gudi_padwa": {
        "name": "Gudi Padwa",
        "type": "regional_festival",
        "lunar_day": "pratipada",
        "month": "chaitra",
        "duration": 1,
        "description": "Marathi New Year celebrated with Gudi (flag) hoisting",
        "significance": "New beginnings, prosperity, Marathi culture",
        "rituals": ["gudi hoisting", "rangoli", "puran poli", "neem leaves"]
    },
    "ugadi": {
        "name": "Ugadi",
        "type": "regional_festival",
        "lunar_day": "pratipada",
        "month": "chaitra",
        "duration": 1,
        "description": "Telugu and Kannada New Year with pachadi preparation",
        "significance": "New year, six tastes of life",
        "rituals": ["ugadi pachadi", "mango leaves decoration", "panchanga reading"]
    },
    "vishu": {
        "name": "Vishu",
        "type": "regional_festival",
        "solar_date": "april_14",
        "duration": 1,
        "description": "Malayalam New Year with Vishukkani arrangement",
        "significance": "Prosperity, good fortune, Kerala culture",
        "rituals": ["vishukkani viewing", "vishukaineetam", "sadhya feast"]
    },
    "pohela_boishakh": {
        "name": "Pohela Boishakh",
        "type": "regional_festival",
        "solar_date": "april_14",
        "duration": 1,
        "description": "Bengali New Year with cultural celebrations",
        "significance": "New year, Bengali culture, prosperity",
        "rituals": ["mangal shobhajatra", "panta bhat", "cultural programs"]
    },
    "bihu": {
        "name": "Rongali Bihu",
        "type": "regional_festival",
        "solar_date": "april_14",
        "duration": 7,
        "description": "Assamese New Year and spring festival",
        "significance": "New year, harvest, Assamese culture",
        "rituals": ["bihu dance", "dhol playing", "gamosa gifting", "community feast"]
    },
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
    
    # Additional Major Festivals
    "akshaya_tritiya": {
        "name": "Akshaya Tritiya",
        "type": "major_festival",
        "lunar_day": "tritiya",
        "month": "vaishakha",
        "duration": 1,
        "description": "The most auspicious day for new beginnings, investments, and spiritual practices. Believed to bring eternal prosperity and success to any venture started on this day.",
        "significance": "Represents eternal prosperity and good fortune, marks the beginning of Treta Yuga, celebrates the friendship of Krishna and Sudama, promotes charitable giving and spiritual merit, and is considered the most auspicious day for gold purchases and new ventures.",
        "rituals": ["gold and jewelry purchases", "charitable donations and feeding the poor", "starting new business ventures", "Vishnu and Lakshmi worship", "fasting and prayers", "reading sacred texts", "planting trees and environmental activities"]
    },
    "raksha_bandhan": {
        "name": "Raksha Bandhan",
        "type": "major_festival",
        "lunar_day": "purnima",
        "month": "sravana",
        "duration": 1,
        "description": "A beautiful festival celebrating the bond between brothers and sisters, where sisters tie protective threads (rakhi) on their brothers' wrists, and brothers pledge to protect their sisters throughout life.",
        "significance": "Celebrates the sacred bond between siblings, promotes family unity and love, represents protection and care in relationships, strengthens social bonds beyond blood relations, and honors the feminine principle of protection.",
        "rituals": ["sisters tying rakhi on brothers' wrists", "brothers giving gifts and promising protection", "family gatherings and feasts", "prayers for siblings' well-being", "exchanging sweets and blessings", "visiting temples together"]
    },
    "nag_panchami": {
        "name": "Nag Panchami",
        "type": "festival",
        "lunar_day": "panchami",
        "month": "sravana",
        "duration": 1,
        "description": "A festival dedicated to the worship of serpents (Nagas), seeking their blessings for protection from snake bites and for fertility and prosperity.",
        "significance": "Honors the serpent deities and their protective power, promotes harmony with nature and wildlife, seeks protection from snake-related dangers, celebrates fertility and life force energy, and maintains ecological balance.",
        "rituals": ["offering milk and flowers to snake idols", "visiting snake temples", "drawing snake images with turmeric", "fasting and prayers", "feeding real snakes (where safe)", "environmental conservation activities"]
    },
    "karthik_purnima": {
        "name": "Karthik Purnima",
        "type": "major_festival",
        "lunar_day": "purnima",
        "month": "kartik",
        "duration": 1,
        "description": "Also known as Dev Diwali, this festival is celebrated as the Diwali of the gods, marked by lighting lamps and taking holy baths in sacred rivers.",
        "significance": "Celebrates the victory of gods over demons, marks the end of the holy month of Kartik, promotes spiritual purification through holy baths, honors Lord Vishnu and Shiva, and brings divine blessings and liberation.",
        "rituals": ["holy bath in sacred rivers", "lighting diyas and lamps", "Ganga aarti ceremonies", "charity and donations", "temple visits and prayers", "cultural programs and processions"]
    },
    
    # Additional Vrats and Observances
    "vat_savitri": {
        "name": "Vat Savitri Vrat",
        "type": "vrat",
        "lunar_day": "amavasya",
        "month": "jyeshtha",
        "duration": 1,
        "description": "A sacred fast observed by married women for their husbands' longevity, inspired by the legend of Savitri who brought her husband Satyavan back from death through her devotion.",
        "significance": "Celebrates the power of a devoted wife's love, ensures husband's long life and well-being, honors the banyan tree as a symbol of longevity, promotes marital fidelity and devotion, and strengthens family bonds.",
        "rituals": ["fasting and prayers under banyan tree", "tying threads around banyan tree", "offering water and flowers to the tree", "listening to Savitri-Satyavan story", "seeking blessings for husband's health", "community gatherings of married women"]
    },
    "ahoi_ashtami": {
        "name": "Ahoi Ashtami",
        "type": "vrat",
        "lunar_day": "ashtami",
        "month": "kartik",
        "duration": 1,
        "description": "A fast observed by mothers for the well-being, health, and long life of their children, dedicated to Goddess Ahoi who protects children from harm.",
        "significance": "Ensures children's health and prosperity, celebrates maternal love and protection, honors the goddess who safeguards children, promotes family welfare, and strengthens the mother-child bond.",
        "rituals": ["nirjala fast by mothers", "drawing Ahoi Mata image", "evening prayers and story recitation", "offering water to stars", "seeking blessings for children", "breaking fast after stargazing"]
    },
    "sharad_purnima": {
        "name": "Sharad Purnima",
        "type": "festival",
        "lunar_day": "purnima",
        "month": "ashwin",
        "duration": 1,
        "description": "The harvest moon festival celebrating the full moon of autumn, believed to shower nectar (amrit) from the moon, bringing health and prosperity.",
        "significance": "Celebrates the beauty of the autumn full moon, promotes health through moonlight exposure, marks the end of monsoon and beginning of winter, honors Goddess Lakshmi, and brings prosperity and well-being.",
        "rituals": ["moonlight meditation and prayers", "preparing kheer and sweets in moonlight", "staying awake to enjoy moonbeams", "Lakshmi worship", "cultural programs and folk dances", "community celebrations under the moon"]
    },
    
    # Astrological Festivals
    "kumbh_mela": {
        "name": "Kumbh Mela",
        "type": "astrological_festival",
        "cycle": "12_years",
        "description": "The largest spiritual gathering in the world, held at four sacred locations when specific planetary alignments occur. Millions of pilgrims gather to take holy baths for spiritual purification.",
        "significance": "Represents the ultimate spiritual pilgrimage, offers liberation from sins through holy bathing, promotes unity among diverse spiritual traditions, celebrates the victory of gods over demons in the cosmic battle for nectar, and provides rare opportunity for spiritual transformation.",
        "rituals": ["holy dip in sacred rivers at auspicious times", "satsang with saints and spiritual teachers", "charitable giving and feeding pilgrims", "spiritual discourses and religious debates", "meditation and yoga practices", "cultural programs and religious processions"]
    }
}

# Monthly Vrat Calendar
MONTHLY_VRATS = {
    "ekadashi": {
        "name": "Ekadashi",
        "frequency": "twice_monthly",
        "days": [11, 26],  # Shukla and Krishna paksha
        "deity": "Vishnu",
        "benefits": "Spiritual purification, moksha, liberation from sins",
        "description": "The most important bi-monthly fast dedicated to Lord Vishnu, observed on the 11th day of both lunar fortnights. Considered highly auspicious for spiritual advancement.",
        "rituals": ["complete fasting from grains and beans", "Vishnu worship and meditation", "chanting Vishnu mantras", "charity and donations", "staying awake in devotion"]
    },
    "pradosh": {
        "name": "Pradosh Vrat",
        "frequency": "twice_monthly", 
        "days": [13, 28],  # Trayodashi
        "deity": "Shiva",
        "benefits": "Prosperity, obstacle removal, material and spiritual success",
        "description": "Sacred fast observed during twilight hours on Trayodashi (13th day) of both lunar fortnights, dedicated to Lord Shiva for removing obstacles and granting prosperity.",
        "rituals": ["evening worship during twilight", "Shiva Linga abhishek", "fasting until evening", "chanting Shiva mantras", "offering bel leaves"]
    },
    "sankashti": {
        "name": "Sankashti Chaturthi",
        "frequency": "monthly",
        "days": [19],  # Krishna paksha chaturthi
        "deity": "Ganesha", 
        "benefits": "Obstacle removal, success in endeavors, wisdom",
        "description": "Monthly fast dedicated to Lord Ganesha on Krishna Paksha Chaturthi, observed for removing obstacles and achieving success in all undertakings.",
        "rituals": ["fasting until moonrise", "Ganesha worship with modaks", "moon worship after sighting", "chanting Ganesha mantras", "charitable acts"]
    },
    "shivaratri": {
        "name": "Masik Shivaratri",
        "frequency": "monthly",
        "days": [14],  # Krishna paksha chaturdashi
        "deity": "Shiva",
        "benefits": "Spiritual growth, liberation, inner transformation",
        "description": "Monthly observance of Shivaratri on Krishna Paksha Chaturdashi, dedicated to Lord Shiva for spiritual advancement and liberation from worldly bondage.",
        "rituals": ["night-long vigil and prayers", "Shiva Linga worship", "fasting and meditation", "chanting Om Namah Shivaya", "offering milk and flowers"]
    },
    "purnima": {
        "name": "Purnima Vrat",
        "frequency": "monthly",
        "days": [15],  # Full moon day
        "deity": "Various (Vishnu, Lakshmi, Satyanarayana)",
        "benefits": "Prosperity, peace, spiritual merit, family harmony",
        "description": "Monthly full moon observance with fasting and prayers, considered highly auspicious for spiritual practices and receiving divine blessings.",
        "rituals": ["fasting and prayers", "Satyanarayana Puja", "charity and donations", "holy bath", "temple visits"]
    },
    "amavasya": {
        "name": "Amavasya Vrat",
        "frequency": "monthly",
        "days": [30],  # New moon day
        "deity": "Ancestors (Pitrs), Shiva",
        "benefits": "Ancestral blessings, spiritual purification, protection",
        "description": "Monthly new moon observance for honoring ancestors and seeking their blessings, also considered auspicious for Shiva worship.",
        "rituals": ["ancestral worship (Pitru Puja)", "offering food to ancestors", "charity in ancestors' names", "Shiva worship", "meditation and prayers"]
    }
}

# Festival Categories
FESTIVAL_CATEGORIES = {
    "major_festivals": [
        "diwali", "holi", "dussehra", "navratri", "janmashtami", 
        "ganesh_chaturthi", "maha_shivratri", "ram_navami", 
        "akshaya_tritiya", "raksha_bandhan", "karthik_purnima"
    ],
    "vrats_and_fasts": [
        "karva_chauth", "teej", "devutthana_ekadashi", "utpanna_ekadashi",
        "vat_savitri", "ahoi_ashtami", "pradosh_vrat", "sankashti_chaturthi"
    ],
    "seasonal_festivals": [
        "makar_sankranti", "baisakhi", "sharad_purnima", "nag_panchami"
    ],
    "regional_festivals": [
        "onam", "durga_puja", "dev_diwali", "kalabhairav_jayanti"
    ],
    "spiritual_festivals": [
        "guru_purnima", "maha_shivratri", "hanuman_jayanti", "kumbh_mela"
    ],
    "krishna_festivals": [
        "janmashtami", "govardhan_puja", "kansa_vadh"
    ],
    "monthly_observances": [
        "ekadashi", "pradosh", "sankashti", "shivaratri", "purnima", "amavasya"
    ],
    "women_festivals": [
        "karva_chauth", "teej", "vat_savitri", "ahoi_ashtami"
    ],
    "ancestral_periods": [
        "pitra_paksha"
    ],
    "special_occasions": [
        "tulasi_vivah", "dev_diwali", "kalabhairav_jayanti"
    ]
}