import { useState, useEffect } from 'react';
import { ArrowUpRight } from 'lucide-react';

const groups = [
  {
    title: 'Traffic overview',
    fields: [
      ['flow_count', 'Flow count', 'flows'],
      ['unique_dst_ports', 'Unique destination ports', 'ports'],
      ['unique_protocols', 'Unique protocols', 'protocols'],
    ],
  },
  {
    title: 'Forward traffic',
    fields: [
      ['forward_packets', 'Total forward packets', 'packets'],
      ['forward_bytes', 'Total forward bytes', 'bytes'],
    ],
  },
  {
    title: 'Backward traffic',
    fields: [
      ['backward_packets', 'Total backward packets', 'packets'],
      ['backward_bytes', 'Total backward bytes', 'bytes'],
    ],
  },
  {
    title: 'Flow characteristics',
    fields: [
      ['flow_duration', 'Flow duration', 'ms'],
      ['flow_bytes_per_sec', 'Flow bytes / s', 'bytes/s'],
      ['flow_packets_per_sec', 'Flow packets / s', 'packets/s'],
      ['backward_packets_per_sec', 'Backward packets / s', 'packets/s'],
    ],
  },
  {
    title: 'TCP activity',
    fields: [
      ['syn_flag_cnt', 'SYN', 'packets'],
      ['ack_flag_cnt', 'ACK', 'packets'],
      ['rst_flag_cnt', 'RST', 'packets'],
      ['fin_flag_cnt', 'FIN', 'packets'],
      ['psh_flag_cnt', 'PSH', 'packets'],
      ['urg_flag_cnt', 'URG', 'packets'],
    ],
  },
  {
    title: 'Network balance',
    fields: [['down_up_ratio', 'Down / up ratio', 'ratio']],
  },
];

const initial = Object.fromEntries(
  groups.flatMap((g) => g.fields.map(([key]) => [key, '']))
);

export default function TrafficForm({ onSubmit, status, presetValues, onPresetConsumed }) {
  const [values, setValues] = useState(initial);
  const [touched, setTouched] = useState({});

  // Load preset values when a demo scenario is selected
  useEffect(() => {
    if (presetValues) {
      const populated = { ...initial };
      for (const [key, val] of Object.entries(presetValues)) {
        if (key in populated) {
          populated[key] = String(val);
        }
      }
      setValues(populated);
      setTouched({});
      onPresetConsumed?.();
    }
  }, [presetValues]);

  const isInvalid = (k) => {
    if (!touched[k]) return false;
    const val = values[k];
    if (val === '' || val === null || val === undefined) return true;
    const num = Number(val);
    return isNaN(num) || !isFinite(num) || num < 0;
  };

  const isFormValid = () => {
    return Object.keys(values).every((k) => {
      const val = values[k];
      if (val === '' || val === null || val === undefined) return false;
      const num = Number(val);
      return !isNaN(num) && isFinite(num) && num >= 0;
    });
  };

  function submit(e) {
    e.preventDefault();
    setTouched(
      Object.fromEntries(Object.keys(values).map((k) => [k, true]))
    );

    if (isFormValid()) {
      const payload = Object.fromEntries(
        Object.entries(values).map(([k, v]) => [k, Number(v)])
      );
      onSubmit(payload);
    }
  }

  return (
    <form className="traffic-form" onSubmit={submit} noValidate>
      {groups.map((group) => (
        <fieldset key={group.title}>
          <legend>{group.title}</legend>
          <div className="field-grid">
            {group.fields.map(([key, label, unit]) => (
              <label className={isInvalid(key) ? 'invalid' : ''} key={key}>
                <span>{label}</span>
                <div className="input-wrap">
                  <input
                    type="number"
                    min="0"
                    step="any"
                    inputMode="decimal"
                    value={values[key]}
                    placeholder="0"
                    onBlur={() => setTouched({ ...touched, [key]: true })}
                    onChange={(e) =>
                      setValues({ ...values, [key]: e.target.value })
                    }
                  />
                  <small>{unit}</small>
                </div>
                {isInvalid(key) && <em>Enter a finite value of 0 or more.</em>}
              </label>
            ))}
          </div>
        </fieldset>
      ))}
      <div className="form-submit">
        <p>Fields use aggregate values from one 5-minute observation window.</p>
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
