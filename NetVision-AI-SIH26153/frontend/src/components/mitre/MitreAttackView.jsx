import React from 'react';
import { ShieldAlert, ShieldCheck, AlertCircle, ExternalLink, Info, CheckCircle2 } from 'lucide-react';

export default function MitreAttackView({ forecastData }) {
  const mitre = forecastData?.mitre_attack;
  const status = mitre?.mapping_status || 'No confident MITRE mapping identified';
  const techniques = mitre?.techniques || [];
  const reason = mitre?.reason;
  const signalGroups = mitre?.signal_groups || {};

  const hasTechniques = techniques.length > 0;

  return (
    <div className="w-full flex flex-col gap-5 select-none font-sans">
      {/* Top Banner */}
      <div className="bg-surface-lowest p-4 border border-outline-variant/40 rounded flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold uppercase tracking-wider text-on-surface flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            MITRE ATT&CK Behavioral Intelligence
          </h2>
          <p className="text-xs font-mono text-outline mt-0.5">
            Phase 8 Evidence-Based Network Behavior to MITRE ATT&CK Correlation Engine
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <div className={`px-3 py-1.5 rounded border font-bold uppercase ${
            hasTechniques
              ? 'bg-amber-500/20 text-amber-400 border-amber-500/40'
              : 'bg-primary/20 text-primary border-primary/30'
          }`}>
            {status}
          </div>
        </div>
      </div>

      {/* Main Content: Mapped Techniques OR Empty State */}
      {hasTechniques ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {techniques.map((tech, idx) => (
            <div key={idx} className="bg-surface-lowest p-5 border border-outline-variant/40 rounded flex flex-col justify-between shadow-lg">
              <div>
                {/* Header */}
                <div className="flex items-start justify-between pb-3 mb-3 border-b border-outline-variant/30">
                  <div>
                    <span className="font-mono text-xs text-amber-400 font-bold bg-amber-500/15 px-2 py-0.5 rounded border border-amber-500/30">
                      {tech.technique_id}
                    </span>
                    <h3 className="text-base font-bold text-on-surface mt-2">{tech.technique_name}</h3>
                  </div>
                  <div className="text-right font-mono text-[10px]">
                    <span className="text-outline uppercase block">TACTIC</span>
                    <span className="text-secondary font-bold uppercase">{tech.tactic}</span>
                  </div>
                </div>

                {/* Badges & Confidence */}
                <div className="flex items-center gap-2 mb-4 font-mono text-xs">
                  <span className="text-outline">CONFIDENCE:</span>
                  <span className="text-amber-400 font-bold bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                    {tech.confidence} CONFIDENCE
                  </span>
                </div>

                {/* Interpretation */}
                <div className="bg-surface-low p-3.5 rounded border border-outline-variant/30 mb-3">
                  <span className="font-mono text-[10px] text-primary uppercase font-semibold block mb-1">
                    BEHAVIORAL INTERPRETATION
                  </span>
                  <p className="text-xs text-on-surface leading-relaxed">
                    {tech.interpretation}
                  </p>
                </div>

                {/* Limitation */}
                <div className="bg-surface-low p-3.5 rounded border border-outline-variant/30 mb-4">
                  <span className="font-mono text-[10px] text-outline uppercase font-semibold block mb-1">
                    SCOPING & LIMITATION
                  </span>
                  <p className="text-xs text-on-surface-variant leading-relaxed">
                    {tech.limitation}
                  </p>
                </div>
              </div>

              {/* Matching Signal Groups */}
              <div className="pt-3 border-t border-outline-variant/30 font-mono text-xs">
                <span className="text-[10px] text-outline uppercase block mb-1.5">MATCHING BEHAVIORAL GROUPS</span>
                <div className="flex flex-wrap gap-1.5">
                  {tech.matching_groups?.map((grp, gIdx) => (
                    <span key={gIdx} className="bg-surface-high text-secondary px-2 py-0.5 rounded text-[10px] border border-outline-variant/40">
                      {grp}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty State: No confident mapping */
        <div className="bg-surface-lowest p-8 border border-outline-variant/40 rounded flex flex-col items-center justify-center text-center">
          <ShieldCheck className="w-12 h-12 text-primary mb-3" />
          <h3 className="text-base font-bold text-on-surface uppercase font-mono">No Confident MITRE ATT&CK Mapping</h3>
          <p className="text-xs font-mono text-on-surface-variant mt-2 max-w-lg leading-relaxed">
            {reason || "Insufficient behavioral evidence in traffic streams to satisfy the configured MITRE ATT&CK decision rules."}
          </p>
          <div className="mt-4 px-3 py-1.5 bg-surface-low border border-outline-variant/30 rounded font-mono text-[11px] text-outline">
            MINIMUM THRESHOLD: 2+ MATCHING BEHAVIORAL SIGNAL GROUPS REQUIRED
          </div>
        </div>
      )}

      {/* Evaluated Signal Groups Breakdown */}
      <div className="bg-surface-lowest p-4 border border-outline-variant/40 rounded flex flex-col">
        <h3 className="font-mono text-xs font-bold text-on-surface uppercase mb-3">
          Evaluated Behavioral Signal Groups
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
          {Object.entries(signalGroups).map(([groupName, active], idx) => (
            <div key={idx} className="bg-surface-low p-3 rounded border border-outline-variant/30 flex items-center justify-between">
              <span className="text-on-surface font-medium truncate uppercase text-[11px]">
                {groupName.replace('_', ' ')}
              </span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                active ? 'bg-primary/20 text-primary border border-primary/30' : 'bg-surface-container text-outline'
              }`}>
                {active ? 'ACTIVE' : 'INACTIVE'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
