/**
 * PHASE 1 ISOLATED DEVELOPMENT FIXTURE DATA
 * 
 * IMPORTANT: This file contains isolated fixture data for Phase 1 UI development
 * and component visualization. It does not connect to the production backend.
 * Phase 2 will replace these mock interfaces with live API endpoints.
 */

export const TRAFFIC_PRESETS = [
  {
    id: 'nominal',
    name: 'Nominal Web Traffic',
    description: 'Standard HTTP/S user traffic with low flow counts and balanced TCP flag ratios.',
    data: {
      flowCount: 420,
      uniqueDstPorts: 4,
      uniqueProtocols: 2,
      totalFwdPackets: 1250,
      totalFwdBytes: 845000,
      totalBwdPackets: 1890,
      totalBwdBytes: 2450000,
      flowDurationMs: 4500,
      flowBytesPerSec: 732222.2,
      flowPacketsPerSec: 697.7,
      bwdPacketsPerSec: 420.0,
      synCount: 15,
      ackCount: 3100,
      rstCount: 2,
      finCount: 12
    }
  },
  {
    id: 'elevated_scanning',
    name: 'Elevated Port Scan Profile',
    description: 'High frequency TCP SYN connection attempts across multiple destination ports.',
    data: {
      flowCount: 8900,
      uniqueDstPorts: 1420,
      uniqueProtocols: 3,
      totalFwdPackets: 18450,
      totalFwdBytes: 1107000,
      totalBwdPackets: 2300,
      totalBwdBytes: 138000,
      flowDurationMs: 12000,
      flowBytesPerSec: 103750.0,
      flowPacketsPerSec: 1729.1,
      bwdPacketsPerSec: 191.6,
      synCount: 16500,
      ackCount: 1200,
      rstCount: 840,
      finCount: 45
    }
  },
  {
    id: 'multistage_intrusion',
    name: 'Multi-stage Intrusion Sequence',
    description: 'Complex pattern featuring recon activity, elevated asymmetry, and persistent outbound volume.',
    data: {
      flowCount: 15400,
      uniqueDstPorts: 310,
      uniqueProtocols: 4,
      totalFwdPackets: 48200,
      totalFwdBytes: 34500000,
      totalBwdPackets: 12400,
      totalBwdBytes: 1200000,
      flowDurationMs: 30000,
      flowBytesPerSec: 1190000.0,
      flowPacketsPerSec: 2020.0,
      bwdPacketsPerSec: 413.3,
      synCount: 8900,
      ackCount: 41000,
      rstCount: 3200,
      finCount: 180
    }
  }
];

export const MOCK_FORECAST_RESULT = {
  timestamp: new Date().toISOString(),
  currentState: {
    label: 'ATTACK',
    probability: 0.842,
    confidence: 'HIGH',
    assessmentSummary: 'The observed traffic profile is currently assessed as an ATTACK state with an estimated attack probability of 84.2%.'
  },
  forecastTimeline: [
    { horizon: 'Current', minutes: 0, probability: 84.2, status: 'ELEVATED' },
    { horizon: '10m', minutes: 10, probability: 88.5, status: 'CRITICAL' },
    { horizon: '20m', minutes: 20, probability: 91.2, status: 'CRITICAL' },
    { horizon: '30m', minutes: 30, probability: 87.8, status: 'CRITICAL' },
    { horizon: '45m', minutes: 45, probability: 79.4, status: 'ELEVATED' },
    { horizon: '60m', minutes: 60, probability: 68.1, status: 'ELEVATED' }
  ],
  decisionThreshold: {
    value: 0.40,
    percentage: 40,
    label: '40% Reference Threshold',
    description: 'Reference probability threshold used by the current-state decision layer.'
  },
  explanationCopy: {
    forecastSummary: 'NetVision AI estimates the probability of an attack state at multiple future time horizons rather than producing only a single static detection result.',
    temporalTrend: 'The Markov World Model projects sustained elevated attack probability peaking at 91.2% over the 20-minute horizon before gradually dissipating over 60 minutes.'
  }
};

export const MOCK_XAI_RESULT = {
  layer1Narrative: 'The forecast is primarily influenced by elevated traffic volume and destination diversity. These observed characteristics contribute strongly to the predicted attack probability.',
  layer2Contributions: [
    {
      feature: 'Destination Port Diversity',
      rawKey: 'unique_dst_ports',
      value: '1,420 unique ports',
      contribution: 'High',
      influence: 'Positive',
      interpretation: 'Broad destination port activity across short intervals contributes significantly to the elevated attack forecast.'
    },
    {
      feature: 'SYN Flag Density',
      rawKey: 'syn_count',
      value: '16,500 SYN packets',
      contribution: 'High',
      influence: 'Positive',
      interpretation: 'Unusually high ratio of TCP SYN requests relative to completed ACK handshakes indicates active scanning activity.'
    },
    {
      feature: 'Flow Packet Rate',
      rawKey: 'flow_pkts_per_sec',
      value: '1,729.1 pkts/s',
      contribution: 'Medium',
      influence: 'Positive',
      interpretation: 'High packet volume rate accelerates security state transition toward elevated risk horizons.'
    },
    {
      feature: 'Flow Duration Asymmetry',
      rawKey: 'bwd_fwd_ratio',
      value: '0.12 backward ratio',
      contribution: 'Medium',
      influence: 'Positive',
      interpretation: 'Low backward packet volume relative to forward requests suggests unacknowledged probe probes.'
    },
    {
      feature: 'RST Flag Ratio',
      rawKey: 'rst_count',
      value: '840 RST flags',
      contribution: 'Low',
      influence: 'Positive',
      interpretation: 'Connection rejections by target endpoints confirm closed port probes.'
    }
  ],
  layer3ShapValues: [
    { feature: 'Unique Dst Ports', shapValue: +0.28, key: 'dst_ports' },
    { feature: 'SYN Flag Rate', shapValue: +0.24, key: 'syn_rate' },
    { feature: 'Flow Pkts/sec', shapValue: +0.16, key: 'flow_pkts' },
    { feature: 'Bwd/Fwd Ratio', shapValue: +0.11, key: 'bwd_ratio' },
    { feature: 'RST Flag Rate', shapValue: +0.05, key: 'rst_rate' },
    { feature: 'Flow Duration', shapValue: -0.04, key: 'duration' }
  ]
};

export const MOCK_MITRE_RESULT = {
  hasCorrelation: true,
  technique: {
    id: 'T1046',
    name: 'Network Service Discovery',
    tactic: 'Reconnaissance',
    tacticsList: ['Reconnaissance', 'Discovery'],
    confidenceScore: 0.89,
    confidenceLabel: 'HIGH CONFIDENCE (89%)',
    summary: 'The observed traffic evidence was correlated with MITRE ATT&CK Technique T1046 based on systemic port probing indicators.',
    evidence: [
      'Sequential SYN attempts across >1,000 distinct TCP ports within 12 seconds.',
      'High ratio of unacknowledged SYN packets (SYN:ACK ratio > 13:1).',
      'Destination port distribution spans known administrative and service ports (22, 80, 443, 3389, 8080).'
    ],
    supportingFeatures: [
      'unique_dst_ports = 1,420',
      'syn_count = 16,500',
      'bwd_pkts_per_sec = 191.6'
    ],
    technicalInterpretation: 'Adversaries may attempt to get a listing of services running on remote hosts to identify vulnerable targets. The observed traffic pattern exhibits signature indicators of automated network port sweeps.',
    limitations: 'MITRE ATT&CK correlation represents behavioral pattern matching based on observed traffic telemetry, separate from the core ML security-state forecast.'
  }
};

export const MOCK_TOPOLOGY_NODES = [
  { id: 'internet', label: 'External Internet', type: 'cloud', ip: '0.0.0.0/0', status: 'external', pos: [-6, 0, 0] },
  { id: 'gateway', label: 'Perimeter Gateway', type: 'firewall', ip: '192.168.1.1', status: 'elevated', pos: [-2.5, 0.5, 0] },
  { id: 'appserver', label: 'Application Cluster', type: 'server', ip: '10.0.1.50', status: 'elevated', pos: [1, 1.2, -1.5] },
  { id: 'authserver', label: 'Auth & Identity', type: 'server', ip: '10.0.1.60', status: 'normal', pos: [1, -1.2, 1.5] },
  { id: 'database', label: 'Database Service', type: 'database', ip: '10.0.2.100', status: 'normal', pos: [4.5, 0, 0] },
  { id: 'endpoints', label: 'User Workstations', type: 'endpoint', ip: '10.0.3.0/24', status: 'normal', pos: [-1, -2, -0.5] }
];

export const MOCK_TOPOLOGY_EDGES = [
  { from: 'internet', to: 'gateway', label: 'Inbound Ingress' },
  { from: 'gateway', to: 'appserver', label: 'HTTP/HTTPS Proxy' },
  { from: 'gateway', to: 'authserver', label: 'RADIUS/OAuth' },
  { from: 'appserver', to: 'database', label: 'DB Query Pool' },
  { from: 'authserver', to: 'database', label: 'User Audit Store' },
  { from: 'gateway', to: 'endpoints', label: 'Internal Segment' }
];
