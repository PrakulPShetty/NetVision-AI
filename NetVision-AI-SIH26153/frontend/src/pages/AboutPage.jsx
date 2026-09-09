import React from 'react';
import NetVisionLogo from '../components/common/NetVisionLogo';
import { 
  Eye, 
  Cpu, 
  TrendingUp, 
  BrainCircuit, 
  ShieldAlert, 
  Layers, 
  CheckCircle2,
  Lock
} from 'lucide-react';

export default function AboutPage() {
  const pillars = [
    {
      id: '01',
      title: 'OBSERVE',
      subtitle: 'Continuous Telemetry Ingestion',
      icon: Eye,
      description: 'Ingests practical network flow telemetry across 5-minute aggregation windows, capturing transport protocol statistics, flag counts, packet rates, and payload byte ratios.'
    },
    {
      id: '02',
      title: 'UNDERSTAND',
      subtitle: 'Runtime Feature Engineering',
      icon: Cpu,
      description: 'Transforms raw network traffic into a validated 138-feature temporal representation using the RuntimeFeatureTransformer without losing subtle protocol flag dynamics.'
    },
    {
      id: '03',
      title: 'FORECAST',
      subtitle: 'Multi-Horizon Markov World Model',
      icon: TrendingUp,
      description: 'Executes a 50:50 soft-voting ensemble (XGBoost + Random Forest-SMOTE) coupled with a 2-state Markov transition model to forecast attack escalation up to +60 minutes into the future.'
    },
    {
      id: '04',
      title: 'EXPLAIN',
      subtitle: 'Probability-Space SHAP Attribution',
      icon: BrainCircuit,
      description: 'Deconstructs ensemble probability predictions into exact feature attributions using interventional TreeSHAP in probability space, ensuring complete model transparency.'
    },
    {
      id: '05',
      title: 'RESPOND',
      subtitle: 'MITRE ATT&CK Behavioral Mapping',
      icon: ShieldAlert,
      description: 'Correlates observable temporal behavior with standardized MITRE ATT&CK techniques (T1046, T1498, T1498.001) to provide actionable prescriptive mitigation recommendations.'
    }
  ];

  return (
    <div className="w-full flex flex-col gap-6 select-none font-sans max-w-6xl mx-auto">
      {/* Hero Header */}
      <div className="bg-surface-lowest p-8 border border-outline-variant/40 rounded flex flex-col items-center text-center shadow-xl">
        <NetVisionLogo className="h-12 mb-4" />
        <h1 className="text-2xl font-bold font-mono text-on-surface uppercase tracking-tight">
          Predictive Network Security Intelligence
        </h1>
        <p className="text-sm font-mono text-outline mt-2 max-w-2xl leading-relaxed">
          NetVision AI transitions enterprise network security from reactive threshold alerts to proactive multi-horizon temporal forecasting and explainable threat intelligence.
        </p>
      </div>

      {/* Why Temporal Forecasting Matters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-surface-lowest p-6 border border-outline-variant/40 rounded">
          <span className="font-mono text-xs text-error font-bold uppercase block mb-2">THE REACTIVE PARADIGM</span>
          <h3 className="text-base font-bold text-on-surface mb-2">Traditional Intrusion Detection</h3>
          <p className="text-xs text-on-surface-variant leading-relaxed">
            Conventional SIEM and NIDS tools trigger notifications only after packet thresholds are breached or signature patterns match known IOCs. By the time an analyst reviews an alert, socket buffers are saturated, Kerberos tickets may be compromised, or data exfiltration has already commenced.
          </p>
        </div>

        <div className="bg-surface-lowest p-6 border border-outline-variant/40 rounded">
          <span className="font-mono text-xs text-primary font-bold uppercase block mb-2">THE PREDICTIVE PARADIGM</span>
          <h3 className="text-base font-bold text-on-surface mb-2">NetVision AI Temporal Forecasting</h3>
          <p className="text-xs text-on-surface-variant leading-relaxed">
            NetVision AI evaluates early volumetric shift and protocol flag anomalies, projecting future attack probabilities across 10, 20, 30, 45, and 60-minute horizons. Security operation centers gain pre-breach lead time to enforce confinement before escalation peaks.
          </p>
        </div>
      </div>

      {/* 5 Core Pillars */}
      <div className="bg-surface-lowest p-6 border border-outline-variant/40 rounded flex flex-col gap-4">
        <h3 className="font-mono text-sm font-bold text-on-surface uppercase pb-3 border-b border-outline-variant/30 flex items-center gap-2">
          <Layers className="w-4 h-4 text-primary" />
          The NetVision Operational Architecture
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mt-2">
          {pillars.map((p) => {
            const Icon = p.icon;
            return (
              <div key={p.id} className="bg-surface-low p-4 rounded border border-outline-variant/30 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-mono text-xs text-primary font-bold bg-primary/10 px-2 py-0.5 rounded border border-primary/20">
                      {p.id}
                    </span>
                    <Icon className="w-5 h-5 text-secondary" />
                  </div>
                  <h4 className="font-mono text-sm font-bold text-on-surface">{p.title}</h4>
                  <span className="font-mono text-[10px] text-outline block mb-2">{p.subtitle}</span>
                  <p className="text-xs text-on-surface-variant leading-relaxed">
                    {p.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Technical Specifications */}
      <div className="bg-surface-lowest p-6 border border-outline-variant/40 rounded flex flex-col">
        <h3 className="font-mono text-sm font-bold text-on-surface uppercase mb-4 pb-3 border-b border-outline-variant/30">
          Core Engine Specifications
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
          <div className="bg-surface-low p-3.5 rounded border border-outline-variant/30">
            <span className="text-[10px] text-outline uppercase block">SUPERVISED ENSEMBLE</span>
            <span className="text-on-surface font-bold text-sm block mt-1">XGBoost + RF-SMOTE</span>
            <span className="text-[10px] text-primary block mt-1">50:50 Soft-Voting</span>
          </div>

          <div className="bg-surface-low p-3.5 rounded border border-outline-variant/30">
            <span className="text-[10px] text-outline uppercase block">WORLD MODEL</span>
            <span className="text-on-surface font-bold text-sm block mt-1">2-State Markov Chain</span>
            <span className="text-[10px] text-secondary block mt-1">+60m Forecast Horizon</span>
          </div>

          <div className="bg-surface-low p-3.5 rounded border border-outline-variant/30">
            <span className="text-[10px] text-outline uppercase block">EXPLAINABILITY</span>
            <span className="text-on-surface font-bold text-sm block mt-1">Probability-Space SHAP</span>
            <span className="text-[10px] text-tertiary block mt-1">Interventional TreeSHAP</span>
          </div>

          <div className="bg-surface-low p-3.5 rounded border border-outline-variant/30">
            <span className="text-[10px] text-outline uppercase block">MITRE CORRELATION</span>
            <span className="text-on-surface font-bold text-sm block mt-1">ATT&CK Behavioral</span>
            <span className="text-[10px] text-amber-400 block mt-1">T1046, T1498, T1498.001</span>
          </div>
        </div>
      </div>
    </div>
  );
}
