import { useState } from 'react';

/**
 * End-to-end system workflow.
 *
 * Documents the pipeline the frontend is built against so the interface is
 * understood as the last mile of a real ML system: dataset → preprocessing →
 * feature engineering → temporal representation → models → ensemble → state
 * transition model → forecasting → XAI → ATT&CK → visualisation.
 */

const PHASES = [
  {
    id: 'data',
    label: 'Data foundation',
    steps: [
      { title: 'CIC-IDS2018', note: 'Benchmark network intrusion dataset used for training and evaluation.' },
      { title: 'Preprocessing', note: 'Cleaning, encoding and scaling of raw flow records.' },
      { title: 'Feature engineering', note: 'Statistical flow descriptors built from packet, byte and timing fields.' },
      { title: 'Temporal representation', note: 'Sequential 5-minute windows so state evolution is observable.' },
    ],
  },
  {
    id: 'models',
    label: 'Modelling',
    steps: [
      { title: 'ML models', note: 'Gradient boosting and Random Forest classifiers trained on the engineered features.' },
      { title: 'Ensemble', note: 'Soft-voting fusion with SMOTE-balanced minority attack classes and a calibrated decision threshold.' },
      { title: 'State transition model', note: 'First-order Markov transition probabilities between consecutive network states.' },
    ],
  },
  {
    id: 'prediction',
    label: 'Forecasting',
    steps: [
      { title: 'Current-state assessment', note: 'Ensemble probability converted into the present BENIGN / ATTACK state.' },
      { title: 'Future-state prediction', note: 'State propagated across 5-minute steps to multi-horizon attack probabilities.' },
    ],
  },
  {
    id: 'delivery',
    label: 'Interpretation & delivery',
    steps: [
      { title: 'XAI / SHAP', note: 'Per-feature attribution that explains the probability.' },
      { title: 'MITRE ATT&CK mapping', note: 'Behavioural evidence matched to techniques under explicit decision rules.' },
      { title: 'Frontend visualisation', note: 'This interface: analysis, forecast, explanation and correlation pages.' },
    ],
  },
];

export default function PipelineTrack() {
  const [selected, setSelected] = useState({ phase: 'data', step: 0 });
  const phase = PHASES.find((item) => item.id === selected.phase) || PHASES[0];
  const step = phase.steps[selected.step] || phase.steps[0];

  return (
    <div className="pipeline">
      <ol className="pipeline-phases">
        {PHASES.map((item, index) => (
          <li key={item.id}>
            <button
              type="button"
              className={`pipeline-phase${item.id === phase.id ? ' active' : ''}`}
              onClick={() => setSelected({ phase: item.id, step: 0 })}
              onMouseEnter={() => setSelected({ phase: item.id, step: 0 })}
            >
              <span className="pipeline-phase-num">{String(index + 1).padStart(2, '0')}</span>
              <span className="pipeline-phase-label">{item.label}</span>
              <span className="pipeline-phase-count">{item.steps.length} stages</span>
            </button>
          </li>
        ))}
      </ol>

      <div className="pipeline-body">
        <ul className="pipeline-steps">
          {phase.steps.map((item, index) => (
            <li key={item.title}>
              <button
                type="button"
                className={`pipeline-step${index === selected.step ? ' active' : ''}`}
                onClick={() => setSelected({ phase: phase.id, step: index })}
                onMouseEnter={() => setSelected({ phase: phase.id, step: index })}
              >
                <span className="pipeline-step-title">{item.title}</span>
              </button>
            </li>
          ))}
        </ul>
        <p className="pipeline-detail">{step.note}</p>
      </div>
    </div>
  );
}
