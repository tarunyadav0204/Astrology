import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import CreditsModal from '../Credits/CreditsModal';
import BirthFormModal from '../BirthForm/BirthFormModal';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import { reportService } from '../../services/reportService';
import './ReportsStudioPage.css';

const REPORT_LANGUAGES = [
  { code: 'english', label: 'English' },
  { code: 'hindi', label: 'Hindi (हिंदी)' },
  { code: 'tamil', label: 'Tamil' },
  { code: 'telugu', label: 'Telugu' },
  { code: 'marathi', label: 'Marathi' },
  { code: 'gujarati', label: 'Gujarati' },
];

const REPORT_TYPES = [
  {
    key: 'partnership',
    title: 'Partnership Report',
    subtitle: 'Best for marriage, business, parent–child, or any two-person study',
    description: 'A premium 20+ page PDF with chart overlays, timing, strengths, friction points, remedies, and next steps.',
    enabled: true,
  },
  {
    key: 'career',
    title: 'Career Report',
    subtitle: 'Coming soon',
    description: 'A future report for work style, timing, and career direction.',
    enabled: false,
  },
  {
    key: 'wealth',
    title: 'Wealth Report',
    subtitle: 'Income, assets, and 12-month dasha timing',
    description: 'A premium 27-page PDF with D1/D2/D10 layers, yogas, spouse money themes, and monthly wealth timing.',
    enabled: true,
  },
  {
    key: 'health',
    title: 'Health Report',
    subtitle: 'Coming soon',
    description: 'A future report for body constitution, care points, and wellness habits.',
    enabled: false,
  },
  {
    key: 'progeny',
    title: 'Progeny Report',
    subtitle: 'Coming soon',
    description: 'A future report for progeny timing and related chart indicators.',
    enabled: false,
  },
];

const REPORT_CONTENTS = [
  {
    title: 'Executive verdict & score layers',
    desc: 'A clear go / caution / wait reading, plus how Guna Milan, Manglik balance, chart support, and timing fit together — not a single score in isolation.',
  },
  {
    title: 'Nakshatra nature for both people',
    desc: 'Moon, Venus, and 7th-lord nakshatra/pada for each person: emotional style, desire pattern, partner-seeking nature, and where the two natures mesh or friction.',
  },
  {
    title: 'Emotional rhythm & communication',
    desc: 'How both people feel and seek comfort, mental rapport, daily repair style, and communication patterns that help or harden conflict.',
  },
  {
    title: 'Physical chemistry & biology',
    desc: 'Venus–Mars attraction flow, intimacy tone, and Nadi-related biological compatibility signals explained in practical language.',
  },
  {
    title: 'Each person’s D1 marriage foundation',
    desc: 'Separate Rashi-chart chapters for both natives: 7th house, 7th lord, Venus/Jupiter support, and visible relationship karma — kept person-attributed.',
  },
  {
    title: 'Jaimini Upapada & Darapada (A7)',
    desc: 'Inner marriage environment (UL) and how the relationship tends to show up in real life (A7) for both people.',
  },
  {
    title: 'D9 Navamsa maturity & pair durability',
    desc: 'Individual Navamsa chapters plus a pair-level durability reading: whether the bond tends to deepen or drift after commitment.',
  },
  {
    title: 'Wealth, career, progeny & shared dharma',
    desc: 'Financial synergy and D2/KP wealth signals, career and public life together, progeny and D7 parenting legacy, plus beliefs and shared dharma.',
  },
  {
    title: 'Dosha demystification & karmic layer',
    desc: 'Manglik, Bhakoot, Gana, Nadi and cancellations explained without scare tactics, plus D60 karmic patterns that can repeat in the bond.',
  },
  {
    title: 'Timing, event materialization & remedies',
    desc: 'KP alliance materialization checks, dasha/transit windows for engagement or marriage pacing, behavioral guidance, and safe Vedic remedy direction.',
  },
  {
    title: 'Charts inside the PDF',
    desc: 'Relevant D1, D9, D2, D7 and related chart overlays so the narrative is grounded in the actual charts, not only prose.',
  },
  {
    title: 'Shareable 20+ page PDF',
    desc: 'A polished document you can reopen, download, and share — structured for families and decision-makers, not only for astrologers.',
  },
];

const faqItems = [
  {
    question: 'What is Reports Studio?',
    answer:
      'Reports Studio creates premium structured Vedic PDF reports. Partnership Report is available now for any two-person relationship study.',
  },
  {
    question: 'What is inside the Partnership Report?',
    answer:
      'A typical report is 20+ pages covering compatibility overview, Ashtakoot and Manglik context, chart overlays, timing climate, strengths, friction points, remedies, and clear next steps.',
  },
  {
    question: 'How is this different from free Kundli matching?',
    answer:
      'Kundli matching gives a fast Ashtakoot score and core signals. Reports Studio builds a deeper multi-chapter PDF with AI narrative, visuals, timing, and remedy-oriented guidance.',
  },
  {
    question: 'Do I pay credits every time I open a report?',
    answer:
      'No. Fresh generate and regenerate use credits. Reopening an existing report for the same pair and language is free.',
  },
  {
    question: 'Do I need exact birth times?',
    answer:
      'Yes for best results. Accurate date, time, and place improve houses, Navamsa, Manglik assessment, and timing windows.',
  },
  {
    question: 'Which languages are supported?',
    answer:
      'Choose the AI narrative language in step 3. English and Hindi are commonly used; additional languages appear in the language list when available.',
  },
  {
    question: 'How long does generation take?',
    answer:
      'Most partnership reports finish within a few minutes. Progress appears while charts are read and chapters are assembled.',
  },
  {
    question: 'Is my birth data private?',
    answer:
      'Birth details are used to calculate charts and generate your report. They are not shown publicly on the marketing page.',
  },
];

const structuredData = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'WebApplication',
      name: 'AstroRoshni Reports Studio',
      url: 'https://astroroshni.com/reports',
      applicationCategory: 'LifestyleApplication',
      operatingSystem: 'Web',
      description:
        'Premium Vedic partnership PDF reports with chart overlays, timing, strengths, friction points, and remedies.',
      publisher: { '@type': 'Organization', name: 'AstroRoshni', url: 'https://astroroshni.com' },
    },
    {
      '@type': 'FAQPage',
      mainEntity: faqItems.map((item) => ({
        '@type': 'Question',
        name: item.question,
        acceptedAnswer: { '@type': 'Answer', text: item.answer },
      })),
    },
    {
      '@type': 'BreadcrumbList',
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' },
        { '@type': 'ListItem', position: 2, name: 'Reports Studio', item: 'https://astroroshni.com/reports' },
      ],
    },
  ],
};

const normalizePerson = (person) => {
  if (!person || typeof person !== 'object') return null;
  const time = person.time != null ? String(person.time) : '';
  const timeShort =
    time.length >= 8 && time[5] === ':' && time[7] === ':'
      ? time.slice(0, 5)
      : time;
  return {
    name: person.name || '',
    date: person.date || '',
    time: timeShort,
    place: person.place || '',
    latitude: person.latitude,
    longitude: person.longitude,
    timezone: person.timezone,
    gender: person.gender,
    chart_id: person.chart_id || person.id || null,
  };
};

const formatBirthLine = (person) => {
  if (!person) return '';
  const parts = [];
  if (person.date) parts.push(person.date);
  if (person.time) parts.push(person.time);
  if (person.place) parts.push(person.place);
  return parts.join(' · ');
};

const ChartSlotCard = ({
  title,
  subtitle,
  person,
  onSelect,
  onCreate,
  onClear,
}) => {
  const filled = Boolean(person?.name && person?.date && person?.time);
  return (
    <div className={`reports-chart-slot ${filled ? 'is-filled' : 'is-empty'}`}>
      <div className="reports-chart-slot-top">
        <div>
          <p className="reports-chart-slot-label">{title}</p>
          {filled ? (
            <>
              <h3>{person.name}</h3>
              <p className="reports-chart-slot-meta">{formatBirthLine(person)}</p>
            </>
          ) : (
            <>
              <h3>{subtitle}</h3>
              <p className="reports-chart-slot-meta">Select a saved chart or create a new one.</p>
            </>
          )}
        </div>
        {filled ? <span className="reports-chart-slot-check" aria-hidden="true">✓</span> : null}
      </div>
      {filled ? (
        <div className="reports-chart-slot-actions">
          <button type="button" className="reports-slot-btn" onClick={onSelect}>
            Change chart
          </button>
          <button type="button" className="reports-slot-btn reports-slot-btn-muted" onClick={onClear}>
            Clear
          </button>
        </div>
      ) : (
        <div className="reports-chart-slot-actions">
          <button type="button" className="reports-slot-btn reports-slot-btn-primary" onClick={onSelect}>
            Select chart
          </button>
          <button type="button" className="reports-slot-btn" onClick={onCreate}>
            Create chart
          </button>
        </div>
      )}
    </div>
  );
};

const ReportsStudioPage = ({
  user,
  onLogout,
  onAdminClick,
  onLogin,
  showLoginButton = true,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { birthData } = useAstrology();
  const { credits, partnershipReportCost, wealthReportCost, fetchBalance } = useCredits();

  const [showCreditsModal, setShowCreditsModal] = useState(false);
  const [activeStep, setActiveStep] = useState(1);
  const [selectedType, setSelectedType] = useState('partnership');
  const [personA, setPersonA] = useState(null);
  const [personB, setPersonB] = useState(null);
  const [language, setLanguage] = useState('english');
  const [loading, setLoading] = useState(false);
  const [checkingExisting, setCheckingExisting] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState('');
  const [reportId, setReportId] = useState(null);
  const [pdfUrl, setPdfUrl] = useState('');
  const [existingReady, setExistingReady] = useState(false);
  const [confirmMode, setConfirmMode] = useState(null); // 'generate' | 'regenerate' | null
  const [chartPickerTarget, setChartPickerTarget] = useState(null); // 'personA' | 'personB' | null
  const [chartPickerTab, setChartPickerTab] = useState('saved'); // 'saved' | 'new'
  const pollRef = useRef(null);
  const mountedRef = useRef(true);

  const isWealth = selectedType === 'wealth';
  const reportCost = Number(
    isWealth ? (wealthReportCost || 9) : (partnershipReportCost || 9)
  ) || 9;

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(location.search || '');
    const shouldOpenLogin = location.state?.openLogin || params.get('login') === '1';
    if (!user && shouldOpenLogin && onLogin) {
      onLogin();
      params.delete('login');
      const search = params.toString();
      navigate(`${location.pathname}${search ? `?${search}` : ''}`, { replace: true, state: {} });
    }
  }, [user, location.state?.openLogin, location.search, onLogin, navigate, location.pathname]);

  const clearPoll = () => {
    if (pollRef.current) {
      clearTimeout(pollRef.current);
      pollRef.current = null;
    }
  };

  const resolvePdfUrl = useCallback(async (id, fallback = '') => {
    if (fallback) return fallback;
    const data = await reportService.getReportPdfUrl(id);
    return data?.pdf_url || '';
  }, []);

  const pollStatus = useCallback(async (id, reportType = 'partnership') => {
    clearPoll();
    try {
      const payload = reportType === 'wealth'
        ? await reportService.getWealthReportStatus(id)
        : await reportService.getPartnershipReportStatus(id);
      const status = String(payload?.status || '').toLowerCase();
      if (!mountedRef.current) return;

      if (status === 'completed') {
        const data = payload?.data || {};
        const url = await resolvePdfUrl(id, data.pdf_url || '');
        if (!mountedRef.current) return;
        setPdfUrl(url);
        setExistingReady(true);
        setLoading(false);
        setStatusMessage('Your premium report is ready.');
        fetchBalance?.().catch(() => {});
        return;
      }

      if (status === 'failed') {
        setLoading(false);
        setError('Something went wrong while preparing your report. Please try again in a moment.');
        setStatusMessage('');
        return;
      }

      setStatusMessage(
        status === 'processing'
          ? (reportType === 'wealth'
            ? 'We are reading your chart and assembling the wealth report now.'
            : 'We are reading both charts and assembling the report now.')
          : "We're getting started on your report. This usually takes just a moment."
      );
      pollRef.current = setTimeout(() => {
        if (mountedRef.current) pollStatus(id, reportType);
      }, 3500);
    } catch (err) {
      console.error('Report status poll failed:', err);
      if (!mountedRef.current) return;
      setLoading(false);
      setError(err?.message || 'Could not check report status.');
    }
  }, [fetchBalance, resolvePdfUrl]);

  useEffect(() => {
    let cancelled = false;
    const typeOk = selectedType === 'partnership' || selectedType === 'wealth';
    if (!user || !personA || !typeOk || (selectedType === 'partnership' && !personB)) {
      setExistingReady(false);
      setReportId(null);
      setPdfUrl('');
      return undefined;
    }
    if (loading) return undefined;

    const timer = setTimeout(async () => {
      setCheckingExisting(true);
      try {
        const data = selectedType === 'wealth'
          ? await reportService.lookupExistingWealthReport(personA, language)
          : await reportService.lookupExistingPartnershipReport(personA, personB, language);
        if (cancelled || !mountedRef.current) return;
        if (data?.exists && data?.report_id) {
          const status = String(data.status || '').toLowerCase();
          const inProgress = Boolean(data.in_progress) || status === 'pending' || status === 'processing';
          setReportId(data.report_id);
          if (inProgress) {
            setExistingReady(false);
            setPdfUrl('');
            setError('');
            setLoading(true);
            setActiveStep(3);
            setStatusMessage(
              status === 'processing'
                ? (selectedType === 'wealth'
                  ? 'We are reading your chart and assembling the wealth report now.'
                  : 'We are reading both charts and assembling the report now.')
                : "We're getting started on your report. This usually takes just a moment."
            );
            pollStatus(data.report_id, selectedType);
          } else {
            setExistingReady(true);
            setStatusMessage(
              selectedType === 'wealth'
                ? 'Your wealth report for this chart is ready. Open it anytime, or regenerate for a fresh reading.'
                : 'Your report for this pair is ready. Open it anytime, or regenerate for a fresh reading.'
            );
          }
        } else {
          setReportId(null);
          setPdfUrl('');
          setExistingReady(false);
          setStatusMessage('');
        }
      } catch (err) {
        console.warn('Existing report lookup failed:', err);
      } finally {
        if (!cancelled && mountedRef.current) setCheckingExisting(false);
      }
    }, 250);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [user, personA, personB, language, selectedType, loading, pollStatus]);

  const requireLogin = () => {
    if (!user) {
      onLogin?.();
      return false;
    }
    return true;
  };

  const startGeneration = async ({ forceRegenerate = false } = {}) => {
    if (!requireLogin()) return;
    if (selectedType === 'wealth') {
      if (!personA) {
        setError('Please select a birth chart before generating.');
        return;
      }
    } else if (!personA || !personB) {
      setError('Please select both charts before generating.');
      return;
    }
    if (!forceRegenerate && credits < reportCost) {
      setShowCreditsModal(true);
      return;
    }
    if (forceRegenerate && credits < reportCost) {
      setShowCreditsModal(true);
      return;
    }

    setConfirmMode(null);
    setError('');
    setLoading(true);
    setExistingReady(false);
    setPdfUrl('');
    setStatusMessage("We're getting started on your report. This usually takes just a moment.");
    setActiveStep(3);

    try {
      const started = selectedType === 'wealth'
        ? await reportService.startWealthReport(personA, language, {
          forceRegenerate,
          chartStyle: 'both',
        })
        : await reportService.startPartnershipReport(personA, personB, language, {
          forceRegenerate,
          chartStyle: 'both',
        });
      const id = started?.report_id;
      if (!id) throw new Error('Could not start the report.');
      setReportId(id);
      await pollStatus(id, selectedType);
    } catch (err) {
      console.error('Start report failed:', err);
      setLoading(false);
      if (err?.status === 402) {
        setShowCreditsModal(true);
        setError('');
        setStatusMessage('');
      } else {
        setError(err?.message || 'Unable to generate report. Please try again.');
        setStatusMessage('');
      }
    }
  };

  const openPdf = async () => {
    try {
      let url = pdfUrl;
      if (!url && reportId) {
        url = await resolvePdfUrl(reportId);
        setPdfUrl(url);
      }
      if (!url) {
        setError('The report is ready, but we could not open the PDF right now.');
        return;
      }
      window.open(url, '_blank', 'noopener,noreferrer');
    } catch (err) {
      setError(err?.message || 'Could not open the PDF.');
    }
  };

  const openChartPicker = (target, tab = 'saved') => {
    if (!requireLogin()) return;
    setChartPickerTab(tab === 'new' ? 'new' : 'saved');
    setChartPickerTarget(target);
  };

  const handleChartPicked = (chart) => {
    const normalized = normalizePerson(chart);
    if (!normalized || !chartPickerTarget) {
      setChartPickerTarget(null);
      return;
    }
    if (chartPickerTarget === 'personA') setPersonA(normalized);
    if (chartPickerTarget === 'personB') setPersonB(normalized);
    setChartPickerTarget(null);
    setError('');
  };

  const bothChartsReady = Boolean(
    personA?.name && personA?.date && personA?.time && personA?.latitude != null && personA?.longitude != null
    && personB?.name && personB?.date && personB?.time && personB?.latitude != null && personB?.longitude != null
  );
  const singleChartReady = Boolean(
    personA?.name && personA?.date && personA?.time && personA?.latitude != null && personA?.longitude != null
  );
  const chartsReady = isWealth ? singleChartReady : bothChartsReady;

  const goToLanguageStep = () => {
    if (!chartsReady) {
      setError(isWealth
        ? 'Please select or create a birth chart before continuing.'
        : 'Please select or create both charts before continuing.');
      return;
    }
    setError('');
    setActiveStep(3);
  };

  const selectedTypeMeta = REPORT_TYPES.find((item) => item.key === selectedType) || REPORT_TYPES[0];

  return (
    <div className="reports-studio-page">
      <SEOHead
        title="Reports Studio — Premium Vedic Partnership PDF Reports | AstroRoshni"
        description="Create premium Vedic partnership PDF reports from two birth charts with timing, strengths, remedies, and clear takeaways."
        keywords="vedic partnership report, marriage compatibility PDF, premium kundli report, reports studio"
        canonical="https://astroroshni.com/reports/"
        structuredData={structuredData}
      />
      <NavigationHeader
        compact
        showZodiacSelector={false}
        user={user}
        onAdminClick={onAdminClick}
        onLogout={onLogout}
        birthData={birthData}
        onChangeNative={() => navigate('/')}
        onCreditsClick={() => setShowCreditsModal(true)}
        onLogin={onLogin}
        showLoginButton={showLoginButton}
      />

      <main className="reports-studio-main">
        <header className="reports-studio-hero">
          <button type="button" className="reports-studio-back" onClick={() => navigate(-1)}>
            ← Back
          </button>
          <p className="reports-studio-eyebrow">Most complete reading</p>
          <h1>Reports Studio</h1>
          <p className="reports-studio-sub">
            Full structured PDF reports with charts, timing, strengths, remedies, and clear takeaways.
            Choose a report type, select the chart(s), confirm language, then generate.
          </p>
          <div className="reports-studio-proof" aria-label="Report coverage">
            <div><strong>27</strong><span>Wealth pages</span></div>
            <div><strong>20+</strong><span>Partnership pages</span></div>
            <div><strong>AI</strong><span>Chapter narrative</span></div>
          </div>
        </header>

        <section className="reports-studio-card" id="reports-studio-tool" aria-label="Reports Studio">
          <div className="reports-studio-steps" aria-label="Progress">
            {['Type', 'Charts', 'Language'].map((label, index) => {
              const step = index + 1;
              const active = activeStep === step;
              const done = activeStep > step;
              return (
                <button
                  key={label}
                  type="button"
                  className={`reports-step-pill ${active ? 'is-active' : ''} ${done ? 'is-done' : ''}`}
                  onClick={() => setActiveStep(step)}
                >
                  <span>{step}</span>
                  {label}
                </button>
              );
            })}
          </div>

          {activeStep === 1 ? (
            <div className="reports-type-grid">
              {REPORT_TYPES.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  disabled={!item.enabled}
                  className={`reports-type-card ${selectedType === item.key ? 'is-selected' : ''} ${!item.enabled ? 'is-disabled' : ''}`}
                  onClick={() => {
                    if (!item.enabled) return;
                    setSelectedType(item.key);
                    if (item.key === 'wealth') setPersonB(null);
                    setActiveStep(2);
                  }}
                >
                  <h3>{item.title}</h3>
                  <p className="reports-type-subtitle">{item.subtitle}</p>
                  <p>{item.description}</p>
                </button>
              ))}
            </div>
          ) : null}

          {activeStep === 2 ? (
            <div className="reports-charts-panel">
              <h2>{isWealth ? 'Choose your chart' : 'Choose both charts'}</h2>
              <p>
                {isWealth
                  ? 'Select a saved chart or create a new one. Details stay read-only after selection.'
                  : 'Select a saved chart or create a new one for each person. Details stay read-only after selection.'}
              </p>
              {!user ? (
                <div className="reports-login-gate">
                  <p>Sign in to use saved charts and generate reports.</p>
                  <button type="button" className="reports-primary-btn" onClick={() => onLogin?.()}>
                    Sign in to continue
                  </button>
                </div>
              ) : (
                <>
                  <div className="reports-chart-slots">
                    <ChartSlotCard
                      title={isWealth ? 'Native' : 'Person A'}
                      subtitle={isWealth ? 'Birth chart' : 'First chart'}
                      person={personA}
                      onSelect={() => openChartPicker('personA', 'saved')}
                      onCreate={() => openChartPicker('personA', 'new')}
                      onClear={() => setPersonA(null)}
                    />
                    {!isWealth ? (
                      <ChartSlotCard
                        title="Person B"
                        subtitle="Second chart"
                        person={personB}
                        onSelect={() => openChartPicker('personB', 'saved')}
                        onCreate={() => openChartPicker('personB', 'new')}
                        onClear={() => setPersonB(null)}
                      />
                    ) : null}
                  </div>
                  <div className="reports-actions">
                    <button type="button" className="reports-secondary-btn" onClick={() => setActiveStep(1)}>
                      Back
                    </button>
                    <button
                      type="button"
                      className="reports-primary-btn"
                      disabled={!chartsReady}
                      onClick={goToLanguageStep}
                    >
                      Continue to language
                    </button>
                  </div>
                  {error && activeStep === 2 ? <p className="reports-error">{error}</p> : null}
                </>
              )}
              {!user ? (
                <button type="button" className="reports-secondary-btn" onClick={() => setActiveStep(1)}>
                  Back
                </button>
              ) : null}
            </div>
          ) : null}

          {activeStep === 3 ? (
            <div className="reports-review-panel">
              <h2>Language & generate</h2>
              <div className="reports-review-grid">
                <div>
                  <span>Type</span>
                  <strong>{selectedTypeMeta.title}</strong>
                </div>
                <div>
                  <span>{isWealth ? 'Chart' : 'Pair'}</span>
                  <strong>
                    {isWealth
                      ? (personA?.name || 'Native')
                      : `${personA?.name || 'Person A'} · ${personB?.name || 'Person B'}`}
                  </strong>
                </div>
                <div>
                  <span>Credits</span>
                  <strong>{existingReady ? 'Already generated' : `${reportCost} credits`}</strong>
                </div>
              </div>

              <label className="reports-language-label" htmlFor="reports-language">
                Report language
              </label>
              <select
                id="reports-language"
                className="reports-language-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                disabled={loading}
              >
                {REPORT_LANGUAGES.map((item) => (
                  <option key={item.code} value={item.code}>{item.label}</option>
                ))}
              </select>

              <div className="reports-actions">
                <button type="button" className="reports-secondary-btn" onClick={() => setActiveStep(2)} disabled={loading}>
                  Back
                </button>
                {existingReady ? (
                  <button type="button" className="reports-primary-btn reports-open-btn" onClick={openPdf} disabled={loading}>
                    Open report
                  </button>
                ) : (
                  <button
                    type="button"
                    className="reports-primary-btn"
                    disabled={loading || checkingExisting || !chartsReady}
                    onClick={() => setConfirmMode('generate')}
                  >
                    {loading
                      ? 'Generating…'
                      : checkingExisting
                        ? 'Checking for existing report…'
                        : `Generate · ${reportCost} credits`}
                  </button>
                )}
              </div>

              {existingReady ? (
                <button
                  type="button"
                  className="reports-regenerate-btn"
                  disabled={loading}
                  onClick={() => setConfirmMode('regenerate')}
                >
                  Regenerate · {reportCost} credits
                </button>
              ) : null}

              {statusMessage ? <p className="reports-status">{statusMessage}</p> : null}
              {error ? <p className="reports-error">{error}</p> : null}
              {pdfUrl ? (
                <button type="button" className="reports-link-btn" onClick={openPdf}>
                  Open PDF in a new tab
                </button>
              ) : null}
            </div>
          ) : null}
        </section>

        <section className="reports-seo-section" aria-labelledby="reports-method-heading">
          <h2 id="reports-method-heading">Why a full Partnership Report?</h2>
          <p>
            Free matching answers “how do the Gunas look?” A Partnership Report answers “what does this relationship
            tend to feel like over time, where is the friction, when is the climate supportive, and what should we do next?”
          </p>
          <p>
            It is a multi-chapter Vedic study of two charts together — marriage, business, parent–child, or any close
            partnership — written as a readable 20+ page PDF with chart overlays, timing windows, and an action plan.
          </p>
          <h3 className="reports-seo-subheading">What you get in the Partnership Report</h3>
          <ul className="reports-contents-grid">
            {REPORT_CONTENTS.map((item) => (
              <li key={item.title}>
                <h4>{item.title}</h4>
                <p>{item.desc}</p>
              </li>
            ))}
          </ul>
          <p className="reports-seo-note">
            Typical chapters include executive verdict, nakshatra nature, emotional and physical chemistry, each person’s
            D1 and D9 foundations, Jaimini UL/A7, wealth–career–progeny domains, dosha and D60 context, dasha/transit
            timing, and remedies — assembled into one shareable PDF.
          </p>
        </section>

        <section className="reports-faq" aria-label="Reports FAQs">
          <h2>Frequently asked questions</h2>
          <div className="reports-faq-grid">
            {faqItems.map((item) => (
              <article key={item.question}>
                <h3>{item.question}</h3>
                <p>{item.answer}</p>
              </article>
            ))}
          </div>
        </section>
      </main>

      {confirmMode ? (
        <div className="reports-modal-backdrop" role="presentation" onClick={() => !loading && setConfirmMode(null)}>
          <div
            className="reports-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="reports-confirm-title"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 id="reports-confirm-title">
              {confirmMode === 'regenerate' ? 'Regenerate report?' : 'Generate report?'}
            </h3>
            <p>
              This will use {reportCost} credits. You currently have {credits} credits.
            </p>
            <div className="reports-modal-actions">
              <button type="button" className="reports-secondary-btn" onClick={() => setConfirmMode(null)}>
                Cancel
              </button>
              <button
                type="button"
                className="reports-primary-btn"
                onClick={() => startGeneration({ forceRegenerate: confirmMode === 'regenerate' })}
              >
                {confirmMode === 'regenerate' ? 'Regenerate' : 'Generate report'}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <CreditsModal isOpen={showCreditsModal} onClose={() => setShowCreditsModal(false)} />

      <BirthFormModal
        key={`reports-chart-${chartPickerTarget}-${chartPickerTab}`}
        isOpen={Boolean(chartPickerTarget)}
        onClose={() => setChartPickerTarget(null)}
        onSubmit={handleChartPicked}
        defaultActiveTab={chartPickerTab}
        title={
          chartPickerTab === 'new'
            ? (chartPickerTarget === 'personB'
              ? 'Create chart for Person B'
              : (isWealth ? 'Create birth chart' : 'Create chart for Person A'))
            : (chartPickerTarget === 'personB'
              ? 'Select chart for Person B'
              : (isWealth ? 'Select birth chart' : 'Select chart for Person A'))
        }
        description={
          chartPickerTab === 'new'
            ? 'Enter birth details to create and save a chart, then use it in this report.'
            : 'Choose a saved chart, or switch to Create to add a new one.'
        }
      />
    </div>
  );
};

export default ReportsStudioPage;
