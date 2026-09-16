import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowUpRight, Info } from 'lucide-react';
import {
  TRAFFIC_GROUPS,
  TRAFFIC_FIELDS,
  createEmptyValues,
  invalidKeys,
} from '../../utils/trafficFields';

/**
 * NetVision AI — 5-minute traffic profile form
 *
 * The 15-field practical input surface (expanded by the backend runtime
 * transformer into the frozen 138-feature model representation).
 *
 * Numeric input behaviour is deliberate:
 *   - browser spin buttons are removed (see .field-input in index.css), because
 *     up/down arrows are not meaningful for traffic counters;
 *   - a mouse wheel over a focused field never changes its value — the field
 *     releases focus so the page scrolls instead of silently overwriting a
 *     value the analyst typed.
 */

const clampNonNegative = (raw) => raw.replace(/[^0-9.]/g, '').replace(/(\..*)\./g, '$1');

function preventWheelValueChange(event) {
  // Blurring during the wheel event stops the browser from applying the
  // increment/decrement, and lets the page scroll as the user intended.
  event.currentTarget.blur();
}

export default function TrafficForm({
  onSubmit,
  status = 'ready',
  presetValues,
  onPresetConsumed,
  onValuesChange,
  resetToken,
}) {
  const [values, setValues] = useState(createEmptyValues);
  const [touched, setTouched] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const formRef = useRef(null);

  // Demo scenarios populate the fields only — inference stays a backend concern.
  useEffect(() => {
    if (!presetValues) return;
    const next = createEmptyValues();
    for (const [key, value] of Object.entries(presetValues)) {
      if (key in next) next[key] = String(value);
    }
    setValues(next);
    setTouched({});
    setSubmitted(false);
    onPresetConsumed?.();
  }, [presetValues, onPresetConsumed]);

  useEffect(() => {
    if (resetToken === undefined) return;
    setValues(createEmptyValues());
    setTouched({});
    setSubmitted(false);
  }, [resetToken]);

  // Surface live values so the page can derive profile statistics.
  // The callback is held in a ref so a new identity from the parent never
  // re-triggers the effect (which would loop through the parent's state).
  const notifyValues = useRef(onValuesChange);
  notifyValues.current = onValuesChange;
  useEffect(() => {
    notifyValues.current?.(values);
  }, [values]);

  const invalid = useMemo(() => new Set(invalidKeys(values)), [values]);
  const filledCount = TRAFFIC_FIELDS.length - invalid.size;
  const showErrors = submitted;
  const showFieldError = (key) => (touched[key] || showErrors) && invalid.has(key);

  const setField = (key, raw) => {
    setValues((prev) => ({ ...prev, [key]: clampNonNegative(raw) }));
  };

  function submit(event) {
    event.preventDefault();
    setSubmitted(true);
    const bad = invalidKeys(values);
    if (bad.length > 0) {
      const firstInvalid = formRef.current?.querySelector(`[data-field="${bad[0]}"] input`);
      firstInvalid?.focus();
      firstInvalid?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }
    onSubmit?.(Object.fromEntries(TRAFFIC_FIELDS.map((f) => [f.key, Number(values[f.key])])));
  }

  return (
    <form className="traffic-form" ref={formRef} onSubmit={submit} noValidate>
      {TRAFFIC_GROUPS.map((group, index) => (
        <fieldset className="form-group" key={group.id}>
          <legend className="form-group-title">
            <span className="legend-num">{String(index + 1).padStart(2, '0')}</span>
            <span>{group.title}</span>
          </legend>
          {group.hint && <p className="form-group-hint">{group.hint}</p>}
          <div className="field-grid">
            {group.fields.map((field) => {
              const value = values[field.key];
              const hasValue = value !== '' && !invalid.has(field.key);
              return (
                <label
                  key={field.key}
                  className={`field${showFieldError(field.key) ? ' invalid' : ''}${hasValue ? ' filled' : ''}`}
                  data-field={field.key}
                >
                  <span className="field-label">
                    {field.label}
                    <i className="field-hint" title={field.hint} aria-hidden="true">
                      <Info size={11} />
                    </i>
                  </span>
                  <span className="input-wrap">
                    <input
                      className="field-input"
                      type="number"
                      inputMode="decimal"
                      step="any"
                      min="0"
                      autoComplete="off"
                      value={value}
                      placeholder="0"
                      aria-invalid={showFieldError(field.key)}
                      aria-describedby={showFieldError(field.key) ? `${field.key}-error` : undefined}
                      onWheel={preventWheelValueChange}
                      onBlur={() => setTouched((prev) => ({ ...prev, [field.key]: true }))}
                      onChange={(event) => setField(field.key, event.target.value)}
                    />
                    <small className="input-unit">{field.unit}</small>
                  </span>
                  {showFieldError(field.key) && (
                    <em className="field-error" id={`${field.key}-error`}>
                      Enter a value of 0 or more.
                    </em>
                  )}
                </label>
              );
            })}
          </div>
        </fieldset>
      ))}

      <div className="form-actions">
        <div className="form-summary" aria-live="polite">
          <p className="form-count">
            <strong>
              {filledCount}/{TRAFFIC_FIELDS.length}
            </strong>{' '}
            profile fields provided
          </p>
          <p className="form-note">
            {showErrors && filledCount < TRAFFIC_FIELDS.length
              ? `${TRAFFIC_FIELDS.length - filledCount} field(s) still need a value before inference can run.`
              : 'Fields describe one 5-minute observation window. Scenario presets populate inputs only — every prediction is computed by the backend model.'}
          </p>
        </div>
        <button className="button primary" disabled={status === 'analyzing'}>
          {status === 'analyzing' ? (
            <>
              <i className="spinner" /> Analyzing profile
            </>
          ) : (
            <>
              Analyze network <ArrowUpRight size={17} />
            </>
          )}
        </button>
      </div>
    </form>
  );
}
