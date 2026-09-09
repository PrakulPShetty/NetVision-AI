import React, { useState } from 'react';
import { MOCK_MITRE_RESULT } from '../../mocks/phase1/mockData';
import { ShieldCheck, ShieldAlert, CheckCircle2, AlertOctagon, Terminal, FileCode, Layers, Info } from 'lucide-react';

export default function MitreIntelView({ mitreData = MOCK_MITRE_RESULT }) {
  const [showEmptyState, setShowEmptyState] = useState(false);

  const activeData = showEmptyState ? { hasCorrelation: false } : mitreData;

  return (
    <div className="space-y-6">
      {/* Header & Toggle Controls */}
      <div className="bg-surface-low border border-surface-border rounded-lg p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs text-content-muted font-mono uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4 text-primary" />
              <span>ATT&CK INTELLIGENCE LAYER</span>
              <span>•</span>
              <span className="text-primary font-semibold">BEHAVIORAL CORRELATION</span>
            </div>
            <h2 className="text-lg font-bold text-content-primary mt-1">MITRE ATT&CK Behavioral Correlation</h2>
            <p className="text-xs text-content-muted mt-1 max-w-3xl leading-relaxed">
              Separate from the core ML security-state forecast, NetVision AI correlates observed traffic characteristics with established MITRE ATT&CK techniques when sufficient evidence is present.
            </p>
          </div>

          {/* Development Toggle Button to test Empty State */}
          <button
            onClick={() => setShowEmptyState(!showEmptyState)}
            className="px-3.5 py-1.5 rounded bg-surface-container hover:bg-surface-high border border-surface-border font-mono text-xs text-content-secondary transition-colors flex items-center gap-2"
          >
            <Layers className="w-3.5 h-3.5 text-primary" />
            <span>{showEmptyState ? 'Show Matched Correlation' : 'Simulate Empty State'}</span>
          </button>
        </div>
      </div>

      {/* Main Content: Matched Correlation vs Empty State */}
      {!activeData.hasCorrelation ? (
        /* EMPTY STATE VIEW */
        <div className="bg-surface-low border border-surface-border rounded-lg p-12 text-center flex flex-col items-center justify-center">
          <div className="w-12 h-12 rounded-full bg-surface-container border border-surface-border flex items-center justify-center text-content-muted mb-4">
            <ShieldCheck className="w-6 h-6 text-primary" />
          </div>
          <h3 className="text-base font-bold text-content-primary">NO CONFIDENT ATT&CK CORRELATION</h3>
          <p className="text-xs text-content-muted mt-2 max-w-md leading-relaxed">
            The observed traffic telemetry does not exhibit sufficient behavioral evidence to map confidently to a specific MITRE ATT&CK technique.
          </p>
          <div className="mt-6 bg-surface-container border border-surface-border px-4 py-2.5 rounded text-xs font-mono text-content-secondary max-w-md">
            Threshold: Requires &ge;75% correlation confidence across packet distribution signals.
          </div>
        </div>
      ) : (
        /* CORRELATED TECHNIQUE DETAILS */
        <div className="space-y-6">
          {/* Technique Overview Header Card */}
          <div className="bg-surface-low border border-surface-border rounded-lg p-6">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-lg bg-elevated-container border border-elevated/40 flex items-center justify-center text-elevated shrink-0 font-mono text-lg font-bold">
                  {activeData.technique.id}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-elevated uppercase tracking-wider">
                      TACTIC: {activeData.technique.tactic}
                    </span>
                    <span className="text-content-muted">•</span>
                    <span className="font-mono text-xs text-primary font-semibold">
                      {activeData.technique.confidenceLabel}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-content-primary mt-1">
                    {activeData.technique.name}
                  </h3>
                  <p className="text-xs text-content-secondary mt-1.5 leading-relaxed">
                    "{activeData.technique.summary}"
                  </p>
                </div>
              </div>

              <div className="bg-surface-container px-4 py-3 rounded-lg border border-surface-border text-right font-mono text-xs">
                <span className="text-content-muted block text-[10px] uppercase">Correlation Confidence</span>
                <span className="text-xl font-bold text-elevated">{(activeData.technique.confidenceScore * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>

          {/* Evidence & Technical Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Section 1: Observed Traffic Evidence */}
            <div className="bg-surface-low border border-surface-border rounded-lg p-6">
              <div className="flex items-center gap-2 pb-3 border-b border-surface-border">
                <CheckCircle2 className="w-4 h-4 text-primary" />
                <h4 className="text-sm font-semibold text-content-primary">Observed Behavioral Evidence</h4>
              </div>

              <ul className="mt-4 space-y-3">
                {activeData.technique.evidence.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs text-content-secondary leading-relaxed">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0 mt-1.5"></span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-6 pt-4 border-t border-surface-border">
                <span className="text-[11px] font-mono text-content-muted block uppercase mb-2">SUPPORTING FEATURE VECTORS</span>
                <div className="flex flex-wrap gap-2">
                  {activeData.technique.supportingFeatures.map((feat, idx) => (
                    <span key={idx} className="font-mono text-[11px] bg-surface-container border border-surface-border px-2.5 py-1 rounded text-primary">
                      {feat}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Section 2: Technical Interpretation & Limitations */}
            <div className="bg-surface-low border border-surface-border rounded-lg p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 pb-3 border-b border-surface-border">
                  <Terminal className="w-4 h-4 text-secondary" />
                  <h4 className="text-sm font-semibold text-content-primary">Technical Interpretation</h4>
                </div>

                <p className="mt-4 text-xs text-content-secondary leading-relaxed">
                  {activeData.technique.technicalInterpretation}
                </p>
              </div>

              <div className="mt-6 bg-surface-container border border-surface-border rounded-lg p-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-content-primary mb-1">
                  <Info className="w-4 h-4 text-primary shrink-0" />
                  <span>Correlation Language Distinction</span>
                </div>
                <p className="text-xs text-content-muted leading-relaxed">
                  "{activeData.technique.limitations}"
                </p>
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
