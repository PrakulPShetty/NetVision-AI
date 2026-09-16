/**
 * NetVision AI — model feature descriptions
 *
 * The ML pipeline exposes the frozen 138-feature representation
 * (e.g. "SYN Flag Cnt_sum", "Flow Duration_mean"). Raw names are not
 * meaningful to a SOC analyst, so every feature is resolved to a readable
 * label, the aggregation the runtime transformer applied, a plain-language
 * meaning, and the traffic behaviour category it belongs to.
 *
 * Descriptions are presentation only — they never invent model output.
 */

const AGGREGATIONS = {
  sum: 'window total',
  mean: 'average across flows',
  max: 'largest single flow',
  min: 'smallest single flow',
  std: 'spread across flows',
  var: 'variance across flows',
};

const BASES = {
  'Tot Fwd Pkts': {
    label: 'Forward packets',
    category: 'Traffic volume',
    meaning: 'Packets sent from source to destination across the observation window.',
  },
  'Tot Bwd Pkts': {
    label: 'Backward packets',
    category: 'Traffic volume',
    meaning: 'Packets returned by the destination. A collapse in return traffic can indicate half-open or one-way behaviour.',
  },
  'TotLen Fwd Pkts': {
    label: 'Forward bytes',
    category: 'Traffic volume',
    meaning: 'Payload volume sent outbound. Large outbound volume with little return traffic is characteristic of floods.',
  },
  'TotLen Bwd Pkts': {
    label: 'Backward bytes',
    category: 'Traffic volume',
    meaning: 'Payload volume received. Bulk inbound transfer usually indicates ordinary download or database traffic.',
  },
  'Flow Duration': {
    label: 'Flow duration',
    category: 'Timing',
    meaning: 'How long flows stayed open. Very short flows accompany scans; long flows accompany sustained sessions.',
  },
  'Flow IAT Mean': {
    label: 'Mean inter-arrival time',
    category: 'Timing',
    meaning: 'Average gap between packets in a flow. Uniform, tiny gaps indicate automated traffic.',
  },
  'Flow IAT Std': {
    label: 'Inter-arrival variability',
    category: 'Timing',
    meaning: 'How irregular packet spacing is. Machine-generated traffic is far more regular than human traffic.',
  },
  'Flow IAT Max': {
    label: 'Longest inter-arrival gap',
    category: 'Timing',
    meaning: 'Longest pause between packets, indicating idle periods inside flows.',
  },
  'Fwd IAT Tot': {
    label: 'Forward total inter-arrival',
    category: 'Timing',
    meaning: 'Accumulated forward packet spacing for the window.',
  },
  'Fwd IAT Mean': {
    label: 'Forward mean inter-arrival',
    category: 'Timing',
    meaning: 'Average spacing between outbound packets.',
  },
  'Fwd IAT Std': {
    label: 'Forward inter-arrival variability',
    category: 'Timing',
    meaning: 'Consistency of outbound packet pacing.',
  },
  'Fwd IAT Max': {
    label: 'Longest forward gap',
    category: 'Timing',
    meaning: 'Longest idle period in the outbound direction.',
  },
  'Bwd IAT Tot': {
    label: 'Backward total inter-arrival',
    category: 'Timing',
    meaning: 'Accumulated return packet spacing for the window.',
  },
  'Bwd IAT Mean': {
    label: 'Backward mean inter-arrival',
    category: 'Timing',
    meaning: 'Average spacing between return packets — a strong discriminator in this model.',
  },
  'Bwd IAT Std': {
    label: 'Backward inter-arrival variability',
    category: 'Timing',
    meaning: 'Consistency of return packet pacing.',
  },
  'Bwd IAT Max': {
    label: 'Longest backward gap',
    category: 'Timing',
    meaning: 'Longest idle period in the return direction.',
  },
  'Bwd IAT Min': {
    label: 'Shortest backward gap',
    category: 'Timing',
    meaning: 'Tightest return packet spacing observed.',
  },
  'Fwd Pkt Len Max': {
    label: 'Largest forward packet',
    category: 'Packet size',
    meaning: 'Largest outbound segment. Full-MTU segments indicate data transfer rather than bare handshakes.',
  },
  'Fwd Pkt Len Min': {
    label: 'Smallest forward packet',
    category: 'Packet size',
    meaning: 'Smallest outbound segment, often a bare TCP control segment.',
  },
  'Fwd Pkt Len Mean': {
    label: 'Average forward packet size',
    category: 'Packet size',
    meaning: 'Typical outbound segment size.',
  },
  'Fwd Pkt Len Std': {
    label: 'Forward packet size variability',
    category: 'Packet size',
    meaning: 'How mixed the outbound packet sizes are.',
  },
  'Bwd Pkt Len Max': {
    label: 'Largest backward packet',
    category: 'Packet size',
    meaning: 'Largest inbound segment.',
  },
  'Bwd Pkt Len Min': {
    label: 'Smallest backward packet',
    category: 'Packet size',
    meaning: 'Smallest inbound segment.',
  },
  'Bwd Pkt Len Mean': {
    label: 'Average backward packet size',
    category: 'Packet size',
    meaning: 'Typical inbound segment size.',
  },
  'Bwd Pkt Len Std': {
    label: 'Backward packet size variability',
    category: 'Packet size',
    meaning: 'How mixed the inbound packet sizes are.',
  },
  'Pkt Len Min': {
    label: 'Smallest packet',
    category: 'Packet size',
    meaning: 'Smallest packet observed in either direction.',
  },
  'Pkt Len Max': {
    label: 'Largest packet',
    category: 'Packet size',
    meaning: 'Largest packet observed in either direction.',
  },
  'Pkt Len Mean': {
    label: 'Average packet size',
    category: 'Packet size',
    meaning: 'Mean packet size across the window.',
  },
  'Pkt Len Std': {
    label: 'Packet size variability',
    category: 'Packet size',
    meaning: 'Uniform traffic such as a flood shows low variability; mixed enterprise traffic is higher.',
  },
  'Pkt Len Var': {
    label: 'Packet size variance',
    category: 'Packet size',
    meaning: 'Squared spread of packet sizes.',
  },
  'Pkt Size Avg': {
    label: 'Average packet size',
    category: 'Packet size',
    meaning: 'Aggregate average packet size across the window.',
  },
  'Flow Byts/s': {
    label: 'Throughput (bytes/s)',
    category: 'Rate',
    meaning: 'Per-flow data rate. Sustained extreme throughput is characteristic of volumetric attacks.',
  },
  'Flow Pkts/s': {
    label: 'Packet rate',
    category: 'Rate',
    meaning: 'Packets per second per flow — the clearest signal of automated, high-rate traffic.',
  },
  'Bwd Pkts/s': {
    label: 'Backward packet rate',
    category: 'Rate',
    meaning: 'Return packets per second. A strong discriminator between responsive and unresponsive destinations.',
  },
  'Fwd PSH Flags': {
    label: 'PSH flag activity',
    category: 'TCP flags',
    meaning: 'Segments pushed for immediate delivery, typical of interactive or scripted payloads.',
  },
  'Fwd URG Flags': {
    label: 'URG flag activity',
    category: 'TCP flags',
    meaning: 'Urgent-pointer segments, rare in legitimate modern traffic.',
  },
  'FIN Flag Cnt': {
    label: 'FIN flag count',
    category: 'TCP flags',
    meaning: 'Graceful connection teardowns. Very low counts suggest connections that never closed cleanly.',
  },
  'SYN Flag Cnt': {
    label: 'SYN flag count',
    category: 'TCP flags',
    meaning: 'Connection attempts. Proportionally high SYN volume with little completion indicates floods or scanning.',
  },
  'RST Flag Cnt': {
    label: 'RST flag count',
    category: 'TCP flags',
    meaning: 'Connection resets, elevated when hosts refuse connections — common in service discovery.',
  },
  'PSH Flag Cnt': {
    label: 'PSH flag count',
    category: 'TCP flags',
    meaning: 'Segments marked for immediate delivery across the window.',
  },
  'ACK Flag Cnt': {
    label: 'ACK flag count',
    category: 'TCP flags',
    meaning: 'Acknowledgements. Most established flows contain at least one.',
  },
  'URG Flag Cnt': {
    label: 'URG flag count',
    category: 'TCP flags',
    meaning: 'Urgent-pointer segments across the window.',
  },
  'CWE Flag Count': {
    label: 'CWE flag count',
    category: 'TCP profile',
    meaning: 'Congestion-window-reduced notifications from the network.',
  },
  'ECE Flag Cnt': {
    label: 'ECE flag count',
    category: 'TCP profile',
    meaning: 'Explicit congestion notifications, an indicator of saturated links.',
  },
  'Down/Up Ratio': {
    label: 'Down/up byte ratio',
    category: 'Directional balance',
    meaning: 'Backward bytes divided by forward bytes. Very low values indicate one-way outbound traffic.',
  },
  'Fwd Header Len': {
    label: 'Forward header length',
    category: 'TCP profile',
    meaning: 'Header overhead in the outbound direction.',
  },
  'Bwd Header Len': {
    label: 'Backward header length',
    category: 'TCP profile',
    meaning: 'Header overhead in the return direction.',
  },
  'Init Fwd Win Byts': {
    label: 'Initial forward window',
    category: 'TCP profile',
    meaning: 'Receive window advertised in the first outbound segment.',
  },
  'Init Bwd Win Byts': {
    label: 'Initial backward window',
    category: 'TCP profile',
    meaning: 'Receive window advertised by the destination.',
  },
  'Fwd Seg Size Min': {
    label: 'Minimum forward segment size',
    category: 'TCP profile',
    meaning: 'Smallest outbound TCP payload segment.',
  },
  'Active Mean': {
    label: 'Average active time',
    category: 'Activity pattern',
    meaning: 'How long flows stay active between idle gaps.',
  },
  'Active Std': {
    label: 'Active time variability',
    category: 'Activity pattern',
    meaning: 'Consistency of active bursts.',
  },
  'Active Max': {
    label: 'Longest active period',
    category: 'Activity pattern',
    meaning: 'Longest continuous activity burst.',
  },
  'Active Min': {
    label: 'Shortest active period',
    category: 'Activity pattern',
    meaning: 'Briefest activity burst.',
  },
  'Idle Mean': {
    label: 'Average idle time',
    category: 'Activity pattern',
    meaning: 'How long flows sit idle between bursts — long idle periods suggest patient reconnaissance.',
  },
  'Idle Std': {
    label: 'Idle time variability',
    category: 'Activity pattern',
    meaning: 'Consistency of idle gaps.',
  },
  'Idle Max': {
    label: 'Longest idle period',
    category: 'Activity pattern',
    meaning: 'Longest inactivity before a flow resumed.',
  },
  'Idle Min': {
    label: 'Shortest idle period',
    category: 'Activity pattern',
    meaning: 'Briefest inactivity gap.',
  },
};

const CACHE = new Map();

/**
 * Resolve a raw model feature name into display metadata.
 * @param {string} raw e.g. "SYN Flag Cnt_sum"
 */
export function describeFeature(raw) {
  if (!raw) return { raw: '', label: 'Unknown feature', aggregation: null, category: 'Other', meaning: '' };
  if (CACHE.has(raw)) return CACHE.get(raw);

  let base = raw;
  let aggregation = null;
  const match = /^(.*)_(sum|mean|max|min|std|var)$/.exec(raw);
  if (match) {
    base = match[1];
    aggregation = match[2];
  }

  const known = BASES[base];
  const prettyBase = base.replace(/_/g, ' ').replace(/\s+/g, ' ').trim();

  const resolved = {
    raw,
    base,
    aggregation,
    aggregationLabel: aggregation ? AGGREGATIONS[aggregation] : null,
    label: known ? known.label : prettyBase,
    category: known ? known.category : 'Other',
    meaning: known ? known.meaning : '',
  };

  CACHE.set(raw, resolved);
  return resolved;
}

/** Sort helper: strongest absolute attribution first. */
export function byAbsoluteSignal(a, b) {
  return Math.abs(b.value) - Math.abs(a.value);
}
