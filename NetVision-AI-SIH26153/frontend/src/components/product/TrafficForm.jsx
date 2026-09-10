import { useState, useEffect } from 'react';
import { ArrowUpRight } from 'lucide-react';

/**
 * NetVision AI — Practical Traffic Profile Form
 *
 * Collects a 5-minute traffic observation window as a practical profile.
 * The backend transformer (RuntimeFeatureTransformer) reconstructs the
 * frozen 138-feature model representation from these fields.
 *
 * Every field maps to at least one Phase 3 / Phase 4 model feature.
 * See docs/architecture/runtime_input_design.md for the full mapping.
 */

const groups = [
  {
    title: 'Observation window',
    hint: 'The traffic summarized below was observed during one 5-minute window.',
    fields: [
      { key: 'flow_count', label: 'Flow count', unit: 'flows', hint: 'Total number of flows (connections) in the 5-minute window. Real CIC-IDS2018 windows contain thousands of flows.' },
      { key: 'unique_dst_ports', label: 'Unique destination ports', unit: 'ports', hint: 'How many distinct destination ports were contacted. Scanning shows very high diversity.' },
      { key: 'unique_protocols', label: 'Unique protocols', unit: 'protocols', hint: 'Distinct L4 protocols observed (e.g., TCP, UDP, ICMP).' },
    ],
  },
  {
    title: 'Traffic volume',
    hint: 'Window totals — the sum of all packets / bytes in each direction.',
    fields: [
      { key: 'forward_packets', label: 'Total forward packets', unit: 'packets', hint: 'All packets sent client → server across the window.' },
      { key: 'backward_packets', label: 'Total backward packets', unit: 'packets', hint: 'All packets sent server → client across the window.' },
      { key: 'forward_bytes', label: 'Total forward bytes', unit: 'bytes', hint: 'Payload bytes sent client → server across the window.' },
      { key: 'backward_bytes', label: 'Total backward bytes', unit: 'bytes', hint: 'Payload bytes sent server → client across the window.' },
    ],
  },
  {
    title: 'Largest flow',
    hint: 'The single most active flow in the window (peak per-flow values).',
    fields: [
      { key: 'max_fwd_packets_per_flow', label: 'Peak forward packets (one flow)', unit: 'packets', hint: 'Most packets any single flow sent in the forward direction.' },
      { key: 'max_bwd_packets_per_flow', label: 'Peak backward packets (one flow)', unit: 'packets', hint: 'Most packets any single flow sent in the backward direction.' },
      { key: 'max_fwd_bytes_per_flow', label: 'Peak forward bytes (one flow)', unit: 'bytes', hint: 'Most bytes any single flow sent forward.' },
      { key: 'max_bwd_bytes_per_flow', label: 'Peak backward bytes (one flow)', unit: 'bytes', hint: 'Most bytes any single flow sent backward.' },
    ],
  },
  {
    title: 'Flow duration',
    hint: 'How long flows live, in seconds. The model measures time in microseconds internally.',
    fields: [
      { key: 'avg_flow_duration_sec', label: 'Average flow duration', unit: 'seconds', hint: 'Typical duration of a flow. Real windows average ~12 s.' },
      { key: 'max_flow_duration_sec', label: 'Longest flow duration', unit: 'seconds', hint: 'Duration of the longest-lived flow (often the 120 s capture timeout).' },
      { key: 'min_flow_duration_sec', label: 'Shortest flow duration', unit: 'seconds', hint: 'Shortest-lived flow (leave 0 if unknown; tiny values are typical).' },
    ],
  },
  {
    title: 'Packet characteristics',
    hint: 'Packet-size profile in bytes, per direction.',
    fields: [
      { key: 'avg_fwd_packet_size', label: 'Average forward packet size', unit: 'bytes', hint: 'Typical forward packet payload size (~57 B for web traffic).' },
      { key: 'avg_bwd_packet_size', label: 'Average backward packet size', unit: 'bytes', hint: 'Typical backward packet payload size (~108 B for web traffic; larger for downloads).' },
      { key: 'max_fwd_packet_size', label: 'Typical largest forward packet', unit: 'bytes', hint: 'Largest packet in a typical flow, forward direction (~1460 B at MTU).' },
      { key: 'max_bwd_packet_size', label: 'Typical largest backward packet', unit: 'bytes', hint: 'Largest packet in a typical flow, backward direction.' },
      { key: 'min_fwd_packet_size', label: 'Smallest forward packet', unit: 'bytes', hint: 'Smallest forward packet observed (~54 B for a bare TCP segment).' },
      { key: 'min_bwd_packet_size', label: 'Smallest backward packet', unit: 'bytes', hint: 'Smallest backward packet observed.' },
      { key: 'pkt_len_std', label: 'Packet size variability', unit: 'bytes', hint: 'Standard deviation of packet sizes. Uniform traffic (e.g., floods) has low variability; mixed traffic is higher.' },
    ],
  },
  {
    title: 'Traffic rates',
    hint: 'Per-flow throughput, in bytes/s and packets/s. Cannot be derived from totals.',
    fields: [
      { key: 'avg_flow_bytes_per_sec', label: 'Average flow bytes / s', unit: 'bytes/s', hint: 'Mean per-flow throughput in bytes per second.' },
      { key: 'avg_flow_packets_per_sec', label: 'Average flow packets / s', unit: 'packets/s', hint: 'Mean per-flow packet rate.' },
      { key: 'avg_bwd_packets_per_sec', label: 'Average backward packets / s', unit: 'packets/s', hint: 'Mean per-flow backward packet rate — a strong attack discriminator in the model.' },
    ],
  },
  {
    title: 'Inter-packet timing',
    hint: 'Gaps between packets within flows (inter-arrival times), in seconds.',
    fields: [
      { key: 'avg_iat_sec', label: 'Average gap between packets', unit: 'seconds', hint: 'Typical inter-arrival time between packets in a flow (~4 s for the reference data).' },
      { key: 'iat_std_sec', label: 'Gap variability', unit: 'seconds', hint: 'Standard deviation of inter-arrival times; bursty traffic varies widely.' },
      { key: 'max_iat_sec', label: 'Longest gap', unit: 'seconds', hint: 'Longest pause between packets in a flow.' },
      { key: 'avg_bwd_iat_sec', label: 'Average backward gap', unit: 'seconds', hint: 'Typical gap between backward packets (~0.5 s for the reference data).' },
    ],
  },
  {
    title: 'TCP flags',
    hint: 'Total flag counts across the window. Each flow carries each flag at most once, so counts cannot exceed flow count.',
    fields: [
      { key: 'syn_flag_cnt', label: 'SYN', unit: 'packets', hint: 'Connection requests. ~3% of flows in normal traffic; near 100% in a SYN flood.' },
      { key: 'ack_flag_cnt', label: 'ACK', unit: 'packets', hint: 'Acknowledgements — most established flows contain at least one.' },
      { key: 'rst_flag_cnt', label: 'RST', unit: 'packets', hint: 'Resets — elevated when hosts refuse connections (e.g., scanning closed ports).' },
      { key: 'fin_flag_cnt', label: 'FIN', unit: 'packets', hint: 'Graceful connection teardowns.' },
      { key: 'psh_flag_cnt', label: 'PSH', unit: 'packets', hint: 'Push — data segments marked for immediate delivery.' },
      { key: 'urg_flag_cnt', label: 'URG', unit: 'packets', hint: 'Urgent data (rare in modern traffic).' },
    ],
  },
  {
    title: 'TCP profile',
    hint: 'TCP behaviour of the flows themselves.',
    fields: [
      { key: 'init_fwd_win_byts', label: 'Initial forward window', unit: 'bytes', hint: 'TCP receive window advertised in the first forward segment (~8.7 KB typical).' },
      { key: 'init_bwd_win_byts', label: 'Initial backward window', unit: 'bytes', hint: 'TCP receive window advertised in the first backward segment (~24 KB typical).' },
      { key: 'fwd_seg_size_min', label: 'Minimum forward segment size', unit: 'bytes', hint: 'Smallest forward TCP payload segment (~17 B typical; 0 for pure handshake traffic).' },
    ],
  },
  {
    title: 'Activity / idle behaviour',
    hint: 'Per-flow activity bursts and idle gaps, in seconds.',
    fields: [
      { key: 'active_mean_sec', label: 'Average active time', unit: 'seconds', hint: 'How long a flow stays active between idle gaps (~0.13 s typical).' },
      { key: 'idle_mean_sec', label: 'Average idle time', unit: 'seconds', hint: 'How long a flow sits idle between bursts (~4.8 s typical).' },
    ],
  },
  {
    title: 'Network balance',
    hint: 'Directional asymmetry of the window.',
    fields: [
      { key: 'down_up_ratio', label: 'Down / up ratio', unit: 'ratio', hint: 'Backward bytes ÷ forward bytes. ~0.45 for the reference data; very low for floods, very high for downloads.' },
    ],
  },
];

const initial = Object.fromEntries(
  groups.flatMap((g) => g.fields.map((f) => [f.key, '']))
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
      {groups.map((group, gi) => (
        <fieldset key={group.title}>
          <legend>
            <span className="legend-num">0{gi + 1}</span> {group.title}
          </legend>
          {group.hint && <p className="group-hint">{group.hint}</p>}
          <div className="field-grid">
            {group.fields.map((field) => (
              <label
                className={isInvalid(field.key) ? 'invalid' : ''}
                key={field.key}
              >
                <span title={field.hint}>
                  {field.label}
                  <i className="field-hint" aria-hidden="true">ⓘ</i>
                </span>
                <div className="input-wrap">
                  <input
                    type="number"
                    min="0"
                    step="any"
                    inputMode="decimal"
                    value={values[field.key]}
                    placeholder="0"
                    onBlur={() => setTouched({ ...touched, [field.key]: true })}
                    onChange={(e) =>
                      setValues({ ...values, [field.key]: e.target.value })
                    }
                  />
                  <small>{field.unit}</small>
                </div>
                {isInvalid(field.key) && <em>Enter a finite value of 0 or more.</em>}
              </label>
            ))}
          </div>
        </fieldset>
      ))}
      <div className="form-submit">
        <p>
          Fields describe one 5-minute observation window. Demo presets populate
          input fields only — all predictions are calculated by the ML model.
        </p>
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