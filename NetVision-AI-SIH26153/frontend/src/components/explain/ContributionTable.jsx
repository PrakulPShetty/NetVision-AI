import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';
import Chip from '../common/Chip';

/**
 * Ranked attribution table.
 *
 * Feature → contribution → direction → importance, with the plain-language
 * meaning available on demand. The interpretation column explains the traffic
 * behaviour behind the number instead of leaving a raw SHAP value on screen.
 */
export default function ContributionTable({ contributions, limit }) {
  const rows = limit ? contributions.slice(0, limit) : contributions;

  return (
    <div className="contribution-table">
      <div className="ct-head">
        <span>Feature</span>
        <span>Aggregation</span>
        <span>Direction</span>
        <span>Importance</span>
        <span>Attribution</span>
      </div>

      {rows.map((row) => (
        <details className="ct-row" key={row.raw}>
          <summary>
            <span className="ct-feature">
              <strong>{row.label}</strong>
              <span className="ct-category">{row.category}</span>
            </span>
            <span className="ct-agg">
              <Chip tone="muted">{row.aggregationLabel || 'direct value'}</Chip>
            </span>
            <span className={`ct-direction ${row.direction}`}>
              {row.direction === 'raises' ? (
                <ArrowUpRight size={14} />
              ) : row.direction === 'lowers' ? (
                <ArrowDownRight size={14} />
              ) : (
                <Minus size={14} />
              )}
              {row.direction === 'raises' ? 'Raises' : row.direction === 'lowers' ? 'Lowers' : 'Neutral'}
            </span>
            <span className="ct-importance">
              <span className="importance-track">
                <span
                  className={`importance-fill ${row.direction}`}
                  style={{ width: `${Math.max(2, row.importance)}%` }}
                />
              </span>
              <span className="importance-value">{row.importance.toFixed(0)}%</span>
            </span>
            <span className={`ct-value ${row.direction}`}>
              {row.value > 0 ? '+' : ''}
              {row.value.toFixed(4)}
            </span>
          </summary>
          <div className="ct-detail">
            <p>{row.interpretation}</p>
            <p className="ct-raw">
              Model feature: <code>{row.raw}</code>
            </p>
          </div>
        </details>
      ))}
    </div>
  );
}
