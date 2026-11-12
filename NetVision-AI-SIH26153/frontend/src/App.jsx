import { useCallback, useEffect, useMemo, useState } from 'react';
import SiteNav from './components/layout/SiteNav';
import SiteFooter from './components/layout/SiteFooter';
import HomePage from './pages/HomePage';
import AnalyzePage from './pages/AnalyzePage';
import ForecastPage from './pages/ForecastPage';
import ExplainPage from './pages/ExplainPage';
import AttackPage from './pages/AttackPage';
import { ROUTES, navigate, useRoute } from './router';
import {
  getHealthStatus,
  submitFeatureForecast,
  submitTrafficForecast,
} from './services/api';
import { normaliseForecast } from './services/forecast';

/**
 * NetVision AI — application shell.
 *
 * Owns everything that must survive navigation between the product pages:
 *
 *   route        which page is rendered (hash based, deep-linkable)
 *   analysis     status / error / normalised result of POST /forecast
 *   engine       live reachability of the FastAPI backend
 *
 * Pages are presentation only: they receive the normalised result and route
 * callbacks, so replacing demo inputs with live telemetry (or swapping the
 * router) never reaches into the pages themselves.
 */

const HEALTH_POLL_MS = 30000;

export default function App() {
  const path = useRoute();
  const [homeSection, setHomeSection] = useState('home');
  const [workflowIndex, setWorkflowIndex] = useState(0);
  const [status, setStatus] = useState('ready'); // ready | analyzing | complete | error
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [engine, setEngine] = useState('checking');
  const [inputMode, setInputMode] = useState(null); // profile | features

  // ---------------------------------------------------------------
  // Engine reachability — real state, never faked
  // ---------------------------------------------------------------
  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      const health = await getHealthStatus();
      if (cancelled) return;
      setEngine(health?.status === 'healthy' ? 'online' : 'offline');
    };
    check();
    const timer = window.setInterval(check, HEALTH_POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const go = useCallback((target, options) => {
    navigate(target, options);
  }, []);

  const runAnalysis = useCallback(async (mode, submit) => {
    setStatus('analyzing');
    setError(null);
    setInputMode(mode);

    const response = await submit();

    if (response.success && response.data) {
      const normalised = normaliseForecast(response.data);
      if (!normalised) {
        setStatus('error');
        setError('The backend returned an unexpected response shape.');
        return;
      }
      setResult(normalised);
      setStatus('complete');
      setEngine('online');
      // Move to the forecast page so the temporal projection is the next thing seen.
      window.setTimeout(() => navigate(ROUTES.forecast), 120);
    } else {
      setStatus('error');
      setError(response.error || 'NetVision AI could not reach the forecasting service.');
      setEngine('offline');
    }
  }, []);

  const analyse = useCallback(
    (traffic) => runAnalysis('profile', () => submitTrafficForecast(traffic)),
    [runAnalysis]
  );

  // A 138-feature model row skips the runtime transformer and is scored
  // directly by the frozen ensemble through POST /forecast.
  const analyseFeatures = useCallback(
    (features) => runAnalysis('features', () => submitFeatureForecast(features)),
    [runAnalysis]
  );

  const activeNavId = useMemo(() => {
    if (path === ROUTES.home) return homeSection === 'about' ? 'about' : 'home';
    if (path === ROUTES.analyze) return 'analyze';
    if (path === ROUTES.forecast) return 'forecast';
    if (path === ROUTES.explain) return 'explain';
    if (path === ROUTES.attack) return 'attack';
    return null;
  }, [path, homeSection]);

  const onNavSelect = useCallback(
    (item) => {
      go(item.to, item.scrollTo ? { scrollTo: item.scrollTo } : undefined);
    },
    [go]
  );

  return (
    <div className="app-shell">
      <SiteNav activeId={activeNavId} onSelect={onNavSelect} health={engine} />

      <main className="app-main">
        {path === ROUTES.analyze && (
          <AnalyzePage
            status={status}
            error={error}
            result={result}
            inputMode={inputMode}
            onAnalyze={analyse}
            onAnalyzeFeatures={analyseFeatures}
            onGo={go}
          />
        )}
        {path === ROUTES.forecast && <ForecastPage status={status} result={result} onGo={go} />}
        {path === ROUTES.explain && <ExplainPage status={status} result={result} onGo={go} />}
        {path === ROUTES.attack && <AttackPage status={status} result={result} onGo={go} />}
        {path === ROUTES.home && (
          <HomePage
            onGo={go}
            onSectionChange={setHomeSection}
            workflowIndex={workflowIndex}
            onWorkflowIndexChange={setWorkflowIndex}
          />
        )}
        {![ROUTES.home, ROUTES.analyze, ROUTES.forecast, ROUTES.explain, ROUTES.attack].includes(path) && (
          <div className="page">
            <div className="not-found">
              <p className="eyebrow">Unknown route</p>
              <h1 className="page-title">{path}</h1>
              <p className="page-description">
                This route does not exist in NetVision AI. Use the navigation above to return to the product pages.
              </p>
              <button type="button" className="button primary" onClick={() => go(ROUTES.home)}>
                Back to home
              </button>
            </div>
          </div>
        )}
      </main>

      <SiteFooter onSelect={onNavSelect} engineState={engine} />
    </div>
  );
}
