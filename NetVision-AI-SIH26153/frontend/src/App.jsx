import { useEffect, useState } from 'react';
import { ArrowDownRight, Menu, X } from 'lucide-react';
import TrafficForm from './components/product/TrafficForm';
import { CurrentAssessment, ForecastPlot, XaiExplanation, MitreCorrelation } from './components/product/Results';
import { submitTrafficForecast } from './services/api';
import { TRAFFIC_PRESETS } from './utils/presets';
import logo from '../netvision updated logo.png';

const nav = [
  ['HOME', 'home'],
  ['ABOUT', 'about'],
  ['ANALYZE', 'analyze'],
  ['FORECAST', 'forecast'],
  ['EXPLAIN', 'explain'],
  ['ATT&CK', 'mitre'],
];

const go = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
const Mark = () => <img className="brand-mark" src={logo} alt="NetVision AI" />;

function formatBackendResponse(data) {
  if (!data) return null;

  // 1. ML Assessment
  const ml = data.ml || data.ml_forecast || {};
  const currentProbability = (ml.ensemble_attack_probability ?? 0) * 100;
  const currentStateLabel = ml.current_state_label || ml.predicted_current_state || (currentProbability >= 40 ? 'ATTACK' : 'BENIGN');

  const assessment = {
    state: currentStateLabel,
    probability: Number(currentProbability.toFixed(2)),
  };

  // 2. World Model Forecast
  const worldModel = data.world_model || {};
  const rawForecasts = worldModel.forecasts || [];

  const forecast = rawForecasts.map((item) => {
    const horizonMin = item.horizon_minutes || (item.steps ? item.steps * 5 : 10);
    const prob = (item.future_attack_probability ?? item.attack_probability ?? 0) * 100;
    return {
      horizon: `${horizonMin}m`,
      probability: Number(prob.toFixed(1)),
    };
  });

  const decisionThreshold = (ml.decision_threshold ?? 0.40) * 100;

  // 3. XAI Explainability
  const rawXai = data.xai || {};
  let xaiSummary = 'The forecast is influenced by the strongest contributing traffic signals observed in the analyzed 5-minute window.';
  let contributions = [];
  let shap = [];

  if (rawXai.top_contributions && Array.isArray(rawXai.top_contributions)) {
    const topFeatureNames = rawXai.top_contributions
      .slice(0, 3)
      .map((item) => item.feature.replace(/_/g, ' '))
      .join(', ');

    if (topFeatureNames) {
      xaiSummary = `The forecast is influenced primarily by ${topFeatureNames}, reflecting the traffic characteristics observed in this 5-minute window.`;
    }

    contributions = rawXai.top_contributions.map((item) => {
      const featName = item.feature.replace(/_/g, ' ');
      const value = item.shap_value || 0;
      const influence = value > 0 ? 'Raises probability' : value < 0 ? 'Lowers probability' : 'No directional effect';
      const directional = value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral';
      const valStr = `${value > 0 ? '+' : ''}${value.toFixed(4)}`;
      const interpretation = `${featName} exerts a ${directional} directional influence (${valStr}) on the ensemble attack probability.`;

      return {
        feature: featName,
        magnitude: Math.abs(value),
        direction: influence,
        interpretation,
      };
    });

    shap = rawXai.top_contributions.map((item) => ({
      feature: item.feature.replace(/_/g, ' '),
      value: item.shap_value || 0,
    }));
  } else if (rawXai.summary) {
    xaiSummary = rawXai.summary;
    contributions = rawXai.contributions || [];
    shap = rawXai.shap || [];
  }

  const xai = {
    summary: xaiSummary,
    contributions,
    shap,
  };

  // 4. MITRE ATT&CK Correlation
  const rawMitre = data.mitre_attack || data.mitre || {};
  let mitre = [];

  if (rawMitre.techniques && Array.isArray(rawMitre.techniques) && rawMitre.techniques.length > 0) {
    mitre = rawMitre.techniques.map((tech) => ({
      id: tech.technique_id || tech.id,
      name: tech.technique_name || tech.name,
      tactic: tech.tactic,
      confidence: typeof tech.confidence === 'number' ? `${tech.confidence}%` : (tech.confidence || 'Not specified'),
      evidence: tech.evidence || [],
      features: tech.supporting_features || tech.features || [],
      interpretation: tech.interpretation || 'Observed traffic evidence was correlated with this ATT&CK technique.',
      limitation: tech.limitation || 'Behavioral flow correlation does not constitute definitive proof of intent.',
    }));
  } else if (rawMitre.id) {
    mitre = [rawMitre];
  }

  return {
    assessment,
    forecast,
    decisionThreshold,
    xai,
    mitre,
  };
}

export default function App() {
  const [active, setActive] = useState('home');
  const [menu, setMenu] = useState(false);
  const [status, setStatus] = useState('ready'); // 'ready' | 'analyzing' | 'complete' | 'error'
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [presetValues, setPresetValues] = useState(null);

  useEffect(() => {
    const o = new IntersectionObserver(
      (entries) => {
        const item = entries.filter((e) => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (item) setActive(item.target.id);
      },
      { rootMargin: '-35% 0px -50% 0px', threshold: [0.05, 0.25] }
    );
    nav.forEach(([, id]) => {
      const e = document.getElementById(id);
      if (e) o.observe(e);
    });
    return () => o.disconnect();
  }, []);

  async function analyse(values) {
    setStatus('analyzing');
    setError(null);
    setResult(null);

    const response = await submitTrafficForecast(values);

    if (response.success && response.data) {
      const formatted = formatBackendResponse(response.data);
      setResult(formatted);
      setStatus('complete');
      setTimeout(() => go('forecast'), 80);
    } else {
      setStatus('error');
      setError(response.error || 'Failed to connect to NetVision AI forecast service.');
    }
  }

  const navigate = (id) => {
    setMenu(false);
    go(id);
  };

  return (
    <div className="app-shell">
      <header className="site-header">
        <button className="brand" aria-label="NetVision AI home" onClick={() => navigate('home')}>
          <Mark />
        </button>
        <nav className="desktop-nav" aria-label="Primary navigation">
          {nav.map(([label, id]) => (
            <button key={id} className={active === id ? 'active' : ''} onClick={() => navigate(id)}>
              {label}
            </button>
          ))}
        </nav>
        <button className="menu-button" aria-label="Toggle navigation" onClick={() => setMenu(!menu)}>
          {menu ? <X size={21} /> : <Menu size={21} />}
        </button>
        {menu && (
          <nav className="mobile-nav">
            {nav.map(([label, id]) => (
              <button key={id} onClick={() => navigate(id)}>
                {label}
              </button>
            ))}
          </nav>
        )}
      </header>
      <main>
        <section id="home" className="hero section-anchor">
          <div className="hero-copy">
            <p className="eyebrow">Predictive network security intelligence</p>
            <h1>
              NETVISION AI
            </h1>
            <p className="hero-subtitle">AI-based Network Attack Forecasting</p>
            <p className="hero-description">
              Forecast future network security states from traffic behavior.
            </p>
            <div className="hero-actions">
              <button className="button primary" onClick={() => navigate('analyze')}>
                Analyze network <ArrowDownRight size={17} />
              </button>
              <button className="text-button" onClick={() => navigate('about')}>
                How it works <ArrowDownRight size={16} />
              </button>
            </div>
          </div>
          <div className="hero-method" aria-label="NetVision AI forecasting workflow">
            <p className="eyebrow">Forecasting workflow</p>
            {['Traffic profile', 'Temporal behavior', 'Current-state assessment', 'Future-state forecast', 'XAI and ATT&CK context'].map((step, index) => (
              <div className="method-step" key={step}><span>0{index + 1}</span><strong>{step}</strong></div>
            ))}
          </div>
        </section>
        <section className="workflow" aria-label="Product workflow">
          {['Observe', 'Assess', 'Forecast', 'Explain', 'Correlate'].map((step, i) => (
            <div className="workflow-step" key={step}>
              <span>0{i + 1}</span>
              <strong>{step}</strong>
              {i < 4 && <i>→</i>}
            </div>
          ))}
        </section>
        <section id="about" className="about-section section-anchor">
          <div className="about-lead">
            <p className="eyebrow">About NetVision AI</p>
            <h2>
              Security should not
              <br />
              stop at detection.
            </h2>
            <p className="about-intro-p">Network security is often focused on understanding what is happening in the traffic being observed.</p>
            <p className="about-question">NetVision AI explores a different question:</p>
            <p className="about-question-lead">How might the network security state evolve from here?</p>
          </div>
          <div className="about-story">
            <div className="about-item">
              <div className="about-item-header">
                <span className="about-item-num">01</span>
                <h3 className="about-item-title">OBSERVE</h3>
              </div>
              <p className="about-item-desc">Network traffic provides the evidence.</p>
            </div>
            <div className="about-item">
              <div className="about-item-header">
                <span className="about-item-num">02</span>
                <h3 className="about-item-title">ASSESS</h3>
              </div>
              <p className="about-item-desc">The ML ensemble estimates the current security state and attack probability.</p>
            </div>
            <div className="about-item">
              <div className="about-item-header">
                <span className="about-item-num">03</span>
                <h3 className="about-item-title">FORECAST</h3>
              </div>
              <p className="about-item-desc">The temporal world model projects future security-state probabilities.</p>
            </div>
            <div className="about-item">
              <div className="about-item-header">
                <span className="about-item-num">04</span>
                <h3 className="about-item-title">EXPLAIN</h3>
              </div>
              <p className="about-item-desc">XAI identifies the traffic signals contributing to the forecast.</p>
            </div>
            <div className="about-item">
              <div className="about-item-header">
                <span className="about-item-num">05</span>
                <h3 className="about-item-title">CORRELATE</h3>
              </div>
              <p className="about-item-desc">MITRE ATT&CK provides behavioral context when sufficient evidence exists.</p>
            </div>
          </div>
        </section>
        <section id="analyze" className="analysis-section section-anchor">
          <div className="section-intro">
            <p className="eyebrow">Input</p>
            <h2>Analyze network traffic</h2>
            <p>Provide a 5-minute traffic profile to generate a security forecast.</p>
          </div>
          <div className="preset-bar">
            <span className="eyebrow" style={{ margin: 0 }}>Demo scenarios</span>
            <div className="preset-buttons">
              {TRAFFIC_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  className="preset-btn"
                  onClick={() => setPresetValues(preset.data)}
                  title={preset.description}
                >
                  {preset.title}
                </button>
              ))}
            </div>
          </div>
          <div className="analysis-layout">
            <TrafficForm onSubmit={analyse} status={status} presetValues={presetValues} onPresetConsumed={() => setPresetValues(null)} />
            <aside className={`readiness ${status}`}>
              <span className="readiness-dot" />
              <p className="eyebrow">
                {status === 'complete'
                  ? 'Results available'
                  : status === 'analyzing'
                  ? 'Analyzing profile'
                  : status === 'error'
                  ? 'Analysis unavailable'
                  : 'Ready for analysis'}
              </p>
              <h3>
                {status === 'complete'
                  ? 'Forecast prepared.'
                  : status === 'analyzing'
                  ? 'Preparing the forecast…'
                  : status === 'error'
                  ? 'Service error.'
                  : 'A practical input surface.'}
              </h3>
              <p>
                {status === 'complete'
                  ? 'Forecast result successfully computed by FastAPI backend.'
                  : status === 'analyzing'
                  ? 'Computing ensemble predictions, Markov world model forecast, SHAP values, and MITRE correlation…'
                  : status === 'error'
                  ? error || 'NetVision AI could not reach the forecasting service. Check that FastAPI is running.'
                  : 'Submit a 5-minute network traffic profile to generate a forecast.'}
              </p>
              {status === 'complete' && (
                <button className="text-button" onClick={() => navigate('forecast')}>
                  View forecast <ArrowDownRight size={16} />
                </button>
              )}
            </aside>
          </div>
        </section>
        <section id="forecast" className="results-section section-anchor">
          <div className="section-intro split-intro">
            <div>
              <p className="eyebrow">Forecast</p>
              <h2>Future security state</h2>
            </div>
            <p>NetVision AI estimates how the security state may evolve across multiple future time horizons.</p>
          </div>
          {result ? (
            <>
              <CurrentAssessment assessment={result.assessment} />
              <ForecastPlot forecast={result.forecast} threshold={result.decisionThreshold} />
            </>
          ) : (
            <Empty label="Forecast unavailable" text="Complete an analysis to activate the current assessment and future probability forecast." />
          )}
        </section>
        <section id="explain" className="explain-section section-anchor">
          <div className="section-intro">
            <p className="eyebrow">Explainability</p>
            <h2>Why this forecast?</h2>
          </div>
          {result ? (
            <XaiExplanation xai={result.xai} />
          ) : (
            <Empty label="Explanation unavailable" text="Contributing signals and their visual explanation will appear with an analysis result." />
          )}
        </section>
        <section id="mitre" className="attack-section section-anchor">
          <div className="section-intro split-intro">
            <div>
              <p className="eyebrow">Behavioral context</p>
              <h2>MITRE ATT&CK correlation</h2>
            </div>
            <p>Where sufficient evidence is present, NetVision AI correlates observed traffic characteristics with relevant MITRE ATT&CK techniques.</p>
          </div>
          {result ? (
            <MitreCorrelation correlation={result.mitre} />
          ) : (
            <Empty label="No correlation to display" text="ATT&CK correlation is evaluated only after a traffic profile has been analyzed." />
          )}
        </section>
      </main>
      <footer id="footer" className="section-anchor">
        <div className="footer-brand">
          <Mark />
          <span>Predictive network security intelligence</span>
        </div>
        <span className="footer-right">Traffic-informed security forecasting</span>
      </footer>
    </div>
  );
}

function Empty({ label, text }) {
  return (
    <div className="empty-result">
      <span className="empty-line" />
      <div>
        <p className="eyebrow">{label}</p>
        <p>{text}</p>
      </div>
    </div>
  );
}
