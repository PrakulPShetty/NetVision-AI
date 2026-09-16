import { useState } from 'react';
import { ArrowRight, Gauge, Timer } from 'lucide-react';
import PageIntro from '../components/common/PageIntro';
import Panel from '../components/common/Panel';
import Callout from '../components/common/Callout';
import EmptyState from '../components/common/EmptyState';
import MetricCard from '../components/common/MetricCard';
import BarList from '../components/common/BarList';
import CurrentStateCard from '../components/forecast/CurrentStateCard';
import ForecastChart from '../components/forecast/ForecastChart';
import HorizonStrip from '../components/forecast/HorizonStrip';
import StateTransition from '../components/forecast/StateTransition';

/**
 * Forecast — future-state prediction only.
 *
 * The page is organised around time and state transition: where the network is
 * now, how the Markov world model evolves that state across 5-minute steps, and
 * what each horizon implies. Every value comes from the backend response.
 */
export default function ForecastPage({ status, result, onGo }) {
  const [selectedMinutes, setSelectedMinutes] = useState(null);

  if (status !== 'complete' || !result) {
    return (
      <div className="page">
        <PageIntro
          eyebrow="Forecast"
          title="Future security state"
          description="NetVision AI projects how the network security state may evolve across multiple future horizons once a traffic profile has been analysed."
        />
        <EmptyState
          eyebrow="No forecast to display"
          text="A forecast is produced per analysed traffic profile. Run an analysis and the current-state assessment, probability timeline and state transitions will appear here."
          action={
            <button type="button" className="button primary" onClick={() => onGo('/analyze')}>
              Analyze a traffic profile <ArrowRight size={15} />
            </button>
          }
        />
      </div>
    );
  }

  const { forecast, ml } = result;
  const threshold = ml.threshold;
  const peak = forecast.reduce((max, point) => (point.probability > max.probability ? point : max), forecast[0]);
  const selected = forecast.find((point) => point.minutes === selectedMinutes) || peak;
  const crossings = forecast.filter((point) => point.aboveThreshold).length;

  return (
    <div className="page">
      <PageIntro
        eyebrow="Forecast"
        title="Future security state"
        description="Forecasting is the distinction of NetVision AI: the current state is propagated through a first-order Markov state-transition model in 5-minute steps, producing attack probabilities across future horizons."
        aside={
          <div className="intro-facts">
            <p>
              <Timer size={14} /> Steps of 5 minutes · horizons to {forecast.length ? forecast[forecast.length - 1].horizon : '—'}
            </p>
            <p>
              <Gauge size={14} /> Decision threshold {threshold.toFixed(0)}%
            </p>
          </div>
        }
      />

      <CurrentStateCard ml={ml} />

      <Panel
        eyebrow="Forecast horizon"
        title="Attack probability timeline"
        aside={
          <span className="panel-note">
            {crossings}/{forecast.length} horizons above the decision threshold
          </span>
        }
      >
        <ForecastChart forecast={forecast} threshold={threshold} />
        <HorizonStrip forecast={forecast} threshold={threshold} selectedMinutes={selected.minutes} onSelect={setSelectedMinutes} />
        <StateTransition
          currentState={ml.state}
          forecast={forecast}
          selectedMinutes={selected.minutes}
          onSelect={setSelectedMinutes}
        />
      </Panel>

      <div className="forecast-detail">
        <Panel
          eyebrow={`Horizon K = ${selected.k} · ${selected.horizon}`}
          title="Projected state at this horizon"
          tone={selected.state === 'ATTACK' ? 'critical' : 'normal'}
        >
          <div className="metric-grid">
            <MetricCard
              label="Projected state"
              value={selected.state}
              tone={selected.state === 'ATTACK' ? 'critical' : 'normal'}
              note={`${selected.steps} × 5-minute Markov step${selected.steps > 1 ? 's' : ''} from the current state`}
            />
            <MetricCard
              label="Attack probability"
              value={selected.probability.toFixed(2)}
              unit="%"
              tone="accent"
              note={`${selected.aboveThreshold ? 'Above' : 'Below'} the ${threshold.toFixed(0)}% decision threshold`}
            />
            <MetricCard
              label="Benign probability"
              value={selected.benignProbability.toFixed(2)}
              unit="%"
              tone="normal"
              note="Complementary state probability in the same projection"
            />
            <MetricCard
              label="Decision margin"
              value={`${selected.probability - threshold >= 0 ? '+' : ''}${(selected.probability - threshold).toFixed(2)}`}
              unit="pp"
              tone={selected.aboveThreshold ? 'elevated' : 'default'}
              note="Distance from the calibrated decision threshold — not a confidence score"
            />
          </div>
        </Panel>

        <Panel
          eyebrow="Contributing behaviour"
          title="Traffic signals behind this forecast"
          aside={
            <button type="button" className="text-button" onClick={() => onGo('/explain')}>
              Full explanation <ArrowRight size={13} />
            </button>
          }
        >
          {result.xai.available ? (
            <>
              <p className="panel-lead">{result.xai.summary}</p>
              <BarList
                items={result.xai.contributions.slice(0, 6).map((row) => ({
                  id: row.raw,
                  label: row.label,
                  value: row.abs,
                  display: `${row.value > 0 ? '+' : ''}${row.value.toFixed(4)}`,
                  tone: row.direction === 'lowers' ? 'normal' : 'alert',
                  hint: row.meaning,
                }))}
                max={result.xai.contributions[0]?.abs || 1}
              />
              <p className="panel-footnote">
                SHAP attribution from the ensemble for the analysed window ({result.xai.method}). Positive values raise the attack
                probability; negative values reduce it.
              </p>
            </>
          ) : (
            <EmptyState text="The explainer returned no ranked contributions for this profile." />
          )}
        </Panel>
      </div>

      <Callout tone="note" title="How to read this forecast">
        <p>
          Each horizon applies the trained 5-minute transition matrix to the current estimated state. The result is a probability of
          being in the ATTACK state at that time — it is not a scheduled event, and a low early probability does not mean the network
          is safe. Probabilities are model estimates from CIC-IDS2018 traffic behaviour.
        </p>
      </Callout>
    </div>
  );
}
