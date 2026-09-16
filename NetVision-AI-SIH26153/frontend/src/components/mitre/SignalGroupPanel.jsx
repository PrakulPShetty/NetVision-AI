import Panel from '../common/Panel';
import Chip from '../common/Chip';

/**
 * Behavioural signal groups evaluated by the backend mapper.
 *
 * This is the audit trail for the ATT&CK page: it shows which behavioural
 * groups were present in the analysed window and which features activated them,
 * whether or not a technique was finally returned.
 */
export default function SignalGroupPanel({ groups }) {
  const activeCount = groups.filter((group) => group.active).length;

  return (
    <Panel
      eyebrow="Evidence evaluation"
      title="Behavioural signal groups"
      aside={
        <span className="panel-note">
          {activeCount}/{groups.length} present in this window
        </span>
      }
    >
      <ul className="signal-grid">
        {groups.map((group) => (
          <li key={group.name} className={`signal-item${group.active ? ' active' : ''}`}>
            <div className="signal-head">
              <span className="signal-name">{group.label}</span>
              <Chip tone={group.active ? 'normal' : 'muted'}>{group.active ? 'Present' : 'Not present'}</Chip>
            </div>
            {group.features.length > 0 ? (
              <div className="signal-features">
                {group.features.map((feature) => (
                  <Chip key={feature.raw} tone="muted" title={feature.meaning}>
                    {feature.label}
                  </Chip>
                ))}
              </div>
            ) : (
              <p className="signal-empty">No supporting feature exceeded its configured evidence threshold.</p>
            )}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
