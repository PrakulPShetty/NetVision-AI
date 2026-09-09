import React from 'react';
import Topology3D from '../components/network/Topology3D';
import { MOCK_FORECAST_RESULT, MOCK_MITRE_RESULT } from '../mocks/phase1/mockData';
import { 
  ShieldAlert, 
  TrendingUp, 
  HelpCircle, 
  ShieldCheck, 
  ArrowRight, 
  Activity, 
  Layers 
} from 'lucide-react';

export default function OverviewPage({ onNavigate }) {
  const forecast = MOCK_FORECAST_RESULT;
  const mitre = MOCK_MITRE_RESULT;

  return (
    <div className="space-y-6">
      {/* 1. System Posture Banner */}
      <div className="bg-surface-low border border-surface-border rounded-lg p-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-mono text-content-muted uppercase tracking-wider">
              <Activity className="w-4 h-4 text-primary" />
              <span>SECURITY POSTURE OVERVIEW</span>
              <span>•</span>
              <span className="text-primary font-semibold">LIVE FORECAST MONITORING</span>
            </div>
            <h1 className="text-xl font-bold text-content-primary">
              Observed Traffic Assessed as <span className="text-critical">ATTACK</span> State
            </h1>
            <p className="text-xs text-content-secondary max-w-2xl leading-relaxed">
              "{forecast.currentState.assessmentSummary}"
            </p>
          </div>

          <div className="flex items-center gap-4 bg-surface-container px-4 py-3 rounded-lg border border-surface-border shrink-0">
            <div>
              <span className="text-[10px] font-mono text-content-muted uppercase block">Peak 20M Horizon Risk</span>
              <span className="text-xl font-mono font-bold text-critical">91.2% Attack Prob</span>
            </div>
            <div className="w-10 h-10 rounded-full bg-critical-container border border-critical/40 flex items-center justify-center text-critical">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>
        </div>
      </div>

      {/* 2. Primary Visual: 3D Network Topology */}
      <Topology3D />

      {/* 3. Product Architecture Workflow & Summary Deck */}
      <div className="bg-surface-low border border-surface-border rounded-lg p-6">
        <div className="flex items-center justify-between pb-4 border-b border-surface-border">
          <div>
            <h2 className="text-base font-semibold text-content-primary">System Intelligence Pipeline</h2>
            <p className="text-xs text-content-muted mt-0.5">
              NetVision AI executes temporal state representation, Markov forecast, XAI, and ATT&CK correlation.
            </p>
          </div>
          <span className="text-xs font-mono text-primary font-semibold">PHASE 1 ARCHITECTURE</span>
        </div>

        {/* Workflow Steps Indicator */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-6">
          <div className="bg-surface-container border border-surface-border p-3.5 rounded-lg">
            <span className="text-[10px] font-mono text-primary block uppercase font-bold">STEP 1</span>
            <span className="text-xs font-semibold text-content-primary block mt-1">OBSERVE</span>
            <span className="text-[11px] text-content-muted block mt-0.5">Traffic Telemetry Ingestion</span>
          </div>
          <div className="bg-surface-container border border-surface-border p-3.5 rounded-lg">
            <span className="text-[10px] font-mono text-primary block uppercase font-bold">STEP 2</span>
            <span className="text-xs font-semibold text-content-primary block mt-1">UNDERSTAND</span>
            <span className="text-[11px] text-content-muted block mt-0.5">Temporal State Representation</span>
          </div>
          <div className="bg-surface-container border border-surface-border p-3.5 rounded-lg">
            <span className="text-[10px] font-mono text-primary block uppercase font-bold">STEP 3</span>
            <span className="text-xs font-semibold text-content-primary block mt-1">FORECAST</span>
            <span className="text-[11px] text-content-muted block mt-0.5">Markov World Model (+60M)</span>
          </div>
          <div className="bg-surface-container border border-surface-border p-3.5 rounded-lg">
            <span className="text-[10px] font-mono text-primary block uppercase font-bold">STEP 4</span>
            <span className="text-xs font-semibold text-content-primary block mt-1">EXPLAIN</span>
            <span className="text-[11px] text-content-muted block mt-0.5">3-Layer SHAP Explainability</span>
          </div>
          <div className="bg-surface-container border border-surface-border p-3.5 rounded-lg col-span-2 md:col-span-1">
            <span className="text-[10px] font-mono text-primary block uppercase font-bold">STEP 5</span>
            <span className="text-xs font-semibold text-content-primary block mt-1">CORRELATE</span>
            <span className="text-[11px] text-content-muted block mt-0.5">MITRE ATT&CK Mapping</span>
          </div>
        </div>

        {/* Quick Navigation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          {/* Card 1: Forecast Overview */}
          <div 
            onClick={() => onNavigate('forecast')}
            className="bg-surface-container hover:bg-surface-high border border-surface-border p-4 rounded-lg cursor-pointer transition-all group"
          >
            <div className="flex items-center justify-between">
              <TrendingUp className="w-5 h-5 text-primary" />
              <ArrowRight className="w-4 h-4 text-content-muted group-hover:text-primary transition-colors" />
            </div>
            <h3 className="text-sm font-semibold text-content-primary mt-3">60-Minute Forecast Curve</h3>
            <p className="text-xs text-content-muted mt-1 leading-relaxed">
              Inspect probability trends across 10m, 20m, 30m, 45m, and 60m horizons with decision reference lines.
            </p>
          </div>

          {/* Card 2: XAI Breakdown */}
          <div 
            onClick={() => onNavigate('xai')}
            className="bg-surface-container hover:bg-surface-high border border-surface-border p-4 rounded-lg cursor-pointer transition-all group"
          >
            <div className="flex items-center justify-between">
              <HelpCircle className="w-5 h-5 text-secondary" />
              <ArrowRight className="w-4 h-4 text-content-muted group-hover:text-secondary transition-colors" />
            </div>
            <h3 className="text-sm font-semibold text-content-primary mt-3">3-Layer XAI Explainability</h3>
            <p className="text-xs text-content-muted mt-1 leading-relaxed">
              Review human-readable narrative, feature contribution table, and SHAP log-odds attribution values.
            </p>
          </div>

          {/* Card 3: ATT&CK Correlation */}
          <div 
            onClick={() => onNavigate('attack')}
            className="bg-surface-container hover:bg-surface-high border border-surface-border p-4 rounded-lg cursor-pointer transition-all group"
          >
            <div className="flex items-center justify-between">
              <ShieldCheck className="w-5 h-5 text-elevated" />
              <ArrowRight className="w-4 h-4 text-content-muted group-hover:text-elevated transition-colors" />
            </div>
            <h3 className="text-sm font-semibold text-content-primary mt-3">MITRE ATT&CK Intel ({mitre.technique.id})</h3>
            <p className="text-xs text-content-muted mt-1 leading-relaxed">
              Correlated technique mapping based on observed destination port diversity and SYN flag volume.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
