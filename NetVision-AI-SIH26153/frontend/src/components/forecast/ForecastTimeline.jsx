import React from 'react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { TrendingUp, Clock, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function ForecastTimeline({ forecastData }) {
  const worldModel = forecastData?.world_model;
  const forecasts = worldModel?.forecasts || [];
  const currentProb = forecastData?.ml?.ensemble_attack_probability ?? 0.0;
  const currentLabel = forecastData?.ml?.predicted_current_state || 'BENIGN';

  // Construct continuous probability chart data: NOW (0m) + future horizons
  const chartData = [
    { horizon: 'NOW (0m)', probability: Number((currentProb * 100).toFixed(1)), state: currentLabel },
    ...forecasts.map((f) => ({
      horizon: `+${f.horizon_minutes}m`,
      probability: Number((f.future_attack_probability * 100).toFixed(1)),
      state: f.state,
    }))
  ];

  return (
    <div className="w-full flex flex-col gap-5 select-none">
      {/* Deck Header */}
      <div className="bg-surface-lowest p-4 border border-outline-variant/40 rounded flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold uppercase tracking-wider text-on-surface flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-secondary" />
            Multi-Horizon Predictive Escalation Model
          </h2>
          <p className="text-xs font-mono text-outline mt-0.5">
            Markov State Transition Chain // State Forecast Window: +60 Minutes
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-error" />
            <span className="text-on-surface-variant">Attack Probability</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-error-container border border-error" />
            <span className="text-error font-semibold">Decision Threshold (40%)</span>
          </div>
        </div>
      </div>

      {/* Discrete Future Horizon Checkpoint Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
        {forecasts.map((f, idx) => {
          const probPct = (f.future_attack_probability * 100).toFixed(1);
          const isHigh = f.future_attack_probability >= 0.4;
          return (
            <div key={idx} className="bg-surface-lowest p-3.5 border border-outline-variant/40 rounded flex flex-col justify-between">
              <div className="flex items-center justify-between font-mono text-[10px]">
                <span className="text-secondary font-bold">HORIZON: +{f.horizon_minutes} MIN</span>
                <span className="text-outline">T+{f.steps * 300}s</span>
              </div>

              <div className="my-3">
                <div className={`text-2xl font-mono font-bold ${isHigh ? 'text-error' : 'text-secondary'}`}>
                  {probPct}%
                </div>
                <span className="text-[10px] font-mono text-outline uppercase mt-0.5 block">
                  Probability of Attack
                </span>
              </div>

              <div className="w-full bg-surface-low h-1 rounded overflow-hidden">
                <div 
                  className={`h-full ${isHigh ? 'bg-error' : 'bg-secondary'}`}
                  style={{ width: `${Math.min(100, Math.max(0, probPct))}%` }}
                />
              </div>

              <div className="mt-2.5 flex items-center justify-between text-[10px] font-mono">
                <span className="text-outline">PREDICTED:</span>
                <span className={`font-bold ${isHigh ? 'text-error' : 'text-primary'}`}>
                  {f.state}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Area Chart & Markov Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Recharts Area Curve (8 cols) */}
        <div className="lg:col-span-8 bg-surface-lowest p-4 border border-outline-variant/40 rounded flex flex-col">
          <div className="flex items-center justify-between font-mono text-xs text-outline mb-4">
            <span>CONTINUOUS PROBABILITY ESCALATION CURVE (%)</span>
            <span>RESOLUTION: 5-MIN MARKOV STEPS</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="probGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ffb4ab" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#89ceff" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d3449" vertical={false} />
                <XAxis dataKey="horizon" stroke="#88929b" tick={{ fill: '#bec8d2', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
                <YAxis domain={[0, 100]} stroke="#88929b" tick={{ fill: '#bec8d2', fontSize: 11, fontFamily: 'JetBrains Mono' }} unit="%" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#171f33', borderColor: '#3e4850', color: '#dae2fd', fontFamily: 'JetBrains Mono', fontSize: '12px' }}
                  formatter={(value) => [`${value}%`, 'Attack Probability']}
                />
                <ReferenceLine y={40} stroke="#ffb4ab" strokeDasharray="4 4" label={{ value: '40% DECISION THRESHOLD', fill: '#ffb4ab', fontSize: 10, position: 'insideTopRight' }} />
                <Area type="monotone" dataKey="probability" stroke="#ffb4ab" strokeWidth={2.5} fillOpacity={1} fill="url(#probGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Markov Transition Vector (4 cols) */}
        <div className="lg:col-span-4 bg-surface-lowest p-4 border border-outline-variant/40 rounded flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between font-mono text-xs text-outline pb-2 mb-3 border-b border-outline-variant/30">
              <span>MARKOV STATE PROGRESSION</span>
              <span className="text-secondary">P_TRANSITION</span>
            </div>

            <div className="flex flex-col gap-3 font-mono text-xs">
              <div className="bg-surface-low p-2.5 rounded border border-outline-variant/30">
                <div className="flex justify-between text-on-surface mb-1">
                  <span>STATE 0: BENIGN</span>
                  <span className="text-primary font-bold">P(0|0) = 0.92</span>
                </div>
                <div className="w-full bg-surface-container h-1 rounded overflow-hidden">
                  <div className="bg-primary h-full" style={{ width: '92%' }} />
                </div>
              </div>

              <div className="bg-surface-low p-2.5 rounded border border-outline-variant/30">
                <div className="flex justify-between text-on-surface mb-1">
                  <span>STATE 1: ATTACK</span>
                  <span className="text-error font-bold">P(1|1) = 0.88</span>
                </div>
                <div className="w-full bg-surface-container h-1 rounded overflow-hidden">
                  <div className="bg-error h-full" style={{ width: '88%' }} />
                </div>
              </div>

              <div className="bg-surface-low p-3 rounded border border-outline-variant/30 text-on-surface-variant leading-relaxed">
                <span className="text-[10px] text-outline uppercase block mb-1">TRANSITION THEORY</span>
                2-state Markov transition chain models state persistence across discrete 5-minute operational steps.
              </div>
            </div>
          </div>

          <div className="pt-3 font-mono text-[10px] text-outline flex items-center justify-between border-t border-outline-variant/30 mt-3">
            <span>MODEL: MARKOV-V2</span>
            <span className="text-primary">HORIZON MAX: 60M</span>
          </div>
        </div>
      </div>
    </div>
  );
}
