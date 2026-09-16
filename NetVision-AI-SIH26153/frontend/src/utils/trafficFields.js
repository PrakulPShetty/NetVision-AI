/**
 * NetVision AI — 5-minute traffic profile definition
 *
 * Field definitions live here (not inside the form component) so that the
 * form, the demo scenarios and the live profile summary all describe the same
 * observation window with identical labels, units and help text.
 *
 * Every field maps to at least one of the 138 model features produced by the
 * runtime feature transformer on the backend.
 */

export const TRAFFIC_GROUPS = [
  {
    id: 'window',
    title: 'Observation window',
    hint: 'The traffic summarized below was observed during one 5-minute window.',
    fields: [
      { key: 'flow_count', label: 'Flow count', unit: 'flows', hint: 'Total number of flows (connections) in the 5-minute window. Real CIC-IDS2018 windows contain thousands of flows.' },
      { key: 'unique_dst_ports', label: 'Unique destination ports', unit: 'ports', hint: 'How many distinct destination ports were contacted. Scanning shows very high diversity.' },
      { key: 'unique_protocols', label: 'Unique protocols', unit: 'protocols', hint: 'Distinct L4 protocols observed (e.g., TCP, UDP, ICMP).' },
    ],
  },
  {
    id: 'volume',
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
    id: 'largest-flow',
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
    id: 'duration',
    title: 'Flow duration',
    hint: 'How long flows live, in seconds. The model measures time in microseconds internally.',
    fields: [
      { key: 'avg_flow_duration_sec', label: 'Average flow duration', unit: 'seconds', hint: 'Typical duration of a flow. Real windows average ~12 s.' },
      { key: 'max_flow_duration_sec', label: 'Longest flow duration', unit: 'seconds', hint: 'Duration of the longest-lived flow (often the 120 s capture timeout).' },
      { key: 'min_flow_duration_sec', label: 'Shortest flow duration', unit: 'seconds', hint: 'Shortest-lived flow (leave 0 if unknown; tiny values are typical).' },
    ],
  },
  {
    id: 'packet-size',
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
    id: 'rates',
    title: 'Traffic rates',
    hint: 'Per-flow throughput, in bytes/s and packets/s. Cannot be derived from totals.',
    fields: [
      { key: 'avg_flow_bytes_per_sec', label: 'Average flow bytes / s', unit: 'bytes/s', hint: 'Mean per-flow throughput in bytes per second.' },
      { key: 'avg_flow_packets_per_sec', label: 'Average flow packets / s', unit: 'packets/s', hint: 'Mean per-flow packet rate.' },
      { key: 'avg_bwd_packets_per_sec', label: 'Average backward packets / s', unit: 'packets/s', hint: 'Mean per-flow backward packet rate — a strong attack discriminator in the model.' },
    ],
  },
  {
    id: 'timing',
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
    id: 'flags',
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
    id: 'tcp',
    title: 'TCP profile',
    hint: 'TCP behaviour of the flows themselves.',
    fields: [
      { key: 'init_fwd_win_byts', label: 'Initial forward window', unit: 'bytes', hint: 'TCP receive window advertised in the first forward segment (~8.7 KB typical).' },
      { key: 'init_bwd_win_byts', label: 'Initial backward window', unit: 'bytes', hint: 'TCP receive window advertised in the first backward segment (~24 KB typical).' },
      { key: 'fwd_seg_size_min', label: 'Minimum forward segment size', unit: 'bytes', hint: 'Smallest forward TCP payload segment (~17 B typical; 0 for pure handshake traffic).' },
    ],
  },
  {
    id: 'activity',
    title: 'Activity / idle behaviour',
    hint: 'Per-flow activity bursts and idle gaps, in seconds.',
    fields: [
      { key: 'active_mean_sec', label: 'Average active time', unit: 'seconds', hint: 'How long a flow stays active between idle gaps (~0.13 s typical).' },
      { key: 'idle_mean_sec', label: 'Average idle time', unit: 'seconds', hint: 'How long a flow sits idle between bursts (~4.8 s typical).' },
    ],
  },
  {
    id: 'balance',
    title: 'Network balance',
    hint: 'Directional asymmetry of the window.',
    fields: [
      { key: 'down_up_ratio', label: 'Down / up ratio', unit: 'ratio', hint: 'Backward bytes ÷ forward bytes. ~0.45 for the reference data; very low for floods, very high for downloads.' },
    ],
  },
];

export const TRAFFIC_FIELDS = TRAFFIC_GROUPS.flatMap((group) =>
  group.fields.map((field) => ({ ...field, group: group.id, groupTitle: group.title }))
);

/** Blank profile: every field starts as an empty string so validation is explicit. */
export function createEmptyValues() {
  return Object.fromEntries(TRAFFIC_FIELDS.map((field) => [field.key, '']));
}

const num = (value) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : NaN;
};

/** Field keys whose current text is empty, negative or non-numeric. */
export function invalidKeys(values) {
  return TRAFFIC_FIELDS.filter((field) => {
    const parsed = num(values[field.key]);
    return Number.isNaN(parsed);
  }).map((field) => field.key);
}

export function isComplete(values) {
  return invalidKeys(values).length === 0;
}

/** Numeric payload sent to the backend (only when the profile is complete). */
export function toPayload(values) {
  return Object.fromEntries(TRAFFIC_FIELDS.map((field) => [field.key, Number(values[field.key])]));
}

/**
 * Descriptive statistics of the entered observation window.
 *
 * These are arithmetic summaries of the user's own input — they are not model
 * output and are always presented as such. They exist so an analyst can sanity
 * check a profile before running inference.
 */
export function deriveProfile(values) {
  const v = Object.fromEntries(TRAFFIC_FIELDS.map((f) => [f.key, num(values[f.key])]));
  const anyValue = TRAFFIC_FIELDS.some((f) => !Number.isNaN(v[f.key]));
  if (!anyValue) return null;

  const get = (key) => (Number.isNaN(v[key]) ? 0 : v[key]);

  const flows = get('flow_count');
  const fwdPackets = get('forward_packets');
  const bwdPackets = get('backward_packets');
  const fwdBytes = get('forward_bytes');
  const bwdBytes = get('backward_bytes');
  const totalPackets = fwdPackets + bwdPackets;
  const totalBytes = fwdBytes + bwdBytes;

  const ports = get('unique_dst_ports');
  const protocols = get('unique_protocols');

  const flags = [
    { key: 'syn_flag_cnt', label: 'SYN', value: get('syn_flag_cnt') },
    { key: 'ack_flag_cnt', label: 'ACK', value: get('ack_flag_cnt') },
    { key: 'rst_flag_cnt', label: 'RST', value: get('rst_flag_cnt') },
    { key: 'fin_flag_cnt', label: 'FIN', value: get('fin_flag_cnt') },
    { key: 'psh_flag_cnt', label: 'PSH', value: get('psh_flag_cnt') },
    { key: 'urg_flag_cnt', label: 'URG', value: get('urg_flag_cnt') },
  ];

  const observations = [];
  if (flows > 0) {
    const synPerFlow = get('syn_flag_cnt') / flows;
    if (synPerFlow >= 0.8) {
      observations.push({ tone: 'critical', text: `${(synPerFlow * 100).toFixed(0)}% of flows carry a SYN — connection attempts dominate this window.` });
    } else if (synPerFlow <= 0.08 && get('syn_flag_cnt') > 0) {
      observations.push({ tone: 'normal', text: `Only ${(synPerFlow * 100).toFixed(1)}% of flows open a connection, consistent with established sessions.` });
    }
    const portsPerFlow = ports / flows;
    if (portsPerFlow >= 0.4) {
      observations.push({ tone: 'elevated', text: `Destination diversity is high: ${ports.toLocaleString()} ports across ${flows.toLocaleString()} flows.` });
    }
    const rstPerFlow = get('rst_flag_cnt') / flows;
    if (rstPerFlow >= 0.3) {
      observations.push({ tone: 'elevated', text: 'RST responses affect a large share of flows — destinations are refusing connections.' });
    }
    if (bwdPackets === 0 && fwdPackets > 0) {
      observations.push({ tone: 'critical', text: 'No return packets recorded — the window is entirely one-directional.' });
    }
  }
  if (observations.length === 0) {
    observations.push({ tone: 'muted', text: 'No single dominant characteristic stands out from the entered totals alone. The ML ensemble evaluates all 138 derived features.' });
  }

  return {
    flows,
    ports,
    protocols,
    fwdPackets,
    bwdPackets,
    fwdBytes,
    bwdBytes,
    totalPackets,
    totalBytes,
    packetsSplit: totalPackets > 0 ? (fwdPackets / totalPackets) * 100 : 0,
    bytesSplit: totalBytes > 0 ? (fwdBytes / totalBytes) * 100 : 0,
    avgPacketSize: totalPackets > 0 ? totalBytes / totalPackets : 0,
    portsPerFlow: flows > 0 ? ports / flows : 0,
    flags,
    maxFlag: Math.max(1, ...flags.map((f) => f.value)),
    observations,
  };
}

/** Compact number formatting for dense metric cards. */
export function formatCompact(value) {
  if (!Number.isFinite(value)) return '—';
  const abs = Math.abs(value);
  if (abs >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
  if (abs >= 10) return value.toFixed(0);
  return value.toFixed(2).replace(/\.00$/, '');
}
