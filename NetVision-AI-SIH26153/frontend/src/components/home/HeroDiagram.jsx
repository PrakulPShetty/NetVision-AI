import { useEffect, useRef, useState } from 'react';

/**
 * Hero visual: the forecasting pipeline expressed as a layered stack.
 *
 * This is deliberately structural — it shows how data moves through the
 * system, not how it looks on any particular profile. No probabilities,
 * counts or statistics are rendered here, so nothing on the landing page can
 * be mistaken for model output. Depth comes from layering, offset shadows and
 * a small scroll parallax (disabled under prefers-reduced-motion).
 */

const LAYERS = [
  { id: 'traffic', label: 'Network traffic', note: '5-minute observation window' },
  { id: 'temporal', label: 'Temporal behaviour', note: 'engineered flow features' },
  { id: 'state', label: 'Current state', note: 'ensemble assessment' },
  { id: 'forecast', label: 'Future state', note: 'Markov horizon projection' },
  { id: 'context', label: 'XAI + ATT&CK', note: 'attribution and correlation' },
];

export default function HeroDiagram() {
  const ref = useRef(null);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (reduce) return undefined;

    let frame = 0;
    const update = () => {
      if (frame) return;
      frame = window.requestAnimationFrame(() => {
        frame = 0;
        const rect = ref.current?.getBoundingClientRect();
        if (!rect) return;
        const progress = Math.min(1, Math.max(0, (window.innerHeight - rect.top) / (window.innerHeight + rect.height)));
        setOffset((progress - 0.35) * 18);
      });
    };

    update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    return () => {
      window.removeEventListener('scroll', update);
      window.removeEventListener('resize', update);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div className="hero-visual" ref={ref}>
      <div className="hero-stack" style={{ transform: `translate3d(0, ${offset.toFixed(2)}px, 0)` }}>
        {LAYERS.map((layer, index) => (
          <div
            className="hero-layer"
            key={layer.id}
            style={{ '--depth': index, zIndex: LAYERS.length - index }}
          >
            <span className="hero-layer-index">{String(index + 1).padStart(2, '0')}</span>
            <span className="hero-layer-copy">
              <strong>{layer.label}</strong>
              <em>{layer.note}</em>
            </span>
          </div>
        ))}
      </div>
      <p className="hero-visual-note">
        Pipeline overview — structural view of how a traffic profile becomes a forecast. No model output is shown on this page.
      </p>
    </div>
  );
}
