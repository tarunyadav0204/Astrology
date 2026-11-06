import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { showToast } from '../../utils/toast';
import './ReelStudioModal.css';
import ReelPlayer from './ReelPlayer';
import { ThemeButton, ThemeModal } from '../Theme';
import CreditsModal from '../Credits/CreditsModal';

const REEL_FORMATS = {
    short: {
        duration: 90,
        label: 'Short Reel',
        detail: 'About 90 seconds · 8–10 scenes',
        description: 'A focused visual answer that is easy to watch and share.',
    },
    deep: {
        duration: 180,
        label: 'Deep Reel',
        detail: 'About 3 minutes · 12–18 scenes',
        description: 'A fuller visual reading with more chart and timing detail.',
    },
};
const REEL_SETTINGS = { language: 'en', visualLevel: 'cinematic' };

function reelProgress(status, preparing = false) {
    if (preparing) return { value: 8, title: 'Preparing your reel', detail: 'Organising your reading into a clear visual story.' };
    if (status === 'queued') return { value: 14, title: 'Your reel is in line', detail: 'We’ll begin creating it shortly.' };
    const assetMatch = String(status).match(/^creating_your_reel_(\d+)_of_(\d+)$/);
    if (assetMatch) {
        const done = Number(assetMatch[1]); const total = Number(assetMatch[2]);
        return { value: Math.min(82, 18 + Math.round((done / total) * 64)), title: 'Bringing your story to life', detail: `${done} of ${total} moments ready` };
    }
    if (status === 'creating_planned_shots') return { value: 18, title: 'Bringing your story to life', detail: 'Creating the visuals and narration for your reading.' };
    if (status === 'premium_compositing') return { value: 87, title: 'Putting your reel together', detail: 'Finishing the visual story and sound.' };
    if (status === 'saving_reel') return { value: 96, title: 'Almost ready', detail: 'Saving your reel securely.' };
    if (status === 'completed') return { value: 100, title: 'Your reel is ready', detail: 'Play, share or download it whenever you like.' };
    return { value: 10, title: 'Preparing your reel', detail: 'Your personal reel is being prepared.' };
}

export default function ReelStudioModal({ messageId, onClose }) {
    const [loading, setLoading] = useState(false);
    const [job, setJob] = useState(null);
    const [jobStatus, setJobStatus] = useState('');
    const [jobError, setJobError] = useState('');
    const [checkingCache, setCheckingCache] = useState(true);
    const [showPlayer, setShowPlayer] = useState(false);
    const [creditQuote, setCreditQuote] = useState(null);
    const [showCreditConfirm, setShowCreditConfirm] = useState(false);
    const [showBuyCredits, setShowBuyCredits] = useState(false);
    const [isRecreating, setIsRecreating] = useState(false);
    const [reelFormat, setReelFormat] = useState('short');
    const [formatQuotes, setFormatQuotes] = useState({});
    const prepareLock = useRef(false);

    useEffect(() => {
        const controller = new AbortController();
        const lookup = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await fetch(`/api/reel-studio/saved/${encodeURIComponent(messageId)}`, {
                    signal: controller.signal, headers: token ? { Authorization: `Bearer ${token}` } : {},
                });
                if (!response.ok) throw new Error('Could not check for your saved reel. Please reopen Reel Studio.');
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
        const loadFormatQuotes = async () => {
            const token = localStorage.getItem('token');
            const entries = await Promise.all(Object.entries(REEL_FORMATS).map(async ([key, format]) => {
                const response = await fetch(`/api/reel-studio/pricing?duration_seconds=${format.duration}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
                return response.ok ? [key, await response.json()] : null;
            }));
            if (active) setFormatQuotes(Object.fromEntries(entries.filter(Boolean)));
        };
        loadFormatQuotes().catch(() => { /* The confirmation still loads its authoritative quote. */ });
        return () => { active = false; };
    }, []);

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

    const requestCreditConfirmation = async (format = 'short', recreating = false) => {
        if (loading) return;
        const selectedFormat = REEL_FORMATS[format] || REEL_FORMATS.short;
        setReelFormat(format in REEL_FORMATS ? format : 'short');
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/api/reel-studio/pricing?duration_seconds=${selectedFormat.duration}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.detail || 'Could not load reel pricing.');
            setCreditQuote(payload); setIsRecreating(recreating); setShowPlayer(false); setShowCreditConfirm(true);
        } catch (error) { showToast(error.message, 'error'); }
        finally { setLoading(false); }
    };
    const prepare = async () => {
        if (prepareLock.current || !creditQuote) return;
        prepareLock.current = true;
        setShowCreditConfirm(false);
        setJob(null); setJobStatus('preparing'); setJobError('');
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/reel-studio/drafts/from-answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                body: JSON.stringify({ message_id: messageId, duration_seconds: REEL_FORMATS[reelFormat].duration, language: REEL_SETTINGS.language, visual_level: REEL_SETTINGS.visualLevel }),
            });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.detail || 'Could not prepare this reel.');
            await queue(payload);
        } catch (error) {
            showToast(error.message || 'Could not prepare this reel.', 'error');
        } finally {
            prepareLock.current = false;
            setLoading(false);
        }
    };

    const recreate = () => {
        const priorDuration = Number(job?.settings?.duration_seconds);
        const format = priorDuration === REEL_FORMATS.deep.duration ? 'deep' : 'short';
        requestCreditConfirmation(format, true);
    };
    const queue = async (draft) => {
        if (!draft?.draft_id) throw new Error('Your reel could not be prepared. Please try again.');
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/reel-studio/jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                body: JSON.stringify({ message_id: messageId, duration_seconds: REEL_FORMATS[reelFormat].duration, language: REEL_SETTINGS.language, visual_level: REEL_SETTINGS.visualLevel, draft_id: draft.draft_id, approved_claim_ids: draft.claims.map((claim) => claim.id), confirmed_credit_cost: creditQuote.credit_cost }),
            });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.detail || 'Could not queue this reel.');
            setJob(payload);
            setJobStatus(payload.status || 'queued');
            window.dispatchEvent(new Event('creditUpdated'));
        } catch (error) { throw new Error(error.message || 'Could not create this reel.'); }
    };
    const download = async () => {
        if (!job?.job_id) return;
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/api/reel-studio/jobs/${encodeURIComponent(job.job_id)}/download`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
            if (!response.ok) throw new Error('The MP4 is not available yet.');
            const url = URL.createObjectURL(await response.blob());
            const link = document.createElement('a'); link.href = url; link.download = 'astroroshni-reel.mp4'; link.click(); URL.revokeObjectURL(url);
        } catch (error) { showToast(error.message || 'Could not download the reel.', 'error'); }
    };
    if (showBuyCredits) return <CreditsModal isOpen onClose={() => { setShowBuyCredits(false); requestCreditConfirmation(reelFormat, isRecreating); }} />;
    if (showCreditConfirm) return <ThemeModal isOpen onClose={() => setShowCreditConfirm(false)} size="sm" className="reel-credit-confirm"
        title={isRecreating ? `Recreate this ${REEL_FORMATS[reelFormat].label}?` : `Create your ${REEL_FORMATS[reelFormat].label}`}
        description={`${REEL_FORMATS[reelFormat].detail}. Credits are charged once creation begins. Replaying a saved reel is free.`}>
        <div className="reel-credit-summary">
            <span className="reel-credit-summary__label">{REEL_FORMATS[reelFormat].label} cost</span>
            <div className="reel-credit-price"><strong>{creditQuote.credit_cost}</strong><span>credits</span></div>
            <span className="reel-credit-summary__balance">Your balance: <b>{creditQuote.credits}</b> credits</span>
        </div>
        <div className="reel-credit-actions"><ThemeButton variant="secondary" onClick={() => setShowCreditConfirm(false)}>Not now</ThemeButton>
            <ThemeButton onClick={creditQuote.credits < creditQuote.credit_cost ? () => { setShowCreditConfirm(false); setShowBuyCredits(true); } : prepare}>
                {creditQuote.credits < creditQuote.credit_cost ? 'Buy credits' : 'Continue'}
            </ThemeButton></div>
    </ThemeModal>;
    if (showPlayer && job?.job_id) return <ReelPlayer jobId={job.job_id} onClose={() => setShowPlayer(false)} onRecreate={recreate} />;
    return createPortal(
        <div className="reel-studio-backdrop" role="presentation" onMouseDown={onClose}>
            <section className="reel-studio-modal" role="dialog" aria-modal="true" aria-labelledby="reel-studio-title" onMouseDown={(event) => event.stopPropagation()}>
                <button type="button" className="reel-studio-close" onClick={onClose} aria-label={job && !['completed', 'failed'].includes(jobStatus) ? 'Close and keep creating your reel' : 'Close Reel Studio'}>×</button>
                <div className="reel-studio-eyebrow">ASTROROSHNI · REEL STUDIO</div>
                <h2 id="reel-studio-title">Your personal reel</h2>
                <p className="reel-studio-intro">A polished visual reading shaped from your chart, timing and the guidance in this conversation.</p>

                {checkingCache ? <p role="status">Checking your saved reel…</p> : jobStatus === 'cache_error' ? <p role="alert">{jobError}</p> : (job || loading) ? <div className="reel-studio-job" aria-live="polite">
                    {jobStatus === 'failed' ? <><span>!</span><h3>We couldn’t finish your reel</h3><p>{jobError || 'Please try again. Your credits will be returned if creation did not complete.'}</p><button type="button" className="reel-studio-secondary" onClick={recreate}>Try again</button></> : <>
                    <span className={jobStatus === 'completed' ? 'is-complete' : ''}>{jobStatus === 'completed' ? '✓' : '◌'}</span>
                    <h3>{reelProgress(jobStatus, loading && !job).title}</h3>
                    <div className="reel-progress" role="progressbar" aria-valuenow={reelProgress(jobStatus, loading && !job).value} aria-valuemin="0" aria-valuemax="100"><i style={{ width: `${reelProgress(jobStatus, loading && !job).value}%` }} /></div>
                    <strong className="reel-progress-value">{reelProgress(jobStatus, loading && !job).value}%</strong>
                    <p>{reelProgress(jobStatus, loading && !job).detail}</p>
                    {jobStatus !== 'completed' && <><small className="reel-progress-note">This can take up to two minutes. It will keep creating in the background if you close this window.</small><button type="button" className="reel-studio-secondary reel-studio-keep-creating" onClick={onClose}>Close — keep creating</button></>}
                    {jobStatus === 'completed' ? <><button type="button" className="reel-studio-primary" onClick={() => setShowPlayer(true)}>Play saved reel</button><button type="button" className="reel-studio-secondary" onClick={download}>Download MP4</button><button type="button" className="reel-studio-secondary" onClick={recreate}>Recreate reel</button></> : null}
                </>}</div> : <>
                    <div className="reel-studio-privacy">◇ Your name and birth details stay private.</div>
                    <div className="reel-format-options">
                        {Object.entries(REEL_FORMATS).map(([key, format]) => <button type="button" key={key} className={`reel-format-option ${key === 'short' ? 'is-recommended' : ''}`} onClick={() => requestCreditConfirmation(key)} disabled={loading}>
                            <span>{key === 'short' ? 'Recommended' : 'More detail'}</span><strong>{format.label}</strong><small>{format.detail} · {formatQuotes[key]?.credit_cost ?? '…'} credits</small><p>{format.description}</p>
                        </button>)}
                    </div>
                </>}
            </section>
        </div>, document.body,
    );
}
