import Chip from '../common/Chip';

/**
 * One correlated ATT&CK technique.
 *
 * A technique is only ever rendered with the evidence that produced it:
 * matched behavioural signal groups, their supporting model features, the
 * backend's interpretation and its explicit limitation. No technique is shown
 * merely because a traffic feature exists.
 */

const confidenceTone = (confidence) => {
  const value = String(confidence).toLowerCase();
  if (value.startsWith('high')) return 'critical';
  if (value.startsWith('medium')) return 'elevated';
  if (value.startsWith('low')) return 'muted';
  return 'neutral';
};

export default function TechniqueCard({ technique }) {
  return (
    <article className="technique-card">
      <header className="technique-head">
        <div className="technique-identity">
          <span className="technique-id">{technique.id}</span>
          <h3 className="technique-name">{technique.name}</h3>
        </div>
        <div className="technique-meta">
          <span className="technique-tactic">{technique.tactic} tactic</span>
          <Chip tone={confidenceTone(technique.confidence)}>
            {String(technique.confidence).toLowerCase().includes('confidence')
              ? technique.confidence
              : `${technique.confidence} confidence`}
          </Chip>
        </div>
      </header>

      <div className="technique-body">
        <div className="technique-block">
          <p className="block-label">Matched behavioural evidence</p>
          <ul className="evidence-list">
            {technique.evidence.map((item) => (
              <li key={item.group} className="evidence-item">
                <span className="evidence-group">{item.label}</span>
                {item.features.length > 0 && (
                  <span className="evidence-features">
                    {item.features.map((feature) => (
                      <Chip key={feature.raw} tone="muted" title={feature.meaning}>
                        {feature.label}
                      </Chip>
                    ))}
                  </span>
                )}
              </li>
            ))}
            {technique.evidence.length === 0 && (
              <li className="evidence-item">
                <span className="evidence-features">
                  {technique.features.map((feature) => (
                    <Chip key={feature.raw} tone="muted" title={feature.meaning}>
                      {feature.label}
                    </Chip>
                  ))}
                </span>
              </li>
            )}
          </ul>
        </div>

        {(technique.interpretation || technique.limitation) && (
          <div className="technique-notes">
            {technique.interpretation && (
              <div className="technique-note">
                <p className="block-label">Interpretation</p>
                <p>{technique.interpretation}</p>
              </div>
            )}
            {technique.limitation && (
              <div className="technique-note limitation">
                <p className="block-label">Scoping and limitation</p>
                <p>{technique.limitation}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </article>
  );
}
