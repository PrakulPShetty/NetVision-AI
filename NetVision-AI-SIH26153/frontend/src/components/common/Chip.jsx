/**
 * Small semantic label used for evidence groups, feature tags and state tags.
 */
export default function Chip({ tone = 'muted', children, title, as: Tag = 'span' }) {
  return (
    <Tag className={`chip chip-${tone}`} title={title}>
      {children}
    </Tag>
  );
}
