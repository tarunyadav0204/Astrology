import React, { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import './ReelPlayer.css';

const clock = (seconds) => `${Math.floor((seconds || 0) / 60)}:${String(Math.floor((seconds || 0) % 60)).padStart(2, '0')}`;
const destinations = { Instagram: 'https://www.instagram.com/', Facebook: 'https://www.facebook.com/', YouTube: 'https://studio.youtube.com/' };
const headers = () => ({ Authorization: `Bearer ${localStorage.getItem('token') || ''}` });
const positionKey = (id) => `reel-position:${id}`;
const iconPaths = {
    share: 'M12 16V3m-5 5 5-5 5 5M5 13v7h14v-7',
    save: 'M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5',
    more: 'M5 12h.01M12 12h.01M19 12h.01',
    close: 'm6 6 12 12M6 18 18 6',
    play: 'm8 5 11 7-11 7Z',
    pause: 'M8 5v14M16 5v14',
};
const Icon = ({ name }) => <svg viewBox="0 0 24 24" aria-hidden="true" width="24" height="24" fill="none" stroke="currentColor" strokeWidth={name === 'more' ? 4 : 1.8} strokeLinecap="round" strokeLinejoin="round"><path d={iconPaths[name]} /></svg>;

export default function ReelPlayer({ jobId, onClose, onRecreate }) {
    const video = useRef(null), container = useRef(null), cache = useRef(new Map());
    const [activeId, setActiveId] = useState(jobId);
    const [library, setLibrary] = useState([]);
    const [media, setMedia] = useState(null), [cover, setCover] = useState(null);
    const [error, setError] = useState(''), [notice, setNotice] = useState('');
    const [playing, setPlaying] = useState(false), [ready, setReady] = useState(false);
    const [time, setTime] = useState(0), [duration, setDuration] = useState(0);
    const [controlsVisible, setControlsVisible] = useState(true), [menu, setMenu] = useState(null);
    const [offset, setOffset] = useState(0), [settling, setSettling] = useState(false);
    const hideTimer = useRef(null), swipeTimer = useRef(null), scrubbing = useRef(false), menuRef = useRef(null), pointer = useRef(null);
    const position = useRef({ id: activeId, time: 0, duration: 0 }), lastSaved = useRef(0);
    menuRef.current = menu;
    const index = library.findIndex((r) => r.job_id === activeId);
    const reel = library[index];
    const revealControls = useCallback(function reveal() {
        setControlsVisible(true);
        window.clearTimeout(hideTimer.current);
        hideTimer.current = window.setTimeout(() => {
            if (scrubbing.current || menuRef.current) reveal();
            else setControlsVisible(false);
        }, 3000);
    }, []);
    const remember = useCallback(() => {
        const p = position.current;
        try { localStorage.setItem(positionKey(p.id), String(p.duration && p.time >= p.duration - 1.5 ? 0 : p.time)); } catch (_) {}
    }, []);
    const prepare = useCallback((id) => {
        if (cache.current.has(id)) return cache.current.get(id);
        const promise = (async () => {
            const response = await fetch(`/api/reel-studio/jobs/${encodeURIComponent(id)}/download`, { headers: headers() });
            if (!response.ok) throw new Error('Could not load the saved reel.');
            const blob = await response.blob();
            return { url: URL.createObjectURL(blob), file: new File([blob], 'astroroshni-reel.mp4', { type: 'video/mp4' }) };
        })();
        cache.current.set(id, promise);
        promise.catch(() => { if (cache.current.get(id) === promise) cache.current.delete(id); });
        return promise;
    }, []);
    useEffect(() => { setActiveId(jobId); }, [jobId]);
    useEffect(() => {
        const controller = new AbortController();
        fetch('/api/reel-studio/history', { headers: headers(), signal: controller.signal }).then((r) => r.ok ? r.json() : null)
            .then((data) => { if (!controller.signal.aborted) setLibrary((data?.reels || []).filter((r) => r.status === 'completed')); }).catch(() => {});
        const previousOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        const entries = cache.current;
        return () => {
            controller.abort(); remember();
            window.clearTimeout(hideTimer.current); window.clearTimeout(swipeTimer.current);
            for (const item of entries.values()) item.then((m) => URL.revokeObjectURL(m.url)).catch(() => {});
            entries.clear(); document.body.style.overflow = previousOverflow;
        };
    }, [remember]);
    useEffect(() => {
        let active = true, coverUrl;
        const controller = new AbortController();
        setMedia(null); setCover(null); setReady(false); setError(''); setNotice(''); setMenu(null);
        setTime(0); setDuration(0); setOffset(0); setSettling(false);
        position.current = { id: activeId, time: 0, duration: 0 };
        revealControls();
        prepare(activeId).then((value) => { if (active) setMedia(value); }).catch((err) => { if (active) setError(err.message); });
        fetch(`/api/reel-studio/jobs/${encodeURIComponent(activeId)}/thumbnail`, { headers: headers(), signal: controller.signal })
            .then((r) => r.ok ? r.blob() : null).then((blob) => {
                if (blob && active) { coverUrl = URL.createObjectURL(blob); setCover(coverUrl); }
            }).catch(() => {});
        return () => { active = false; controller.abort(); if (coverUrl) URL.revokeObjectURL(coverUrl); };
    }, [activeId, prepare, revealControls]);
    useEffect(() => {
        if (!media) return;
        const next = library[index + 1]?.job_id;
        const keep = [activeId, library[index - 1]?.job_id, next];
        for (const [id, item] of cache.current) if (!keep.includes(id)) {
            cache.current.delete(id); item.then((m) => URL.revokeObjectURL(m.url)).catch(() => {});
        }
        if (index >= 0 && next) prepare(next).catch(() => {});
    }, [activeId, index, library, media, prepare]);
    const move = useCallback((direction) => {
        const next = library[index + direction];
        if (!next || settling) { setOffset(0); return; }
        remember(); video.current?.pause();
        setSettling(true); setOffset(-direction * window.innerHeight);
        swipeTimer.current = window.setTimeout(() => setActiveId(next.job_id), 180);
    }, [index, library, remember, settling]);
    const toggle = useCallback(() => {
        const node = video.current;
        if (!node || !media) return;
        if (!node.paused) node.pause();
        else node.play().catch(() => setError('Tap play again to start playback.'));
        revealControls();
    }, [media, revealControls]);
    useEffect(() => {
        const key = (event) => {
            if (event.target.closest('input,button')) return;
            revealControls();
            if (event.key === 'Escape' && !document.fullscreenElement) onClose();
            if (event.key === 'ArrowDown') { event.preventDefault(); move(1); }
            if (event.key === 'ArrowUp') { event.preventDefault(); move(-1); }
            if (event.code === 'Space') { event.preventDefault(); toggle(); }
        };
        const hidden = () => { if (document.hidden) { remember(); video.current?.pause(); } };
        window.addEventListener('keydown', key); document.addEventListener('visibilitychange', hidden);
        return () => { window.removeEventListener('keydown', key); document.removeEventListener('visibilitychange', hidden); };
    }, [move, onClose, remember, revealControls, toggle]);
    const download = () => {
        if (!media) return;
        const link = document.createElement('a');
        link.href = media.url; link.download = media.file.name; link.click();
    };
    const share = async (destination) => {
        if (!media) return;
        setMenu(null); video.current?.pause();
        try {
            if (navigator.canShare?.({ files: [media.file] }) && navigator.share) {
                if (destination) setNotice(`Choose ${destination} in the share sheet to continue publishing.`);
                await navigator.share({ files: [media.file], title: 'AstroRoshni reel' });
            } else {
                download();
                if (destination) window.open(destinations[destination], '_blank', 'noopener,noreferrer');
                setNotice(destination ? `MP4 downloaded. Select it in ${destination} to finish uploading.` : 'MP4 downloaded. You can share the saved file.');
            }
        } catch (err) { if (err.name !== 'AbortError') setError('Could not share this reel. Try saving the MP4.'); }
        revealControls();
    };
    const close = async () => {
        remember(); video.current?.pause();
        if (document.fullscreenElement === container.current) await document.exitFullscreen().catch(() => {});
        onClose();
    };
    const railButton = (name, label, action) => <button disabled={!media} onClick={action}><Icon name={name} /><span>{label}</span></button>;
    return createPortal(<div className="reel-player" ref={container} role="dialog" aria-modal="true" aria-label="Reel player" tabIndex={-1}
        data-controls-visible={controlsVisible || !!error} onMouseMove={revealControls} onPointerDown={revealControls} onFocus={revealControls}>
        <div className="reel-player-scene" style={{ transform: `translateY(${offset}px)`, transition: settling ? 'transform 180ms ease-out' : 'none' }}>
            {cover && <img className="reel-player-backdrop" src={cover} alt="" />}
            <video key={activeId} ref={video} src={media?.url} className="reel-player-video" playsInline autoPlay
                onLoadedMetadata={(e) => {
                    const length = e.currentTarget.duration; setDuration(length); position.current.duration = length;
                    let saved = 0; try { saved = Number(localStorage.getItem(positionKey(activeId))) || 0; } catch (_) {}
                    if (saved > 0 && saved < length - 1.5) e.currentTarget.currentTime = saved;
                }}
                onTimeUpdate={(e) => {
                    setTime(e.currentTarget.currentTime); position.current.time = e.currentTarget.currentTime;
                    if (Date.now() - lastSaved.current > 5000) { remember(); lastSaved.current = Date.now(); }
                }}
                onCanPlay={() => setReady(true)} onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} onEnded={() => { setPlaying(false); remember(); revealControls(); }}
                onError={() => { if (media) setError('This reel could not be played. Try saving the MP4.'); }} />
            {!ready && cover && <img className="reel-player-poster" src={cover} alt="" />}
        </div>
        <div className="reel-player-gesture" onPointerDown={(e) => { pointer.current = { y: e.clientY, x: e.clientX }; e.currentTarget.setPointerCapture(e.pointerId); }}
            onPointerMove={(e) => {
                if (!pointer.current || settling) return;
                const dy = e.clientY - pointer.current.y, dx = e.clientX - pointer.current.x;
                if (Math.abs(dy) > Math.abs(dx) * 1.25) setOffset(library[index + (dy < 0 ? 1 : -1)] ? dy : dy * 0.15);
            }}
            onPointerUp={(e) => {
                if (!pointer.current) return;
                const dy = e.clientY - pointer.current.y, dx = e.clientX - pointer.current.x; pointer.current = null;
                if (Math.abs(dy) > 72 && Math.abs(dy) > Math.abs(dx) * 1.25) move(dy < 0 ? 1 : -1);
                else { setOffset(0); revealControls(); }
            }} onPointerCancel={() => { pointer.current = null; setOffset(0); }} />
        <div className="reel-player-top reel-player-overlay"><span><img src="/images/astroroshni-icon.png" alt="" />AstroRoshni</span>
            {index >= 0 && <small>{index + 1} / {library.length}</small>}
            <button onClick={close} aria-label="Close reel player"><Icon name="close" /></button></div>
        {!ready && !error && <p className="reel-player-loading" role="status">Opening saved reel…</p>}
        {ready && <button className="reel-player-center reel-player-overlay" onClick={toggle} aria-label={playing ? 'Pause' : 'Play'}><Icon name={playing ? 'pause' : 'play'} /></button>}
        <div className="reel-player-rail reel-player-overlay">
            {railButton('share', 'Share', () => setMenu('share'))}
            {railButton('save', 'Save', download)}
            {railButton('more', 'More', () => setMenu('more'))}
        </div>
        <div className="reel-player-controls reel-player-overlay">
            {reel?.question && <p className="reel-player-question">{reel.question}</p>}
            {(error || notice) && <p role="status">{error || notice}</p>}
            <input type="range" aria-label="Reel timeline" min="0" max={duration || 0} step="0.1" value={time}
                onPointerDown={() => { scrubbing.current = true; }} onPointerUp={() => { scrubbing.current = false; revealControls(); }}
                onPointerCancel={() => { scrubbing.current = false; }} onBlur={() => { scrubbing.current = false; }}
                disabled={!duration} onChange={(e) => { const value = Number(e.target.value); video.current.currentTime = value; setTime(value); }} />
            <span className="reel-player-time">{clock(time)} / {clock(duration)}</span>
        </div>
        {!controlsVisible && <div className="reel-player-passive"><i style={{ width: `${duration ? time / duration * 100 : 0}%` }} /></div>}
        {menu && <div className="reel-player-menu-backdrop" onClick={() => setMenu(null)}>
            <div className="reel-player-menu" role="dialog" aria-label={menu === 'share' ? 'Share reel' : 'Reel options'} onClick={(e) => e.stopPropagation()}>
                <h3>{menu === 'share' ? 'Share reel' : 'Reel options'}</h3>
                {menu === 'share' ? <>
                    <button onClick={() => share()}>Share with another app</button>
                    {Object.keys(destinations).map((name) => <button key={name} onClick={() => share(name)}>{name}</button>)}
                </> : <>
                    <button onClick={() => { video.current.currentTime = 0; setMenu(null); }}>Play from beginning</button>
                    {document.fullscreenEnabled && <button onClick={() => { container.current.requestFullscreen().catch(() => setNotice('Full-screen mode is unavailable.')); setMenu(null); }}>Full screen</button>}
                    {activeId === jobId && onRecreate && <button onClick={() => { remember(); video.current?.pause(); onRecreate(); }}>Recreate</button>}
                </>}
                <button onClick={() => setMenu(null)}>Close</button>
            </div>
        </div>}
    </div>, document.body);
}
