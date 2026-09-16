/**
 * Layered content panel — the core surface of the application.
 *
 * `tone` controls the semantic accent (border + heading colour) and
 * `interactive` enables the subtle hover elevation used across the product.
 */
export default function Panel({
  as: Tag = 'section',
  eyebrow,
  title,
  titleAs: TitleTag = 'h3',
  aside,
  footer,
  tone = 'default',
  interactive = false,
  className = '',
  bodyClassName = '',
  children,
  ...rest
}) {
  return (
    <Tag className={`panel tone-${tone}${interactive ? ' interactive' : ''} ${className}`} {...rest}>
      {(eyebrow || title || aside) && (
        <header className="panel-head">
          <div className="panel-head-copy">
            {eyebrow && <p className="eyebrow">{eyebrow}</p>}
            {title && <TitleTag className="panel-title">{title}</TitleTag>}
          </div>
          {aside && <div className="panel-aside">{aside}</div>}
        </header>
      )}
      <div className={`panel-body ${bodyClassName}`}>{children}</div>
      {footer && <footer className="panel-foot">{footer}</footer>}
    </Tag>
  );
}
