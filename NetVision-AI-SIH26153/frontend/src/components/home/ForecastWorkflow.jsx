import { useState } from 'react';

/**
 * Interactive product workflow (01 OBSERVE → 05 CORRELATE).
 *
 * Hover or focus previews a stage, clicking pins it open. Each stage states
 * what the system does and which page exposes it — this replaces the previous
 * purely decorative strip of stage names.
 */

export const WORKFLOW_STAGES = [
  {
    num: '01',
    title: 'OBSERVE',
    subtitle: 'Traffic observation',
    summary: 'A 5-minute traffic profile describes what the network was doing.',
    detail:
      'Fifteen practical telemetry attributes — flow counts, packet and byte volumes per direction, rates, timings and TCP flag activity — are expanded by the runtime feature transformer into the frozen 138-feature representation the trained models expect.',
    route: '/analyze',
    routeLabel: 'Analyze',
  },
  {
    num: '02',
    title: 'ASSESS',
    subtitle: 'Current network state',
    summary: 'The ensemble estimates the present security state and attack probability.',
    detail:
      'An XGBoost plus Random Forest (SMOTE) soft-voting ensemble scores the window. The ensemble probability is compared against the calibrated decision threshold to label the current state as BENIGN or ATTACK, with the component probabilities shown separately.',
    route: '/analyze',
    routeLabel: 'Analyze',
  },
  {
    num: '03',
    title: 'FORECAST',
    subtitle: 'Future-state prediction',
    summary: 'The current state is projected forward across multiple horizons.',
    detail:
      'A first-order Markov state-transition model trained on sequential CIC-IDS2018 windows propagates the current state in 5-minute steps, producing an attack probability for each forecast horizon rather than a single present-tense verdict.',
    route: '/forecast',
    routeLabel: 'Forecast',
  },
  {
    num: '04',
    title: 'EXPLAIN',
    subtitle: 'Explainability',
    summary: 'SHAP attribution shows which traffic behaviour produced the probability.',
    detail:
      'Probability-space SHAP values decompose the prediction into per-feature contributions with direction and relative importance, and the base-plus-attributions reconstruction is checked against the model probability so the explanation is auditable.',
    route: '/explain',
    routeLabel: 'Explain',
  },
  {
    num: '05',
    title: 'CORRELATE',
    subtitle: 'MITRE ATT&CK context',
    summary: 'Behavioural evidence is matched against ATT&CK decision rules.',
    detail:
      'The mapper evaluates configured behavioural signal groups and only reports a technique once a minimum set of groups is present. Each mapping is displayed with its supporting features, interpretation and limitation.',
    route: '/attack',
    routeLabel: 'ATT&CK',
  },
];

export default function ForecastWorkflow({ onGo, activeIndex, onActiveIndexChange }) {
  const [internalIndex, setInternalIndex] = useState(0);
  const active = activeIndex ?? internalIndex;
  const setActive = onActiveIndexChange ?? setInternalIndex;
  const stage = WORKFLOW_STAGES[active];

  return (
    <div className="workflow-stepper">
      <ul className="workflow-list" role="tablist" aria-label="Forecasting workflow">
        {WORKFLOW_STAGES.map((item, index) => (
          <li key={item.num}>
            <button
              type="button"
              role="tab"
              aria-selected={index === active}
              className={`workflow-item${index === active ? ' active' : ''}`}
              onMouseEnter={() => setActive(index)}
              onFocus={() => setActive(index)}
              onClick={() => setActive(index)}
            >
              <span className="workflow-num">{item.num}</span>
              <span className="workflow-copy">
                <span className="workflow-title">{item.title}</span>
                <span className="workflow-summary">{item.summary}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>

      <div className="workflow-detail" role="tabpanel" key={stage.num}>
        <p className="workflow-detail-eyebrow">
          {stage.num} · {stage.subtitle}
        </p>
        <p className="workflow-detail-text">{stage.detail}</p>
        <button type="button" className="text-button" onClick={() => onGo(stage.route)}>
          Open {stage.routeLabel} →
        </button>
      </div>
    </div>
  );
}
