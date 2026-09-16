import { ArrowRight, Circle, CircleCheck, CircleDashed, TriangleAlert } from 'lucide-react';
import Chip from '../common/Chip';

/**
 * Pipeline tracker for the Analyze page.
 *
 * Before an analysis every stage is idle. While inference runs the stages are
 * shown as a single queued pipeline rather than a fake progress animation.
 * Once a response arrives, each stage reports the real numbers returned by the
 * backend and links to the page that expands it.
 */

export default function AnalysisStages({ status, result, onGo }) {
  const stages = buildStages({ status, result });

  return (
    <ol className={`stage-list status-${status}`}>
      {stages.map((stage) => (
        <li key={stage.id} className={`stage state-${stage.state}`}>
          <span className="stage-marker" aria-hidden="true">
            {stage.state === 'complete' ? (
              <CircleCheck size={15} />
            ) : stage.state === 'running' ? (
              <CircleDashed size={15} className="spin-slow" />
            ) : stage.state === 'attention' ? (
              <TriangleAlert size={15} />
            ) : (
              <Circle size={15} />
            )}
          </span>
          <div className="stage-copy">
            <p className="stage-title">
              <span className="stage-num">{stage.num}</span>
              {stage.title}
              {stage.tag && <Chip tone={stage.tagTone || 'muted'}>{stage.tag}</Chip>}
            </p>
            <p className="stage-detail">{stage.detail}</p>
          </div>
          {stage.to && stage.state === 'complete' && (
            <button type="button" className="stage-link" onClick={() => onGo(stage.to)}>
              Open <ArrowRight size={13} />
            </button>
          )}
        </li>
      ))}
    </ol>
  );
}

function buildStages({ status, result }) {
  const idle = status === 'ready' || status === 'error';
  const running = status === 'analyzing';
  const done = status === 'complete' && Boolean(result);

  const peak = done && result.forecast.length
    ? result.forecast.reduce((max, point) => (point.probability > max.probability ? point : max), result.forecast[0])
    : null;

  const techniqueCount = done ? result.mitre.techniques.length : 0;

  const base = [
    {
      id: 'observe',
      num: '01',
      title: 'Observation window',
      detail: done
        ? 'Traffic profile accepted and expanded by the runtime feature transformer into the frozen 138-feature model representation.'
        : running
        ? 'Accepting the 5-minute traffic profile and expanding it into model features.'
        : 'Waiting for a 5-minute traffic profile.',
      state: done ? 'complete' : running ? 'running' : 'idle',
      tag: done ? '138 features' : null,
      tagTone: 'info',
    },
    {
      id: 'assess',
      num: '02',
      title: 'Current network state',
      detail: done
        ? `Ensemble attack probability ${result.ml.probability.toFixed(2)}% against the calibrated ${result.ml.threshold.toFixed(0)}% decision threshold.`
        : running
        ? 'Scoring the profile with the XGBoost + Random Forest (SMOTE) ensemble.'
        : 'Current state is assessed after a profile is submitted.',
      state: done ? 'complete' : running ? 'running' : 'idle',
      tag: done ? result.ml.state : null,
      tagTone: result?.ml?.state === 'ATTACK' ? 'critical' : 'normal',
    },
    {
      id: 'forecast',
      num: '03',
      title: 'Future-state forecast',
      detail: done
        ? `Markov world model projected ${result.forecast.length} horizons from the current state; highest attack probability ${peak ? peak.probability.toFixed(1) : '—'}% at ${peak ? peak.horizon : '—'}.`
        : running
        ? 'Propagating the current state through the Markov transition model across future horizons.'
        : 'Forecast horizons appear once the current state is known.',
      state: done ? 'complete' : running ? 'running' : 'idle',
      tag: done ? `${result.forecast.length} horizons` : null,
      tagTone: 'info',
      to: done ? '/forecast' : null,
    },
    {
      id: 'explain',
      num: '04',
      title: 'Explainability',
      detail: done
        ? result.xai.available
          ? `SHAP attribution ranked ${result.xai.contributions.length} contributing signals; ${result.xai.raisers.length} increased and ${result.xai.reducers.length} reduced the attack probability.`
          : 'The explainer returned no ranked contributions for this profile.'
        : running
        ? 'Calculating SHAP attributions in probability space.'
        : 'Explanations are produced for the profile being analysed.',
      state: done ? (result.xai.available ? 'complete' : 'attention') : running ? 'running' : 'idle',
      tag: done && result.xai.available ? result.xai.method : null,
      tagTone: 'info',
      to: done && result.xai.available ? '/explain' : null,
    },
    {
      id: 'correlate',
      num: '05',
      title: 'ATT&CK correlation',
      detail: done
        ? techniqueCount
          ? `${techniqueCount} technique${techniqueCount > 1 ? 's' : ''} matched the configured evidence rules across ${result.mitre.signalGroups.length} evaluated signal groups.`
          : result.mitre.reason || 'Insufficient behavioural evidence to satisfy the configured MITRE decision rules.'
        : running
        ? 'Evaluating behavioural signal groups against the MITRE ATT&CK rules.'
        : 'Correlation requires a completed analysis.',
      state: done ? (techniqueCount ? 'complete' : 'attention') : running ? 'running' : 'idle',
      tag: done ? (techniqueCount ? `${techniqueCount} technique${techniqueCount > 1 ? 's' : ''}` : 'No confident mapping') : null,
      tagTone: techniqueCount ? 'elevated' : 'muted',
      to: done ? '/attack' : null,
    },
  ];

  if (idle) {
    return base.map((stage) => ({ ...stage, tag: null, to: null }));
  }
  return base;
}
