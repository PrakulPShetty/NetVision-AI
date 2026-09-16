/**
 * Page header used by every route so the information hierarchy stays identical
 * across the product: eyebrow → title → description → optional actions.
 */
export default function PageIntro({ eyebrow, title, description, actions, aside, className = '' }) {
  return (
    <header className={`page-intro ${aside ? 'split-intro' : ''} ${className}`}>
      <div className="page-intro-copy">
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1 className="page-title">{title}</h1>
        {description && <p className="page-description">{description}</p>}
        {actions && <div className="page-actions">{actions}</div>}
      </div>
      {aside && <div className="page-intro-aside">{aside}</div>}
    </header>
  );
}
