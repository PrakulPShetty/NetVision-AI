/**
 * Neutral pre-analysis state.
 *
 * An empty state never pretends to hold data: it names what is missing, why,
 * and which action produces it.
 */
export default function EmptyState({ eyebrow, text, action, tone = 'default' }) {
  return (
    <div className={`empty-state tone-${tone}`}>
      <span className="empty-rule" aria-hidden="true" />
      <div className="empty-copy">
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <p className="empty-text">{text}</p>
        {action && <div className="empty-action">{action}</div>}
      </div>
    </div>
  );
}
