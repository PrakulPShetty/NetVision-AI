import Panel from '../common/Panel';
import BarList from '../common/BarList';
import Chip from '../common/Chip';

/**
 * Current network state, as estimated by the ML ensemble.
 *
 * The probability is shown against the calibrated decision threshold used by
 * the backend, so the reader can see why the state was labelled the way it was
 * instead of a bare number.
 */
export default function CurrentStateCard({ ml, compact = false }) {
  const attack = ml.state === 'ATTACK';
  const tone = attack ? 'critical' : 'normal';

  return (
    <Panel
      eyebrow="Current state"
      title="Assessment of the observed window"
      tone={tone}
      aside={<Chip tone={attack ? 'critical' : 'normal'}>{attack ? 'Above decision threshold' : 'Below decision threshold'}</Chip>}
    >
      <div className="state-readout">
        <div className="state-primary">
          <p className={`state-value tone-${tone}`}>{ml.state}</p>
          <p className="state-caption">Ensemble state label · threshold {ml.threshold.toFixed(0)}%</p>
        </div>
        <div className="state-probability">
          <span className="state-probability-value">
            {ml.probability.toFixed(2)}
            <small>%</small>
          </span>
          <span className="state-probability-label">attack probability</span>
        </div>
      </div>

      <div className="threshold-track" role="img" aria-label={`Attack probability ${ml.probability.toFixed(2)} percent against a ${ml.threshold.toFixed(0)} percent threshold`}>
        <span className={`threshold-fill tone-${tone}`} style={{ width: `${Math.min(100, ml.probability)}%` }} />
        <span className="threshold-mark" style={{ left: `${ml.threshold}%` }}>
          <span className="threshold-label">threshold</span>
        </span>
      </div>

      <p className="threshold-note">
        Decision margin{' '}
        <strong className={ml.margin >= 0 ? 'positive' : 'negative'}>
          {ml.margin >= 0 ? '+' : ''}
          {ml.margin.toFixed(2)} percentage points
        </strong>{' '}
        relative to the calibrated threshold.
      </p>

      {!compact && (ml.xgb !== null || ml.rf !== null) && (
        <div className="profile-block">
          <p className="block-label">Ensemble components</p>
          <BarList
            max={100}
            items={[
              { id: 'xgb', label: 'XGBoost', value: ml.xgb ?? 0, display: ml.xgb === null ? '—' : `${ml.xgb.toFixed(2)}%`, tone: 'accent' },
              { id: 'rf', label: 'Random Forest (SMOTE)', value: ml.rf ?? 0, display: ml.rf === null ? '—' : `${ml.rf.toFixed(2)}%`, tone: 'default' },
              { id: 'ens', label: 'Soft-voting ensemble', value: ml.probability, display: `${ml.probability.toFixed(2)}%`, tone: 'alert' },
            ]}
          />
        </div>
      )}
    </Panel>
  );
}
