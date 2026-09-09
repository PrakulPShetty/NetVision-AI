import React from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ReferenceLine, 
  CartesianGrid 
} from 'recharts';
import { MOCK_FORECAST_RESULT } from '../../mocks/phase1/mockData';
import { TrendingUp, Clock, AlertTriangle, ShieldCheck, HelpCircle } from 'lucide-react';

export default function ForecastChart({ forecastData = MOCK_FORECAST_RESULT }) {
  const { currentState, forecastTimeline, decisionThreshold, explanationCopy } = forecastData;

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-surface-high border border-surface-border p-3 rounded shadow-xl font-sans text-xs">
          <div className="flex items-center gap-2 font-mono text-content-secondary border-b border-surface-border pb-1.5 mb-1.5">
            <Clock className="w-3.5 h-3.5 text-primary" />
            <span>Horizon: {data.horizon} ({data.minutes}m)</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-content-muted">Attack Probability:</span>
            <span className="font-mono font-bold text-primary text-sm">{data.probability}%</span>
          </div>
          <div className="flex items-center justify-between gap-4 mt-1">
            <span className="text-content-muted">Assessed Status:</span>
            <span className={`font-mono text-[11px] font-semibold ${
              data.probability >= 80 ? 'text-critical' : data.probability >= 40 ? 'text-elevated' : 'text-normal-text'
            }`}>
              {data.status}
            </span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Current State Summary Banner */}
      <div className="bg-surface-low border border-surface-border rounded-lg p-6">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 text-xs text-content-muted font-mono uppercase tracking-wider">
              <span>CURRENT ASSESSMENT</span>
              <span>•</span>
              <span className="text-primary font-semibold">OBSERVED TRAFFIC WINDOW</span>
            </div>
            <h2 className="text-lg font-bold text-content-primary mt-1">
              Current Security State: <span className={currentState.label === 'ATTACK' ? 'text-critical' : 'text-primary'}>{currentState.label}</span>
            </h2>
            <p className="text-xs text-content-secondary mt-1.5 max-w-2xl leading-relaxed">
              "{currentState.assessmentSummary}"
            </p>
          </div>

          <div className="flex items-center gap-4 bg-surface-container p-3.5 rounded-lg border border-surface-border">
            <div className="text-right">
              <span className="text-[11px] text-content-muted block uppercase font-mono">ESTIMATED PROBABILITY</span>
              <span className="text-2xl font-mono font-bold text-critical">{(currentState.probability * 100).toFixed(1)}%</span>
            </div>
            <div className="w-12 h-12 rounded-full bg-critical-container border border-critical/40 flex items-center justify-center text-critical">
              <AlertTriangle className="w-6 h-6" />
            </div>
          </div>
        </div>
      </div>

      {/* Forecast Line Chart Card */}
      <div className="bg-surface-low border border-surface-border rounded-lg p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-5 border-b border-surface-border">
          <div>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              <h3 className="text-base font-semibold text-content-primary">60-Minute Security State Forecast</h3>
            </div>
            <p className="text-xs text-content-muted mt-0.5">
              Future attack state probability estimates across 10m, 20m, 30m, 45m, and 60m horizons.
            </p>
          </div>

          <div className="flex items-center gap-4 font-mono text-xs">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 bg-primary"></span>
              <span className="text-content-secondary">Forecast Curve</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 border-t-2 border-dashed border-elevated"></span>
              <span className="text-content-secondary">Decision Threshold (40%)</span>
            </div>
          </div>
        </div>

        {/* Recharts Area Chart Container */}
        <div className="h-72 w-full mt-6 subtle-grid rounded pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={forecastTimeline} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#14b8a6" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#263044" vertical={false} />
              <XAxis 
                dataKey="horizon" 
                stroke="#64748b" 
                tick={{ fill: '#94a3b8', fontSize: 12, fontFamily: 'JetBrains Mono' }} 
              />
              <YAxis 
                domain={[0, 100]} 
                unit="%" 
                stroke="#64748b" 
                tick={{ fill: '#94a3b8', fontSize: 12, fontFamily: 'JetBrains Mono' }} 
              />
              <Tooltip content={<CustomTooltip />} />
              
              {/* Decision Reference Line */}
              <ReferenceLine 
                y={decisionThreshold.percentage} 
                stroke="#f59e0b" 
                strokeDasharray="4 4" 
                strokeWidth={1.5}
                label={{ 
                  value: `Decision Ref (${decisionThreshold.percentage}%)`, 
                  fill: '#f59e0b', 
                  fontSize: 11, 
                  position: 'insideTopRight',
                  fontFamily: 'JetBrains Mono'
                }} 
              />

              <Area 
                type="monotone" 
                dataKey="probability" 
                stroke="#14b8a6" 
                strokeWidth={2.5} 
                fillOpacity={1} 
                fill="url(#forecastGradient)" 
                dot={{ r: 4, fill: '#14b8a6', strokeWidth: 2, stroke: '#0b0d10' }}
                activeDot={{ r: 6, fill: '#2dd4bf', stroke: '#f8fafc', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Threshold Callout & Explanatory Context */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 pt-5 border-t border-surface-border text-xs">
          <div className="bg-surface-container border border-surface-border rounded-lg p-3.5 flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-elevated shrink-0 mt-0.5" />
            <div>
              <span className="font-mono font-semibold text-elevated block mb-0.5">
                DECISION REFERENCE: {decisionThreshold.percentage}%
              </span>
              <p className="text-content-secondary leading-relaxed">
                "{decisionThreshold.description}"
              </p>
            </div>
          </div>

          <div className="bg-surface-container border border-surface-border rounded-lg p-3.5 flex items-start gap-3">
            <HelpCircle className="w-5 h-5 text-primary shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-content-primary block mb-0.5">
                FORECAST METHODOLOGY
              </span>
              <p className="text-content-muted leading-relaxed">
                "{explanationCopy.forecastSummary}"
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
