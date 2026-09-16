/**
 * Forecast horizons as selectable cards.
 *
 * Forecasting is the distinction of the product, so each horizon is a first
 * class object: the Markov step count (K), the projected state, the attack
 * probability and its margin against the decision threshold. Selecting a card
 * expands it on the Forecast page.
 */
export default function HorizonStrip({ forecast, threshold, selectedMinutes, onSelect }) {
  return (
    <ul className="horizon-strip">
      {forecast.map((point) => {
        const active = point.minutes === selectedMinutes;
        const margin = point.probability - threshold;
        return (
          <li key={point.minutes}>
            <button
              type="button"
              className={`horizon-card${active ? ' active' : ''} ${point.state === 'ATTACK' ? 'attack' : 'benign'}`}
              onClick={() => onSelect(point.minutes)}
              aria-pressed={active}
            >
              <span className="horizon-head">
                <span className="horizon-k">K = {point.k}</span>
                <span className="horizon-minutes">{point.minutes} min</span>
              </span>
              <span className="horizon-prob">
                {point.probability.toFixed(1)}
                <small>%</small>
              </span>
              <span className="horizon-state">{point.state}</span>
              <span className="horizon-margin">
                {margin >= 0 ? '+' : ''}
                {margin.toFixed(1)} pp vs threshold
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
