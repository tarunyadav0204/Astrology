const VERDICT_LABEL_KEYS = {
  'Well supported': 'wellSupported',
  'Under stress': 'underStress',
  'Supported but pressured': 'supportedButPressured',
  'Quietly supported': 'quietlySupported',
  'Sensitive area': 'sensitiveArea',
  'Balanced but not strongly marked': 'balanced',
  'Actively unfolding now': 'activelyUnfolding',
  'Lightly activated now': 'lightlyActivated',
  'Natal pattern, not especially triggered now': 'natalPattern',
};

const DIGNITY_KEYS = {
  'own sign': 'ownSign',
  exalted: 'exalted',
  moolatrikona: 'moolatrikona',
  favorable: 'favorable',
  debilitated: 'debilitated',
  unfavorable: 'unfavorable',
  neutral: 'neutral',
};

const RELATION_KEYS = {
  'strong temporal support with the sign owner': 'greatFriend',
  'friendly support with the sign owner': 'friend',
  'neutral support with the sign owner': 'neutral',
  'friction with the sign owner': 'enemy',
  'strong friction with the sign owner': 'greatEnemy',
};

const ROLE_KEYS = {
  'Yogi lord': 'yogiLord',
  'Avayogi lord': 'avayogiLord',
  'Dagdha lord': 'dagdhaLord',
};

const PLANET_RE = 'Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|Gulika|Mandi';
const ORDINAL_RE = '\\d+(?:st|nd|rd|th)';

function tp(t, planet) {
  return t(`home.planet_names.${planet}`, planet);
}

function translateDignity(t, dignity) {
  const key = DIGNITY_KEYS[dignity];
  return key ? t(`chartScreen.houseDrawer.dignity.${key}`, dignity) : dignity;
}

function translateRelation(t, relation) {
  const key = RELATION_KEYS[relation];
  return key ? t(`chartScreen.houseDrawer.relations.${key}`, relation) : relation;
}

function translateOrdinalList(t, list) {
  return list
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean)
    .map((ord) => {
      const n = parseInt(ord, 10);
      return Number.isFinite(n) ? t('chartScreen.houseDrawer.houseOrdinal', { n, defaultValue: `${n}` }) : ord;
    })
    .join(', ');
}

export function translateHouseVerdictLabel(t, label) {
  if (!label) return '';
  const key = VERDICT_LABEL_KEYS[label];
  return key ? t(`chartScreen.houseDrawer.verdicts.${key}`, label) : label;
}

export function translateOccupantRole(t, role) {
  if (!role) return '';
  const key = ROLE_KEYS[role];
  return key ? t(`chartScreen.houseDrawer.roles.${key}`, role) : role;
}

export function translateAshtakClassification(t, classification) {
  const value = String(classification || 'moderate').toLowerCase();
  if (value === 'strong') return t('chartScreen.houseDrawer.strong', 'strong');
  if (value === 'weak') return t('chartScreen.houseDrawer.weak', 'weak');
  return t('chartScreen.houseDrawer.moderate', 'moderate');
}

export function translateHouseInterpretation(t, insight, houseNum) {
  if (!insight) return '';
  const chartName = t(`chartScreen.chartNames.${insight.chart_id}`, insight.chart_name || insight.chart_id);
  const area = t(`houses.${houseNum}.area`, t(`houses.${houseNum}.title`, `House ${houseNum}`));
  const conditionLabel = translateHouseVerdictLabel(t, insight.verdict?.label);
  const timingLabel = translateHouseVerdictLabel(t, insight.timing_verdict?.label);
  const conditionKey = insight.verdict?.key;
  const conditionExact = insight.verdict?.label;

  if (conditionKey === 'strong') {
    return t('chartScreen.houseDrawer.interpretation.strong', {
      chart: chartName,
      house: houseNum,
      condition: conditionLabel.toLowerCase(),
      area,
      timing: timingLabel.toLowerCase(),
      defaultValue:
        'In {{chart}}, the {{house}} house is coming through as {{condition}}. {{area}} has cleaner support here, and the current timing is {{timing}}.',
    });
  }
  if (conditionExact === 'Supported but pressured') {
    return t('chartScreen.houseDrawer.interpretation.pressured', {
      chart: chartName,
      house: houseNum,
      area,
      defaultValue:
        'In {{chart}}, the {{house}} house shows both support and pressure. {{area}} can deliver, but results are shaped by effort, maturity, and timing.',
    });
  }
  if (conditionExact === 'Under stress') {
    return t('chartScreen.houseDrawer.interpretation.stress', {
      chart: chartName,
      house: houseNum,
      area,
      defaultValue:
        'In {{chart}}, the {{house}} house is under noticeable pressure. {{area}} may require patience, better choices, and stronger timing support.',
    });
  }
  return t('chartScreen.houseDrawer.interpretation.balanced', {
    chart: chartName,
    house: houseNum,
    area,
    defaultValue:
      'In {{chart}}, the {{house}} house is not weak, but it is not overemphasized either. {{area}} depends more on the lord, aspects, and timing than on a single dominant signature.',
  });
}

export function translateHouseInsightFactor(t, label) {
  if (!label) return '';
  const text = String(label);

  let m;

  m = text.match(new RegExp(`^(${PLANET_RE}) is (.+)\\.$`));
  if (m && DIGNITY_KEYS[m[2]]) {
    return t('chartScreen.houseDrawer.factors.planetIsDignity', {
      planet: tp(t, m[1]),
      dignity: translateDignity(t, m[2]),
      defaultValue: '{{planet}} is {{dignity}}.',
    });
  }

  m = text.match(new RegExp(`^(${PLANET_RE}), the house lord, sits in a (kendra|trikona|dusthana)\\.$`));
  if (m) {
    return t(`chartScreen.houseDrawer.factors.lordSitsIn.${m[2]}`, {
      planet: tp(t, m[1]),
      defaultValue: text,
    });
  }

  m = text.match(new RegExp(`^(${PLANET_RE}) gains strength through an upachaya placement\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.upachaya', {
      planet: tp(t, m[1]),
      defaultValue: text,
    });
  }

  m = text.match(new RegExp(`^(${PLANET_RE}) is the Yogi lord\\.?$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.isYogiLord', { planet: tp(t, m[1]), defaultValue: text });
  }
  m = text.match(new RegExp(`^(${PLANET_RE}) is the Avayogi lord\\.?$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.isAvayogiLord', { planet: tp(t, m[1]), defaultValue: text });
  }
  m = text.match(new RegExp(`^(${PLANET_RE}) is functioning as a Dagdha lord\\.?$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.isDagdhaLord', { planet: tp(t, m[1]), defaultValue: text });
  }
  m = text.match(new RegExp(`^(${PLANET_RE}) is the Yogi lord for this chart\\.?$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.isYogiLordChart', { planet: tp(t, m[1]), defaultValue: text });
  }
  m = text.match(new RegExp(`^(${PLANET_RE}) is the Avayogi lord for this chart\\.?$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.isAvayogiLordChart', { planet: tp(t, m[1]), defaultValue: text });
  }
  m = text.match(new RegExp(`^(${PLANET_RE}) is the Dagdha lord for this chart\\.?$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.isDagdhaLordChart', { planet: tp(t, m[1]), defaultValue: text });
  }

  m = text.match(
    new RegExp(
      `^(${PLANET_RE}), the house lord, is retrograde and behaves less straightforwardly here\\.$`,
    ),
  );
  if (m) {
    return t('chartScreen.houseDrawer.factors.lordRetroHard', { planet: tp(t, m[1]), defaultValue: text });
  }
  m = text.match(
    new RegExp(
      `^(${PLANET_RE}), the house lord, is retrograde, making this house more reflective and internally active\\.$`,
    ),
  );
  if (m) {
    return t('chartScreen.houseDrawer.factors.lordRetroSoft', { planet: tp(t, m[1]), defaultValue: text });
  }

  m = text.match(new RegExp(`^(${PLANET_RE}) is in Gandanta\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.inGandanta', { planet: tp(t, m[1]), defaultValue: text });
  }

  m = text.match(new RegExp(`^(${PLANET_RE}) has (.+)\\.$`));
  if (m && RELATION_KEYS[m[2]]) {
    return t('chartScreen.houseDrawer.factors.hasRelation', {
      planet: tp(t, m[1]),
      relation: translateRelation(t, m[2]),
      defaultValue: text,
    });
  }

  if (text === 'This house falls on the Yogi sign axis.') {
    return t('chartScreen.houseDrawer.factors.yogiAxis', 'This house falls on the Yogi sign axis.');
  }
  if (text === 'This house falls on the Avayogi sign axis.') {
    return t('chartScreen.houseDrawer.factors.avayogiAxis', 'This house falls on the Avayogi sign axis.');
  }
  if (text === 'This house falls on the Dagdha sign axis.') {
    return t('chartScreen.houseDrawer.factors.dagdhaAxis', 'This house falls on the Dagdha sign axis.');
  }
  if (text === 'This is marked as a yogi house in the chart.') {
    return t('chartScreen.houseDrawer.factors.yogiHouse', 'This is marked as a yogi house in the chart.');
  }
  if (text === 'This house falls in the badhaka axis for the ascendant.') {
    return t('chartScreen.houseDrawer.factors.badhakaAxis', 'This house falls in the badhaka axis for the ascendant.');
  }
  if (text === 'The house cusp itself falls in Gandanta.') {
    return t('chartScreen.houseDrawer.factors.cuspGandanta', 'The house cusp itself falls in Gandanta.');
  }
  if (text === 'Mangal Dosha is impacting this house axis.') {
    return t('chartScreen.houseDrawer.factors.mangalDosha', 'Mangal Dosha is impacting this house axis.');
  }
  if (text === 'Kaal Sarp Dosha adds pressure to the chart pattern here.') {
    return t('chartScreen.houseDrawer.factors.kaalSarp', 'Kaal Sarp Dosha adds pressure to the chart pattern here.');
  }
  if (text === 'Pitra Dosha is directly affecting ninth-house themes.') {
    return t('chartScreen.houseDrawer.factors.pitraDosha', 'Pitra Dosha is directly affecting ninth-house themes.');
  }
  if (text === 'Overall house assessment comes through as Uttama.') {
    return t('chartScreen.houseDrawer.factors.uttama', 'Overall house assessment comes through as Uttama.');
  }
  if (text === 'Overall house assessment comes through as Adhama.') {
    return t('chartScreen.houseDrawer.factors.adhama', 'Overall house assessment comes through as Adhama.');
  }

  m = text.match(new RegExp(`^Gandanta affects resident planets? (.+)\\.$`));
  if (m) {
    const planets = m[1]
      .split(',')
      .map((p) => tp(t, p.trim()))
      .join(', ');
    return t('chartScreen.houseDrawer.factors.gandantaResidents', { planets, defaultValue: text });
  }

  m = text.match(new RegExp(`^The house lord (${PLANET_RE}) is in Gandanta\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.lordGandanta', { planet: tp(t, m[1]), defaultValue: text });
  }

  m = text.match(/^Overall Gandanta impact on this house is (high|medium)\.$/i);
  if (m) {
    return t('chartScreen.houseDrawer.factors.gandantaImpact', {
      level: t(`chartScreen.houseDrawer.${m[1].toLowerCase() === 'high' ? 'high' : 'medium'}`, m[1]),
      defaultValue: text,
    });
  }

  m = text.match(new RegExp(`^(${PLANET_RE}) occupies this house as the (Yogi|Avayogi|Dagdha) lord\\.$`));
  if (m) {
    const roleKey = { Yogi: 'yogi', Avayogi: 'avayogi', Dagdha: 'dagdha' }[m[2]];
    return t(`chartScreen.houseDrawer.factors.occupiesAs.${roleKey}`, {
      planet: tp(t, m[1]),
      defaultValue: text,
    });
  }

  m = text.match(
    new RegExp(
      `^(${PLANET_RE}) is placed in a sign ruled by a (.+)\\.$`,
    ),
  );
  if (m && RELATION_KEYS[m[2]]) {
    return t('chartScreen.houseDrawer.factors.placedRuledBy', {
      planet: tp(t, m[1]),
      relation: translateRelation(t, m[2]),
      defaultValue: text,
    });
  }

  m = text.match(
    new RegExp(`^(${PLANET_RE}) is in a sign ruled by its natural (friend|enemy) (${PLANET_RE})\\.$`),
  );
  if (m) {
    return t(`chartScreen.houseDrawer.factors.naturalSign.${m[2]}`, {
      planet: tp(t, m[1]),
      other: tp(t, m[3]),
      defaultValue: text,
    });
  }

  m = text.match(new RegExp(`^(${PLANET_RE}) is placed in its own nakshatra\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.ownNakshatra', { planet: tp(t, m[1]), defaultValue: text });
  }

  m = text.match(
    new RegExp(`^(${PLANET_RE}) is in a nakshatra ruled by its natural (friend|enemy) (${PLANET_RE})\\.$`),
  );
  if (m) {
    return t(`chartScreen.houseDrawer.factors.naturalNakshatra.${m[2]}`, {
      planet: tp(t, m[1]),
      other: tp(t, m[3]),
      defaultValue: text,
    });
  }

  m = text.match(new RegExp(`^(${PLANET_RE}) occupies this house in (.+) dignity\\.$`));
  if (m && DIGNITY_KEYS[m[2]]) {
    return t('chartScreen.houseDrawer.factors.occupiesDignity', {
      planet: tp(t, m[1]),
      dignity: translateDignity(t, m[2]),
      defaultValue: text,
    });
  }

  m = text.match(new RegExp(`^(${PLANET_RE}) occupies this house and supports its matters\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.occupiesSupports', { planet: tp(t, m[1]), defaultValue: text });
  }
  m = text.match(new RegExp(`^(${PLANET_RE}) occupies this house and adds pressure to its matters\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.occupiesPressure', { planet: tp(t, m[1]), defaultValue: text });
  }

  m = text.match(
    new RegExp(`^(${PLANET_RE}) is retrograde here, making its results more irregular or delayed\\.$`),
  );
  if (m) {
    return t('chartScreen.houseDrawer.factors.retroHard', { planet: tp(t, m[1]), defaultValue: text });
  }
  m = text.match(
    new RegExp(
      `^(${PLANET_RE}) is retrograde here, adding inward strength and reworking to this house\\.$`,
    ),
  );
  if (m) {
    return t('chartScreen.houseDrawer.factors.retroSoft', { planet: tp(t, m[1]), defaultValue: text });
  }

  m = text.match(new RegExp(`^(${PLANET_RE}) aspects this house with pressure\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.aspectPressure', { planet: tp(t, m[1]), defaultValue: text });
  }
  m = text.match(new RegExp(`^(${PLANET_RE}) aspects this house\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.aspects', { planet: tp(t, m[1]), defaultValue: text });
  }
  m = text.match(new RegExp(`^(${PLANET_RE}) aspects this house as the Yogi lord\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.aspectYogi', { planet: tp(t, m[1]), defaultValue: text });
  }
  m = text.match(
    new RegExp(
      `^(${PLANET_RE}) is retrograde while aspecting this house, so its influence is more inward and reconsidering than direct\\.$`,
    ),
  );
  if (m) {
    return t('chartScreen.houseDrawer.factors.aspectRetro', { planet: tp(t, m[1]), defaultValue: text });
  }

  m = text.match(
    new RegExp(
      `^(${PLANET_RE}) aspects this house from the (${ORDINAL_RE}) while ruling (.+)\\.$`,
    ),
  );
  if (m) {
    return t('chartScreen.houseDrawer.factors.aspectFromRuling', {
      planet: tp(t, m[1]),
      from: translateOrdinalList(t, m[2]),
      ruling: translateOrdinalList(t, m[3]),
      defaultValue: text,
    });
  }

  m = text.match(
    new RegExp(
      `^(${PLANET_RE}) aspects this house while also carrying (.+) lordship\\.$`,
    ),
  );
  if (m) {
    return t('chartScreen.houseDrawer.factors.aspectCarrying', {
      planet: tp(t, m[1]),
      houses: translateOrdinalList(t, m[2]),
      defaultValue: text,
    });
  }

  m = text.match(/^Sarvashtakavarga gives strong support with (\d+) SAV points\.$/);
  if (m) {
    return t('chartScreen.houseDrawer.factors.savStrong', { points: m[1], defaultValue: text });
  }
  m = text.match(/^Sarvashtakavarga is weak here with (\d+) SAV points\.$/);
  if (m) {
    return t('chartScreen.houseDrawer.factors.savWeak', { points: m[1], defaultValue: text });
  }

  m = text.match(new RegExp(`^(${PLANET_RE})'s Bhinnashtakavarga is supportive here with (\\d+) points\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.bavSupportive', {
      planet: tp(t, m[1]),
      points: m[2],
      defaultValue: text,
    });
  }
  m = text.match(new RegExp(`^(${PLANET_RE})'s Bhinnashtakavarga is thin here with (\\d+) points\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.bavThin', {
      planet: tp(t, m[1]),
      points: m[2],
      defaultValue: text,
    });
  }
  m = text.match(new RegExp(`^This is one of the strongest BAV houses for (${PLANET_RE})\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.bavStrongest', { planet: tp(t, m[1]), defaultValue: text });
  }
  m = text.match(new RegExp(`^This is one of the weakest BAV houses for (${PLANET_RE})\\.$`));
  if (m) {
    return t('chartScreen.houseDrawer.factors.bavWeakest', { planet: tp(t, m[1]), defaultValue: text });
  }

  m = text.match(/^(.+) (?:is also touching|also touches) this house\.$/);
  if (m) {
    return t('chartScreen.houseDrawer.factors.yogaTouches', { yoga: m[1], defaultValue: text });
  }

  m = text.match(
    new RegExp(
      `^(Mahadasha|Antardasha|Pratyantardasha) is running through (${PLANET_RE}), the house lord\\.$`,
    ),
  );
  if (m) {
    return t('chartScreen.houseDrawer.factors.dashaLord', {
      dasha: t(`chartScreen.houseDrawer.dashaNames.${m[1].toLowerCase()}`, m[1]),
      planet: tp(t, m[2]),
      defaultValue: text,
    });
  }
  m = text.match(
    new RegExp(
      `^(Mahadasha|Antardasha|Pratyantardasha) is running through (${PLANET_RE}), an occupant of this house\\.$`,
    ),
  );
  if (m) {
    return t('chartScreen.houseDrawer.factors.dashaOccupant', {
      dasha: t(`chartScreen.houseDrawer.dashaNames.${m[1].toLowerCase()}`, m[1]),
      planet: tp(t, m[2]),
      defaultValue: text,
    });
  }
  m = text.match(
    new RegExp(
      `^(Mahadasha|Antardasha|Pratyantardasha) is running through (${PLANET_RE}), which aspects this house\\.$`,
    ),
  );
  if (m) {
    return t('chartScreen.houseDrawer.factors.dashaAspect', {
      dasha: t(`chartScreen.houseDrawer.dashaNames.${m[1].toLowerCase()}`, m[1]),
      planet: tp(t, m[2]),
      defaultValue: text,
    });
  }

  m = text.match(/^Current transits through this sign include (.+)\.$/);
  if (m) {
    const planets = m[1]
      .split(',')
      .map((p) => tp(t, p.trim()))
      .join(', ');
    return t('chartScreen.houseDrawer.factors.transitsInclude', { planets, defaultValue: text });
  }

  // Last resort: swap known planet tokens inside otherwise English text.
  return text.replace(new RegExp(`\\b(${PLANET_RE})\\b`, 'g'), (planet) => tp(t, planet));
}
