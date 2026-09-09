import React from 'react';
import NetVisionLogo from '../components/common/NetVisionLogo';
import { ArrowRight, ShieldCheck, Activity, Cpu, TrendingUp, HelpCircle, Layers } from 'lucide-react';

export default function LandingPage({ onNavigate }) {
  return (
    <div className="min-h-[80vh] flex flex-col justify-center py-8 space-y-12">
      {/* Main Hero Section */}
      <div className="bg-surface-low border border-surface-border rounded-xl p-8 sm:p-12 relative overflow-hidden subtle-grid">
        <div className="max-w-3xl space-y-6 relative z-10">
          
          {/* Prominent Official Logo Display */}
          <div className="inline-block pb-2">
            <NetVisionLogo className="h-16" showText={false} />
          </div>

          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-container border border-primary/30 text-xs font-mono text-primary font-semibold">
              <Activity className="w-3.5 h-3.5" />
              <span>PREDICTIVE NETWORK SECURITY INTELLIGENCE</span>
            </div>
            
            <h1 className="text-3xl sm:text-5xl font-extrabold text-content-primary tracking-tight leading-tight">
              NETVISION <span className="text-primary">AI</span>
            </h1>
          </div>

          <p className="text-base sm:text-lg text-content-secondary leading-relaxed max-w-2xl">
            NetVision AI analyzes network traffic and forecasts how the network security state may evolve over time.
          </p>

          {/* Primary & Secondary Call to Actions */}
          <div className="pt-4 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
            <button
              onClick={() => onNavigate('analysis')}
              className="px-8 py-3.5 rounded-lg bg-primary hover:bg-primary-light text-background font-bold text-sm transition-all flex items-center justify-center gap-2 shadow-lg hover:shadow-primary/20"
            >
              <span>ANALYZE NETWORK</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => onNavigate('about')}
              className="px-6 py-3.5 rounded-lg bg-surface-container hover:bg-surface-high border border-surface-border text-content-primary font-semibold text-sm transition-colors flex items-center justify-center gap-2"
            >
              <span>ABOUT NETVISION AI</span>
            </button>
          </div>
        </div>
      </div>

      {/* Feature Pillar Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div 
          onClick={() => onNavigate('forecast')}
          className="bg-surface-low hover:bg-surface-container border border-surface-border p-6 rounded-lg cursor-pointer transition-all group"
        >
          <div className="w-10 h-10 rounded-lg bg-primary-container border border-primary/30 flex items-center justify-center text-primary mb-4">
            <TrendingUp className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-content-primary">60-Minute State Forecasting</h3>
          <p className="text-xs text-content-muted mt-2 leading-relaxed">
            Markov World Model projects security risk probability trends over 10m, 20m, 30m, 45m, and 60m horizons.
          </p>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-primary font-medium group-hover:translate-x-1 transition-transform">
            <span>Explore Forecast Model</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </div>

        <div 
          onClick={() => onNavigate('xai')}
          className="bg-surface-low hover:bg-surface-container border border-surface-border p-6 rounded-lg cursor-pointer transition-all group"
        >
          <div className="w-10 h-10 rounded-lg bg-surface-high border border-surface-border flex items-center justify-center text-secondary mb-4">
            <HelpCircle className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-content-primary">3-Layer Model Explainability</h3>
          <p className="text-xs text-content-muted mt-2 leading-relaxed">
            Transparent XAI delivering human-readable narratives, contribution tables, and SHAP attribution metrics.
          </p>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-secondary font-medium group-hover:translate-x-1 transition-transform">
            <span>Review Explainability</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </div>

        <div 
          onClick={() => onNavigate('attack')}
          className="bg-surface-low hover:bg-surface-container border border-surface-border p-6 rounded-lg cursor-pointer transition-all group"
        >
          <div className="w-10 h-10 rounded-lg bg-elevated-container border border-elevated/30 flex items-center justify-center text-elevated mb-4">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-content-primary">MITRE ATT&CK Correlation</h3>
          <p className="text-xs text-content-muted mt-2 leading-relaxed">
            Behavioral evidence correlation linking observed traffic telemetry to established MITRE techniques.
          </p>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-elevated font-medium group-hover:translate-x-1 transition-transform">
            <span>View ATT&CK Mapping</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </div>
      </div>
    </div>
  );
}
