import { useCallback, useMemo, useState } from 'react';
import { ArrowRight, RotateCcw, ShieldAlert, Timer } from 'lucide-react';
import PageIntro from '../components/common/PageIntro';
import Panel from '../components/common/Panel';
import Callout from '../components/common/Callout';
import MetricCard from '../components/common/MetricCard';
import PresetScenarios from '../components/analysis/PresetScenarios';
import TrafficForm from '../components/analysis/TrafficForm';
import ProfileSummary from '../components/analysis/ProfileSummary';
import AnalysisStages from '../components/analysis/AnalysisStages';
import { TRAFFIC_PRESETS } from '../utils/presets';
import { deriveProfile } from '../utils/trafficFields';

/**
 * Analyze — the input surface.
 *
 * Workflow: choose a demonstration scenario or enter values manually, review
 * the derived summary of that window, then run inference. The page only ever
 * displays numbers produced by the backend pipeline; before a response exists
 * it stays in an explicit idle state.
 */
export default function AnalyzePage({ status, error, result, onAnalyze, onGo }) {
  const [presetValues, setPresetValues] = useState(null);
  const [activePreset, setActivePreset] = useState(null);
  const [values, setValues] = useState(null);
  const [resetToken, setResetToken] = useState(undefined);

  const profile = useMemo(() => (values ? deriveProfile(values) : null), [values]);

  const loadPreset = (preset) => {
    setActivePreset(preset.id);
    setPresetValues(preset.data);
  };

  const clearProfile = () => {
    setActivePreset(null);
    setResetToken(Date.now());
  };

  const handleValuesChange = useCallback((next) => setValues(next), []);
  const handlePresetConsumed = useCallback(() => setPresetValues(null), []);

  const statusCopy = {
    ready: {
      label: 'Ready for analysis',
      title: 'Awaiting a traffic profile',
      text: 'Submit the 5-minute observation window to run the forecasting pipeline. Nothing is predicted until you do.',
    },
    analyzing: {
      label: 'Analyzing profile',
      title: 'Pipeline running',
      text: 'Scoring the ensemble, propagating the Markov world model, computing SHAP attributions and evaluating ATT&CK evidence.',
    },
    complete: {
      label: 'Analysis complete',
      title: 'Forecast computed',
      text: 'Results below come from the backend pipeline for this exact profile. Open the dedicated pages for the full forecast, explanation and correlation trail.',
    },
    error: {
      label: 'Analysis unavailable',
      title: 'Forecast service error',
      text: error || 'NetVision AI could not reach the forecasting service.',
    },
  }[status];

  return (
    <div className="page">
      <PageIntro
        eyebrow="Input"
        title="Analyze network traffic"
        description="Provide a 5-minute traffic profile to generate a security forecast. The profile is expanded by the runtime feature transformer into the 138 features the trained ensemble expects."
        aside={
          <div className="intro-facts">
            <p>
              <Timer size={14} /> 1 observation window · 5 minutes
            </p>
            <p>
              <ShieldAlert size={14} /> 15 practical inputs → 138 model features
            </p>
          </div>
        }
      />

      <Panel
        eyebrow="Demo scenarios"
        title="Load a representative traffic profile"
        aside={
          <button type="button" className="text-button" onClick={clearProfile}>
            <RotateCcw size={14} /> Clear profile
          </button>
        }
        footer={
          <p className="panel-footnote">
            Scenarios populate the input fields with profiles anchored to genuine CIC-IDS2018 distributions. They are inputs only —
            the assessment, forecast, SHAP values and ATT&amp;CK correlation are always computed by the backend model.
          </p>
        }
      >
        <PresetScenarios presets={TRAFFIC_PRESETS} activeId={activePreset} onSelect={loadPreset} />
      </Panel>

      <div className="analysis-layout">
        <Panel
          eyebrow="Observation window"
          title="Traffic profile"
          className="analysis-form-panel"
          aside={<span className="panel-note">All values describe one 5-minute window</span>}
        >
          <TrafficForm
            onSubmit={onAnalyze}
            status={status}
            presetValues={presetValues}
            onPresetConsumed={handlePresetConsumed}
            onValuesChange={handleValuesChange}
            resetToken={resetToken}
          />
        </Panel>

        <aside className="analysis-side">
          <Panel eyebrow={statusCopy.label} title={statusCopy.title} tone={status === 'error' ? 'critical' : status === 'complete' ? 'normal' : 'default'}>
            <p className="status-text">{statusCopy.text}</p>
            {status === 'analyzing' && (
              <p className="status-running">
                <i className="spinner" /> Running inference…
              </p>
            )}
            {status === 'complete' && (
              <div className="status-actions">
                <button type="button" className="button primary small" onClick={() => onGo('/forecast')}>
                  View forecast <ArrowRight size={14} />
                </button>
                <button type="button" className="text-button" onClick={() => onGo('/explain')}>
                  Why this result <ArrowRight size={14} />
                </button>
              </div>
            )}
            {status === 'error' && (
              <Callout tone="critical" title="Check the engine">
                Start the FastAPI backend (<code>python -m uvicorn backend.app.main:app --reload</code>) and submit the profile again.
              </Callout>
            )}
          </Panel>

          <ProfileSummary profile={profile} />
        </aside>
      </div>

      {status === 'complete' && result && (
        <Panel
          eyebrow="Result summary"
          title="What the pipeline returned for this profile"
          aside={
            <div className="summary-links">
              <button type="button" className="text-button" onClick={() => onGo('/forecast')}>
                Forecast <ArrowRight size={13} />
              </button>
              <button type="button" className="text-button" onClick={() => onGo('/explain')}>
                Explain <ArrowRight size={13} />
              </button>
              <button type="button" className="text-button" onClick={() => onGo('/attack')}>
                ATT&amp;CK <ArrowRight size={13} />
              </button>
            </div>
          }
        >
          <div className="metric-grid">
            <MetricCard
              label="Current state"
              value={result.ml.state}
              tone={result.ml.state === 'ATTACK' ? 'critical' : 'normal'}
              note={`Ensemble label at threshold ${result.ml.threshold.toFixed(0)}%`}
            />
            <MetricCard
              label="Attack probability"
              value={result.ml.probability.toFixed(2)}
              unit="%"
              tone="accent"
              note={`Margin ${result.ml.margin >= 0 ? '+' : ''}${result.ml.margin.toFixed(2)} pp`}
            />
            <MetricCard
              label="Forecast horizons"
              value={result.forecast.length}
              tone="default"
              note={
                result.forecast.length
                  ? `Highest ${Math.max(...result.forecast.map((point) => point.probability)).toFixed(1)}% at ${
                      result.forecast.reduce((max, point) => (point.probability > max.probability ? point : max)).horizon
                    }`
                  : 'No horizons returned'
              }
            />
            <MetricCard
              label="Leading signal"
              value={result.xai.raisers[0] ? result.xai.raisers[0].label : '—'}
              tone="default"
              size="sm"
              note={result.xai.raisers[0] ? `+${result.xai.raisers[0].value.toFixed(4)} attribution` : 'No positive contributor reported'}
            />
            <MetricCard
              label="ATT&CK techniques"
              value={result.mitre.techniques.length}
              tone={result.mitre.techniques.length ? 'elevated' : 'normal'}
              size="sm"
              note={result.mitre.techniques.length ? result.mitre.status : result.mitre.reason || 'No confident mapping'}
            />
          </div>
        </Panel>
      )}

      <Panel
        eyebrow="Pipeline"
        title="How this profile is processed"
        aside={<span className="panel-note">Evidence-based stages, no simulated progress</span>}
      >
        <AnalysisStages status={status} result={result} onGo={onGo} />
      </Panel>
    </div>
  );
}
