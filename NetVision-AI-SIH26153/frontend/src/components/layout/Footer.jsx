import React from 'react';
import { Cpu, Terminal } from 'lucide-react';

export default function Footer({ forecastData }) {
  const currentRisk = forecastData?.ml?.predicted_current_state || 'NOMINAL';
  const isAttack = currentRisk === 'ATTACK';

  return (
    <footer className="fixed bottom-0 left-60 right-0 h-8 bg-surface-lowest border-t border-outline-variant/40 z-40 flex items-center justify-between px-5 text-xs font-mono text-outline select-none">
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1.5 text-on-surface-variant">
          <Cpu className="w-3.5 h-3.5 text-primary" />
          <span>FastAPI Pipeline v1.0</span>
        </span>
        <span>//</span>
        <span>XGBoost + RF-SMOTE (50:50 Ensemble)</span>
        <span>//</span>
        <span>Markov World Model</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <Terminal className="w-3.5 h-3.5 text-outline" />
          <span className="text-outline">CURRENT STATE:</span>
          <span className={`font-bold ${isAttack ? 'text-error animate-pulse' : 'text-primary'}`}>
            {currentRisk}
          </span>
        </div>
        <span>//</span>
        <span>SYSTEM HEALTH: 100%</span>
      </div>
    </footer>
  );
}
