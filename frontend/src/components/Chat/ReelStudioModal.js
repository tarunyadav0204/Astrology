import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { showToast } from '../../utils/toast';
import './ReelStudioModal.css';
import ReelPlayer from './ReelPlayer';
import { ThemeButton } from '../Theme';
import CreditsModal from '../Credits/CreditsModal';

const REEL_FORMATS = {
    short: {
        duration: 90,
        label: "Short Video Reading",
        detail: 'About 90 seconds · 8–10 scenes',
        description: 'A focused visual answer that is easy to watch and share.',
    },
    deep: {
        duration: 180,
        label: "Deep Video Reading",
        detail: 'About 3 minutes · 12–18 scenes',
        description: 'A fuller visual reading with more chart and timing detail.',
    },
};
const REEL_SETTINGS = { visualLevel: 'cinematic' };

function reelProgress(status, preparing = false) {
    if (preparing) return { value: 8, title: "Preparing your video reading", detail: 'Organising your reading into a clear visual story.' };
    if (status === 'queued') return { value: 14, title: "Your video reading is in line", detail: 'We’ll begin creating it shortly.' };
    const assetMatch = String(status).match(/^creating_your_reel_(\d+)_of_(\d+)$/);
    if (assetMatch) {
        const done = Number(assetMatch[1]); const total = Number(assetMatch[2]);
        return { value: Math.min(82, 18 + Math.round((done / total) * 64)), title: 'Bringing your story to life', detail: `${done} of ${total} moments ready` };
    }
    if (status === 'creating_planned_shots') return { value: 18, title: 'Bringing your story to life', detail: 'Creating the visuals and narration for your reading.' };
    if (status === 'premium_compositing') return { value: 87, title: "Putting your video reading together", detail: 'Finishing the visual story and sound.' };
    if (status === 'saving_reel') return { value: 96, title: 'Almost ready', detail: "Saving your video reading securely." };
    if (status === 'completed') return { value: 100, title: "Your video reading is ready", detail: 'Play, share or download it whenever you like.' };
    return { value: 10, title: "Preparing your video reading", detail: "Your personal video reading is being prepared." };
}

export default function ReelStudioModal({ messageId, onClose, initialLanguage }) {
    const [loading, setLoading] = useState(false);
    const [job, setJob] = useState(null);
    const [jobStatus, setJobStatus] = useState('');
    const [jobError, setJobError] = useState('');
    const [checkingCache, setCheckingCache] = useState(true);
    const [showPlayer, setShowPlayer] = useState(false);
    const [creditQuote, setCreditQuote] = useState(null);
    const [showSetup, setShowSetup] = useState(false);
    const [language, setLanguage] = useState(() => (initialLanguage || localStorage.getItem('reelLanguage')) === 'hi' ? 'hi' : 'en');
    const [presenterEnabled, setPresenterEnabled] = useState(false);
    const [pricingError, setPricingError] = useState(false);
    const [pricingRetry, setPricingRetry] = useState(0);
    const [showBuyCredits, setShowBuyCredits] = useState(false);
    const [isRecreating, setIsRecreating] = useState(false);
    const [reelFormat, setReelFormat] = useState('short');
    const prepareLock = useRef(false);

    useEffect(() => {
        const controller = new AbortController();
        const lookup = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await fetch(`/api/reel-studio/saved/${encodeURIComponent(messageId)}`, {
                    signal: controller.signal, headers: token ? { Authorization: `Bearer ${token}` } : {},
                });
                if (!response.ok) throw new Error("Could not check for your saved video reading. Please reopen AstroRoshni Studio.");
                const payload = await response.json();
                if (controller.signal.aborted) return;
                if (payload.job) {
                    setJob(payload.job); setJobStatus(payload.job.status);
                    if (payload.job.status === 'completed') setShowPlayer(true);
                }
            } catch (error) {
                if (error.name !== 'AbortError') { setJobError(error.message); setJobStatus('cache_error'); }
            } finally { if (!controller.signal.aborted) setCheckingCache(false); }
        };
        lookup();
        return () => controller.abort();
    }, [messageId]);

    useEffect(() => {
        let active = true;
        setCreditQuote(null); setPricingError(false);
        const token = localStorage.getItem('token');
        fetch(`/api/reel-studio/pricing?duration_seconds=${REEL_FORMATS[reelFormat].duration}&presenter_enabled=${presenterEnabled}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
            .then(async (response) => {
                if (!response.ok) throw new Error('Could not load pricing');
                const data = await response.json();
                if (!Number.isFinite(data.credit_cost) || !Number.isFinite(data.credits)) throw new Error('Invalid price');
                if (presenterEnabled && data.presenter_enabled !== true) throw new Error('Presenter pricing is not available yet');
                if (active) setCreditQuote({ ...data, format: reelFormat, presenter: presenterEnabled });
            }).catch(() => { if (active) setPricingError(true); });
        return () => { active = false; };
    }, [reelFormat, presenterEnabled, pricingRetry]);
    const quoteReady = creditQuote && creditQuote.format === reelFormat && creditQuote.presenter === presenterEnabled;

    useEffect(() => {
        if (!job?.job_id || ['completed', 'failed'].includes(jobStatus)) return undefined;
        let active = true;
        const poll = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await fetch(`/api/reel-studio/jobs/${encodeURIComponent(job.job_id)}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
                const payload = await response.json();
                if (!active || !response.ok) return;
                setJobStatus(payload.status || 'rendering');
                if (['completed', 'failed'].includes(payload.status)) window.dispatchEvent(new Event('creditUpdated'));
                if (payload.status === 'completed') setShowPlayer(true);
                setJobError(payload.error_message || '');
            } catch (_) { /* Retain the last state while a request is retried. */ }
        };
        poll();
        const timer = window.setInterval(poll, 4000);
        return () => { active = false; window.clearInterval(timer); };
    }, [job?.job_id, jobStatus]);

    const prepare = async () => {
        if (prepareLock.current || !quoteReady) return;
        if (creditQuote.credits < creditQuote.credit_cost) { setShowBuyCredits(true); return; }
        prepareLock.current = true;
        setShowSetup(false);
        localStorage.setItem('reelLanguage', language);
        setJob(null); setJobStatus('preparing'); setJobError('');
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/reel-studio/drafts/from-answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                body: JSON.stringify({ message_id: messageId, duration_seconds: REEL_FORMATS[reelFormat].duration, language, presenter_enabled: presenterEnabled, visual_level: REEL_SETTINGS.visualLevel }),
            });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.detail || "Could not prepare this video reading.");
            await queue(payload);
        } catch (error) {
            showToast(error.message || "Could not prepare this video reading.", 'error');
        } finally {
            prepareLock.current = false;
            setLoading(false);
        }
    };

    const recreate = () => {
        const priorDuration = Number(job?.settings?.duration_seconds);
        const format = priorDuration === REEL_FORMATS.deep.duration ? 'deep' : 'short';
        setReelFormat(format); setPresenterEnabled(false); setIsRecreating(true); setShowPlayer(false); setShowSetup(true);
    };
    const queue = async (draft) => {
        if (!draft?.draft_id) throw new Error("Your video reading could not be prepared. Please try again.");
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/reel-studio/jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                body: JSON.stringify({ message_id: messageId, duration_seconds: REEL_FORMATS[reelFormat].duration, language, presenter_enabled: presenterEnabled, visual_level: REEL_SETTINGS.visualLevel, draft_id: draft.draft_id, approved_claim_ids: draft.claims.map((claim) => claim.id), confirmed_credit_cost: creditQuote.credit_cost }),
            });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.detail || "Could not queue this video reading.");
            setJob(payload);
            setJobStatus(payload.status || 'queued');
            window.dispatchEvent(new Event('creditUpdated'));
        } catch (error) { throw new Error(error.message || "Could not create this video reading."); }
    };
    const download = async () => {
        if (!job?.job_id) return;
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/api/reel-studio/jobs/${encodeURIComponent(job.job_id)}/download`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
            if (!response.ok) throw new Error('The MP4 is not available yet.');
            const url = URL.createObjectURL(await response.blob());
            const link = document.createElement('a'); link.href = url; link.download = 'astroroshni-video-reading.mp4'; link.click(); URL.revokeObjectURL(url);
        } catch (error) { showToast(error.message || "Could not download the video reading.", 'error'); }
    };
    if (showBuyCredits) return <CreditsModal isOpen onClose={() => { setShowBuyCredits(false); setPricingRetry((n) => n + 1); }} />;
    if (showPlayer && job?.job_id) return <ReelPlayer jobId={job.job_id} onClose={() => setShowPlayer(false)} onRecreate={recreate} />;
    return createPortal(
        <div className="reel-studio-backdrop" role="presentation" onMouseDown={onClose}>
            <section className="reel-studio-modal" role="dialog" aria-modal="true" aria-labelledby="reel-studio-title" onMouseDown={(event) => event.stopPropagation()}>
                <button type="button" className="reel-studio-close" onClick={onClose} aria-label={job && !['completed', 'failed'].includes(jobStatus) ? "Close and keep creating your video reading" : "Close AstroRoshni Studio"}>×</button>
                <div className="reel-studio-eyebrow">ASTROROSHNI STUDIO</div>
                <h2 id="reel-studio-title">Your personal video reading</h2>
                <p className="reel-studio-intro">A polished visual reading shaped from your chart, timing and the guidance in this conversation.</p>

                {checkingCache ? <p role="status">Checking your saved video reading…</p> : jobStatus === 'cache_error' ? <p role="alert">{jobError}</p> : ((job && !showSetup) || loading) ? <div className="reel-studio-job" aria-live="polite">
                    {jobStatus === 'failed' ? <><span>!</span><h3>We couldn’t finish your video reading</h3><p>Please try again. Your credits will be returned if creation did not complete.</p><button type="button" className="reel-studio-secondary" onClick={recreate}>Try again</button></> : <>
                    <span className={jobStatus === 'completed' ? 'is-complete' : ''}>{jobStatus === 'completed' ? '✓' : '◌'}</span>
                    <h3>{reelProgress(jobStatus, loading && !job).title}</h3>
                    <div className="reel-progress" role="progressbar" aria-valuenow={reelProgress(jobStatus, loading && !job).value} aria-valuemin="0" aria-valuemax="100"><i style={{ width: `${reelProgress(jobStatus, loading && !job).value}%` }} /></div>
                    <strong className="reel-progress-value">{reelProgress(jobStatus, loading && !job).value}%</strong>
                    <p>{reelProgress(jobStatus, loading && !job).detail}</p>
                    {jobStatus !== 'completed' && <><small className="reel-progress-note">This can take around five minutes. It will keep creating in the background if you close this window.</small><button type="button" className="reel-studio-secondary reel-studio-keep-creating" onClick={onClose}>Close — keep creating</button></>}
                    {jobStatus === 'completed' ? <><button type="button" className="reel-studio-primary" onClick={() => setShowPlayer(true)}>Play saved video reading</button><button type="button" className="reel-studio-secondary" onClick={download}>Download MP4</button><button type="button" className="reel-studio-secondary" onClick={recreate}>Recreate video reading</button></> : null}
                </>}</div> : <>
                    <div className="reel-setup">
                        <h3>{isRecreating ? "Recreate your video reading" : "Make it your video reading"}</h3>
                        <fieldset><legend>Language</legend><div className="reel-setup-options">
                            {[['en', 'English'], ['hi', 'हिन्दी']].map(([code, label]) => <button type="button" key={code} aria-pressed={language === code} onClick={() => setLanguage(code)}>{label}</button>)}
                        </div></fieldset>
                        <fieldset><legend>Length</legend><div className="reel-setup-options">
                            {Object.entries(REEL_FORMATS).map(([key, format]) => <button type="button" key={key} aria-pressed={reelFormat === key} onClick={() => setReelFormat(key)}>{key === 'short' ? 'Short · ~90 sec' : 'Detailed · ~3 min'}</button>)}
                        </div></fieldset>
                        <label className="reel-setup-presenter"><span><strong>Add a presenter</strong><small>An Indian female host opens and closes your video reading, 5 seconds each.</small>{quoteReady && <small>+{creditQuote.presenter_addon_cost} credits</small>}</span><input type="checkbox" checked={presenterEnabled} onChange={(event) => setPresenterEnabled(event.target.checked)} /></label>
                        <div className="reel-credit-summary" aria-live="polite">{quoteReady ? <><strong>{creditQuote.credit_cost} credits total</strong><span>Your balance: {creditQuote.credits} credits</span></> : pricingError ? <button type="button" onClick={() => setPricingRetry((n) => n + 1)}>Could not load pricing. Retry</button> : <span>Checking credits…</span>}</div>
                        <small>Saved video readings are free to replay. Credits are charged when creation begins.</small>
                        <ThemeButton disabled={!quoteReady || loading} onClick={prepare}>{quoteReady && creditQuote.credits < creditQuote.credit_cost ? 'Buy credits' : "Create video reading"}</ThemeButton>
                    </div>
                </>}
            </section>
        </div>, document.body,
    );
}
