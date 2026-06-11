import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import CreditsModal from '../Credits/CreditsModal';
import SEOHead from '../SEO/SEOHead';
import UniversalAIInsights from '../Shared/UniversalAIInsights';
import { useAstrology } from '../../context/AstrologyContext';
import { generatePageSEO } from '../../config/seo.config';
import { WealthReportPDF } from '../PDF/WealthReportPDF';
import { HealthReportPDF } from '../PDF/HealthReportPDF';
import { MarriageReportPDF } from '../PDF/MarriageReportPDF';
import { EducationReportPDF } from '../PDF/EducationReportPDF';
import './AnalysisDetailPage.css';

const PAGE_META = {
  career: {
    seoKey: 'careerGuidance',
    path: '/career-guidance',
    headline: 'Career Analysis by Date of Birth',
    kicker: 'Vedic career astrology',
    blurb:
      'Find your suitable profession, job or business direction, D10 career strength, Amatyakaraka work function, and career timing from your birth chart.',
    icon: '💼',
    pdf: null
  },
  health: {
    seoKey: 'healthAnalysis',
    path: '/health-analysis',
    headline: 'Health Analysis by Date of Birth',
    kicker: 'Vedic health astrology',
    blurb:
      'Understand constitution, vitality, sensitive body systems, D30 Trimsamsa signals, stress and sleep patterns, health timing windows, and preventive wellness guidance from your birth chart.',
    icon: '🏥',
    pdf: HealthReportPDF
  },
  wealth: {
    seoKey: 'wealthAnalysis',
    path: '/wealth-analysis',
    headline: 'Wealth Analysis by Date of Birth',
    kicker: 'Vedic wealth astrology',
    blurb:
      'Understand wealth promise, income sources, Dhana yogas, cashflow, savings, assets, risk patterns, career-to-money links, and wealth timing from your birth chart.',
    icon: '💰',
    pdf: WealthReportPDF
  },
  marriage: {
    seoKey: 'marriageAnalysis',
    path: '/marriage-analysis',
    headline: 'Marriage Analysis by Date of Birth',
    kicker: 'Vedic marriage astrology',
    blurb:
      'Understand marriage promise, spouse nature, D9 Navamsa maturity, Darakaraka, Upapada Lagna, relationship timing, harmony, and friction factors from your birth chart.',
    icon: '💍',
    pdf: MarriageReportPDF
  },
  progeny: {
    seoKey: 'progenyAnalysis',
    path: '/progeny-analysis',
    headline: 'Progeny Analysis by Date of Birth',
    kicker: 'Vedic progeny astrology',
    blurb:
      'Understand children promise, D1 5th house support, D7 Saptamsa strength, Jupiter, fertility sphuta, family expansion timing, obstacles, remedies, and parenting guidance from your birth chart.',
    icon: '👶',
    pdf: null
  },
  education: {
    seoKey: 'educationAnalysis',
    path: '/education',
    headline: 'Education Analysis by Date of Birth',
    kicker: 'Vedic education astrology',
    blurb:
      'Discover learning potential, subject fit, academic strengths, D24 education indicators, exam support, higher study promise, and study guidance from your birth chart.',
    icon: '🎓',
    pdf: EducationReportPDF
  }
};

const careerFaqItems = [
  {
    question: 'What is career analysis by date of birth?',
    answer:
      'Career analysis by date of birth studies your birth chart to understand professional direction, suitable industries, job or business fit, timing for growth, and the kind of work that matches your natural strengths.'
  },
  {
    question: 'Which birth details are needed for career astrology?',
    answer:
      'You need your birth date, accurate birth time, and birth place. Exact time and place help calculate the Lagna, 10th house, D10 Dashamsha chart, Amatyakaraka, nakshatra, dasha, and transit timing.'
  },
  {
    question: 'What does the D10 Dashamsha chart show?',
    answer:
      'The D10 or Dashamsha chart is used in Vedic astrology to study profession, authority, career fruits, reputation, and how your work develops after effort. AstroRoshni uses D10 with the main birth chart instead of reading it alone.'
  },
  {
    question: 'Can astrology tell whether job or business is better?',
    answer:
      'It can show tendencies. The report compares employment, business, freelancing, leadership, public dealing, networks, and daily work patterns through the 6th, 7th, 10th, and 11th houses with D10 confirmation.'
  },
  {
    question: 'What is Amatyakaraka in career analysis?',
    answer:
      'Amatyakaraka is a Jaimini career significator that helps describe your work function and execution style. It is useful for understanding whether your chart leans toward analysis, management, communication, advising, research, operations, or technical work.'
  },
  {
    question: 'Can this report suggest suitable professions?',
    answer:
      'Yes. The career report ranks likely field and role clusters using the 10th house, 10th lord, D10, Amatyakaraka, nakshatra career patterns, planetary strength, and timing support.'
  },
  {
    question: 'Does the report show career timing?',
    answer:
      'Yes. It looks at current dasha and transit support to identify career growth, job change, promotion, business, and breakthrough windows as supportive, mixed, or weak periods.'
  },
  {
    question: 'Can it help if I am confused between multiple careers?',
    answer:
      'Yes. The report separates aptitude, work function, income model, ecosystem, visibility, and risk so you can compare options more clearly instead of choosing from a generic profession list.'
  },
  {
    question: 'Is this career guidance guaranteed?',
    answer:
      'No astrology report should be treated as a guarantee. Use it as structured guidance alongside your skills, education, market conditions, financial needs, and practical career counseling.'
  },
  {
    question: 'Is my birth data private?',
    answer:
      'Your birth details are used to calculate and save your personal career report. They are not shown publicly on the career guidance page.'
  }
];

const careerMethodCards = [
  ['10th House and Lord', 'Profession, authority, reputation, work direction, and how career effort becomes visible in the outer world.'],
  ['D10 Dashamsha', 'The divisional career chart for professional fruits, status, responsibility, and long-term growth after sustained work.'],
  ['Amatyakaraka', 'Jaimini career significator for your execution style, work function, and professional calling.'],
  ['Nakshatra and Grahas', 'Career nature, skill themes, industry signatures, modern role fit, and repeated work patterns.'],
  ['Job vs Business', 'Employment, entrepreneurship, freelancing, leadership, public dealing, and income model indications.'],
  ['Dasha and Transits', 'Timing climate for job change, promotion, growth, business launch, pressure, or course correction.']
];

const careerReportItems = [
  'Top career direction and professional purpose',
  'Suitable professions, industries, and role clusters',
  'Day-to-day work function and strongest skills',
  'Job, business, freelancing, or leadership fit',
  'Corporate, government, startup, foreign, or independent path',
  'Career instability, blocks, and wrong-path warnings',
  'Breakthrough or change windows from dasha and transit timing',
  '90-day and 12-month practical career action plan'
];

const marriageFaqItems = [
  {
    question: 'What is marriage analysis by date of birth?',
    answer:
      'Marriage analysis by date of birth studies your Vedic birth chart to understand relationship promise, spouse nature, marriage timing, compatibility patterns, harmony, delays, and long-term partnership stability.'
  },
  {
    question: 'Which birth details are needed for marriage astrology?',
    answer:
      'You need your birth date, accurate birth time, and birth place. These details help calculate the Lagna, 7th house, D9 Navamsa, Darakaraka, Upapada Lagna, dasha, and transit timing.'
  },
  {
    question: 'What does the 7th house show in marriage analysis?',
    answer:
      'The 7th house shows partnership, spouse tendencies, commitment, attraction, and how relationship themes appear in life. The 7th lord and planets influencing the 7th house refine the reading.'
  },
  {
    question: 'Why is D9 Navamsa important for marriage?',
    answer:
      'D9 or Navamsa shows how the relationship promise matures after commitment. It helps separate initial attraction from long-term adjustment, continuity, and the deeper fruit of marriage.'
  },
  {
    question: 'What are Darakaraka and Upapada Lagna?',
    answer:
      'Darakaraka describes partner nature in Jaimini astrology, while Upapada Lagna shows formal alliance, marriage manifestation, and continuity. AstroRoshni reads these along with D1 and D9.'
  },
  {
    question: 'Can this report show marriage timing?',
    answer:
      'Yes. The report checks dasha, transit, and Jaimini timing support to identify relationship milestones, commitment windows, marriage timing, repair phases, or partnership maturation periods.'
  },
  {
    question: 'Can married people use this report?',
    answer:
      'Yes. The report is useful for married, engaged, separated, divorced, or unmarried users. It adjusts the language toward current bond quality, continuity, repair, future phases, or timing as relevant.'
  },
  {
    question: 'Does this replace Kundli matching?',
    answer:
      'No. Marriage analysis studies one person’s relationship promise and timing, while Kundli matching compares two charts. They answer different questions and work best together.'
  },
  {
    question: 'Does the report identify delays or doshas?',
    answer:
      'Yes. It can highlight Saturn delay, Mars/Mangal factors, Rahu-Ketu irregularity, 6th/8th/12th pressure, cancellation factors, and practical guidance without fear-based language.'
  },
  {
    question: 'Is marriage prediction guaranteed?',
    answer:
      'No. Marriage astrology should be used as guidance, not a guarantee. Relationship outcomes also depend on choice, maturity, communication, family context, and practical effort.'
  }
];

const marriageMethodCards = [
  ['7th House and Lord', 'Marriage promise, partner tendencies, attraction, commitment style, and visible relationship patterns.'],
  ['D9 Navamsa', 'The maturity layer for long-term harmony, continuity, adjustment, and how marriage evolves after commitment.'],
  ['Darakaraka', 'Jaimini partner significator for spouse nature, relationship lessons, and the qualities drawn through partnership.'],
  ['Upapada and A7', 'Formal alliance, lived relationship manifestation, family visibility, continuity, and practical partnership experience.'],
  ['Doshas and Friction', 'Mars, Saturn, Rahu-Ketu, 6/8/12 pressure, delay, cancellation factors, and repair potential.'],
  ['Dasha and Transits', 'Relationship lifecycle timing for commitment, marriage, harmony tests, repair windows, or partnership maturation.']
];

const marriageReportItems = [
  'Marriage promise and relationship lifecycle summary',
  'Spouse or partner nature from 7th house, D9, and Darakaraka',
  'Love, arranged, family-supported, or unconventional relationship pattern',
  'D9 Navamsa maturity and post-commitment harmony',
  'Upapada Lagna, A7, and Jaimini relationship manifestation',
  'Doshas, delays, friction factors, and cancellation support',
  'Marriage timing, commitment windows, or current relationship phases',
  'Practical relationship guidance, remedies, and happiness key'
];

const healthFaqItems = [
  {
    question: 'What is health analysis by date of birth?',
    answer:
      'Health analysis by date of birth studies your Vedic birth chart for constitution, vitality, sensitive body systems, stress patterns, recovery tendency, and timing windows for extra caution. It is wellness guidance, not medical diagnosis.'
  },
  {
    question: 'Which birth details are needed for health astrology?',
    answer:
      'You need your birth date, accurate birth time, and birth place. These details help calculate the Lagna, 1st/6th/8th/12th houses, D9 resilience, D30 Trimsamsa, dasha, and transit timing.'
  },
  {
    question: 'What does D30 Trimsamsa show in health analysis?',
    answer:
      'D30 or Trimsamsa is used to refine vulnerabilities, misfortune patterns, and health-sensitive indications. AstroRoshni compares D1 visible patterns with D9 resilience and D30 confirmation.'
  },
  {
    question: 'Can astrology diagnose disease?',
    answer:
      'No. Astrology cannot diagnose disease, prescribe treatment, or replace doctors. The report only highlights astrological body-system themes and preventive monitoring areas.'
  },
  {
    question: 'What houses are important for health astrology?',
    answer:
      'The 1st house shows body and vitality, the 6th house shows illness and immunity battles, the 8th house shows chronic or hidden vulnerability, and the 12th house shows sleep, recovery, isolation, and hospitalization themes.'
  },
  {
    question: 'Does the report cover mental and emotional health?',
    answer:
      'Yes. It studies Moon, Mercury, the 4th house, 12th house, Rahu, Saturn, and current activations to discuss stress, sleep, emotional sensitivity, and mental wellness patterns in non-diagnostic language.'
  },
  {
    question: 'Can the report show health timing windows?',
    answer:
      'Yes. The report checks dasha and transit triggers to identify months or periods where extra caution, rest, routine, or professional checkups may be wise.'
  },
  {
    question: 'Does it suggest remedies or lifestyle guidance?',
    answer:
      'Yes. It gives non-medical wellness guidance tied to constitution, dosha balance, sleep, stress, digestion, movement, routine, and planetary support. It does not prescribe treatment.'
  },
  {
    question: 'Should I use this if I already have symptoms?',
    answer:
      'If you have symptoms, pain, mental distress, or medical concerns, consult a qualified healthcare professional. Use the astrology report only as reflective wellness guidance alongside medical care.'
  },
  {
    question: 'Is my health data private?',
    answer:
      'Your birth details are used to calculate and save your personal health report. They are not shown publicly on the health analysis page.'
  }
];

const healthMethodCards = [
  ['Lagna and Vitality', 'Body constitution, baseline stamina, vitality pattern, recovery tendency, and how your system responds to pressure.'],
  ['Health Houses', '1st, 6th, 8th, and 12th house signals for body, immunity, chronic themes, sleep, recovery, and caution areas.'],
  ['D30 Trimsamsa', 'A deeper divisional layer for vulnerability refinement, disease-pattern confirmation, and hidden stress indicators.'],
  ['Moon and Mercury', 'Mental wellness, emotional sensitivity, stress processing, sleep rhythm, and nervous-system style.'],
  ['Dosha and Elements', 'Constitutional tendencies, digestion/metabolism patterns, agni, movement, routine, and preventive lifestyle themes.'],
  ['Dasha and Transits', 'Health timing windows where extra caution, rest, professional checkups, or routine discipline may be helpful.']
];

const healthReportItems = [
  'Core constitution, vitality, and recovery pattern',
  'Primary health vulnerabilities by body system',
  'Body parts and systems needing special attention',
  'Mental, emotional, stress, and sleep indicators',
  'Digestion, metabolism, immunity, and recovery capacity',
  'Acute, chronic, sensitivity-based, or preventive pattern classification',
  'Health caution windows from dasha and transit timing',
  'D30 Trimsamsa insight and practical preventive wellness guidance'
];

const educationFaqItems = [
  {
    question: 'What is education analysis by date of birth?',
    answer:
      'Education analysis by date of birth studies your Vedic birth chart to understand learning potential, academic strengths, subject suitability, higher education promise, exam support, and study obstacles.'
  },
  {
    question: 'Which birth details are needed for education astrology?',
    answer:
      'You need your birth date, accurate birth time, and birth place. These details help calculate education houses, Mercury, Jupiter, Moon, D24 education chart, dasha, and transit timing.'
  },
  {
    question: 'Which houses matter for education?',
    answer:
      'The 4th house shows foundation education and schooling, the 5th house shows intelligence and performance, and the 9th house shows higher education, university studies, research, and foreign education.'
  },
  {
    question: 'What does D24 show in education analysis?',
    answer:
      'D24 or Chaturvimshamsha/Siddhamsa is the divisional chart used for education, learning, knowledge, academic depth, and mastery. It helps refine what the main birth chart indicates.'
  },
  {
    question: 'Can the report suggest suitable subjects?',
    answer:
      'Yes. The report uses Mercury, Jupiter, Moon, Mars, Venus, Saturn, Sun, education houses, and chart strengths to suggest subject directions and learning paths.'
  },
  {
    question: 'Does it help with competitive exams?',
    answer:
      'Yes. The education report can discuss academic performance, exam temperament, concentration, obstacles, and timing support. It should be used alongside disciplined preparation and educational counseling.'
  },
  {
    question: 'Can it show higher education or foreign study potential?',
    answer:
      'Yes. The 9th house, Jupiter, D24, dasha periods, and related education indicators help assess higher education, advanced degrees, research, and foreign education themes.'
  },
  {
    question: 'Does the report identify study obstacles?',
    answer:
      'Yes. It checks Saturn, Rahu, difficult dasha periods, weak education houses, and learning-style mismatches that may show breaks, delays, distraction, or confidence issues.'
  },
  {
    question: 'Is education astrology guaranteed?',
    answer:
      'No. Education astrology is guidance, not a guarantee. Academic success depends on preparation, teachers, resources, health, family support, environment, and consistent effort.'
  },
  {
    question: 'Is my birth data private?',
    answer:
      'Your birth details are used to calculate and save your personal education report. They are not shown publicly on the education analysis page.'
  }
];

const educationMethodCards = [
  ['4th House', 'Foundation education, schooling, study environment, basic learning support, and graduation foundations.'],
  ['5th House', 'Intelligence, creativity, retention, exam performance, confidence, and competitive academic output.'],
  ['9th House', 'Higher education, university study, advanced degrees, research, mentors, and foreign education themes.'],
  ['Mercury and Jupiter', 'Learning capacity, analysis, communication, wisdom, teaching ability, and academic success.'],
  ['D24 Education Chart', 'Chaturvimshamsha/Siddhamsa layer for education depth, mastery, and the fruit of sustained learning.'],
  ['Timing and Obstacles', 'Dasha, transit, Saturn/Rahu pressure, education yogas, Ashtakavarga support, and study windows.']
];

const educationReportItems = [
  'Natural learning potential and intelligence pattern',
  'Best subjects, academic streams, and career-linked study paths',
  'Higher education, research, Masters, PhD, or foreign study support',
  'Study method based on Mercury, Moon, and learning style',
  'Competitive exam temperament and academic performance support',
  'Obstacles, breaks, delays, distraction, or confidence challenges',
  'Education yogas, planetary strengths, and Ashtakavarga indicators',
  'Practical study guidance and concentration remedies'
];

const wealthFaqItems = [
  {
    question: 'What is wealth analysis by date of birth?',
    answer:
      'Wealth analysis by date of birth studies your Vedic birth chart for income source, savings capacity, asset-building pattern, Dhana yogas, financial risk, business or job wealth path, and timing for growth.'
  },
  {
    question: 'Which birth details are needed for wealth astrology?',
    answer:
      'You need your birth date, accurate birth time, and birth place. These details help calculate wealth houses, income houses, Dhana yogas, dasha, transit timing, and career-to-money connections.'
  },
  {
    question: 'Which houses matter most for wealth?',
    answer:
      'The 2nd house shows accumulated wealth and savings, the 5th shows speculation and intelligence gains, the 9th shows fortune, and the 11th shows income, gains, and networks.'
  },
  {
    question: 'Does the report check Dhana Yogas?',
    answer:
      'Yes. The report looks for Dhana, Lakshmi, Raja, Viparita, and other prosperity combinations when supported by the chart, and explains what they can realistically produce.'
  },
  {
    question: 'Can it show my best income source?',
    answer:
      'Yes. It can indicate whether wealth is more likely through salary, business, advisory work, creative/client-facing work, property, foreign or technology sources, investments, or networks.'
  },
  {
    question: 'Can astrology tell if trading or investing suits me?',
    answer:
      'It can show suitability and risk tendencies, especially through the 5th, 8th, 11th, and 12th houses. The report avoids financial recommendations and frames trading or investing as educational guidance only.'
  },
  {
    question: 'Does the report show savings and cashflow patterns?',
    answer:
      'Yes. It studies the 2nd house, 11th house, Jupiter, Venus, Mercury, Saturn, dasha support, and risk houses to describe whether money accumulates steadily, comes in bursts, or leaks through expenses.'
  },
  {
    question: 'Can it show wealth timing?',
    answer:
      'Yes. The report checks current dasha, transits, and wealth activations to identify supportive, mixed, or weak windows for income growth, asset building, or financial caution.'
  },
  {
    question: 'Is this financial advice?',
    answer:
      'No. Wealth astrology is educational guidance, not financial advice. Do not use it as a substitute for licensed financial, tax, legal, or investment advice.'
  },
  {
    question: 'Is my financial data private?',
    answer:
      'The report uses your birth details to calculate wealth indications. Your personal report is saved to your account and not shown publicly on the wealth analysis page.'
  }
];

const wealthMethodCards = [
  ['2nd House', 'Accumulated wealth, savings discipline, family assets, speech-linked income, liquidity, and money retention.'],
  ['11th House', 'Income, gains, networks, fulfilment of desires, patrons, bonuses, and recurring financial inflow.'],
  ['5th and 9th Houses', 'Speculation, intelligence gains, fortune, dharmic support, education-linked wealth, and luck patterns.'],
  ['Dhana Yogas', 'Prosperity combinations including Dhana, Lakshmi, Raja, Viparita, and wealth-producing house links.'],
  ['Income Source', 'Salary, business, freelancing, advisory work, creative income, property, foreign, technology, or network gains.'],
  ['Risk and Timing', 'Debt, losses, impulsive spending, trading risk, hidden expenses, dasha support, and wealth growth windows.']
];

const wealthReportItems = [
  'Core wealth promise and accumulation strength',
  'Primary income source and earning method',
  'Cashflow, savings, liquidity, and asset-building pattern',
  'Dhana yogas and prosperity combinations',
  'Job, business, trading, investment, and property suitability',
  'Financial risk, debt, loss, and over-spending patterns',
  'Career-to-money connection and monetization path',
  'Wealth timing, 90-day plan, 12-month strategy, and mistakes to avoid'
];

const progenyFaqItems = [
  {
    question: 'What is progeny analysis by date of birth?',
    answer:
      'Progeny analysis by date of birth studies your Vedic birth chart for children promise, family expansion support, D7 Saptamsa strength, Jupiter, fertility sphuta, timing windows, obstacles, remedies, and parenting themes.'
  },
  {
    question: 'Which birth details are needed for progeny astrology?',
    answer:
      'You need your birth date, accurate birth time, birth place, and gender in your birth profile. Accurate birth data helps calculate the Lagna, D1 5th house, D7 Saptamsa, dasha, and timing indicators.'
  },
  {
    question: 'Why is gender required for progeny analysis?',
    answer:
      'Gender is used only because some classical progeny calculations and interpretation rules depend on chart context. It is not used for judgment, and the report does not predict the gender of a child.'
  },
  {
    question: 'What does the D1 5th house show about children?',
    answer:
      'The 5th house shows children promise, blessings through children, creativity, intelligence, and visible support or pressure around family expansion. Its lord, occupants, aspects, and strength are read carefully.'
  },
  {
    question: 'What is D7 Saptamsa in progeny analysis?',
    answer:
      'D7 or Saptamsa is the divisional chart used for progeny, child-related karma, family expansion, and parenting support. AstroRoshni reads D7 with the main birth chart instead of using it alone.'
  },
  {
    question: 'What does Jupiter show in progeny astrology?',
    answer:
      'Jupiter is the natural significator for children, wisdom, protection, blessings, and growth. Its strength, dignity, aspects, and dasha connection help refine the progeny reading.'
  },
  {
    question: 'What is fertility sphuta?',
    answer:
      'Fertility sphuta is a symbolic astrological factor used in some progeny calculations. It is not a medical fertility test and should never replace consultation with qualified healthcare professionals.'
  },
  {
    question: 'Can the report show timing for family expansion?',
    answer:
      'Yes. The report studies dasha, transit, D1 and D7 support, Jupiter activation, and timing indicators to describe supportive windows, mixed periods, and caution periods for family expansion.'
  },
  {
    question: 'Can existing parents use this report?',
    answer:
      'Yes. Existing parents can use the parenting focus to understand parenting style, child relationship dynamics, support themes, and family harmony. In parenting mode, the report avoids conception timing.'
  },
  {
    question: 'Is progeny analysis medical advice or child gender prediction?',
    answer:
      'No. Progeny astrology is spiritual and reflective guidance, not medical diagnosis or treatment advice. AstroRoshni does not provide child gender prediction.'
  }
];

const progenyMethodCards = [
  ['D1 5th House', 'Children promise, visible family expansion themes, blessings, support, pressure, and the role of the 5th lord.'],
  ['D7 Saptamsa', 'The divisional progeny chart for child-related karma, family expansion support, and deeper promise strength.'],
  ['Jupiter', 'Natural significator for children, wisdom, protection, growth, blessings, and supportive timing activation.'],
  ['Fertility Sphuta', 'Symbolic progeny factor used as astrological support, never as a medical fertility diagnosis.'],
  ['Dasha and Timing', 'Current activation, supportive windows, caution periods, and the timing climate for family expansion.'],
  ['Parenting and Remedies', 'Focus-specific guidance for first child, next child, or parenting, with practical remedies and supportive actions.']
];

const progenyReportItems = [
  'Core progeny promise and promise strength',
  'D1 5th house, 5th lord, planets, and pressure factors',
  'D7 Saptamsa support level and progeny indicators',
  'Jupiter and fertility sphuta interpretation',
  'Current dasha activation and timing climate',
  'Supportive windows, mixed periods, and caution periods',
  'Obstacles, delays, support factors, and remedies',
  'Focus-specific guidance for first child, next child, or parenting'
];

const AnalysisDetailPage = ({ analysisType, user, onLogout, onAdminClick, onLogin, onOpenRegister }) => {
  const navigate = useNavigate();
  const { chartData, birthData } = useAstrology();
  const [showBirthModal, setShowBirthModal] = useState(false);
  const [showCreditsModal, setShowCreditsModal] = useState(false);
  const [birthModalTab, setBirthModalTab] = useState('saved');

  const meta = PAGE_META[analysisType];
  const seoData = useMemo(
    () => generatePageSEO(meta.seoKey, { path: meta.path }),
    [meta.seoKey, meta.path]
  );

  const hasBirth = Boolean(
    birthData?.name &&
    birthData?.date &&
    birthData?.latitude != null &&
    birthData?.longitude != null
  );
  const isCareer = analysisType === 'career';
  const isMarriage = analysisType === 'marriage';
  const isHealth = analysisType === 'health';
  const isEducation = analysisType === 'education';
  const isWealth = analysisType === 'wealth';
  const isProgeny = analysisType === 'progeny';
  const isSeoEnriched = isCareer || isMarriage || isHealth || isEducation || isWealth || isProgeny;
  const analysisLabel = isProgeny ? 'Progeny' : isWealth ? 'Wealth' : isEducation ? 'Education' : isHealth ? 'Health' : isMarriage ? 'Marriage' : 'Career';
  const analysisSlug = analysisLabel.toLowerCase();
  const activeFaqItems = isProgeny ? progenyFaqItems : isWealth ? wealthFaqItems : isEducation ? educationFaqItems : isHealth ? healthFaqItems : isMarriage ? marriageFaqItems : careerFaqItems;
  const activeMethodCards = isProgeny ? progenyMethodCards : isWealth ? wealthMethodCards : isEducation ? educationMethodCards : isHealth ? healthMethodCards : isMarriage ? marriageMethodCards : careerMethodCards;
  const activeReportItems = isProgeny ? progenyReportItems : isWealth ? wealthReportItems : isEducation ? educationReportItems : isHealth ? healthReportItems : isMarriage ? marriageReportItems : careerReportItems;
  const activeProofItems = isMarriage
    ? ['D9 Navamsa', '7th house', 'Darakaraka', 'Marriage timing']
    : isHealth
      ? ['D30 Trimsamsa', 'Vitality', 'Stress & sleep', 'Health timing']
      : isEducation
        ? ['D24 Siddhamsa', '5th house', 'Mercury & Jupiter', 'Exam timing']
        : isWealth
          ? ['Dhana yogas', '2nd & 11th houses', 'Income source', 'Wealth timing']
          : isProgeny
            ? ['D7 Saptamsa', 'D1 5th house', 'Jupiter', 'Timing windows']
            : ['D10 Dashamsha', '10th house', 'Amatyakaraka', 'Career timing'];

  const openBirthPicker = (mode = 'saved') => {
    if (!user) {
      onLogin?.();
      return;
    }
    setBirthModalTab(mode);
    setShowBirthModal(true);
  };

  const handlePrimaryCta = () => {
    if (!user) {
      onLogin?.();
      return;
    }
    if (!hasBirth) {
      openBirthPicker('new');
      return;
    }
    document.querySelector('.analysis-detail-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const handleAdminClick = () => {
    if (onAdminClick) onAdminClick();
  };

  const structuredData = isSeoEnriched
    ? {
        '@context': 'https://schema.org',
        '@graph': [
          {
            '@type': 'WebApplication',
            name: isHealth
              ? 'AstroRoshni Health Analysis by Date of Birth'
              : isEducation
                ? 'AstroRoshni Education Analysis by Date of Birth'
                : isWealth
                  ? 'AstroRoshni Wealth Analysis by Date of Birth'
                  : isProgeny
                    ? 'AstroRoshni Progeny Analysis by Date of Birth'
                    : isMarriage
                      ? 'AstroRoshni Marriage Analysis by Date of Birth'
                      : 'AstroRoshni Career Analysis by Date of Birth',
            url: `https://astroroshni.com${meta.path}`,
            applicationCategory: 'LifestyleApplication',
            operatingSystem: 'Web',
            description: seoData.description,
            publisher: {
              '@type': 'Organization',
              name: 'AstroRoshni',
              url: 'https://astroroshni.com'
            }
          },
          {
            '@type': 'Service',
            name: meta.headline,
            serviceType: isHealth
              ? 'Vedic health astrology report'
              : isEducation
                ? 'Vedic education astrology report'
                : isWealth
                  ? 'Vedic wealth astrology report'
                  : isProgeny
                    ? 'Vedic progeny astrology report'
                    : isMarriage
                      ? 'Vedic marriage astrology report'
                      : 'Vedic career astrology report',
            description: seoData.description,
            provider: { '@type': 'Organization', name: 'AstroRoshni' },
            areaServed: 'Worldwide'
          },
          {
            '@type': 'FAQPage',
            mainEntity: activeFaqItems.map((item) => ({
              '@type': 'Question',
              name: item.question,
              acceptedAnswer: {
                '@type': 'Answer',
                text: item.answer
              }
            }))
          },
          {
            '@type': 'BreadcrumbList',
            itemListElement: [
              {
                '@type': 'ListItem',
                position: 1,
                name: 'Home',
                item: 'https://astroroshni.com/'
              },
              {
                '@type': 'ListItem',
                position: 2,
                name: isProgeny ? 'Progeny Analysis' : isWealth ? 'Wealth Analysis' : isEducation ? 'Education Analysis' : isHealth ? 'Health Analysis' : isMarriage ? 'Marriage Analysis' : 'Career Guidance',
                item: `https://astroroshni.com${meta.path}`
              }
            ]
          }
        ]
      }
    : {
        '@context': 'https://schema.org',
        '@type': 'Service',
        name: meta.headline,
        description: seoData.description,
        provider: { '@type': 'Organization', name: 'AstroRoshni' }
      };

  return (
    <div
      className={`analysis-detail-page ${isCareer ? 'analysis-detail-page--career' : ''} ${isMarriage ? 'analysis-detail-page--marriage' : ''} ${isHealth ? 'analysis-detail-page--health' : ''} ${isEducation ? 'analysis-detail-page--education' : ''} ${isWealth ? 'analysis-detail-page--wealth' : ''} ${isProgeny ? 'analysis-detail-page--progeny' : ''}`}
      style={isSeoEnriched ? { '--analysis-hero-image': `url(${process.env.PUBLIC_URL || ''}/images/software/birth-chart.png)` } : undefined}
    >
      <SEOHead
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={structuredData}
      />

      <NavigationHeader
        compact
        showZodiacSelector={false}
        user={user}
        onAdminClick={handleAdminClick}
        onLogout={onLogout}
        onLogin={!user ? onLogin : undefined}
        showLoginButton={!user}
        birthData={birthData}
        onChangeNative={
          !user
            ? () => onLogin?.()
            : (mode) => {
                setBirthModalTab(mode === 'create' ? 'new' : 'saved');
                setShowBirthModal(true);
              }
        }
        onCreateBirthChart={
          !user
            ? () => onLogin?.()
            : () => {
                setBirthModalTab('new');
                setShowBirthModal(true);
              }
        }
        onSelectBirthChart={
          !user
            ? () => onLogin?.()
            : () => {
                setBirthModalTab('saved');
                setShowBirthModal(true);
              }
        }
        onCreditsClick={() => setShowCreditsModal(true)}
      />

      <main className="analysis-detail-main">
        <header className="analysis-detail-hero">
          <div className="analysis-detail-hero__inner">
            <button type="button" className="analysis-detail-back" onClick={() => navigate('/')}>
              ← Home
            </button>
            <p className="analysis-detail-kicker">{meta.kicker}</p>
            <h1 className="analysis-detail-title">
              <span className="analysis-detail-title__icon" aria-hidden>{meta.icon}</span>
              {meta.headline}
            </h1>
            <p className="analysis-detail-blurb">{meta.blurb}</p>
            {isSeoEnriched && (
              <>
                <div className="career-detail-hero-actions">
                  <button type="button" className="career-detail-primary" onClick={handlePrimaryCta}>
                    {user ? (hasBirth ? `Run ${analysisSlug} report` : 'Enter birth details') : 'Sign in to start'}
                  </button>
                  <button type="button" className="career-detail-secondary" onClick={() => openBirthPicker('saved')}>
                    Select saved chart
                  </button>
                </div>
                <div className="career-detail-proof" aria-label={`${analysisLabel} analysis coverage`}>
                  {activeProofItems.map((item) => (
                    <span key={item}>{item}</span>
                  ))}
                </div>
              </>
            )}
          </div>
        </header>

        <div className="analysis-detail-body">
          {isSeoEnriched && (
            <section className="career-detail-intro" aria-label={`${analysisLabel} report coverage`}>
              <div className="career-detail-section-heading">
                <p>{analysisLabel} report engine</p>
                <h2>
                  {isProgeny
                    ? 'What AstroRoshni checks before giving progeny guidance'
                    : isWealth
                    ? 'What AstroRoshni checks before giving wealth guidance'
                    : isEducation
                    ? 'What AstroRoshni checks before giving education guidance'
                    : isHealth
                    ? 'What AstroRoshni checks before giving health guidance'
                    : isMarriage
                    ? 'What AstroRoshni checks before giving marriage guidance'
                    : 'What AstroRoshni checks before giving career guidance'}
                </h2>
              </div>
              <div className="career-detail-method-grid">
                {activeMethodCards.map(([title, body]) => (
                  <article key={title}>
                    <h3>{title}</h3>
                    <p>{body}</p>
                  </article>
                ))}
              </div>
            </section>
          )}

          {!user ? (
            <div className="analysis-detail-empty">
              <div className="analysis-detail-empty__card">
                <span className="analysis-detail-empty__icon" aria-hidden>{meta.icon}</span>
                <h2>Sign in to continue</h2>
                <p>
                  Sign in to save a birth chart on your account, then you can run this report—the same flow as
                  our mobile app. New here? Create a free account.
                </p>
                <div className="analysis-detail-empty__actions">
                  <button type="button" className="analysis-detail-empty__cta" onClick={() => onLogin?.()}>
                    Sign in
                  </button>
                  <button
                    type="button"
                    className="analysis-detail-empty__cta analysis-detail-empty__cta--secondary"
                    onClick={() => (onOpenRegister || onLogin)?.()}
                  >
                    Create account
                  </button>
                </div>
              </div>
            </div>
          ) : hasBirth ? (
            <div className="analysis-detail-panel">
              <UniversalAIInsights
                analysisType={analysisType}
                chartData={chartData}
                birthDetails={birthData}
                PDFComponent={meta.pdf}
                hideConfirmationIntro
              />
            </div>
          ) : (
            <div className="analysis-detail-empty">
              <div className="analysis-detail-empty__card">
                <span className="analysis-detail-empty__icon" aria-hidden>{meta.icon}</span>
                <h2>Add birth details</h2>
                <p>
                  We need your accurate birth date, time, and place to generate this report—same flow as our
                  mobile app.
                </p>
                <button
                  type="button"
                  className="analysis-detail-empty__cta"
                  onClick={() => setShowBirthModal(true)}
                >
                  Enter birth details
                </button>
              </div>
            </div>
          )}

          {isSeoEnriched && (
            <>
              <section className="career-detail-report-scope" aria-label={`${analysisLabel} report sections`}>
                <div>
                  <p className="career-detail-eyebrow">Personalised report</p>
                  <h2>
                    {isProgeny
                      ? 'Built for compassionate family guidance, not medical claims'
                      : isWealth
                      ? 'Built for real money decisions, not generic prosperity claims'
                      : isEducation
                      ? 'Built for real study decisions, not generic academic predictions'
                      : isHealth
                      ? 'Built for preventive wellness reflection, not medical diagnosis'
                      : isMarriage
                      ? 'Built for real relationship decisions, not generic marriage predictions'
                      : 'Built for real career decisions, not a generic profession list'}
                  </h2>
                  {isProgeny ? (
                    <p>
                      The report separates progeny promise, D1 5th house support, D7 Saptamsa strength, Jupiter,
                      fertility sphuta, timing, obstacles, remedies, and parenting focus. It is spiritual guidance,
                      not medical diagnosis, treatment advice, or child gender prediction.
                    </p>
                  ) : isWealth ? (
                    <p>
                      The report separates income source, accumulation, asset-building, wealth yogas, risk, timing,
                      and practical strategy. It is educational astrology guidance and should not replace financial,
                      tax, legal, or investment advice.
                    </p>
                  ) : isEducation ? (
                    <p>
                      The report separates learning potential, subject fit, higher education promise, study method,
                      academic timing, and obstacles. It is astrological guidance and should support, not replace,
                      teachers, counselors, preparation, and practical planning.
                    </p>
                  ) : isHealth ? (
                    <p>
                      The report separates constitution, vitality, vulnerable systems, mental wellness, timing, and
                      preventive guidance. It is designed for proactive awareness and should always stay secondary to
                      qualified medical care.
                    </p>
                  ) : isMarriage ? (
                    <p>
                      The report separates promise, timing, partner nature, manifestation, continuity, and friction.
                      That matters because attraction, marriage timing, family support, and long-term harmony are
                      related but not the same thing.
                    </p>
                  ) : (
                    <p>
                      The report separates aptitude, profession, work function, timing, and risk. That matters because
                      two people can have the same suitable field but very different paths: employee, founder, consultant,
                      technical specialist, manager, researcher, public-facing leader, or quiet expert.
                    </p>
                  )}
                </div>
                <ul>
                  {activeReportItems.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>

              <section className="career-detail-seo-copy" aria-label={`${analysisLabel} astrology guide`}>
                <article>
                  <h2>
                    {isProgeny
                      ? 'Progeny astrology by D1 5th house and D7 Saptamsa'
                      : isWealth
                      ? 'Wealth astrology by 2nd, 5th, 9th, and 11th houses'
                      : isEducation
                      ? 'Education astrology by 4th, 5th, 9th houses and D24'
                      : isHealth
                      ? 'Health astrology by Lagna, health houses, and D30'
                      : isMarriage
                        ? 'Marriage astrology by 7th house and D9 Navamsa'
                        : 'Career astrology by 10th house and D10 chart'}
                  </h2>
                  {isProgeny ? (
                    <p>
                      The D1 5th house shows the visible promise for children, blessings, and pressure factors,
                      while D7 Saptamsa refines progeny and family expansion support. AstroRoshni reads both with
                      Jupiter, fertility sphuta, dasha, and transit timing.
                    </p>
                  ) : isWealth ? (
                    <p>
                      The 2nd house shows accumulated wealth and savings, the 11th house shows gains and networks,
                      the 5th shows speculation and intelligence gains, and the 9th shows fortune. AstroRoshni reads
                      these with Jupiter, Venus, Mercury, Saturn, dasha, and transit timing.
                    </p>
                  ) : isEducation ? (
                    <p>
                      The 4th house shows foundation education, the 5th house shows intelligence and performance,
                      and the 9th house shows higher education. D24 adds a deeper layer for learning, knowledge,
                      academic depth, and mastery.
                    </p>
                  ) : isHealth ? (
                    <p>
                      The Lagna shows the body and constitution, while the 6th, 8th, and 12th houses show illness,
                      chronic vulnerability, recovery, sleep, and caution patterns. D30 Trimsamsa adds a deeper layer
                      for refining sensitive indications.
                    </p>
                  ) : isMarriage ? (
                    <p>
                      The 7th house shows partnership, spouse themes, and commitment patterns. D9 Navamsa shows how
                      the promise matures after commitment. AstroRoshni reads D1 and D9 together with Venus, Jupiter,
                      Darakaraka, Upapada Lagna, A7, dasha, and transit timing.
                    </p>
                  ) : (
                    <p>
                      The 10th house shows karma, profession, reputation, authority, and visible work. The 10th lord
                      shows how career energy moves through life, while the D10 Dashamsha chart helps confirm the fruit
                      of professional effort. AstroRoshni reads these together with Amatyakaraka, nakshatra signatures,
                      yogas, dasha, and transit timing.
                    </p>
                  )}
                </article>
                <article>
                  <h2>
                    {isProgeny
                      ? 'Children timing, family expansion, obstacles, and parenting guidance'
                      : isWealth
                      ? 'Income source, savings, assets, risk, and growth timing'
                      : isEducation
                      ? 'Subject fit, exam support, higher studies, and study obstacles'
                      : isHealth
                      ? 'Vitality, stress, sleep, digestion, and caution windows'
                      : isMarriage
                        ? 'Marriage timing, spouse nature, harmony, and delays'
                        : 'Suitable profession, job change, business, and growth timing'}
                  </h2>
                  {isProgeny ? (
                    <p>
                      A useful progeny report should answer practical questions: whether the chart shows support,
                      which periods look more active, where delays or caution may appear, and how remedies or parenting
                      choices can support family harmony without replacing medical care.
                    </p>
                  ) : isWealth ? (
                    <p>
                      A useful wealth report should answer practical questions: where income is likely to come from,
                      whether money accumulates or leaks, which asset-building path is more natural, what risks to
                      avoid, and when financial growth windows look supportive.
                    </p>
                  ) : isEducation ? (
                    <p>
                      A useful education astrology report should answer practical questions: which subjects suit the
                      student, how they learn best, whether higher studies are supported, where obstacles may arise,
                      and which periods are better for exams or focused study.
                    </p>
                  ) : isHealth ? (
                    <p>
                      A useful health astrology report should avoid diagnosis and instead highlight body-system
                      themes, recovery pattern, digestion and stress tendencies, and periods where routine, rest, or
                      medical checkups may deserve extra attention.
                    </p>
                  ) : isMarriage ? (
                    <p>
                      A useful marriage report should answer practical questions: what kind of partner pattern appears,
                      whether commitment timing is supportive, where delay or friction may arise, and what improves
                      long-term peace. The report is designed around those relationship decisions.
                    </p>
                  ) : (
                    <p>
                      A useful career report should answer practical questions: which field fits, what role type suits
                      you, whether job or business is stronger, where instability may come from, and when the next
                      supportive window for growth or change appears. The report is designed around those decisions.
                    </p>
                  )}
                </article>
              </section>

              <section className="career-detail-faq" aria-label={`${analysisLabel} analysis FAQ`}>
                <h2>{analysisLabel} Analysis FAQ</h2>
                <div className="career-detail-faq-grid">
                  {activeFaqItems.map((item) => (
                    <article key={item.question}>
                      <h3>{item.question}</h3>
                      <p>{item.answer}</p>
                    </article>
                  ))}
                </div>
              </section>
            </>
          )}
        </div>
      </main>

      {user ? (
        <BirthFormModal
          isOpen={showBirthModal}
          onClose={() => setShowBirthModal(false)}
          onSubmit={() => setShowBirthModal(false)}
          defaultActiveTab={birthModalTab}
          title={`${meta.headline} — Birth details`}
          description="Please provide your birth information to generate your personalized analysis."
        />
      ) : null}
      <CreditsModal isOpen={showCreditsModal} onClose={() => setShowCreditsModal(false)} onLogin={onLogin} />
    </div>
  );
};

export default AnalysisDetailPage;
