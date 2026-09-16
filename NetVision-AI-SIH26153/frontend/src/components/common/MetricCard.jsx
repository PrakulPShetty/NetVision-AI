/**
 * Metric card with deliberate depth: layered surface, thin border and a small
 * hover elevation so dense metric grids stay readable but feel physical.
 */
export default function MetricCard({
  label,
  value,
  unit,
  note,
  tone = 'default',
  size = 'md',
  hint,
  children,
}) {
  return (
    <div className={`metric metric-${size} tone-${tone}`} title={hint}>
      <p className="metric-label">{label}</p>
      <p className="metric-value">
        {value}
        {unit && <small>{unit}</small>}
      </p>
      {note && <p className="metric-note">{note}</p>}
      {children}
    </div>
  );
}
