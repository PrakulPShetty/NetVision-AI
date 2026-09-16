import { ArrowRight, CheckCircle2, XCircle } from 'lucide-react';
import PageIntro from '../components/common/PageIntro';
import Panel from '../components/common/Panel';
import Callout from '../components/common/Callout';
import EmptyState from '../components/common/EmptyState';
import MetricCard from '../components/common/MetricCard';
import Chip from '../components/common/Chip';
import BarList from '../components/common/BarList';
import ContributionTable from '../components/explain/ContributionTable';

/**
 * Explain — why the model believes the forecast.
 *
 * Hierarchy: forecast → why → top contributing features → evidence. The
 * technical SHAP values are present but subordinate to the plain-language
 * interpretation, so a non-specialist reader can follow the reasoning.
 */
export default function ExplainPage({ status, result, onGo }) {
  if (status !== 'complete' || !result) {
    return (
      <div className="page">
        <PageIntro
          eyebrow="Explainability"
          title="Why this forecast?"
          description="NetVision AI uses SHAP (SHapley Additive exPlanations) in probability space to attribute each forecast to the traffic behaviour that produced it."
        />
        <EmptyState
          eyebrow="No explanation to display"
          text="An explanation is produced for a specific analysed profile. Run an analysis and the ranked contributing signals will appear here with their direction and relative importance."
          action={
            <button type="button" className="button primary" onClick={() => onGo('/analyze')}>
              Analyze a traffic profile <ArrowRight size={15} />
            </button>
          }
        />
      </div>
    );
  }

  const { xai, ml } = result;

  return (
    <div className="page">
      <PageIntro
        eyebrow="Explainability"
        title="Why this forecast?"
        description="Feature attributions describe how the trained ensemble reached this probability for this exact observation window. They explain the forecast — they are not a separate classifier."
        aside={
          <div className="intro-facts">
            <p>
              Method: {xai.method}
            </p>
            <p>
              {xai.contributions.length} ranked signals · {xai.raisers.length} raising · {xai.reducers.length} reducing
            </p>
          </div>
        }
      />

      <Panel eyebrow="Forecast" title="What is being explained" tone={ml.state === 'ATTACK' ? 'critical' : 'normal'}>
        <div className="metric-grid">
          <MetricCard
            label="Current state"
            value={ml.state}
            tone={ml.state === 'ATTACK' ? 'critical' : 'normal'}
            note={`Decision threshold ${ml.threshold.toFixed(0)}%`}
          />
          <MetricCard label="Attack probability" value={ml.probability.toFixed(2)} unit="%" tone="accent" />
          <MetricCard
            label="Attribution base"
            value={xai.baseProbability === null ? '—' : xai.baseProbability.toFixed(2)}
            unit="%"
            note="Background expectation the attributions are measured against"
          />
          <MetricCard
            label="Reconstruction check"
            value={xai.reconstructedProbability === null ? '—' : xai.reconstructedProbability.toFixed(2)}
            unit="%"
            tone={xai.validationPassed === false ? 'critical' : 'normal'}
            note={
              xai.validationPassed === null
                ? 'Base + attributions should reproduce the model probability'
                : xai.validationPassed
                ? 'Base + attributions reproduce the model probability'
                : 'Reconstruction exceeded the expected tolerance'
            }
          />
        </div>
      </Panel>

      <Panel
        eyebrow="Why?"
        title="What drove this probability"
        aside={
          xai.validationPassed === null ? null : (
            <Chip tone={xai.validationPassed ? 'normal' : 'critical'}>
              {xai.validationPassed ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
              {xai.validationPassed ? 'Attribution validated' : 'Attribution check failed'}
            </Chip>
          )
        }
      >
        <p className="panel-lead">{xai.summary}</p>
        <div className="split-bars">
          <div className="split-block">
            <p className="block-label">Increasing attack probability</p>
            {xai.raisers.length ? (
              <BarList
                items={xai.raisers.slice(0, 6).map((row) => ({
                  id: row.raw,
                  label: row.label,
                  value: row.value,
                  display: `+${row.value.toFixed(4)}`,
                  tone: 'alert',
                  tag: row.category,
                  hint: row.meaning,
                }))}
              />
            ) : (
              <p className="muted-note">No signal increased the attack probability for this window.</p>
            )}
          </div>
          <div className="split-block">
            <p className="block-label">Reducing attack probability</p>
            {xai.reducers.length ? (
              <BarList
                items={xai.reducers.slice(0, 6).map((row) => ({
                  id: row.raw,
                  label: row.label,
                  value: Math.abs(row.value),
                  display: row.value.toFixed(4),
                  tone: 'normal',
                  tag: row.category,
                  hint: row.meaning,
                }))}
              />
            ) : (
              <p className="muted-note">No signal reduced the attack probability for this window.</p>
            )}
          </div>
        </div>
      </Panel>

      <Panel
        eyebrow="Evidence"
        title="Ranked contributing features"
        aside={<span className="panel-note">Select a row for the traffic behaviour behind the number</span>}
      >
        <ContributionTable contributions={xai.contributions} />
        <p className="panel-footnote">
          Attribution is expressed in probability space by the backend explainer. Magnitudes are comparable within this window only.
        </p>
      </Panel>

      <Callout tone="note" title="Interpretation, not causation">
        <p>
          SHAP values describe each feature&apos;s contribution to this prediction given the trained model and the background
          traffic distribution. They indicate directional influence and must not be read as proof that a behaviour was malicious.
        </p>
      </Callout>
    </div>
  );
}
