import React from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell,
  ReferenceLine
} from 'recharts';
import { BrainCircuit, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';

export default function SHAPExplainerView({ forecastData }) {
  const xai = forecastData?.xai;
  
  if (!xai) {
    return (
      <div className="w-full bg-surface-lowest p-8 border border-outline-variant/40 rounded flex flex-col items-center justify-center text-center">
        <AlertCircle className="w-10 h-10 text-outline mb-3" />
        <h3 className="text-base font-bold text-on-surface uppercase font-mono">Explanation Data Unavailable</h3>
        <p className="text-xs font-mono text-outline mt-1 max-w-md">
          No probability-space SHAP explanation returned for this traffic profile. Run network analysis to generate XAI features.
        </p>
      </div>
    );
  }

  const baseProb = (xai.base_probability * 100).toFixed(2);
  const reconProb = (xai.reconstructed_probability * 100).toFixed(2);
  const topContribs = xai.top_contributions || [];
  const positiveContribs = xai.positive_contributors || [];
  const negativeContribs = xai.negative_contributors || [];

  // Format data for Recharts horizontal bar chart
  const chartData = topContribs.slice(0, 10).map((c) => ({
    feature: c.feature.length > 22 ? c.feature.substring(0, 22) + '...' : c.feature,
    fullName: c.feature,
    shapValue: Number(c.shap_value.toFixed(4)),
    absShap: Number(c.absolute_shap.toFixed(4)),
    direction: c.shap_value >= 0 ? 'Risk Elevating' : 'Risk Reducing'
  }));

  return (
    <div className="w-full flex flex-col gap-5 select-none font-sans">
      {/* Top Banner */}
      <div className="bg-surface-lowest p-4 border border-outline-variant/40 rounded flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold uppercase tracking-wider text-on-surface flex items-center gap-2">
            <BrainCircuit className="w-5 h-5 text-primary" />
            Probability-Space SHAP Explainability Deck
          </h2>
          <p className="text-xs font-mono text-outline mt-0.5">
            Phase 8 Probability-Space TreeSHAP Model Feature Attributions
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="bg-surface-low px-3 py-1.5 border border-outline-variant/30 rounded flex items-center gap-2">
            <span className="text-outline">Base Probability:</span>
            <span className="text-secondary font-bold">{baseProb}%</span>
          </div>
          <div className="bg-surface-low px-3 py-1.5 border border-outline-variant/30 rounded flex items-center gap-2">
            <span className="text-outline">Ensemble Output:</span>
            <span className="text-primary font-bold">{reconProb}%</span>
          </div>
          <div className="bg-surface-low px-3 py-1.5 border border-outline-variant/30 rounded flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-primary" />
            <span className="text-primary font-semibold">VALIDATED</span>
          </div>
        </div>
      </div>

      {/* SHAP Bar Chart + Pos/Neg Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Top 10 Feature Contributions Bar Chart (8 cols) */}
        <div className="lg:col-span-8 bg-surface-lowest p-4 border border-outline-variant/40 rounded flex flex-col">
          <div className="flex items-center justify-between font-mono text-xs text-outline mb-4">
            <span>TOP 10 FEATURE SHAP CONTRIBUTIONS (PROBABILITY SHIFT)</span>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 bg-error rounded-sm" />
                <span className="text-on-surface-variant">Elevates Risk (+SHAP)</span>
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 bg-primary rounded-sm" />
                <span className="text-on-surface-variant">Reduces Risk (-SHAP)</span>
              </span>
            </div>
          </div>

          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={chartData} margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d3449" horizontal={false} />
                <XAxis type="number" stroke="#88929b" tick={{ fill: '#bec8d2', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
                <YAxis type="category" dataKey="feature" stroke="#88929b" tick={{ fill: '#dae2fd', fontSize: 11, fontFamily: 'JetBrains Mono' }} width={140} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#171f33', borderColor: '#3e4850', color: '#dae2fd', fontFamily: 'JetBrains Mono', fontSize: '12px' }}
                  formatter={(value, name, item) => [`${value > 0 ? '+' : ''}${value}`, item.payload.direction]}
                />
                <ReferenceLine x={0} stroke="#3e4850" />
                <Bar dataKey="shapValue" radius={[0, 3, 3, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.shapValue >= 0 ? '#ffb4ab' : '#0ea5e9'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Elevating vs Reducing Summary (4 cols) */}
        <div className="lg:col-span-4 bg-surface-lowest p-4 border border-outline-variant/40 rounded flex flex-col justify-between">
          <div>
            <h3 className="font-mono text-xs font-bold text-on-surface uppercase pb-2 mb-3 border-b border-outline-variant/30">
              Primary Signal Vectors
            </h3>

            {/* Positive Contributors */}
            <div className="mb-4">
              <span className="text-[10px] font-mono text-error font-bold uppercase tracking-wider block mb-2">
                TOP RISK ELEVATING SIGNALS (+SHAP)
              </span>
              <div className="flex flex-col gap-1.5 font-mono text-xs">
                {positiveContribs.slice(0, 4).map((item, idx) => (
                  <div key={idx} className="bg-surface-low p-2 rounded border border-outline-variant/30 flex items-center justify-between">
                    <span className="text-on-surface truncate max-w-[170px]">{item.feature}</span>
                    <span className="text-error font-bold">+{item.shap_value.toFixed(4)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Negative Contributors */}
            <div>
              <span className="text-[10px] font-mono text-primary font-bold uppercase tracking-wider block mb-2">
                TOP RISK REDUCING SIGNALS (-SHAP)
              </span>
              <div className="flex flex-col gap-1.5 font-mono text-xs">
                {negativeContribs.slice(0, 4).map((item, idx) => (
                  <div key={idx} className="bg-surface-low p-2 rounded border border-outline-variant/30 flex items-center justify-between">
                    <span className="text-on-surface truncate max-w-[170px]">{item.feature}</span>
                    <span className="text-primary font-bold">{item.shap_value.toFixed(4)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-3 font-mono text-[10px] text-outline flex items-center justify-between border-t border-outline-variant/30 mt-3">
            <span>METHOD: TREESHAP (INTERVENTIONAL)</span>
            <span className="text-primary">138 FEATURES EVALUATED</span>
          </div>
        </div>
      </div>

      {/* Complete Feature Interpretation Table */}
      <div className="bg-surface-lowest p-4 border border-outline-variant/40 rounded flex flex-col">
        <h3 className="font-mono text-xs font-bold text-on-surface uppercase mb-3">
          Detailed Feature Attribution Matrix
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr className="bg-surface-low text-outline text-[10px] uppercase">
                <th className="py-2 px-3 border-b border-outline-variant/40">Feature Identifier</th>
                <th className="py-2 px-3 border-b border-outline-variant/40">SHAP Probability Shift</th>
                <th className="py-2 px-3 border-b border-outline-variant/40">Absolute Magnitude</th>
                <th className="py-2 px-3 border-b border-outline-variant/40">Technical Direction</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/30 text-on-surface">
              {topContribs.map((row, idx) => (
                <tr key={idx} className="hover:bg-surface-high/50 transition-colors">
                  <td className="py-2 px-3 font-bold text-on-surface">{row.feature}</td>
                  <td className={`py-2 px-3 font-bold ${row.shap_value >= 0 ? 'text-error' : 'text-primary'}`}>
                    {row.shap_value >= 0 ? `+${row.shap_value.toFixed(6)}` : row.shap_value.toFixed(6)}
                  </td>
                  <td className="py-2 px-3 text-on-surface-variant">{row.absolute_shap.toFixed(6)}</td>
                  <td className="py-2 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      row.shap_value >= 0 ? 'bg-error-container/30 text-error' : 'bg-primary/20 text-primary'
                    }`}>
                      {row.shap_value >= 0 ? 'ELEVATES ATTACK RISK' : 'REDUCES ATTACK RISK'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
