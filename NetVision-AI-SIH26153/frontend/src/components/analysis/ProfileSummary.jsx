import Panel from '../common/Panel';
import BarList from '../common/BarList';
import EmptyState from '../common/EmptyState';
import { formatCompact } from '../../utils/trafficFields';

/**
 * Live description of the profile currently entered in the form.
 *
 * Everything shown here is arithmetic on the analyst's own input (totals,
 * directional split, flag distribution, derived ratios). It is explicitly not
 * model output, and it is labelled as such so it can never be mistaken for a
 * prediction.
 */

const pct = (value) => `${value.toFixed(1)}%`;

export default function ProfileSummary({ profile, compact = false }) {
  if (!profile) {
    return (
      <Panel eyebrow="Profile preview" title="Nothing entered yet">
        <EmptyState
          text="As soon as you enter values (or load a demo scenario) this panel summarizes the observation window you are about to submit. It describes your input only — the model's assessment appears after analysis."
        />
      </Panel>
    );
  }

  const flagItems = profile.flags
    .filter((flag) => flag.value > 0)
    .map((flag) => ({
      id: flag.key,
      label: flag.label,
      value: flag.value,
      display: formatCompact(flag.value),
      tone: flag.key === 'syn_flag_cnt' || flag.key === 'rst_flag_cnt' ? 'alert' : 'default',
      tag: profile.flows > 0 ? `${((flag.value / profile.flows) * 100).toFixed(0)}% of flows` : undefined,
    }));

  return (
    <Panel
      eyebrow="Profile preview"
      title="Observation window summary"
      aside={<span className="panel-note">Derived from your input only</span>}
    >
      <DL
        rows={[
          ['Flows', formatCompact(profile.flows)],
          ['Destination ports', formatCompact(profile.ports)],
          ['Protocols', formatCompact(profile.protocols)],
          ['Total packets', formatCompact(profile.totalPackets)],
          ['Total bytes', formatCompact(profile.totalBytes)],
          ['Average packet size', `${profile.avgPacketSize.toFixed(0)} B`],
        ]}
      />

      <div className="profile-split">
        <div className="split-head">
          <span>Forward {pct(profile.packetsSplit)}</span>
          <span>Backward {pct(100 - profile.packetsSplit)}</span>
        </div>
        <div className="split-bar" role="img" aria-label={`Forward packets ${pct(profile.packetsSplit)} of the window`}>
          <span className="split-fill forward" style={{ width: `${profile.packetsSplit}%` }} />
          <span className="split-fill backward" style={{ width: `${100 - profile.packetsSplit}%` }} />
        </div>
        <p className="split-note">
          Packet direction balance · ports per flow {(profile.portsPerFlow * 100).toFixed(1)}%
        </p>
      </div>

      {!compact && flagItems.length > 0 && (
        <div className="profile-block">
          <p className="block-label">TCP flag distribution</p>
          <BarList items={flagItems} />
        </div>
      )}

      <div className="profile-block">
        <p className="block-label">What stands out in these totals</p>
        <ul className="observation-list">
          {profile.observations.map((observation, index) => (
            <li key={index} className={`observation tone-${observation.tone}`}>
              <span className="observation-dot" aria-hidden="true" />
              <span>{observation.text}</span>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}

function DL({ rows }) {
  return (
    <dl className="dl">
      {rows.map(([term, value]) => (
        <div className="dl-row" key={term}>
          <dt>{term}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
