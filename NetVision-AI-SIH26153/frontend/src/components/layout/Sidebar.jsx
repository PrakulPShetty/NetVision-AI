import React from 'react';
import { 
  BarChart3, 
  Network, 
  Globe2, 
  TrendingUp, 
  BrainCircuit, 
  ShieldAlert, 
  Info 
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: BarChart3, badge: null },
    { id: 'analysis', label: 'Network Analysis', icon: Network, badge: 'Live Input' },
    { id: 'simulation', label: 'Network Simulation', icon: Globe2, badge: 'Spatial Graph' },
    { id: 'forecast', label: 'Forecast & Horizons', icon: TrendingUp, badge: '+60m' },
    { id: 'xai', label: 'XAI / Explainability', icon: BrainCircuit, badge: 'SHAP' },
    { id: 'mitre', label: 'ATT&CK Intelligence', icon: ShieldAlert, badge: 'MITRE' },
    { id: 'about', label: 'About NetVision AI', icon: Info, badge: null },
  ];

  return (
    <aside className="fixed left-0 top-14 bottom-8 w-60 bg-surface-lowest border-r border-outline-variant/40 z-40 flex flex-col justify-between select-none">
      <div className="py-4">
        <div className="px-5 mb-3">
          <span className="font-mono text-[10px] text-outline uppercase tracking-wider font-semibold">
            OPERATIONAL DECKS
          </span>
        </div>

        <nav className="flex flex-col gap-1 px-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded transition-all text-left ${
                  isActive
                    ? 'bg-primary-container/20 text-primary border border-primary/40 font-semibold shadow-sm'
                    : 'text-on-surface-variant hover:bg-surface-high hover:text-on-surface'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-primary' : 'text-outline'}`} />
                  <span className="text-sm font-sans tracking-tight">{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`font-mono text-[9px] px-1.5 py-0.2 rounded uppercase ${
                    isActive ? 'bg-primary/20 text-primary' : 'bg-surface-container text-outline'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Model Engine Sync Status Card */}
      <div className="p-3.5 m-3 border border-outline-variant/40 bg-surface-low rounded">
        <div className="flex items-center justify-between text-[10px] font-mono text-outline uppercase mb-1">
          <span>MODEL INFERENCE</span>
          <span className="text-primary font-bold">READY</span>
        </div>
        <div className="font-mono text-[11px] text-on-surface-variant truncate font-semibold">
          XGB-L9 + RF-SMOTE // MARKOV
        </div>
        <div className="flex items-center justify-between text-[10px] font-mono text-outline mt-1">
          <span>SHAP: PROB-SPACE</span>
          <span>138 FEATS</span>
        </div>
      </div>
    </aside>
  );
}
