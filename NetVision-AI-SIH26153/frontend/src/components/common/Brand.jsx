import { useState } from 'react';

/**
 * NetVision AI brand lockup.
 *
 * The official artwork is dark ink on transparency, so it disappears on the
 * dark application surfaces. A light-on-dark treatment of the same artwork is
 * shipped in /public/brand and used on every dark surface — no boxed plate,
 * no recoloured guesswork at runtime.
 */

const ASSETS = {
  lockup: '/brand/netvision-lockup-light.png',
  mark: '/brand/netvision-mark-light.png',
};

export default function Brand({
  variant = 'lockup',
  height,
  subline = false,
  onClick,
  className = '',
  title = 'NetVision AI — home',
}) {
  const [failed, setFailed] = useState(false);
  const resolvedHeight = height ?? (variant === 'mark' ? 34 : 28);

  const content = (
    <>
      {failed ? (
        <span className="brand-fallback">NETVISION AI</span>
      ) : (
        <img
          className="brand-lockup"
          style={{ height: `${resolvedHeight}px` }}
          src={ASSETS[variant]}
          alt="NetVision AI"
          onError={() => setFailed(true)}
        />
      )}
      {subline && <span className="brand-sub">Predictive network security intelligence</span>}
    </>
  );

  if (!onClick) {
    return <span className={`brand ${className}`}>{content}</span>;
  }

  return (
    <button type="button" className={`brand ${className}`} onClick={onClick} title={title} aria-label={title}>
      {content}
    </button>
  );
}
