import React, { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import './ReelPlayer.css';

const clock = (seconds) => `${Math.floor((seconds || 0) / 60)}:${String(Math.floor((seconds || 0) % 60)).padStart(2, '0')}`;
const destinations = { Instagram: 'https://www.instagram.com/', Facebook: 'https://www.facebook.com/', YouTube: 'https://studio.youtube.com/' };

export default function ReelPlayer({ jobId, onClose, onRecreate }) {
    const video = useRef(null);
    const container = useRef(null);
    const [media, setMedia] = useState(null);
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');
    const [playing, setPlaying] = useState(false);
    const [time, setTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [controlsVisible, setControlsVisible] = useState(true);
    const hideTimer = useRef(null);
    const scrubbing = useRef(false);
    const revealControls = useCallback(function reveal() {
        setControlsVisible(true);
        window.clearTimeout(hideTimer.current);
        hideTimer.current = window.setTimeout(() => {
            if (scrubbing.current) reveal();
            else setControlsVisible(false);
        }, 3000);
    }, []);
    useEffect(() => {
        revealControls();
        return () => window.clearTimeout(hideTimer.current);
    }, [revealControls]);
    useEffect(() => { if (media) revealControls(); }, [media, revealControls]);
    useEffect(() => {
        const controller = new AbortController();
        let url;
        const previousOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        const load = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await fetch(`/api/reel-studio/jobs/${encodeURIComponent(jobId)}/download`, {
                    signal: controller.signal, headers: token ? { Authorization: `Bearer ${token}` } : {},
                });
                if (!response.ok) throw new Error('Could not load the saved reel.');
                const blob = await response.blob();
                if (controller.signal.aborted) return;
                url = URL.createObjectURL(blob);
                setMedia({ url, file: new File([blob], 'astroroshni-reel.mp4', { type: 'video/mp4' }) });
            } catch (err) { if (err.name !== 'AbortError') setError(err.message); }
        };
        load();
        return () => { controller.abort(); if (url) URL.revokeObjectURL(url); document.body.style.overflow = previousOverflow; };
    }, [jobId]);

    const download = () => {
        const link = document.createElement('a');
        link.href = media.url; link.download = media.file.name; link.click();
    };
    const share = async (destination) => {
        video.current?.pause();
        try {
            if (navigator.canShare?.({ files: [media.file] }) && navigator.share) {
                if (destination) setNotice(`Choose ${destination} in the share sheet to continue publishing.`);
                await navigator.share({ files: [media.file], title: 'AstroRoshni reel' });
            } else {
                download();
                if (destination) {
                    window.open(destinations[destination], '_blank', 'noopener,noreferrer');
                    setNotice(`MP4 downloaded. Select it in ${destination} to finish uploading.`);
                } else setNotice('MP4 downloaded. You can share the saved file.');
            }
        } catch (err) { if (err.name !== 'AbortError') setError('Could not share this reel. Try downloading the MP4.'); }
    };
    const stop = () => { video.current?.pause(); if (video.current) video.current.currentTime = 0; setTime(0); };
    const close = async () => {
        stop();
        if (document.fullscreenElement === container.current) await document.exitFullscreen().catch(() => {});
        onClose();
    };
    useEffect(() => {
        const key = (event) => { revealControls(); if (event.key === 'Escape' && !document.fullscreenElement) onClose(); };
        window.addEventListener('keydown', key);
        return () => window.removeEventListener('keydown', key);
    }, [onClose, revealControls]);
    return createPortal(<div className="reel-player" ref={container} role="dialog" aria-modal="true" aria-label="Reel player"
        data-controls-visible={controlsVisible} onMouseMove={revealControls} onPointerDown={revealControls} onFocus={revealControls}
        onPointerUp={() => { scrubbing.current = false; revealControls(); }} onPointerCancel={() => { scrubbing.current = false; revealControls(); }}>
        <video ref={video} src={media?.url} className="reel-player-video" playsInline autoPlay
            onTimeUpdate={(event) => setTime(event.target.currentTime)} onLoadedMetadata={(event) => setDuration(event.target.duration)}
            onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} onEnded={() => setPlaying(false)}
            onError={() => setError('This reel could not be played. Try downloading the MP4.')} />
        <div className="reel-player-top"><span>AstroRoshni</span><div>
            {document.fullscreenEnabled && <button onClick={() => container.current.requestFullscreen().catch(() => setNotice('Full-screen mode is unavailable in this browser.'))}>Full screen</button>}
            <button onClick={close} aria-label="Close reel player">×</button></div></div>
        {!media && !error && <p className="reel-player-loading" role="status">Opening saved reel…</p>}
        <div className="reel-player-controls">
            {(error || notice) && <p role="status">{error || notice}</p>}
            <input type="range" aria-label="Reel timeline" min="0" max={duration || 0} step="0.1" value={time}
                onPointerDown={() => { scrubbing.current = true; revealControls(); }}
                disabled={!duration} onChange={(event) => { const value = Number(event.target.value); video.current.currentTime = value; setTime(value); }} />
            <div className="reel-player-actions">
                <button disabled={!media} onClick={() => { if (playing) video.current.pause(); else video.current.play().catch(() => setError('Tap play again to start playback.')); }}>{playing ? 'Pause' : 'Play'}</button>
                <button disabled={!media} onClick={stop}>Stop</button><span>{clock(time)} / {clock(duration)}</span>
                <button disabled={!media} onClick={() => share()}>Share</button><button disabled={!media} onClick={download}>Download</button>
                <button onClick={() => { stop(); onRecreate(); }}>Recreate</button>
            </div>
            <div className="reel-player-social" aria-label="Upload reel">{Object.keys(destinations).map((destination) =>
                <button key={destination} disabled={!media} onClick={() => share(destination)}>{destination}</button>)}</div>
        </div>
    </div>, document.body);
}
