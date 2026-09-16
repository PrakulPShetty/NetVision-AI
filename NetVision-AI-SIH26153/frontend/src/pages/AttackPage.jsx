import { ArrowRight, ShieldCheck } from 'lucide-react';
import PageIntro from '../components/common/PageIntro';
import Panel from '../components/common/Panel';
import Callout from '../components/common/Callout';
import EmptyState from '../components/common/EmptyState';
import Chip from '../components/common/Chip';
import TechniqueCard from '../components/mitre/TechniqueCard';
import SignalGroupPanel from '../components/mitre/SignalGroupPanel';

/**
 * ATT&CK — evidence-based behavioural correlation.
 *
 * Correlation is only attempted when a profile has actually been analysed, and
 * a technique is only shown together with the behavioural groups that matched
 * the backend's decision rules.
 */
export default function AttackPage({ status, result, onGo }) {
  if (status !== 'complete' || !result) {
    return (
      <div className="page">
        <PageIntro
          eyebrow="Behavioural context"
          title="MITRE ATT&amp;CK correlation"
          description="NetVision AI correlates observed traffic behaviour with MITRE ATT&CK techniques when — and only when — the configured evidence rules are satisfied."
        />
        <EmptyState
          eyebrow="No correlation to display"
          text="ATT&CK correlation becomes available after traffic analysis. A technique is never mapped merely because a feature exists: the mapper requires a minimum set of behavioural signal groups before it returns one."
          action={
            <button type="button" className="button primary" onClick={() => onGo('/analyze')}>
              Analyze a traffic profile <ArrowRight size={15} />
            </button>
          }
        />
      </div>
    );
  }

  const { mitre, ml } = result;

  return (
    <div className="page">
      <PageIntro
        eyebrow="Behavioural context"
        title="MITRE ATT&amp;CK correlation"
        description="Where sufficient evidence is present, observed traffic characteristics are correlated with published MITRE ATT&CK techniques. Every mapping is shown with its evidence, interpretation and explicit limitation."
        aside={
          <div className="intro-facts">
            <p>
              <ShieldCheck size={14} /> {mitre.techniques.length} technique{mitre.techniques.length === 1 ? '' : 's'} returned for this profile
            </p>
            <p>{mitre.signalGroups.length} behavioural signal groups evaluated</p>
          </div>
        }
      />

      <Panel
        eyebrow="Mapping status"
        title={mitre.identified ? 'MITRE ATT&CK mapping identified' : 'No confident MITRE ATT&CK mapping'}
        tone={mitre.identified ? 'elevated' : 'normal'}
        aside={
          <div className="mapping-meta">
            <Chip tone={ml.state === 'ATTACK' ? 'critical' : 'normal'}>Current state {ml.state}</Chip>
            <Chip tone="muted">Attack probability {ml.probability.toFixed(2)}%</Chip>
          </div>
        }
      >
        <p className="status-text">
          {mitre.identified
            ? 'The behavioural evidence in this window satisfied the configured decision rules for the technique(s) below.'
            : mitre.reason || 'Insufficient behavioural evidence to satisfy the configured decision rules for this window.'}
        </p>
      </Panel>

      {mitre.identified ? (
        <div className="technique-list">
          {mitre.techniques.map((technique) => (
            <TechniqueCard key={`${technique.id}-${technique.name}`} technique={technique} />
          ))}
        </div>
      ) : (
        <EmptyState
          eyebrow="No confident mapping"
          text="A technique is only reported when the required number of behavioural signal groups is present in the analysed window. The evaluation below shows exactly which groups were present and which were not."
        />
      )}

      {mitre.signalGroups.length > 0 && <SignalGroupPanel groups={mitre.signalGroups} />}

      <Callout tone="warning" title="Scope of correlation">
        <p>
          ATT&amp;CK correlation here is behavioural and evidence based. Flow-level telemetry cannot establish intent, and a mapped
          technique means the observed behaviour is consistent with a known adversary pattern — it is not proof of an intrusion.
        </p>
      </Callout>
    </div>
  );
}
