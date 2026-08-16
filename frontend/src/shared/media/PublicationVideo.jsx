import { useEffect, useRef } from "react";

import { createPublicationVideoLifecycle } from "./publicationVideoLifecycle";

export default function PublicationVideo({
  className,
  controls = false,
  detail = false,
  preload = "metadata",
  src,
}) {
  const videoRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return undefined;
    return createPublicationVideoLifecycle({ video, observeViewport: !detail });
  }, [detail, src]);

  return (
    <video
      ref={videoRef}
      src={src}
      muted
      loop
      playsInline
      controls={controls}
      preload={preload}
      className={className}
    />
  );
}
