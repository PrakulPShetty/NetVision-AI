import React from 'react';
import { MOCK_XAI_RESULT } from '../../mocks/phase1/mockData';
import { HelpCircle, FileText, Table, BarChart2, ArrowUpRight, ArrowDownRight, Info } from 'lucide-react';

export default function ExplainabilityView({ xaiData = MOCK_XAI_RESULT }) {
  const { layer1Narrative, layer2Contributions, layer3ShapValues } = xaiData;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-surface-low border border-surface-border rounded-lg p-6">
        <div className="flex items-center gap-2 text-xs text-content-muted font-mono uppercase tracking-wider">
          <HelpCircle className="w-4 h-4 text-primary" />
          <span>MODEL EXPLAINABILITY (XAI)</span>
          <span>•</span>
          <span className="text-primary font-semibold">3-LAYER ATTRITION ANALYSIS</span>
        </div>
        <h2 className="text-lg font-bold text-content-primary mt-1">Why This Security Forecast?</h2>
        <p className="text-xs text-content-muted mt-1 max-w-3xl leading-relaxed">
          NetVision AI provides multi-layered explainability to detail which specific traffic signals and feature contributions influenced the model forecast.
        </p>
      </div>

      {/* LAYER 1: Human-Readable Textual Explanation */}
      <div className="bg-surface-low border border-surface-border rounded-lg p-6">
        <div className="flex items-center gap-2 pb-3 border-b border-surface-border">
          <FileText className="w-4 h-4 text-primary" />
          <h3 className="text-sm font-semibold text-content-primary">Layer 1: Human-Readable Narrative</h3>
        </div>
        
        <div className="mt-4 bg-surface-container border border-surface-border rounded-lg p-5">
          <p className="text-sm text-content-primary leading-relaxed">
            "{layer1Narrative}"
          </p>
          <div className="mt-3 pt-3 border-t border-surface-border flex items-center gap-2 text-xs text-content-muted">
            <Info className="w-3.5 h-3.5 text-primary shrink-0" />
            <span>Generated from top SHAP feature attribution metrics in probability space.</span>
          </div>
        </div>
      </div>

      {/* LAYER 2: Feature Contribution Table */}
      <div className="bg-surface-low border border-surface-border rounded-lg p-6">
        <div className="flex items-center justify-between pb-3 border-b border-surface-border">
          <div className="flex items-center gap-2">
            <Table className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-content-primary">Layer 2: Contributing Features Table</h3>
          </div>
          <span className="text-xs font-mono text-content-muted">RANKED BY SHAP WEIGHT</span>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-surface-border font-mono text-content-muted bg-surface-container">
                <th className="py-3 px-4">FEATURE</th>
                <th className="py-3 px-4">OBSERVED VALUE</th>
                <th className="py-3 px-4">CONTRIBUTION</th>
                <th className="py-3 px-4">INFLUENCE</th>
                <th className="py-3 px-4">TECHNICAL INTERPRETATION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {layer2Contributions.map((item, idx) => (
                <tr key={idx} className="hover:bg-surface-container/50 transition-colors">
                  <td className="py-3 px-4 font-semibold text-content-primary">
                    {item.feature}
                    <span className="block text-[10px] font-mono text-content-muted font-normal">{item.rawKey}</span>
                  </td>
                  <td className="py-3 px-4 font-mono text-content-secondary">{item.value}</td>
                  <td className="py-3 px-4 font-mono">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      item.contribution === 'High' 
                        ? 'bg-critical-container text-critical border border-critical/30' 
                        : 'bg-elevated-container text-elevated border border-elevated/30'
                    }`}>
                      {item.contribution}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono">
                    <div className="flex items-center gap-1 text-critical">
                      <ArrowUpRight className="w-3.5 h-3.5" />
                      <span>{item.influence}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-content-secondary max-w-md leading-relaxed">
                    {item.interpretation}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* LAYER 3: SHAP Visualization */}
      <div className="bg-surface-low border border-surface-border rounded-lg p-6">
        <div className="flex items-center justify-between pb-3 border-b border-surface-border">
          <div className="flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-content-primary">Layer 3: SHAP Contribution Impact</h3>
          </div>
          <div className="flex items-center gap-3 font-mono text-xs">
            <div className="flex items-center gap-1 text-critical">
              <span className="w-2.5 h-2.5 rounded-sm bg-critical"></span>
              <span>Pushes Toward Attack</span>
            </div>
            <div className="flex items-center gap-1 text-primary">
              <span className="w-2.5 h-2.5 rounded-sm bg-primary"></span>
              <span>Pushes Toward Benign</span>
            </div>
          </div>
        </div>

        <div className="mt-6 space-y-4">
          {layer3ShapValues.map((item, idx) => {
            const isPositive = item.shapValue > 0;
            const absVal = Math.abs(item.shapValue);
            const maxVal = 0.35;
            const barWidth = `${(absVal / maxVal) * 100}%`;

            return (
              <div key={idx} className="flex items-center text-xs">
                <div className="w-44 font-mono text-content-secondary truncate text-right pr-4">
                  {item.feature}
                </div>
                
                {/* Horizontal Diverging Bar Container */}
                <div className="flex-1 h-6 bg-surface-container border border-surface-border rounded relative flex items-center px-2">
                  <div className="absolute left-1/2 top-0 bottom-0 w-px bg-surface-border"></div>
                  
                  {isPositive ? (
                    <div 
                      className="h-3.5 bg-critical rounded-r transition-all ml-[50%]"
                      style={{ width: `${(absVal / maxVal) * 50}%` }}
                    ></div>
                  ) : (
                    <div 
                      className="h-3.5 bg-primary rounded-l transition-all mr-[50%] ml-auto"
                      style={{ width: `${(absVal / maxVal) * 50}%` }}
                    ></div>
                  )}
                </div>

                <div className="w-20 font-mono text-right pl-4">
                  <span className={`font-bold ${isPositive ? 'text-critical' : 'text-primary'}`}>
                    {isPositive ? `+${item.shapValue.toFixed(2)}` : item.shapValue.toFixed(2)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-6 pt-4 border-t border-surface-border text-xs text-content-muted flex items-center gap-2">
          <Info className="w-3.5 h-3.5 text-primary shrink-0" />
          <span>SHAP values quantify the exact log-odds contribution of each feature to the final forecast probability.</span>
        </div>
      </div>
    </div>
  );
}
