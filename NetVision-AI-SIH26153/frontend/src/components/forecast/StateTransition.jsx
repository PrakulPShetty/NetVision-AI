import { ArrowRight } from 'lucide-react';

/**
 * State-transition view of the forecast.
 *
 * The world model is a first-order Markov chain over the binary network state
 * (BENIGN / ATTACK) with 5-minute steps, so the projection is a sequence of
 * states rather than a single label. This ribbon makes that sequence and its
 * transitions explicit.
 */
export default function StateTransition({ currentState, forecast, selectedMinutes, onSelect }) {
  const changes = forecast.filter((point, index) => {
    const previous = index === 0 ? currentState : forecast[index - 1].state;
    return previous !== point.state;
  });

  return (
    <div className="transition">
      <div className="transition-track">
        <button
          type="button"
          className={`transition-node current ${currentState === 'ATTACK' ? 'attack' : 'benign'}`}
          onClick={() => onSelect(null)}
          title="Current network state"
        >
          <span className="transition-label">Now</span>
          <span className="transition-state">{currentState}</span>
        </button>

        {forecast.map((point) => (
          <div className="transition-step" key={point.minutes}>
            <ArrowRight className="transition-arrow" size={15} aria-hidden="true" />
            <button
              type="button"
              className={`transition-node${point.minutes === selectedMinutes ? ' active' : ''} ${point.state === 'ATTACK' ? 'attack' : 'benign'}`}
              onClick={() => onSelect(point.minutes)}
              title={`Projected state at ${point.horizon}`}
            >
              <span className="transition-label">{point.horizon}</span>
              <span className="transition-state">{point.state}</span>
              <span className="transition-prob">{point.probability.toFixed(1)}%</span>
            </button>
          </div>
        ))}
      </div>

      <p className="transition-note">
        {changes.length === 0
          ? 'The projected state remains unchanged across all evaluated horizons.'
          : `Projected transition${changes.length > 1 ? 's' : ''} at ${changes
              .map((point) => point.horizon)
              .join(', ')} — each node is one 5-minute Markov step applied to the current state.`}
      </p>
    </div>
  );
}
