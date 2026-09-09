/**
 * NetVision AI — Demo Input Presets
 * 
 * Provides predefined practical network traffic INPUT VALUES for testing & demonstration.
 * NOTE: These are strictly input statistics. All predictions, forecasts, SHAP values, 
 * and MITRE mappings are computed live by the FastAPI backend engine.
 */

export const TRAFFIC_PRESETS = [
  {
    id: 'nominal',
    title: 'Nominal Enterprise Baseline',
    badge: 'BENIGN TRAFFIC',
    badgeColor: 'bg-primary/20 text-primary border-primary/30',
    description: 'Standard background HTTP/S, SSL, and DB query traffic across 5-minute aggregation window.',
    data: {
      flow_count: 50,
      unique_dst_ports: 4,
      unique_protocols: 2,
      forward_packets: 320,
      backward_packets: 480,
      forward_bytes: 48000,
      backward_bytes: 210000,
      flow_duration: 120000,
      flow_bytes_per_sec: 2150.0,
      flow_packets_per_sec: 6.67,
      backward_packets_per_sec: 4.0,
      syn_flag_cnt: 8,
      ack_flag_cnt: 780,
      rst_flag_cnt: 0,
      fin_flag_cnt: 12,
      psh_flag_cnt: 45,
      urg_flag_cnt: 0,
    }
  },
  {
    id: 'reconnaissance',
    title: 'Port Discovery & Reconnaissance',
    badge: 'SUSPICIOUS RECON',
    badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    description: 'Broad multi-port connection attempts across internal subnet with high destination port diversity (T1046).',
    data: {
      flow_count: 450,
      unique_dst_ports: 85,
      unique_protocols: 2,
      forward_packets: 1800,
      backward_packets: 950,
      forward_bytes: 140000,
      backward_bytes: 65000,
      flow_duration: 250000,
      flow_bytes_per_sec: 820.0,
      flow_packets_per_sec: 11.0,
      backward_packets_per_sec: 3.8,
      syn_flag_cnt: 420,
      ack_flag_cnt: 510,
      rst_flag_cnt: 180,
      fin_flag_cnt: 5,
      psh_flag_cnt: 12,
      urg_flag_cnt: 0,
    }
  },
  {
    id: 'volumetric_flood',
    title: 'Volumetric SYN Flood Attack',
    badge: 'CRITICAL ATTACK',
    badgeColor: 'bg-error-container/40 text-error border-error/40',
    description: 'Concentrated high-density TCP SYN connection request flood targeting application gateway (T1498.001 / T1498).',
    data: {
      flow_count: 2450,
      unique_dst_ports: 2,
      unique_protocols: 1,
      forward_packets: 18500,
      backward_packets: 240,
      forward_bytes: 1180000,
      backward_bytes: 12000,
      flow_duration: 300000,
      flow_bytes_per_sec: 3973.33,
      flow_packets_per_sec: 62.47,
      backward_packets_per_sec: 0.8,
      syn_flag_cnt: 18200,
      ack_flag_cnt: 120,
      rst_flag_cnt: 40,
      fin_flag_cnt: 0,
      psh_flag_cnt: 0,
      urg_flag_cnt: 0,
    }
  }
];
