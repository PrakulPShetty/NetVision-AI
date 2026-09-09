import React from 'react';
import TrafficInputForm from '../components/analysis/TrafficInputForm';
import { ArrowRight, CheckCircle2 } from 'lucide-react';

export default function NetworkAnalysisPage({ onAnalyze, isAnalyzing, hasResult, onNavigate }) {
  return (
    <div className="space-y-6">
      <TrafficInputForm onAnalyze={onAnalyze} isAnalyzing={isAnalyzing} />

      {hasResult && (
        <div className="bg-surface-low border border-primary/40 rounded-lg p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-primary shrink-0" />
            <div>
              <span className="text-sm font-semibold text-content-primary block">
                Analysis Completed — Telemetry Forecast Generated
              </span>
              <span className="text-xs text-content-muted">
                Observed traffic profile has been processed through the temporal forecast state pipeline.
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate('forecast')}
              className="px-4 py-2 rounded bg-primary text-background font-semibold text-xs hover:bg-primary-light transition-colors flex items-center gap-1.5"
            >
              <span>View Forecast Curve</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => onNavigate('xai')}
              className="px-4 py-2 rounded bg-surface-container hover:bg-surface-high border border-surface-border text-xs text-content-secondary font-medium transition-colors"
            >
              <span>View XAI Breakdown</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
