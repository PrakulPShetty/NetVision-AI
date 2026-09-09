import { Info, ChevronDown } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export function CurrentAssessment({ assessment }) {
  return (
    <div className="assessment">
      <div>
        <p className="eyebrow">Current security state</p>
        <h3 className={assessment.state.toLowerCase()}>{assessment.state}</h3>
      </div>
      <div>
        <p className="eyebrow">Attack probability</p>
        <strong>
          {assessment.probability.toFixed(2)}
          <small>%</small>
        </strong>
      </div>
      <p className="assessment-note">
        Current security state computed by ensemble model (XGBoost + Random Forest-SMOTE).
      </p>
    </div>
  );
}

export function ForecastPlot({ forecast, threshold }) {
  return (
    <div className="forecast-panel">
      <div className="chart-heading">
        <div>
          <p className="eyebrow">Attack probability forecast</p>
          <h3>Projection across future horizons</h3>
        </div>
        <p>
          <Info size={15} /> Decision reference <b>{threshold}%</b>
        </p>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={310}>
          <AreaChart data={forecast} margin={{ top: 14, right: 18, bottom: 4, left: -18 }}>
            <defs>
              <linearGradient id="forecastFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0" stopColor="#bb7658" stopOpacity=".25" />
                <stop offset="1" stopColor="#bb7658" stopOpacity="0" />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="#d6cebf" strokeDasharray="2 5" />
            <XAxis dataKey="horizon" stroke="#5F5A52" tickLine={false} axisLine={false} />
            <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} stroke="#5F5A52" tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ background: '#ffffff', border: '1px solid #d6cebf', borderRadius: 0 }}
              labelStyle={{ color: '#262521' }}
              formatter={(v) => [`${v}%`, 'Attack probability']}
            />
            <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ color: '#262521', fontSize: 12 }} />
            <ReferenceLine
              y={threshold}
              stroke="#bb7658"
              strokeDasharray="5 5"
              label={{ value: 'DECISION REFERENCE', position: 'insideTopRight', fill: '#bb7658', fontSize: 10 }}
            />
            <Area
              type="monotone"
              dataKey="probability"
              name="Attack probability"
              stroke="#bb7658"
              strokeWidth={2.5}
              fill="url(#forecastFill)"
              activeDot={{ r: 6, fill: '#ffffff', stroke: '#bb7658', strokeWidth: 3 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <p className="reference-copy">
        Reference used by the current-state decision layer. Rather than producing only a current detection result, NetVision AI projects the probability of future attack states across multiple time horizons.
      </p>
      <div className="horizon-summary">
        {forecast.map((point) => (
          <div key={point.horizon}>
            <span>{point.horizon}</span>
            <strong>{point.probability.toFixed(1)}%</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export function XaiExplanation({ xai }) {
  return (
    <div className="xai-layout">
      <div className="xai-copy">
        <p>{xai.summary}</p>
        <p className="technical-note">Contributions indicate directional influence on this forecast; they do not represent causal proof.</p>
      </div>
      <div className="contribution-table">
        <div className="table-head">
          <span>Feature</span>
          <span>Magnitude</span>
          <span>Direction</span>
          <span>Interpretation</span>
        </div>
        {xai.contributions &&
          xai.contributions.map((row) => (
            <div className="table-row" key={row.feature}>
              <strong>{row.feature}</strong>
              <span>
                {row.magnitude.toFixed(4)}
              </span>
              <span className={row.direction.startsWith('Raises') ? 'positive' : 'negative'}>{row.direction}</span>
              <p>{row.interpretation}</p>
            </div>
          ))}
      </div>
      <div className="shap-view">
        <div>
          <p className="eyebrow">SHAP contribution view</p>
          <h3>Relative signal influence</h3>
        </div>
        <div className="shap-bars">
          {xai.shap &&
            xai.shap.map((item) => (
              <div className="shap-row" key={item.feature}>
                <span>{item.feature}</span>
                <div>
                  <i style={{ width: `${Math.min(Math.abs(item.value) * 100, 100)}%` }} className={item.value < 0 ? 'negative-bar' : ''} />
                </div>
                <b>
                  {item.value > 0 ? '+' : ''}
                  {item.value.toFixed(2)}
                </b>
              </div>
            ))}
        </div>
        <p className="technical-note">Positive values increase the displayed attack probability; negative values reduce it.</p>
      </div>
    </div>
  );
}

export function MitreCorrelation({ correlation }) {
  if (!correlation?.length) {
    return (
      <div className="mitre-empty">
        <p className="eyebrow">NO CONFIDENT MITRE ATT&CK CORRELATION</p>
        <p>Insufficient behavioral evidence was available to associate the observed traffic with a specific MITRE ATT&CK technique.</p>
      </div>
    );
  }

  return correlation.map((technique) => (
    <div className="mitre-result" key={technique.id}>
      <div className="mitre-title">
        <span>{technique.id}</span>
        <div>
          <p className="eyebrow">Technique</p>
          <h3>{technique.name}</h3>
        </div>
        <p>
          <b>{technique.confidence}</b>
          <br />
          confidence
        </p>
      </div>
      <div className="mitre-grid">
        <div>
          <p className="eyebrow">Tactic</p>
          <strong>{technique.tactic}</strong>
        </div>
        <div>
          <p className="eyebrow">Evidence</p>
          <p>{Array.isArray(technique.evidence) ? technique.evidence.map((item) => item.signal_group || item).join(' · ') : technique.evidence}</p>
        </div>
        <div>
          <p className="eyebrow">Supporting features</p>
          <p className="mono">{Array.isArray(technique.features) ? technique.features.join(' · ') : ''}</p>
        </div>
        <details>
          <summary>
            Interpretation and limitation <ChevronDown size={16} />
          </summary>
          <p>{technique.interpretation}</p>
          <p className="technical-note">{technique.limitation}</p>
        </details>
      </div>
    </div>
  ));
}
