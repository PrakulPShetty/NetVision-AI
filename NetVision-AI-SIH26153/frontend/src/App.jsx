import React, { useState, useEffect } from 'react';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import Footer from './components/layout/Footer';

import OverviewPage from './pages/OverviewPage';
import TrafficInputForm from './components/analysis/TrafficInputForm';
import TopologyGraph from './components/network/TopologyGraph';
import ForecastTimeline from './components/forecast/ForecastTimeline';
import SHAPExplainerView from './components/xai/SHAPExplainerView';
import MitreAttackView from './components/mitre/MitreAttackView';
import AboutPage from './pages/AboutPage';

import { getHealthStatus, submitTrafficForecast } from './services/api';
import { TRAFFIC_PRESETS } from './utils/presets';
import { AlertTriangle, RefreshCw, Loader2, CheckCircle2 } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [forecastData, setForecastData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState('');
  const [backendHealth, setBackendHealth] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Check health and run initial baseline forecast on app launch
  useEffect(() => {
    async function initApp() {
      const health = await getHealthStatus();
      setBackendHealth(health);

      // Perform initial forecast with Nominal preset
      runForecast(TRAFFIC_PRESETS[0].data, false);
    }
    initApp();
  }, []);

  // Submit forecast to FastAPI backend with processing transition stages
  const runForecast = async (trafficInput, showTransition = true) => {
    setErrorMessage(null);

    if (showTransition) {
      setIsAnalyzing(true);
      const stages = [
        'INGESTING TRAFFIC TELEMETRY',
        'BUILDING TEMPORAL STATE REPRESENTATION',
        'RUNNING XGBOOST + RF-SMOTE ENSEMBLE',
        'EXECUTING MARKOV WORLD MODEL (+60M)',
        'COMPUTING PROBABILITY-SPACE SHAP',
        'CORRELATING MITRE ATT&CK BEHAVIOR'
      ];

      for (let i = 0; i < stages.length; i++) {
        setAnalysisStep(stages[i]);
        await new Promise((res) => setTimeout(res, 180));
      }
    }

    const res = await submitTrafficForecast(trafficInput);

    if (res.success) {
      setForecastData(res.data);
    } else {
      setErrorMessage(res.error || 'Forecast processing failed.');
    }

    setIsAnalyzing(false);
    setAnalysisStep('');
  };

  // Render main view based on active tab
  const renderActiveView = () => {
    if (errorMessage) {
      return (
        <div className="bg-surface-lowest p-8 border border-error/40 rounded flex flex-col items-center justify-center text-center my-6">
          <AlertTriangle className="w-12 h-12 text-error mb-3" />
          <h3 className="text-base font-bold font-mono text-on-surface uppercase">Forecast Engine Error</h3>
          <p className="text-xs font-mono text-error mt-2 max-w-md">{errorMessage}</p>
          <button
            onClick={() => runForecast(TRAFFIC_PRESETS[0].data, true)}
            className="mt-4 px-4 py-2 bg-surface-high hover:bg-surface-variant text-on-surface font-mono text-xs rounded border border-outline-variant/40 flex items-center gap-2"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Forecast Request</span>
          </button>
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return <OverviewPage forecastData={forecastData} onNavigate={setActiveTab} />;

      case 'analysis':
        return (
          <div className="flex flex-col gap-6">
            <TrafficInputForm onAnalyze={(data) => runForecast(data, true)} isAnalyzing={isAnalyzing} />
            {forecastData && (
              <div className="mt-4 flex flex-col gap-6">
                <div className="flex items-center justify-between pb-2 border-b border-outline-variant/30">
                  <h3 className="font-mono text-xs font-bold text-primary uppercase">INFERENCE RESULTS DECK</h3>
                  <span className="font-mono text-[10px] text-outline">UPDATED VIA LIVE BACKEND</span>
                </div>
                <ForecastTimeline forecastData={forecastData} />
                <SHAPExplainerView forecastData={forecastData} />
                <MitreAttackView forecastData={forecastData} />
              </div>
            )}
          </div>
        );

      case 'simulation':
        return <TopologyGraph forecastData={forecastData} />;

      case 'forecast':
        return <ForecastTimeline forecastData={forecastData} />;

      case 'xai':
        return <SHAPExplainerView forecastData={forecastData} />;

      case 'mitre':
        return <MitreAttackView forecastData={forecastData} />;

      case 'about':
        return <AboutPage />;

      default:
        return <OverviewPage forecastData={forecastData} onNavigate={setActiveTab} />;
    }
  };

  return (
    <div className="min-h-screen bg-background text-on-surface flex flex-col font-sans">
      {/* Top Header */}
      <Header backendHealth={backendHealth} isAnalyzing={isAnalyzing} />

      {/* Navigation Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Operational Workspace */}
      <div className="pl-60 pt-14 pb-12 flex-1 flex flex-col">
        <main className="flex-1 p-6 w-full max-w-7xl mx-auto">
          {/* Processing Transition Overlay */}
          {isAnalyzing && (
            <div className="mb-6 p-4 bg-surface-lowest border border-primary/40 rounded flex items-center justify-between font-mono text-xs shadow-lg animate-pulse">
              <div className="flex items-center gap-3">
                <Loader2 className="w-5 h-5 text-primary animate-spin" />
                <div>
                  <span className="text-primary font-bold block">{analysisStep}</span>
                  <span className="text-[10px] text-outline">FastAPI Pipeline Execution in Progress</span>
                </div>
              </div>
              <span className="text-secondary font-semibold">STAGE 100% IN-FLIGHT</span>
            </div>
          )}

          {renderActiveView()}
        </main>
      </div>

      {/* Bottom Status Bar */}
      <Footer forecastData={forecastData} />
    </div>
  );
}
