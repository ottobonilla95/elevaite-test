import type { JSX } from "react";

export function VideoPanel(): JSX.Element {
  return (
    <div className="right-panel">
      <video className="arrows-video" autoPlay loop muted playsInline>
        <source src="/arrows.mp4" type="video/mp4" />
      </video>
    </div>
  );
}
