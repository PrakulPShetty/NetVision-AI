import { Check, FlaskConical } from 'lucide-react';
import Chip from '../common/Chip';

/**
 * Demonstration scenarios.
 *
 * These are input profiles only. Selecting one populates the form; it never
 * produces a result by itself, and the UI says so on every card.
 */

const TONE_BY_ID = {
  normal: 'normal',
  high_volume: 'elevated',
  syn_flood: 'critical',
  scanning: 'elevated',
  mixed: 'neutral',
};

export default function PresetScenarios({ presets, activeId, onSelect }) {
  return (
    <div className="preset-grid">
      {presets.map((preset) => {
        const active = preset.id === activeId;
        return (
          <button
            key={preset.id}
            type="button"
            className={`preset-card${active ? ' active' : ''}`}
            onClick={() => onSelect(preset)}
            aria-pressed={active}
          >
            <span className="preset-top">
              <Chip tone={TONE_BY_ID[preset.id] || 'neutral'}>{preset.badge}</Chip>
              {active ? (
                <span className="preset-state active">
                  <Check size={12} /> Loaded into form
                </span>
              ) : (
                <span className="preset-state">
                  <FlaskConical size={12} /> Scenario
                </span>
              )}
            </span>
            <span className="preset-title">{preset.title}</span>
            <span className="preset-desc">{preset.description}</span>
          </button>
        );
      })}
    </div>
  );
}
