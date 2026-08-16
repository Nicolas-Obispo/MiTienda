export const PUBLICATION_VIDEO_VISIBILITY_THRESHOLD = 0.6;

let activePublicationVideo = null;

function pauseVideo(video) {
  video?.pause?.();
  if (activePublicationVideo === video) activePublicationVideo = null;
}
function playVideo(video) {
  if (!video) return;
  if (activePublicationVideo && activePublicationVideo !== video) {
    activePublicationVideo.pause?.();
  }
  activePublicationVideo = video;
  try {
    const playback = video.play?.();
    playback?.catch?.(() => {});
  } catch {
    // Safari y otros navegadores pueden rechazar play() sin interaccion.
  }
}

export function createPublicationVideoLifecycle({
  video,
  documentObject = globalThis.document,
  IntersectionObserverClass = globalThis.IntersectionObserver,
  observeViewport = true,
  threshold = PUBLICATION_VIDEO_VISIBILITY_THRESHOLD,
}) {
  let disposed = false;
  let sufficientlyVisible = !observeViewport;

  const syncPlayback = () => {
    if (disposed) return;
    if (!documentObject?.hidden && sufficientlyVisible) playVideo(video);
    else pauseVideo(video);
  };

  const handleVisibilityChange = () => syncPlayback();
  documentObject?.addEventListener?.("visibilitychange", handleVisibilityChange);

  let observer = null;
  if (observeViewport && typeof IntersectionObserverClass === "function") {
    observer = new IntersectionObserverClass((entries) => {
      const entry = entries.find(({ target }) => target === video);
      if (!entry) return;
      sufficientlyVisible = Boolean(entry.isIntersecting && entry.intersectionRatio >= threshold);
      syncPlayback();
    }, { threshold: [threshold] });
    observer.observe(video);
  } else if (observeViewport) {
    // Fallback seguro: sin observador, un video de listado no se reproduce solo.
    sufficientlyVisible = false;
    pauseVideo(video);
  } else {
    syncPlayback();
  }

  return () => {
    disposed = true;
    observer?.disconnect?.();
    documentObject?.removeEventListener?.("visibilitychange", handleVisibilityChange);
    pauseVideo(video);
  };
}
