/** Shared podcast audio: only one clip should play at a time across chat bubbles. */

let activeAudio = null;
let activeBlobUrl = null;

export function stopAndRevokePodcastPlayback() {
    if (activeAudio) {
        try {
            activeAudio.pause();
            activeAudio.src = '';
        } catch (_) {}
        activeAudio = null;
    }
    if (activeBlobUrl) {
        try {
            URL.revokeObjectURL(activeBlobUrl);
        } catch (_) {}
        activeBlobUrl = null;
    }
}

/** Stops any other clip, then tracks this one for global teardown. */
export function registerPodcastPlayback(audioEl, blobUrl) {
    stopAndRevokePodcastPlayback();
    activeAudio = audioEl;
    activeBlobUrl = blobUrl;
}

export function base64ToAudioBlob(base64, mime = 'audio/mpeg') {
    const binary = atob(base64);
    const len = binary.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return new Blob([bytes], { type: mime });
}

export function podcastLangFromUiLanguage(language) {
    const l = (language || 'english').toLowerCase();
    return l.startsWith('hi') ? 'hi' : 'en';
}
