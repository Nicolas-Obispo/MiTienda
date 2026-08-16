const STORY_VIDEO_EXTENSIONS = new Set([".mov", ".mp4", ".webm", ".ogg"]);
const STORY_IMAGE_EXTENSIONS = new Set([
  ".avif",
  ".bmp",
  ".gif",
  ".jpeg",
  ".jpg",
  ".png",
  ".svg",
  ".webp",
]);

function getMediaExtension(url) {
  if (!url || typeof url !== "string") return "";

  const pathname = url.split(/[?#]/, 1)[0].toLowerCase();
  const dotIndex = pathname.lastIndexOf(".");
  return dotIndex >= 0 ? pathname.slice(dotIndex) : "";
}

export function isStoryVideoUrl(url) {
  return STORY_VIDEO_EXTENSIONS.has(getMediaExtension(url));
}

export function isStoryImageUrl(url) {
  return STORY_IMAGE_EXTENSIONS.has(getMediaExtension(url));
}

export function collectStoryImageUrls(historias, getMediaUrl, max = 10) {
  if (!Array.isArray(historias) || typeof getMediaUrl !== "function") return [];

  const urls = [];
  for (const historia of historias) {
    const url = getMediaUrl(historia);
    if (!isStoryImageUrl(url)) continue;

    urls.push(url);
    if (urls.length >= max) break;
  }

  return urls;
}

export function pauseStoryVideo(video) {
  if (!video || typeof video.pause !== "function") return;
  video.pause();
}

export function playStoryVideo(video, documentObject = globalThis.document) {
  if (!video || typeof video.play !== "function" || documentObject?.hidden) {
    return Promise.resolve(false);
  }

  try {
    const playResult = video.play();
    return Promise.resolve(playResult).then(
      () => true,
      () => false
    );
  } catch {
    // Safari puede rechazar play() sin gesto aun cuando el video sea muted.
    return Promise.resolve(false);
  }
}
