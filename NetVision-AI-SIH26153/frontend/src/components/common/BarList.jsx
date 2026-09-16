/**
 * Horizontal bar list.
 *
 * Used wherever a magnitude comparison is the point: SHAP attributions, TCP
 * flag distribution, directional splits. Bars are scaled against the largest
 * value in the list so the comparison stays honest within the current view.
 */
export default function BarList({ items, max, onSelect, activeId }) {
  const ceiling = max ?? Math.max(1, ...items.map((item) => Math.abs(item.value)));
  const label = (value) =>
    typeof value === 'number' ? value.toFixed(2).replace(/\.00$/, '') : (value ?? '—');

  return (
    <ul className="bar-list">
      {items.map((item) => {
        const width = Math.min(100, (Math.abs(item.value) / ceiling) * 100);
        const interactive = typeof onSelect === 'function';
        return (
          <li
            key={item.id ?? item.label}
            className={`bar-row${activeId && activeId === (item.id ?? item.label) ? ' active' : ''}`}
          >
            {interactive ? (
              <button
                type="button"
                className="bar-button"
                onClick={() => onSelect(item)}
                title={item.hint || item.label}
              >
                <BarBody item={item} width={width} label={label} />
              </button>
            ) : (
              <BarBody item={item} width={width} label={label} />
            )}
          </li>
        );
      })}
    </ul>
  );
}

function BarBody({ item, width, label }) {
  return (
    <>
      <span className="bar-label" title={item.hint || item.label}>
        {item.label}
        {item.tag && <em className="bar-tag">{item.tag}</em>}
      </span>
      <span className="bar-track">
        <span
          className={`bar-fill ${item.tone || 'default'}${item.value < 0 ? ' negative' : ''}`}
          style={{ width: `${width}%` }}
        />
      </span>
      <span className="bar-value">{item.display ?? label(item.value)}</span>
    </>
  );
}
