import React, { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { showToast } from '../../utils/toast';
import './ReelStudioModal.css';

const LEVELS = [
    { id: 'none', title: 'Chart-led', note: 'Animated real kundali, dashas and voice', estimate: 'Lowest cost' },
    { id: 'hybrid', title: 'Studio', note: 'On-screen narrator, real chart and live-action B-roll', estimate: 'Recommended' },
    { id: 'cinematic', title: 'Premium', note: 'Narrator-led cinematic edit with chart and dasha inserts', estimate: 'Premium credits' },
];

export default function ReelStudioModal({ messageId, onClose }) {
    const [duration, setDuration] = useState(180);
    const [language, setLanguage] = useState('en');
    const [visualLevel, setVisualLevel] = useState('cinematic');
    const [draft, setDraft] = useState(null);
    const [loading, setLoading] = useState(false);
    const [approved, setApproved] = useState(false);
    const [queueing, setQueueing] = useState(false);
    const [job, setJob] = useState(null);
    const [jobStatus, setJobStatus] = useState('');
    const [jobError, setJobError] = useState('');
    const selectedLevel = useMemo(() => LEVELS.find((level) => level.id === visualLevel), [visualLevel]);

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
                setJobError(payload.error_message || '');
            } catch (_) { /* Retain the last state while a request is retried. */ }
        };
        poll();
        const timer = window.setInterval(poll, 4000);
        return () => { active = false; window.clearInterval(timer); };
    }, [job?.job_id, jobStatus]);

    const prepare = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/reel-studio/drafts/from-answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                body: JSON.stringify({ message_id: messageId, duration_seconds: duration, language, visual_level: visualLevel }),
            });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.detail || 'Could not prepare this reel.');
            setDraft(payload);
        } catch (error) {
            showToast(error.message || 'Could not prepare this reel.', 'error');
        } finally {
            setLoading(false);
        }
    };

    const cost = draft?.cost_projection?.estimated_total;
    const queue = async () => {
        // A plan prepared before server-side approved-plan persistence was
        // introduced cannot be safely queued: re-planning here would defeat
        // the evidence review and can produce a different script.
        if (!draft?.draft_id) {
            setApproved(false);
            setDraft(null);
            showToast('This storyboard was prepared by an older Reel Studio version. Please prepare a fresh storyboard before queuing.', 'error');
            return;
        }
        setQueueing(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/reel-studio/jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                body: JSON.stringify({ message_id: messageId, duration_seconds: duration, language, visual_level: visualLevel, draft_id: draft.draft_id, approved_claim_ids: draft.claims.map((claim) => claim.id) }),
            });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.detail || 'Could not queue this reel.');
            setJob(payload);
            setJobStatus(payload.status || 'queued');
            showToast(`Reel rendering · estimated production cost ₹${payload.cost_projection.estimated_total}`, 'success');
        } catch (error) {
            showToast(error.message || 'Could not queue this reel.', 'error');
        } finally { setQueueing(false); }
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
    return createPortal(
        <div className="reel-studio-backdrop" role="presentation" onMouseDown={onClose}>
            <section className="reel-studio-modal" role="dialog" aria-modal="true" aria-labelledby="reel-studio-title" onMouseDown={(event) => event.stopPropagation()}>
                <button type="button" className="reel-studio-close" onClick={onClose} aria-label="Close Reel Studio">×</button>
                <div className="reel-studio-eyebrow">ASTROROSHNI · REEL STUDIO</div>
                <h2 id="reel-studio-title">Turn this reading into a reel</h2>
                <p className="reel-studio-intro">A narrator-led edit: an animated astrologer portrait, your actual kundali and dasha periods, plus generated editorial stills. You approve the claims before anything renders.</p>

                {job ? <div className="reel-studio-job" aria-live="polite">
                    <span className={jobStatus === 'completed' ? 'is-complete' : ''}>{jobStatus === 'completed' ? '✓' : '◌'}</span>
                    <h3>{jobStatus === 'completed' ? 'Your reel is ready' : String(jobStatus || 'queued').replaceAll('_', ' ')}</h3>
                    <p>{jobStatus === 'completed' ? 'Your final vertical MP4 is ready to download or share.' : jobStatus === 'failed' ? (jobError || 'The reel could not be completed.') : 'Creating the animated presenter, chart and dasha inserts, editorial stills and final MP4…'}</p>
                    {jobStatus === 'completed' ? <button type="button" className="reel-studio-primary" onClick={download}>Download MP4</button> : null}
                </div> : !draft ? <>
                    <div className="reel-studio-field">
                        <span>Length</span>
                        <div className="reel-studio-segmented">
                            {[60, 120, 180].map((seconds) => <button type="button" key={seconds} className={duration === seconds ? 'is-selected' : ''} onClick={() => setDuration(seconds)}>{seconds < 60 ? `${seconds}s` : `${seconds / 60}m`}</button>)}
                        </div>
                    </div>
                    <div className="reel-studio-field">
                        <span>Voice language</span>
                        <div className="reel-studio-segmented">
                            <button type="button" className={language === 'en' ? 'is-selected' : ''} onClick={() => setLanguage('en')}>English</button>
                            <button type="button" className={language === 'hi' ? 'is-selected' : ''} onClick={() => setLanguage('hi')}>Hindi</button>
                        </div>
                    </div>
                    <div className="reel-studio-field"><span>Visual treatment</span></div>
                    <div className="reel-studio-levels">
                        {LEVELS.map((level) => <button type="button" key={level.id} onClick={() => setVisualLevel(level.id)} className={`reel-studio-level ${visualLevel === level.id ? 'is-selected' : ''}`}>
                            <strong>{level.title}</strong><small>{level.note}</small><em>{level.estimate}</em>
                        </button>)}
                    </div>
                    <div className="reel-studio-privacy">◇ Client name and birth details stay hidden by default.</div>
                    <button type="button" className="reel-studio-primary" onClick={prepare} disabled={loading}>{loading ? 'Building your storyboard…' : `Prepare ${selectedLevel.title} storyboard`}</button>
                </> : <>
                    <div className="reel-studio-ready"><span>✓</span><div><strong>Storyboard ready</strong><small>{draft.storyboard.length} scenes · ~{Math.ceil((draft.estimated_duration_seconds || duration) / 10) * 10}s · {language === 'hi' ? 'Hindi' : 'English'}</small></div><b>₹{cost}</b></div>
                    <div className="reel-studio-section-title">Evidence review</div>
                    <div className="reel-studio-claims">
                        {draft.claims.map((claim) => <div key={claim.id} className={`reel-studio-claim reel-studio-claim--${claim.status}`}><span>{claim.status === 'interpretation' ? '◇' : '◌'}</span><div><small>{claim.status === 'interpretation' ? 'Interpretation' : 'Needs chart validation'}</small><p>{claim.text}</p></div></div>)}
                    </div>
                    <div className="reel-studio-section-title">Scene plan</div>
                    <ol className="reel-studio-scenes">{draft.storyboard.map((scene) => <li key={scene.id}><b>{scene.type.replaceAll('_', ' ')}</b><span>{scene.start_seconds}s–{scene.end_seconds}s</span><p>{scene.narration}</p></li>)}</ol>
                    <label className="reel-studio-approve"><input type="checkbox" checked={approved} onChange={(event) => setApproved(event.target.checked)} /> I’ve reviewed the claims and approve this plan.</label>
                    <button type="button" className="reel-studio-primary" disabled={!approved || queueing} onClick={queue}>{queueing ? 'Queuing render…' : 'Approve & queue render'}</button>
                    <button type="button" className="reel-studio-secondary" onClick={() => setDraft(null)}>Adjust format</button>
                </>}
            </section>
        </div>, document.body,
    );
}
