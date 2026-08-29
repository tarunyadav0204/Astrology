import React, { useEffect, useMemo, useState } from 'react';
import './PodcastGenerationExperience.css';

const STAGES = [
    { after: 0, icon: '◇', label: 'Reading your consultation' },
    { after: 25, icon: '✎', label: 'Shaping it into a natural conversation' },
    { after: 65, icon: '◉', label: 'Preparing Ananya and Arjun' },
    { after: 110, icon: '♬', label: 'Creating the voices' },
    { after: 165, icon: '≋', label: 'Mixing your podcast' },
    { after: 220, icon: '✦', label: 'Adding the finishing touches' },
    { after: 300, icon: '◷', label: 'Still working — your podcast is safe' },
];

const formatElapsed = (seconds) => (
    `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
);

export default function PodcastGenerationExperience({ startedAt, onCancel }) {
    const [elapsedSeconds, setElapsedSeconds] = useState(() => (
        Math.max(0, Math.floor((Date.now() - startedAt) / 1000))
    ));

    useEffect(() => {
        const update = () => setElapsedSeconds(Math.max(0, Math.floor((Date.now() - startedAt) / 1000)));
        update();
        const timer = window.setInterval(update, 1000);
        return () => window.clearInterval(timer);
    }, [startedAt]);

    const stageIndex = useMemo(() => STAGES.reduce(
        (selected, stage, index) => (elapsedSeconds >= stage.after ? index : selected),
        0,
    ), [elapsedSeconds]);
    const stage = STAGES[stageIndex];

    return (
        <section className="podcast-generation-studio" role="status" aria-live="polite">
            <div className="podcast-generation-eyebrow">ASTROROSHNI PODCAST STUDIO</div>
            <div className="podcast-generation-hosts" aria-hidden="true">
                <div className="podcast-generation-host podcast-generation-host--ananya">A</div>
                <div className="podcast-generation-wave">
                    {[0, 1, 2, 3, 4].map((bar) => <i key={bar} style={{ '--bar': bar }} />)}
                </div>
                <div className="podcast-generation-host podcast-generation-host--arjun">A</div>
            </div>
            <div className="podcast-generation-host-labels" aria-hidden="true">
                <span>ANANYA</span><span>ARJUN</span>
            </div>
            <h3>Creating your podcast</h3>
            <div className="podcast-generation-status">
                <span className="podcast-generation-status-icon" aria-hidden="true">{stage.icon}</span>
                <span className="podcast-generation-status-copy">
                    <strong>{stage.label}</strong>
                    <small>Creation steps may overlap</small>
                </span>
                <time>{formatElapsed(elapsedSeconds)}</time>
            </div>
            <div className="podcast-generation-stages" aria-hidden="true">
                {STAGES.slice(0, 6).map((item, index) => (
                    <i
                        key={item.label}
                        className={`${index <= Math.min(stageIndex, 5) ? 'is-reached' : ''} ${index === Math.min(stageIndex, 5) ? 'is-current' : ''}`}
                    />
                ))}
            </div>
            <p>
                {elapsedSeconds < 300
                    ? 'Usually ready in 3–4 minutes. Playback will begin automatically when it is ready.'
                    : 'Longer readings can take a little more time. No action is needed.'}
            </p>
            <div className="podcast-generation-note">
                Keep this window open while the podcast is created.
            </div>
            <button type="button" className="podcast-generation-cancel" onClick={onCancel}>
                Cancel generation
            </button>
        </section>
    );
}
