import { useState } from 'react';

/**
 * NetVision AI brand lockup.
 *
 * Serves the ORIGINAL project artwork — `design-reference/branding/netvision updated logo.png`
 * copied byte-for-byte to /brand/netvision-logo.png. It is never recoloured or redrawn.
 * The artwork is dark ink designed for light backgrounds, so on the dark interface it
 * sits on a small light plate ("framed") that keeps it sharp, visible and high-contrast.
 */

const ART_SRC = '/brand/netvision-logo.png';
const ART_ASPECT = 1983 / 793; // intrinsic aspect ratio of the original artwork

export default function Brand({
  height = 30,
  framed = true,
  onClick,
  className = '',
  title = 'NetVision AI — home',
}) {
  const [failed, setFailed] = useState(false);

  const art = failed ? (
    <span className="brand-fallback">NETVISION AI</span>
  ) : (
    <img
      className="brand-art"
      style={{ height: `${height}px`, width: `${Math.round(height * ART_ASPECT)}px` }}
      src={ART_SRC}
      alt="NetVision AI"
      onError={() => setFailed(true)}
    />
  );

  const classes = `brand${framed ? ' framed' : ''}${className ? ` ${className}` : ''}`;

  if (!onClick) {
    return <span className={classes}>{art}</span>;
  }

  return (
    <button type="button" className={classes} onClick={onClick} title={title} aria-label={title}>
      {art}
    </button>
  );
}
