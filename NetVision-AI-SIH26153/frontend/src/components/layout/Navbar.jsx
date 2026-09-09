import React from 'react';
import NetVisionLogo from '../common/NetVisionLogo';
import { 
  Home, 
  Activity, 
  Network, 
  TrendingUp, 
  HelpCircle, 
  ShieldCheck, 
  Info 
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'landing', label: 'Landing', icon: Home, badge: null },
    { id: 'overview', label: 'Overview', icon: Activity, badge: null },
    { id: 'analysis', label: 'Network Analysis', icon: Network, badge: null },
    { id: 'forecast', label: 'Forecast', icon: TrendingUp, badge: '60M' },
    { id: 'xai', label: 'Explainability', icon: HelpCircle, badge: '3-Layer' },
    { id: 'attack', label: 'ATT&CK Intel', icon: ShieldCheck, badge: 'T1046' },
    { id: 'about', label: 'About', icon: Info, badge: null },
  ];

  return (
    <header className="bg-surface-low border-b border-surface-border sticky top-0 z-50 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Official Logo Brand */}
          <div className="cursor-pointer" onClick={() => setActiveTab('landing')}>
            <NetVisionLogo className="h-9" showText={true} />
          </div>

          {/* Navigation Bar Tabs */}
          <nav className="flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-surface-high text-primary border-b-2 border-primary'
                      : 'text-content-secondary hover:text-content-primary hover:bg-surface-container'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-primary' : 'text-content-muted'}`} />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                      isActive 
                        ? 'bg-primary-container text-primary-light border border-primary/30' 
                        : 'bg-surface-high text-content-muted'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* System Environment Status Badge */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-surface-container px-3 py-1.5 rounded-md border border-surface-border">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              <span className="text-xs font-mono text-content-secondary">PHASE 1 STANDALONE</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
