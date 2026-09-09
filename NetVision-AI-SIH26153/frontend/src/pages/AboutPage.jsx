import React from 'react';
import NetVisionLogo from '../components/common/NetVisionLogo';
import { Shield, Eye, Cpu, TrendingUp, HelpCircle, ShieldCheck, Zap } from 'lucide-react';

export default function AboutPage() {
  const workflowSteps = [
    {
      step: '01',
      title: 'OBSERVE',
      subtitle: 'Traffic Telemetry Ingestion',
      icon: Eye,
      description: 'Ingests network flow telemetry, packet counts, TCP flag ratios, and flow duration vectors in real time.'
    },
    {
      step: '02',
      title: 'UNDERSTAND',
      subtitle: 'Temporal State Representation',
      icon: Cpu,
      description: 'Transforms raw network feature vectors into temporal window representations to capture evolving attack dynamics.'
    },
    {
      step: '03',
      title: 'FORECAST',
      subtitle: 'Markov World Model',
      icon: TrendingUp,
      description: 'Projects security state probabilities over 10m, 20m, 30m, 45m, and 60m future time horizons.'
    },
    {
      step: '04',
      title: 'EXPLAIN',
      subtitle: '3-Layer XAI Engine',
      icon: HelpCircle,
      description: 'Generates human-readable narrative, feature contribution tables, and SHAP log-odds attribution values.'
    },
    {
      step: '05',
      title: 'CORRELATE',
      subtitle: 'MITRE ATT&CK Mapping',
      icon: ShieldCheck,
      description: 'Maps observed behavioral evidence to recognized MITRE ATT&CK techniques (e.g. T1046) when confident evidence exists.'
    },
    {
      step: '06',
      title: 'RESPOND',
      subtitle: 'Proactive Defensive Action',
      icon: Zap,
      description: 'Enables security teams to enact proactive mitigation before high-risk future horizons are reached.'
    }
  ];

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Product Hero Banner */}
      <div className="bg-surface-low border border-surface-border rounded-lg p-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-6 border-b border-surface-border">
          <NetVisionLogo className="h-12" showText={true} />
          <div className="font-mono text-xs text-primary bg-primary-container border border-primary/30 px-3 py-1.5 rounded">
            PREDICTIVE SECURITY PLATFORM
          </div>
        </div>

        <div className="mt-6 space-y-4">
          <h1 className="text-2xl font-bold text-content-primary">
            Shifting Cybersecurity from Reactive Detection to Predictive Intelligence
          </h1>
          <p className="text-sm text-content-secondary leading-relaxed max-w-3xl">
            Traditional network security systems focus primarily on identifying suspicious activity after an intrusion has already materialized. 
            <strong className="text-content-primary ml-1">NetVision AI</strong> introduces a paradigm shift by forecasting how the overall network security state will evolve across future time horizons.
          </p>
        </div>
      </div>

      {/* Core Architectural Workflow */}
      <div className="bg-surface-low border border-surface-border rounded-lg p-8">
        <h2 className="text-lg font-bold text-content-primary mb-2">Core System Architecture & Workflow</h2>
        <p className="text-xs text-content-muted mb-6">
          The six operational phases powering NetVision AI security intelligence:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workflowSteps.map((step) => {
            const Icon = step.icon;
            return (
              <div key={step.step} className="bg-surface-container border border-surface-border rounded-lg p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-primary">{step.step}</span>
                    <Icon className="w-5 h-5 text-primary" />
                  </div>
                  <h3 className="text-base font-bold text-content-primary mt-3">{step.title}</h3>
                  <span className="text-xs font-mono text-content-muted block mb-2">{step.subtitle}</span>
                  <p className="text-xs text-content-secondary leading-relaxed">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Technical Distinction Statement */}
      <div className="bg-surface-low border border-surface-border rounded-lg p-6">
        <h3 className="text-sm font-bold text-content-primary mb-2">Technological Distinction</h3>
        <p className="text-xs text-content-secondary leading-relaxed">
          NetVision AI evaluates network telemetry through an ensemble machine learning classifier coupled with a temporal Markov World Model. Rather than asserting static binary alerts, the platform continuously estimates risk trajectories, provides transparent model explainability, and maps behavioral evidence directly to MITRE ATT&CK tactical frameworks.
        </p>
      </div>
    </div>
  );
}
