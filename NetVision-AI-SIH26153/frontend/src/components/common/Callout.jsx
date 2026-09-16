/**
 * Contextual note block: methodology notes, scoping statements and limitations.
 * Never used for decorative emphasis.
 */
export default function Callout({ tone = 'note', title, children }) {
  return (
    <div className={`callout callout-${tone}`}>
      {title && <p className="callout-title">{title}</p>}
      <div className="callout-body">{children}</div>
    </div>
  );
}
