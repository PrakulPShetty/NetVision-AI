import React from 'react';
import { Shield, Cpu, Lock } from 'lucide-react';

export default function FooterBar() {
  return (
    <footer className="bg-surface-dim border-t border-surface-border py-4 mt-auto text-xs text-content-muted">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-content-secondary font-medium">
            <Shield className="w-3.5 h-3.5 text-primary" />
            <span>NETVISION AI</span>
          </div>
          <span>—</span>
          <span>Predictive Network Security Intelligence</span>
        </div>

        <div className="flex items-center gap-6 font-mono text-[11px]">
          <div className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-secondary" />
            <span>ENSEMBLE + MARKOV WORLD MODEL</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-primary" />
            <span>XAI + MITRE CORRELATION</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
