// Native scroll/layout callbacks can run during React commits. Publish only
// changed button visibility, on a later frame, to avoid a scroll/render loop.
export function createChatJumpControlScheduler(publish, schedule, cancel) {
    let current = { showTop: false, showBottom: false };
    let pending = current;
    let frame = null;
    return {
        update(next) {
            pending = next;
            if (frame !== null || (current.showTop === next.showTop && current.showBottom === next.showBottom)) return;
            frame = schedule(() => {
                frame = null;
                if (current.showTop === pending.showTop && current.showBottom === pending.showBottom) return;
                current = pending;
                publish(current);
            });
        },
        dispose() {
            if (frame !== null) cancel(frame);
            frame = null;
        },
    };
}
