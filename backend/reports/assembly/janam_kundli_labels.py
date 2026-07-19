"""English ↔ Hindi display labels for Janam Kundli fact values."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .janam_kundli_i18n import is_hindi

SIGN_HI = {
    "Aries": "मेष",
    "Taurus": "वृषभ",
    "Gemini": "मिथुन",
    "Cancer": "कर्क",
    "Leo": "सिंह",
    "Virgo": "कन्या",
    "Libra": "तुला",
    "Scorpio": "वृश्चिक",
    "Sagittarius": "धनु",
    "Capricorn": "मकर",
    "Aquarius": "कुंभ",
    "Pisces": "मीन",
}

PLANET_HI = {
    "Sun": "सूर्य",
    "Moon": "चंद्र",
    "Mars": "मंगल",
    "Mercury": "बुध",
    "Jupiter": "गुरु",
    "Venus": "शुक्र",
    "Saturn": "शनि",
    "Rahu": "राहु",
    "Ketu": "केतु",
    "Ascendant": "लग्न",
    "Lagna": "लग्न",
}

PLANET_ABBR_EN = {
    "Sun": "Su",
    "Moon": "Mo",
    "Mars": "Ma",
    "Mercury": "Me",
    "Jupiter": "Ju",
    "Venus": "Ve",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke",
}

PLANET_ABBR_HI = {
    "Sun": "सू",
    "Moon": "चं",
    "Mars": "मं",
    "Mercury": "बु",
    "Jupiter": "गु",
    "Venus": "शु",
    "Saturn": "श",
    "Rahu": "रा",
    "Ketu": "के",
}

NAKSHATRA_HI = {
    "Ashwini": "अश्विनी",
    "Bharani": "भरणी",
    "Krittika": "कृत्तिका",
    "Rohini": "रोहिणी",
    "Mrigashira": "मृगशिरा",
    "Ardra": "आर्द्रा",
    "Punarvasu": "पुनर्वसु",
    "Pushya": "पुष्य",
    "Ashlesha": "आश्लेषा",
    "Magha": "मघा",
    "Purva Phalguni": "पूर्व फाल्गुनी",
    "Uttara Phalguni": "उत्तर फाल्गुनी",
    "Hasta": "हस्त",
    "Chitra": "चित्रा",
    "Swati": "स्वाति",
    "Vishakha": "विशाखा",
    "Anuradha": "अनुराधा",
    "Jyeshtha": "ज्येष्ठा",
    "Mula": "मूल",
    "Purva Ashadha": "पूर्वाषाढ़ा",
    "Uttara Ashadha": "उत्तराषाढ़ा",
    "Shravana": "श्रवण",
    "Dhanishta": "धनिष्ठा",
    "Shatabhisha": "शतभिषा",
    "Purva Bhadrapada": "पूर्व भाद्रपद",
    "Uttara Bhadrapada": "उत्तर भाद्रपद",
    "Revati": "रेवती",
}

TITHI_HI = {
    "Pratipada": "प्रतिपदा",
    "Dwitiya": "द्वितीया",
    "Tritiya": "त्रितीया",
    "Chaturthi": "चतुर्थी",
    "Panchami": "पंचमी",
    "Shashthi": "षष्ठी",
    "Saptami": "सप्तमी",
    "Ashtami": "अष्टमी",
    "Navami": "नवमी",
    "Dashami": "दशमी",
    "Ekadashi": "एकादशी",
    "Dwadashi": "द्वादशी",
    "Trayodashi": "त्रयोदशी",
    "Chaturdashi": "चतुर्दशी",
    "Purnima": "पूर्णिमा",
    "Amavasya": "अमावस्या",
}

PAKSHA_HI = {
    "Shukla": "शुक्ल",
    "Krishna": "कृष्ण",
}

VARA_HI = {
    "Sunday": "रविवार",
    "Monday": "सोमवार",
    "Tuesday": "मंगलवार",
    "Wednesday": "बुधवार",
    "Thursday": "गुरुवार",
    "Friday": "शुक्रवार",
    "Saturday": "शनिवार",
}

YOGA_HI = {
    "Vishkumbha": "विष्कंभ",
    "Priti": "प्रीति",
    "Ayushman": "आयुष्मान",
    "Saubhagya": "सौभाग्य",
    "Shobhana": "शोभन",
    "Atiganda": "अतिगंड",
    "Sukarma": "सुकर्म",
    "Dhriti": "धृति",
    "Shula": "शूल",
    "Ganda": "गंड",
    "Vriddhi": "वृद्धि",
    "Dhruva": "ध्रुव",
    "Vyaghata": "व्याघात",
    "Harshana": "हर्षण",
    "Vajra": "वज्र",
    "Siddhi": "सिद्धि",
    "Vyatipata": "व्यतीपात",
    "Variyan": "वरीयान",
    "Parigha": "परिघ",
    "Shiva": "शिव",
    "Siddha": "सिद्ध",
    "Sadhya": "साध्य",
    "Shubha": "शुभ",
    "Shukla": "शुक्ल",
    "Brahma": "ब्रह्म",
    "Indra": "इंद्र",
    "Vaidhriti": "वैधृति",
}

KARANA_HI = {
    "Bava": "बव",
    "Balava": "बालव",
    "Kaulava": "कौलव",
    "Taitila": "तैतिल",
    "Gara": "गर",
    "Vanija": "वणिज",
    "Vishti": "विष्टि",
    "Kimstughna": "किंस्तुघ्न",
    "Shakuni": "शकुनि",
    "Chatushpada": "चतुष्पद",
    "Naga": "नाग",
}

DIGNITY_HI = {
    "exalted": "उच्च",
    "exaltation": "उच्च",
    "debilitated": "नीच",
    "debilitation": "नीच",
    "own": "स्वगृह",
    "own_sign": "स्वगृह",
    "own sign": "स्वगृह",
    "moolatrikona": "मूलत्रिकोण",
    "friendly": "मित्र",
    "friend": "मित्र",
    "enemy": "शत्रु",
    "neutral": "सम",
    "favorable": "अनुकूल",
    "unfavorable": "प्रतिकूल",
    "strong": "बलवान",
    "weak": "दुर्बल",
}

FRIENDSHIP_HI = {
    "self": "स्व",
    "own_sign": "स्वराशि",
    "great_friend": "अति मित्र",
    "friend": "मित्र",
    "neutral": "सम",
    "enemy": "शत्रु",
    "great_enemy": "अति शत्रु",
}

FUNCTIONAL_HI = {
    "benefic": "शुभ",
    "malefic": "अशुभ",
    "neutral": "सम",
    "yogakaraka": "योगकारक",
}

COMBUST_HI = {
    "combust": "अस्त",
    "cazimi": "अस्त-मध्य",
    "normal": "—",
}

AVASTHA_HI = {
    "Bal": "बाल",
    "Kumar": "कुमार",
    "Yuva": "युवा",
    "Vriddha": "वृद्ध",
    "Mrit": "मृत",
    "—": "—",
}

SPECIAL_ROLE_HI = {
    "Yogi": "योगी",
    "Avayogi": "अवयोगी",
    "Tithi Shunya": "तिथि शून्य",
    "Dagdha": "दग्ध",
    "Badhaka": "बाधक",
}

TARA_HI = {
    "Janma": "जन्म",
    "Sampat": "संपत्",
    "Vipat": "विपत्",
    "Kshema": "क्षेम",
    "Pratyak": "प्रत्यक्",
    "Sadhana": "साधना",
    "Naidhana": "नैधन",
    "Mitra": "मित्र",
    "Ati Mitra": "अति मित्र",
}

TARA_QUALITY_HI = {
    "supportive": "सहायक",
    "challenging": "चुनौतीपूर्ण",
    "neutral": "सम",
    "excellent": "उत्कृष्ट",
    "good": "शुभ",
    "bad": "अशुभ",
}

GANA_HI = {
    "Deva": "देव",
    "Manushya": "मनुष्य",
    "Rakshasa": "राक्षस",
}

NADI_HI = {
    "Adya": "आद्य",
    "Madhya": "मध्य",
    "Antya": "अंत्य",
}

YONI_HI = {
    "Horse": "अश्व",
    "Elephant": "गज",
    "Sheep": "मेष",
    "Serpent": "सर्प",
    "Dog": "श्वान",
    "Cat": "बिड़ाल",
    "Rat": "मूषक",
    "Cow": "गौ",
    "Buffalo": "महिष",
    "Tiger": "व्याघ्र",
    "Deer": "मृग",
    "Monkey": "वानर",
    "Mongoose": "नकुल",
    "Lion": "सिंह",
}

GUNA_HI = {
    "Sattva": "सत्त्व",
    "Rajas": "रजस्",
    "Tamas": "तमस्",
}

ELEMENT_HI = {
    "Fire": "अग्नि",
    "Earth": "पृथ्वी",
    "Air": "वायु",
    "Water": "जल",
    "Ether": "आकाश",
}

STRENGTH_HI = {
    "High": "उच्च",
    "Medium": "मध्यम",
    "Low": "निम्न",
    "Strong": "बलवान",
    "Weak": "दुर्बल",
}

NAKSHATRA_QUALITY_HI = {
    "Swift": "शीघ्र",
    "Creative": "सृजनात्मक",
    "Sharp": "तीक्ष्ण",
    "Growing": "वर्धमान",
    "Soft": "मृदु",
    "Movable": "चर",
    "Fierce": "उग्र",
    "Fixed": "स्थिर",
    "Mixed": "मिश्र",
}

DEITY_HI = {
    "Ashwini Kumaras": "अश्विनी कुमार",
    "Yama": "यम",
    "Agni": "अग्नि",
    "Brahma": "ब्रह्मा",
    "Soma": "सोम",
    "Rudra": "रुद्र",
    "Aditi": "अदिति",
    "Brihaspati": "बृहस्पति",
    "Nagas": "नाग",
    "Sarpas": "सर्प",
    "Pitrs": "पितर",
    "Pitris (Ancestors)": "पितर",
    "Bhaga": "भग",
    "Aryaman": "अर्यमा",
    "Savitar": "सवितृ",
    "Savitr": "सवितृ",
    "Tvashtar": "त्वष्टा",
    "Vayu": "वायु",
    "Indra-Agni": "इंद्र-अग्नि",
    "Indragni": "इंद्र-अग्नि",
    "Mitra": "मित्र",
    "Indra": "इंद्र",
    "Nirrti": "निर्ऋति",
    "Nirriti": "निर्ऋति",
    "Apas": "आपः",
    "Apas (Water)": "आपः",
    "Vishve Devas": "विश्वेदेव",
    "Vishvedevas": "विश्वेदेव",
    "Vishvadevas": "विश्वेदेव",
    "Vishnu": "विष्णु",
    "Vasus": "वसु",
    "Varuna": "वरुण",
    "Aja Ekapada": "अज एकपाद",
    "Ahir Budhnya": "अहिर्बुध्न्य",
    "Ahirbudhnya": "अहिर्बुध्न्य",
    "Pushan": "पूषन्",
}

DIRECTION_HI = {
    "North": "उत्तर",
    "South": "दक्षिण",
    "East": "पूर्व",
    "West": "पश्चिम",
    "North-East": "उत्तर-पूर्व",
    "North-West": "उत्तर-पश्चिम",
    "South-East": "दक्षिण-पूर्व",
    "South-West": "दक्षिण-पश्चिम",
}

SYMBOL_HI = {
    "Coral": "प्रवाल",
    "Horse head": "अश्व मुख",
    "Yoni": "योनि",
    "Razor/Flame": "क्षुर / अग्नि",
    "Cart/Chariot": "शकट",
    "Deer head": "मृग मुख",
    "Teardrop": "अश्रु",
    "Bow": "धनुष",
    "Flower": "पुष्प",
    "Serpent": "सर्प",
    "Palanquin": "पालकी",
    "Cot/Bed": "शय्या",
    "Hand": "हस्त",
    "Pearl": "मुक्ता",
    "Sword": "खड्ग",
    "Archway": "तोरण",
    "Lotus": "कमल",
    "Earring": "कुंडल",
    "Lion's tail / Couch": "सिंह पुच्छ",
    "Elephant tusk": "गज दंत",
    "Ear / Three footprints": "कर्ण / पदचिह्न",
    "Drum": "दुंदुभि",
    "Empty circle": "रिक्त चक्र",
    "Sword / Two faces": "खड्ग / द्विमुख",
    "Twin / Couch": "युग्म / शय्या",
    "Fish / Drum": "मत्स्य / मृदंग",
}

PADA_NATURE_HI = {
    "Initiative, beginning, action": "पहल, आरंभ, कर्म",
    "Stability, material, practical": "स्थिरता, भौतिक, व्यावहारिक",
    "Communication, movement, flexibility": "संवाद, गति, लचीलापन",
    "Emotion, intuition, completion": "भावना, अंतर्ज्ञान, पूर्णता",
}

GEMSTONE_HI = {
    "Ruby": "माणिक्य",
    "Pearl": "मोती",
    "Red Coral": "मूंगा",
    "Emerald": "पन्ना",
    "Yellow Sapphire": "पुखराज",
    "Diamond": "हीरा",
    "White Sapphire": "सफेद पुखराज",
    "Blue Sapphire": "नीलम",
    "Hessonite": "गोमेद",
    "Cat's Eye": "लहसुनिया",
    "Diamond or White Sapphire": "हीरा या सफेद पुखराज",
}

SHAKTI_HI = {
    "Pradhvamsa Shakti (Power to scatter)": "प्रध्वंसा शक्ति (बिखराने की शक्ति)",
    "Shidravyapani Shakti (Quick Reach)": "शीघ्रव्यापनी शक्ति (शीघ्र पहुँच)",
    "Apabharani Shakti (Removal of burden)": "अपभरणी शक्ति (भार हटाना)",
    "Dahana Shakti (Power to burn/purify)": "दहन शक्ति (शुद्धिकरण)",
    "Rohana Shakti (Power to grow)": "रोहण शक्ति (वृद्धि)",
    "Prinana Shakti (Power of fulfillment)": "प्रीणन शक्ति (तृप्ति)",
    "Yatna Shakti (Power of effort)": "यत्न शक्ति (प्रयास)",
    "Vasutva Shakti (Power of wealth/renewal)": "वसुत्व शक्ति (समृद्धि/नवीकरण)",
    "Brahmavarchasa Shakti (Power of spiritual glow)": "ब्रह्मवर्चस शक्ति",
    "Visasleshana Shakti (Power to paralyze/detach)": "विषश्लेषण शक्ति",
    "Tyagekshemana Shakti (Power to leave the body)": "त्यागेक्षेमण शक्ति",
    "Prajana Shakti (Power of procreation)": "प्रजन शक्ति",
    "Chayani Shakti (Power of accumulation)": "चयनी शक्ति",
    "Hasta Sthapaniya Shakti (Power to put in hand)": "हस्तस्थापनीय शक्ति",
    "Punya Chayani Shakti (Power of merit)": "पुण्य चयनी शक्ति",
    "Vyapana Shakti (Power to achieve)": "व्यापन शक्ति",
    "Radhana Shakti (Power of worship)": "राधना शक्ति",
    "Arohana Shakti (Power to rise/conquer)": "आरोहण शक्ति",
    "Barhana Shakti (Power to root out)": "बर्हण शक्ति",
    "Varchasva Shakti (Power of invigoration)": "वर्चस्व शक्ति",
    "Apradhrishya Shakti (Power of victory)": "अप्रधृष्य शक्ति (विजय)",
    "Aprati Shakti (Power of connection)": "अप्रति शक्ति",
    "Khyapayitri Shakti (Power to give fame)": "ख्यापयित्री शक्ति",
    "Bheshaja Shakti (Power of healing)": "भेषज शक्ति",
    "Yajamana Shakti (Power of sacrifice)": "यजमान शक्ति",
    "Varshodyamana Shakti (Power to bring rain/growth)": "वर्षोद्यमन शक्ति",
    "Kshiradyapani Shakti (Power of nourishment)": "क्षीराद्यपानी शक्ति",
}

VRIKSHA_HI = {
    "Arjuna": "अर्जुन",
    "Amla": "आँवला",
    "Peepal": "पीपल",
    "Banyan": "वट",
    "Neem": "नीम",
    "Mango": "आम",
    "Jackfruit": "कटहल",
    "Ashoka": "अशोक",
    "Bamboo": "बाँस",
    "Palash": "पलाश",
    "Bael": "बिल्व",
    "Jasmine": "चमेली",
    "Shami": "शमी",
    "Kadamba": "कदंब",
    "Mahua": "महुआ",
    "Sal": "साल",
    "Semal": "सेमल",
    "Madar": "मदार",
    "Nagkesar": "नागकेसर",
    "Jamun": "जामुन",
    "Strychnine Tree (Kuchila)": "कुचला वृक्ष",
    "Cluster Fig (Gular)": "गूलर",
    "Cutch Tree (Khair)": "खैर",
    "Long Pepper (Krishun)": "पिप्पली",
    "Wood Apple (Kaitha)": "कैथा",
    "Maulsari": "मौलसिरी",
    "Kher": "खैर",
}

ACTIVITY_HI = {
    "Independence and movement": "स्वतंत्रता और गति",
    "Swift action and healing": "शीघ्र कर्म और उपचार",
    "Letting go and transformation": "त्याग और रूपांतरण",
    "Purification and cutting negativity": "शुद्धिकरण",
    "Growth and nourishment": "वृद्धि और पोषण",
    "Seeking and exploration": "खोज और अन्वेषण",
    "Intense effort and transformation": "तीव्र प्रयास",
    "Renewal and return to basics": "नवीकरण",
    "Nourishment and spiritual practice": "पोषण और साधना",
    "Detachment and serpent wisdom": "वैराग्य और नाग ज्ञान",
    "Ancestral worship and authority": "पितृ पूजा और अधिकार",
    "Pleasure and creative expression": "आनंद और सृजन",
    "Service and accumulation": "सेवा और संचय",
    "Skillful work and craftsmanship": "कौशलपूर्ण कार्य",
    "Artistic creation and beauty": "कला और सौंदर्य",
    "Goal achievement and determination": "लक्ष्य सिद्धि",
    "Devotion and friendship": "भक्ति और मित्रता",
    "Leadership and protection": "नेतृत्व और रक्षा",
    "Root-cause analysis and foundational work": "मूल कारण विश्लेषण",
    "Invigoration and purification": "ऊर्जा और शुद्धिकरण",
    "Victory and righteous action": "विजय और धर्म कर्म",
    "Listening and learning": "श्रवण और अधिगम",
    "Music and rhythmic activities": "संगीत और लय",
    "Strategic planning and medicinal consumption": "योजना और औषधि",
    "Sacrifice and spiritual intensity": "त्याग और तीव्र साधना",
    "Deep meditation and rain-making": "गहन ध्यान",
    "Nourishment and completion": "पोषण और पूर्णता",
}

REASON_HI = {
    "Functional malefic for this lagna": "इस लग्न के लिए कार्यात्मक पाप ग्रह",
    "only if suitability checks support it": "केवल उपयुक्तता जाँच के बाद",
}

WEEKDAY_HI = {
    "Sunday": "रविवार",
    "Monday": "सोमवार",
    "Tuesday": "मंगलवार",
    "Wednesday": "बुधवार",
    "Thursday": "गुरुवार",
    "Friday": "शुक्रवार",
    "Saturday": "शनिवार",
    "Any day": "किसी भी दिन",
}

COLOR_HI = {
    "Gold": "सुनहरा",
    "saffron": "केसरिया",
    "Saffron": "केसरिया",
    "orange": "नारंगी",
    "Orange": "नारंगी",
    "White": "सफेद",
    "silver": "रजत",
    "Silver": "रजत",
    "cream": "क्रीम",
    "Cream": "क्रीम",
    "Red": "लाल",
    "deep orange": "गहरा नारंगी",
    "Green": "हरा",
    "light green": "हल्का हरा",
    "Yellow": "पीला",
    "mustard": "सरसों पीला",
    "Mustard": "सरसों पीला",
    "pastel pink": "हल्का गुलाबी",
    "Blue": "नीला",
    "dark grey": "गहरा धूसर",
    "Dark grey": "गहरा धूसर",
    "black": "काला",
    "Black": "काला",
    "Smoke grey": "धुँधला धूसर",
    "dark blue": "गहरा नीला",
    "earthy tones": "मिट्टी के रंग",
    "Dull white": "मंद सफेद",
    "smoky grey": "धुँआ धूसर",
    "muted tones": "मंद रंग",
}

REMEDY_ROLE_HI = {
    "Mahadasha lord": "महादशा स्वामी",
    "Antardasha lord": "अन्तर्दशा स्वामी",
    "Priority planet": "प्राथमिक ग्रह",
}

YOGA_NAME_HI = {
    "Kendra-Trikona Raj Yoga": "केंद्र-त्रिकोण राज योग",
    "Viparita Raja Yoga": "विपरीत राज योग",
    "Vipareeta Raja Yoga (Health)": "विपरीत राज योग (स्वास्थ्य)",
    "Dharma-Karma Yoga": "धर्म-कर्म योग",
    "Pasha Yoga": "पाश योग",
    "Adhi Yoga": "अधि योग",
    "Vasi Yoga": "वसि योग",
    "Vesi Yoga": "वेसि योग",
    "Ubhayachari Yoga": "उभयचरी योग",
    "Parivartana Yoga": "परिवर्तन योग",
    "Maha Yoga": "महा योग",
    "Khala Yoga": "खल योग",
    "Śani-Karma Yoga": "शनि-कर्म योग",
    "Sani-Karma Yoga": "शनि-कर्म योग",
    "Saraswati Yoga": "सरस्वती योग",
    "Saraswati Yoga (Aspect)": "सरस्वती योग (दृष्टि)",
    "Guru-Mangal Yoga": "गुरु-मंगल योग",
    "Budhaditya Yoga": "बुधादित्य योग",
    "Mangal Dosha": "मंगल दोष",
    "Ayur Yoga": "आयुर् योग",
    "Chandra Sukha Yoga": "चंद्र सुख योग",
    "Gaja Kesari Yoga": "गज केसरी योग",
    "Dainya Yoga": "दैन्य योग",
    "Ganda Mool": "गंड मूल",
    "Abhijit": "अभिजित्",
    "Gola Yoga": "गोल योग",
    "Yuga Yoga": "युग योग",
    "Shula Yoga": "शूल योग",
    "Kedara Yoga": "केदार योग",
    "Dama Yoga": "दाम योग",
    "Veena Yoga": "वीणा योग",
}


def _lookup(mapping: Dict[str, str], value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text in mapping:
        return mapping[text]
    # Case-insensitive English keys
    for key, hi in mapping.items():
        if key.lower() == text.lower():
            return hi
    return None


def label_sign(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(SIGN_HI, text) or text
    return text


def label_planet(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(PLANET_HI, text) or text
    return text


def label_planet_abbr(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return PLANET_ABBR_HI.get(text) or _lookup(PLANET_ABBR_HI, text) or text[:2]
    return PLANET_ABBR_EN.get(text) or text[:2]


def label_nakshatra(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(NAKSHATRA_HI, text) or text
    return text


def label_dignity(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(DIGNITY_HI, text) or text
    return text.replace("_", " ")


def label_friendship(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(FRIENDSHIP_HI, text) or text.replace("_", " ")
    return text.replace("_", " ")


def label_functional(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(FUNCTIONAL_HI, text) or text
    return text.replace("_", " ")


def label_combust(value: Any, language: Any) -> str:
    text = str(value or "").strip().lower()
    if not text or text == "normal":
        return "—"
    if is_hindi(language):
        return _lookup(COMBUST_HI, text) or text
    if text == "combust":
        return "Combust"
    if text == "cazimi":
        return "Cazimi"
    return text


def label_avastha(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "—"
    if is_hindi(language):
        return _lookup(AVASTHA_HI, text) or text
    return text


def label_special_roles(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text or text == "—":
        return "—"
    if not is_hindi(language):
        return text
    parts = [p.strip() for p in text.split(";") if p.strip()]
    return "; ".join(SPECIAL_ROLE_HI.get(p, p) for p in parts)


def label_tara(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(TARA_HI, text) or text
    return text


def label_tara_quality(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(TARA_QUALITY_HI, text) or text
    return text.replace("_", " ")


def label_gana(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(GANA_HI, text) or text
    return text


def label_nadi(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(NADI_HI, text) or text
    return text


def label_yoni(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(YONI_HI, text) or text
    return text


def label_guna(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(GUNA_HI, text) or text
    return text


def label_element(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(ELEMENT_HI, text) or text
    return text


def label_strength(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(STRENGTH_HI, text) or text
    return text


def label_nakshatra_quality(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(NAKSHATRA_QUALITY_HI, text) or text
    return text


def label_deity(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(DEITY_HI, text) or text
    return text


def label_direction(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(DIRECTION_HI, text) or text
    return text


def label_symbol(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(SYMBOL_HI, text) or text
    return text


def label_pada_nature(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(PADA_NATURE_HI, text) or text
    return text


_GEMSTONE_SUITABILITY_SUFFIXES = (
    ", only if suitability checks support it",
    " only if suitability checks support it",
)


def normalize_gemstone_name(value: Any) -> str:
    """Strip remedy-engine suitability clauses; keep the stone name only."""
    text = str(value or "").strip()
    if not text:
        return ""
    for suffix in _GEMSTONE_SUITABILITY_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)].strip()
        elif suffix in text:
            text = text.split(suffix)[0].strip().rstrip(",")
    return text.strip(" ,;")


def label_gemstone(value: Any, language: Any) -> str:
    text = normalize_gemstone_name(value)
    if not text:
        return ""
    if is_hindi(language):
        # Multi-option strings like "Diamond or White Sapphire"
        mapped = _lookup(GEMSTONE_HI, text)
        if mapped:
            return mapped
        parts = [p.strip() for p in re.split(r"\s+or\s+", text, flags=re.IGNORECASE) if p.strip()]
        if len(parts) > 1:
            return " या ".join(label_gemstone(p, language) for p in parts)
        return text
    return text


def label_shakti(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(SHAKTI_HI, text) or text
    return text


def label_vriksha(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(VRIKSHA_HI, text) or text
    return text


def label_activity(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(ACTIVITY_HI, text) or text
    return text


def label_weekday(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(WEEKDAY_HI, text) or text
    return text


def label_colors(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text or not is_hindi(language):
        return text
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return text
    out = []
    for part in parts:
        mapped = _lookup(COLOR_HI, part)
        if mapped:
            out.append(mapped)
            continue
        # Token-wise for phrases like "Gold, saffron, orange"
        tokens = [t.strip() for t in re.split(r"[/,]", part) if t.strip()]
        if len(tokens) > 1:
            out.append(" / ".join(_lookup(COLOR_HI, tok) or tok for tok in tokens))
        else:
            out.append(part)
    return ", ".join(out)


def label_remedy_role(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(REMEDY_ROLE_HI, text) or text
    return text


def label_reason(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if not is_hindi(language):
        return text
    mapped = _lookup(REASON_HI, text)
    if mapped:
        return mapped
    # Soft-replace known English fragments inside longer reason strings.
    out = text
    for en, hi in REASON_HI.items():
        if en in out:
            out = out.replace(en, hi)
    return out


def label_yoga_name(value: Any, language: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if is_hindi(language):
        return _lookup(YOGA_NAME_HI, text) or localize_evidence_text(text, language)
    return text


# Long phrase → Hindi (applied before planet tokens so "from the Moon" stays intact).
_EVIDENCE_PHRASES_HI: tuple[tuple[str, str], ...] = tuple(
    sorted(
        [
            (
                "reduces hospitalization and mental health issues",
                "अस्पताल और मानसिक तनाव कम करता है",
            ),
            (
                "emotional stability, good digestive health",
                "भावनात्मक स्थिरता, अच्छा पाचन",
            ),
            (
                "structured, responsible work style",
                "अनुशासित, उत्तरदायी कार्य शैली",
            ),
            (
                "technical and scientific education aptitude",
                "तकनीकी/वैज्ञानिक शिक्षा रुचि",
            ),
            ("marriage delays and conflicts", "विवाह में विलंब और संघर्ष"),
            ("favorable house - good longevity", "अनुकूल भाव — अच्छी आयु"),
            ("good learning ability", "अच्छी अधिगम क्षमता"),
            ("dharmic career success", "धार्मिक/कर्म क्षेत्र में सफलता"),
            (
                "Benefics in the 6th, 7th, or 8th from the Moon. Indicates leadership, wealth, and a happy life.",
                "चंद्र से 6, 7 या 8वें भाव में शुभ ग्रह। संकेत: नेतृत्व, धन और सुखमय जीवन।",
            ),
            (
                "Benefics in the 6th, 7th, or 8th from the Moon",
                "चंद्र से 6, 7 या 8वें भाव में शुभ ग्रह",
            ),
            (
                "Planets in the 12th house from the Sun. Makes the person charitable, and famous.",
                "सूर्य से 12वें भाव में ग्रह। जातक को परोपकारी और प्रसिद्ध बनाता है।",
            ),
            (
                "Planets in the 12th house from the Sun",
                "सूर्य से 12वें भाव में ग्रह",
            ),
            (
                "Planets in the 2nd house from the Sun. Makes the person truthful, and skillful.",
                "सूर्य से 2वें भाव में ग्रह। जातक को सत्यवादी और कुशल बनाता है।",
            ),
            (
                "All planets in five signs - can be bound by obligations.",
                "पाँच राशियों में सभी ग्रह — दायित्वों में बाँध सकते हैं।",
            ),
            ("All planets in five signs", "पाँच राशियों में सभी ग्रह"),
            ("can be bound by obligations", "दायित्वों में बाँध सकते हैं"),
            ("Indicates leadership, wealth, and a happy life", "संकेत: नेतृत्व, धन और सुखमय जीवन"),
            ("Makes the person charitable, and famous", "जातक को परोपकारी और प्रसिद्ध बनाता है"),
            ("Makes the person truthful, and skillful", "जातक को सत्यवादी और कुशल बनाता है"),
            ("Mercury, Jupiter, Venus in mutual aspect", "बुध, गुरु, शुक्र परस्पर दृष्टि"),
            ("Exchange between lord of", "भाव स्वामियों का परस्पर परिवर्तन — भाव"),
            ("from the Moon", "चंद्र से"),
            ("from the Sun", "सूर्य से"),
            ("from the Lagna", "लग्न से"),
            ("Dusthana lord", "दुस्थान स्वामी"),
            ("dusthana house", "दुस्थान भाव"),
            ("Lagna lord", "लग्न स्वामी"),
            ("mutual aspect", "परस्पर दृष्टि"),
            ("in mutual", "परस्पर"),
            ("own/exaltation sign", "स्वराशि/उच्च राशि"),
            ("spotless reputation", "निर्मल प्रतिष्ठा"),
            ("career-centric personality", "करियर-केंद्रित व्यक्तित्व"),
            ("fortune supports profession", "भाग्य व्यवसाय का समर्थन करता है"),
            ("health challenges", "स्वास्थ्य चुनौतियाँ"),
            ("disease proneness", "रोग प्रवृत्ति"),
            ("chronic health issues", "दीर्घकालिक स्वास्थ्य समस्याएँ"),
            ("natural healing ability, strong immunity", "प्राकृतिक उपचार क्षमता, मजबूत रोग प्रतिरोध"),
            ("strong vitality and leadership in health", "बलवान जीवनशक्ति और स्वास्थ्य में नेतृत्व"),
            ("victory over diseases", "रोगों पर विजय"),
            ("reduces chronic health issues", "दीर्घकालिक स्वास्थ्य समस्याएँ कम करता है"),
            ("strong marriage", "दृढ़ विवाह"),
            ("beautiful spouse, happy marriage", "सुंदर जीवनसाथी, सुखी विवाह"),
            ("harmonious marriage, spiritual spouse", "सामंजस्यपूर्ण विवाह, आध्यात्मिक जीवनसाथी"),
            ("balanced marriage, good values", "संतुलित विवाह, अच्छे मूल्य"),
            ("good marriage", "अच्छा विवाह"),
            ("marriage challenges", "विवाह चुनौतियाँ"),
            ("wisdom and prosperity", "ज्ञान और समृद्धि"),
            ("wealth yoga", "धन योग"),
        ],
        key=lambda kv: -len(kv[0]),
    )
)


def localize_evidence_text(value: Any, language: Any) -> str:
    """Best-effort Hindiization of calculator evidence strings.

    Phrase replacements run before planet-token swaps so patterns like
    ``from the Moon`` are not broken by an earlier ``Moon`` → ``चंद्र`` pass.
    """
    text = str(value or "").strip()
    if not text or not is_hindi(language):
        return text
    mapped_name = _lookup(YOGA_NAME_HI, text)
    if mapped_name:
        return mapped_name

    out = text
    for en, hi in _EVIDENCE_PHRASES_HI:
        out = re.compile(re.escape(en), re.IGNORECASE).sub(hi, out)

    # Structural patterns: "7th lord Saturn", "in 8th house", "in dusthana house 8".
    out = re.sub(
        r"\b(\d+)(?:st|nd|rd|th)\s+lord\b",
        r"\1वें भाव के स्वामी",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\bin\s+dusthana\s+house\s+(\d+)\b",
        r"दुस्थान भाव \1 में",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\bin\s+(\d+)(?:st|nd|rd|th)\s+house\b",
        r"\1वें भाव में",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\b(\d+)(?:st|nd|rd|th)\s+house\b",
        r"\1वें भाव",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(r"\b(\d+)(?:st|nd|rd|th)\b", r"\1वें", out, flags=re.IGNORECASE)
    # After Hindi house tokens: "in दुस्थान भाव 8" / "in 8वें भाव"
    out = re.sub(r"\bin\s+(दुस्थान भाव\s+\d+)\b", r"\1 में", out, flags=re.IGNORECASE)
    out = re.sub(r"\bin\s+(\d+वें भाव)\b", r"\1 में", out)

    for en, hi in sorted(PLANET_HI.items(), key=lambda kv: -len(kv[0])):
        out = re.sub(rf"\b{re.escape(en)}\b", hi, out, flags=re.IGNORECASE)
    for en, hi in STRENGTH_HI.items():
        out = re.sub(rf"\b{re.escape(en)}\b", hi, out, flags=re.IGNORECASE)

    word_map = [
        ("Indicates", "संकेत:"),
        ("Makes the person", "जातक को बनाता है"),
        ("connected", "युक्त"),
        ("connection", "योग"),
        ("create", "से"),
        ("with", "के साथ"),
        ("Planets", "ग्रह"),
        ("planets", "ग्रह"),
        ("Benefics", "शुभ ग्रह"),
        ("benefics", "शुभ ग्रह"),
        ("Malefics", "पाप ग्रह"),
        ("malefics", "पाप ग्रह"),
        ("malefic", "पाप ग्रह"),
        ("Dusthana", "दुस्थान"),
        ("dusthana", "दुस्थान"),
        ("Kendra", "केंद्र"),
        ("kendra", "केंद्र"),
        ("Trikona", "त्रिकोण"),
        ("trikona", "त्रिकोण"),
        ("aspect", "दृष्टि"),
        ("Aspect", "दृष्टि"),
        ("lord", "स्वामी"),
        ("house", "भाव"),
        ("signs", "राशियाँ"),
        ("sign", "राशि"),
        (" and ", " और "),
        (" or ", " या "),
        (" in ", " में "),
        (" of ", " के "),
    ]
    for en, hi in word_map:
        out = out.replace(en, hi)

    out = re.sub(r"\s+", " ", out).strip()
    out = re.sub(r"\s+([,.;:])", r"\1", out)
    return out


def localize_fact_names(value: Any, language: Any) -> Any:
    """Recursively localize common English astrology name fields for Hindi LLM/PDF chrome."""
    if not is_hindi(language):
        return value
    if isinstance(value, list):
        return [localize_fact_names(item, language) for item in value]
    if not isinstance(value, dict):
        return value

    out: Dict[str, Any] = {}
    for key, raw in value.items():
        key_l = str(key).lower()
        if key_l in {"sign_name", "ascendant_sign_name"} and isinstance(raw, str):
            out[key] = label_sign(raw, language)
            continue
        if key_l == "moon_sign_basis" and isinstance(raw, str):
            # Pure sign token → Hindi; free-text notes left unchanged.
            out[key] = label_sign(raw, language) if _lookup(SIGN_HI, raw) else raw
            continue
        if key_l in {"nakshatra", "nakshatra_name"} and isinstance(raw, str):
            out[key] = label_nakshatra(raw, language)
            continue
        if key_l in {"planet", "dispositor", "lord", "pada_lord"} and isinstance(raw, str):
            out[key] = label_planet(raw, language)
            continue
        if key_l in {"tara_name", "tara"} and isinstance(raw, str):
            out[key] = label_tara(raw, language)
            continue
        if key_l in {"tara_quality", "tara_effect"} and isinstance(raw, str):
            out[key] = label_tara_quality(raw, language)
            continue
        if key_l == "gana" and isinstance(raw, str):
            out[key] = label_gana(raw, language)
            continue
        if key_l == "nadi" and isinstance(raw, str):
            out[key] = label_nadi(raw, language)
            continue
        if key_l == "yoni" and isinstance(raw, str):
            out[key] = label_yoni(raw, language)
            continue
        if key_l == "guna" and isinstance(raw, str):
            out[key] = label_guna(raw, language)
            continue
        if key_l in {"element", "pada_element"} and isinstance(raw, str):
            out[key] = label_element(raw, language)
            continue
        if key_l in {"deity", "nakshatra_deity"} and isinstance(raw, str):
            out[key] = label_deity(raw, language)
            continue
        if key_l in {"quality", "nakshatra_quality"} and isinstance(raw, str):
            out[key] = label_nakshatra_quality(raw, language)
            continue
        if key_l == "strength" and isinstance(raw, str):
            out[key] = label_strength(raw, language)
            continue
        if key_l == "gemstone" and isinstance(raw, str):
            out[key] = label_gemstone(raw, language)
            continue
        if key_l in {"functional_benefics", "priority_order", "planets"} and isinstance(raw, list):
            out[key] = [
                label_planet(p, language) if isinstance(p, str) else localize_fact_names(p, language)
                for p in raw
            ]
            continue
        if key_l == "special_roles" and isinstance(raw, str):
            out[key] = label_special_roles(raw, language)
            continue
        if key_l == "aspects_received" and isinstance(raw, str):
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            out[key] = ", ".join(label_planet(p, language) for p in parts) if parts else raw
            continue
        if key_l == "dignity":
            out[key] = label_dignity(raw, language)
            continue
        if key_l == "functional_nature":
            out[key] = label_functional(raw, language)
            continue
        if key_l in {"natural_friendship", "temporal_friendship", "compound_friendship"}:
            out[key] = label_friendship(raw, language)
            continue
        if key_l == "combustion_status":
            out[key] = label_combust(raw, language)
            continue
        if key_l == "avastha":
            out[key] = label_avastha(raw, language)
            continue
        out[key] = localize_fact_names(raw, language)
    return out


def _nested_name(value: Any) -> str:
    """Extract display name from calculator nested objects or plain strings."""
    if value is None:
        return ""
    if isinstance(value, dict):
        name = value.get("name") or value.get("tithi_name") or value.get("nakshatra_name")
        paksha = value.get("paksha")
        name_text = str(name or "").strip()
        if name_text and paksha and str(paksha).strip() and name_text not in {"Purnima", "Amavasya", "पूर्णिमा", "अमावस्या"}:
            return f"{str(paksha).strip()} {name_text}"
        return name_text or str(value.get("number") or "")
    return str(value).strip()


def label_tithi(value: Any, language: Any) -> str:
    raw = _nested_name(value)
    if not raw:
        return ""
    if not is_hindi(language):
        return raw
    parts = raw.split()
    if len(parts) == 2 and parts[0] in PAKSHA_HI:
        paksha = PAKSHA_HI[parts[0]]
        tithi = _lookup(TITHI_HI, parts[1]) or parts[1]
        return f"{paksha} {tithi}"
    return _lookup(TITHI_HI, raw) or " ".join(_lookup(TITHI_HI, p) or _lookup(PAKSHA_HI, p) or p for p in parts)


def label_vara(value: Any, language: Any) -> str:
    raw = _nested_name(value)
    if not raw:
        return ""
    if is_hindi(language):
        return _lookup(VARA_HI, raw) or raw
    return raw


def label_yoga(value: Any, language: Any) -> str:
    raw = _nested_name(value)
    if not raw:
        return ""
    if is_hindi(language):
        return _lookup(YOGA_HI, raw) or raw
    return raw


def label_karana(value: Any, language: Any) -> str:
    raw = _nested_name(value)
    if not raw:
        return ""
    if is_hindi(language):
        return _lookup(KARANA_HI, raw) or raw
    return raw


def format_clock(value: Any) -> str:
    """Format ISO datetime / time-like values as HH:MM for panchang display."""
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    # 1990-05-15T06:12:34 or 06:12:34
    if "T" in text:
        text = text.split("T", 1)[1]
    text = text.replace("Z", "")
    if "+" in text[1:]:
        text = text.split("+", 1)[0]
    parts = text.split(":")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    return text
