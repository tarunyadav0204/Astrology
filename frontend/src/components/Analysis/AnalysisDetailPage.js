import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
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
    headline: 'Career Analysis',
    kicker: 'AI-powered Vedic insights',
    blurb: 'Discover strengths, timing, and direction for your professional life—one personalized report.',
    icon: '💼',
    pdf: null
  },
  health: {
    seoKey: 'healthAnalysis',
    path: '/health-analysis',
    headline: 'Health & Wellness Analysis',
    kicker: 'AI-powered Vedic insights',
    blurb: 'Understand constitutional patterns and wellness themes from your chart—educational only; always consult licensed professionals for medical care.',
    icon: '🏥',
    pdf: HealthReportPDF
  },
  wealth: {
    seoKey: 'wealthAnalysis',
    path: '/wealth-analysis',
    headline: 'Wealth & Finance Analysis',
    kicker: 'AI-powered Vedic insights',
    blurb: 'Explore prosperity indicators, timing, and money themes—educational guidance, not financial advice.',
    icon: '💰',
    pdf: WealthReportPDF
  },
  marriage: {
    seoKey: 'marriageAnalysis',
    path: '/marriage-analysis',
    headline: 'Marriage Analysis',
    kicker: 'AI-powered Vedic insights',
    blurb:
      'Explore relationship patterns, compatibility themes, and marriage timing from your chart—guidance only; relationships take mutual effort.',
    icon: '💍',
    pdf: MarriageReportPDF
  },
  progeny: {
    seoKey: 'progenyAnalysis',
    path: '/progeny-analysis',
    headline: 'Progeny Analysis',
    kicker: 'AI-powered Vedic insights',
    blurb:
      'Explore progeny promise, timing windows, and family expansion guidance from your chart—supportive guidance only, not medical advice.',
    icon: '👶',
    pdf: null
  },
  education: {
    seoKey: 'educationAnalysis',
    path: '/education',
    headline: 'Education Analysis',
    kicker: 'AI-powered Vedic insights',
    blurb:
      'Discover learning strengths, academic timing, and study success themes from your chart—guidance only; results depend on your effort and choices.',
    icon: '🎓',
    pdf: EducationReportPDF
  }
};

const AnalysisDetailPage = ({ analysisType, user, onLogout, onAdminClick }) => {
  const navigate = useNavigate();
  const { chartData, birthData } = useAstrology();
  const [showBirthModal, setShowBirthModal] = useState(false);
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

  const handleAdminClick = () => {
    if (onAdminClick) onAdminClick();
  };

  return (
    <div className="analysis-detail-page">
      <SEOHead
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={{
          '@context': 'https://schema.org',
          '@type': 'Service',
          name: meta.headline,
          description: seoData.description,
          provider: { '@type': 'Organization', name: 'AstroRoshni' }
        }}
      />

      <NavigationHeader
        compact
        showZodiacSelector={false}
        user={user}
        onAdminClick={handleAdminClick}
        onLogout={onLogout}
        birthData={birthData}
        onChangeNative={(mode) => {
          setBirthModalTab(mode === 'create' ? 'new' : 'saved');
          setShowBirthModal(true);
        }}
        onCreateBirthChart={() => {
          setBirthModalTab('new');
          setShowBirthModal(true);
        }}
        onSelectBirthChart={() => {
          setBirthModalTab('saved');
          setShowBirthModal(true);
        }}
        onCreditsClick={() => navigate('/credits')}
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
          </div>
        </header>

        <div className="analysis-detail-body">
          {hasBirth ? (
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
        </div>
      </main>

      <BirthFormModal
        isOpen={showBirthModal}
        onClose={() => setShowBirthModal(false)}
        onSubmit={() => setShowBirthModal(false)}
        defaultActiveTab={birthModalTab}
        title={`${meta.headline} — Birth details`}
        description="Please provide your birth information to generate your personalized analysis."
      />
    </div>
  );
};

export default AnalysisDetailPage;
