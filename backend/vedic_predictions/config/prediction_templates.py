# Transit aspect prediction templates based on classical Vedic texts

PLANET_ASPECT_TEMPLATES = {
    'Mars': {
        '4th_house': {
            'theme': 'Direct Mars energy affecting home and foundations',
            'positive': 'Mars brings courage, determination, property gains, mother\'s support',
            'negative': 'Mars causes conflicts at home, property disputes, mother\'s health issues',
            'neutral': 'Mars increases activity in domestic matters, property decisions'
        },
        '7th_house': {
            'theme': 'Confrontational Mars energy in partnerships',
            'positive': 'Mars brings victory over enemies, business expansion, spouse support',
            'negative': 'Mars triggers marital conflicts, business disputes, legal battles',
            'neutral': 'Mars increases activity in partnerships, competitive situations'
        },
        '8th_house': {
            'theme': 'Penetrating Mars energy creating deep transformation',
            'positive': 'Mars brings breakthrough courage, reveals hidden strength, helps overcome obstacles',
            'negative': 'Mars triggers aggressive confrontations, impulsive actions, energy conflicts',
            'neutral': 'Mars creates intense focus, penetrating insights, transformative drive'
        }
    },
    'Jupiter': {
        '5th_house': {
            'theme': 'Expansive Jupiter wisdom affecting creativity and children',
            'positive': 'Jupiter brings children\'s progress, creative success, spiritual growth',
            'negative': 'Jupiter causes over-optimism in speculation, children\'s issues',
            'neutral': 'Jupiter encourages educational pursuits, creative projects, spiritual practices'
        },
        '7th_house': {
            'theme': 'Beneficial Jupiter energy in partnerships',
            'positive': 'Jupiter brings marriage prospects, business success, harmonious relationships',
            'negative': 'Jupiter creates over-expectations from spouse, business over-expansion',
            'neutral': 'Jupiter provides partnership opportunities, relationship guidance'
        },
        '9th_house': {
            'theme': 'Jupiter\'s higher wisdom and spiritual guidance',
            'positive': 'Jupiter brings spiritual advancement, father\'s support, higher learning',
            'negative': 'Jupiter triggers religious conflicts, over-philosophizing',
            'neutral': 'Jupiter inspires spiritual practices, higher education, dharmic activities'
        }
    },
    'Saturn': {
        '3rd_house': {
            'theme': 'Saturn\'s disciplined effort affecting communication and skills',
            'positive': 'Saturn brings skill development, sibling support, methodical progress',
            'negative': 'Saturn causes communication delays, sibling issues, slow progress',
            'neutral': 'Saturn encourages structured learning, disciplined practice, careful planning'
        },
        '7th_house': {
            'theme': 'Saturn\'s serious energy in partnerships',
            'positive': 'Saturn brings stable marriage, long-term partnerships, mature relationships',
            'negative': 'Saturn causes marital delays, partnership restrictions, relationship tests',
            'neutral': 'Saturn demands serious relationship decisions, partnership evaluations'
        },
        '10th_house': {
            'theme': 'Saturn\'s disciplinary influence on career and authority',
            'positive': 'Saturn brings career stability, authority positions, recognition',
            'negative': 'Saturn causes career delays, authority conflicts, reputation challenges',
            'neutral': 'Saturn requires career restructuring, professional responsibilities'
        }
    },
    'Mercury': {
        '7th_house': {
            'theme': 'Mercury\'s intellectual energy in partnerships and communication',
            'positive': 'Mercury brings clear communication, business intelligence, networking success',
            'negative': 'Mercury causes miscommunication, overthinking in relationships, contract disputes',
            'neutral': 'Mercury enhances analytical thinking, business discussions, partnership planning'
        }
    },
    'Venus': {
        '7th_house': {
            'theme': 'Venus\'s harmonious energy in relationships and partnerships',
            'positive': 'Venus brings romantic opportunities, artistic success, harmonious relationships',
            'negative': 'Venus causes over-indulgence, relationship complications, financial overspending',
            'neutral': 'Venus enhances creativity, social connections, aesthetic appreciation'
        }
    },
    'Sun': {
        '7th_house': {
            'theme': 'Sun\'s authoritative energy affecting partnerships and public image',
            'positive': 'Sun brings leadership recognition, spouse support, public success',
            'negative': 'Sun causes ego conflicts in relationships, authority disputes, partnership dominance',
            'neutral': 'Sun enhances leadership qualities, public visibility, partnership responsibilities'
        }
    },
    'Moon': {
        '7th_house': {
            'theme': 'Moon\'s emotional energy affecting relationships and public connections',
            'positive': 'Moon brings emotional fulfillment, public popularity, nurturing relationships',
            'negative': 'Moon causes emotional instability, mood swings in partnerships, public criticism',
            'neutral': 'Moon enhances emotional intelligence, intuitive connections, caring relationships'
        }
    },
    'Rahu': {
        '5th_house': {
            'theme': 'Rahu\'s amplifying energy affecting creativity and intelligence',
            'positive': 'Rahu brings innovative thinking, speculative gains, foreign connections in creativity',
            'negative': 'Rahu causes confusion in decision-making, risky speculation, children\'s issues',
            'neutral': 'Rahu enhances unconventional creativity, research abilities, technological interests'
        },
        '7th_house': {
            'theme': 'Rahu\'s intensifying energy in partnerships and public life',
            'positive': 'Rahu brings foreign partnerships, unconventional success, mass appeal',
            'negative': 'Rahu causes deceptive relationships, partnership scandals, public controversies',
            'neutral': 'Rahu enhances ambition in partnerships, desire for recognition, social climbing'
        },
        '9th_house': {
            'theme': 'Rahu\'s transformative energy affecting higher wisdom and fortune',
            'positive': 'Rahu brings foreign spiritual teachers, unconventional learning, sudden fortune',
            'negative': 'Rahu causes religious confusion, false gurus, ethical conflicts',
            'neutral': 'Rahu enhances interest in foreign philosophies, alternative spirituality, research'
        }
    },
    'Ketu': {
        '5th_house': {
            'theme': 'Ketu\'s detaching energy affecting creativity and intelligence',
            'positive': 'Ketu brings spiritual creativity, intuitive intelligence, past-life skills',
            'negative': 'Ketu causes creative blocks, confusion in studies, children\'s detachment',
            'neutral': 'Ketu enhances spiritual practices, mystical interests, inner wisdom'
        },
        '7th_house': {
            'theme': 'Ketu\'s separating energy in partnerships and public life',
            'positive': 'Ketu brings spiritual partnerships, detachment from ego, inner fulfillment',
            'negative': 'Ketu causes partnership separations, public withdrawal, relationship dissatisfaction',
            'neutral': 'Ketu enhances spiritual seeking, desire for meaningful connections, inner reflection'
        },
        '9th_house': {
            'theme': 'Ketu\'s enlightening energy affecting higher wisdom and spirituality',
            'positive': 'Ketu brings spiritual enlightenment, mystical experiences, divine grace',
            'negative': 'Ketu causes spiritual confusion, rejection of traditions, father\'s detachment',
            'neutral': 'Ketu enhances meditation, spiritual practices, philosophical detachment'
        }
    }
}

DASHA_AMPLIFIERS = {
    'mahadasha': 3.0,
    'antardasha': 2.0,
    'pratyantardasha': 1.5,
    'sookshmadasha': 1.2,
    'pranadasha': 1.1
}

TIMING_MODIFIERS = {
    'exact': 1.0,
    'approaching': 0.8,
    'separating': 0.6,
    'peak': 1.2
}