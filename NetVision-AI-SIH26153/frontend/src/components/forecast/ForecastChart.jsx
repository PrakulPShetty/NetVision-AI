import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { CHART, tooltipStyles } from './chartTheme';

/**
 * Attack-probability timeline produced by the Markov world model.
 *
 * Two complementary series are plotted (attack and benign probability) because
 * the model's state probabilities always sum to one — showing only the attack
 * curve would hide how confident the projection actually is.
 */
export default function ForecastChart({ forecast, threshold, height = 300 }) {
  return (
    <div className="chart-frame" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={forecast} margin={{ top: 16, right: 20, bottom: 4, left: -14 }}>
          <defs>
            <linearGradient id="attackFill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" stopColor={CHART.copper} stopOpacity="0.32" />
              <stop offset="1" stopColor={CHART.copper} stopOpacity="0" />
            </linearGradient>
            <linearGradient id="benignFill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" stopColor={CHART.sage} stopOpacity="0.16" />
              <stop offset="1" stopColor={CHART.sage} stopOpacity="0" />
            </linearGradient>
          </defs>

          <CartesianGrid vertical={false} stroke={CHART.grid} strokeDasharray="2 6" />
          <XAxis dataKey="horizon" stroke={CHART.axis} tickLine={false} axisLine={false} tick={{ fill: CHART.axis, fontSize: 11 }} />
          <YAxis
            domain={[0, 100]}
            stroke={CHART.axis}
            tickLine={false}
            axisLine={false}
            tick={{ fill: CHART.axis, fontSize: 11 }}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip content={<ForecastTooltip threshold={threshold} />} cursor={{ stroke: CHART.copper, strokeDasharray: '3 4' }} />
          <Legend verticalAlign="top" align="right" height={28} iconType="plainline" wrapperStyle={{ ...tooltipStyles.legend }} />

          <ReferenceLine
            y={threshold}
            stroke={CHART.amber}
            strokeDasharray="5 5"
            label={{ value: `DECISION THRESHOLD ${threshold.toFixed(0)}%`, position: 'insideBottomRight', fill: CHART.amber, fontSize: 10 }}
          />

          <Area
            type="monotone"
            dataKey="benignProbability"
            name="Benign probability"
            stroke={CHART.sage}
            strokeWidth={1.6}
            fill="url(#benignFill)"
            dot={{ r: 2.5, fill: CHART.sage, strokeWidth: 0 }}
          />
          <Area
            type="monotone"
            dataKey="probability"
            name="Attack probability"
            stroke={CHART.copper}
            strokeWidth={2.4}
            fill="url(#attackFill)"
            activeDot={{ r: 5, fill: '#0b0e17', stroke: CHART.copper, strokeWidth: 2.5 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function ForecastTooltip({ active, payload, threshold }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;

  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip-head">
        Horizon {point.horizon} · K = {point.k}
      </p>
      <ul className="chart-tooltip-list">
        <li>
          <span className="dot attack" /> Attack probability
          <strong>{point.probability.toFixed(2)}%</strong>
        </li>
        <li>
          <span className="dot benign" /> Benign probability
          <strong>{point.benignProbability.toFixed(2)}%</strong>
        </li>
      </ul>
      <p className="chart-tooltip-foot">
        Projected state <strong>{point.state}</strong>
        <br />
        {point.aboveThreshold ? 'Above' : 'Below'} the {threshold.toFixed(0)}% decision threshold · {point.steps} × 5-minute Markov step
        {point.steps > 1 ? 's' : ''}
      </p>
    </div>
  );
}
