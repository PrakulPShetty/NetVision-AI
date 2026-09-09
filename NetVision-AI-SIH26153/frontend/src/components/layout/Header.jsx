import React, { useState, useEffect } from 'react';
import NetVisionLogo from '../common/NetVisionLogo';
import { Activity, ShieldCheck, Clock, Server, AlertCircle } from 'lucide-react';

export default function Header({ backendHealth, isAnalyzing }) {
  const [timeString, setTimeString] = useState('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setTimeString(now.toUTCString().split(' ')[4] + ' UTC');
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  const isHealthy = backendHealth?.status === 'healthy';

  return (
    <header className="fixed top-0 left-0 right-0 h-14 bg-surface-lowest border-b border-outline-variant/40 z-50 flex items-center justify-between px-5 select-none">
      {/* Brand Logo & Enclave Info */}
      <div className="flex items-center gap-4">
        <NetVisionLogo className="h-8" />
        <span className="hidden md:inline-flex font-mono text-[10px] px-2 py-0.5 bg-surface-container border border-outline-variant/40 text-secondary rounded">
          ENCLAVE-04 // US-EAST-PROD
        </span>
      </div>

      {/* Live Operational Metrics & Clock */}
      <div className="flex items-center gap-4 text-xs font-mono">
        {/* Pipeline Ingress Stream */}
        <div className="hidden sm:flex items-center gap-2 bg-surface-low px-3 py-1 border border-outline-variant/30 rounded">
          <span className={`w-2 h-2 rounded-full ${isAnalyzing ? 'bg-amber-400 animate-ping' : 'bg-primary animate-pulse'}`} />
          <span className="text-primary tracking-tight">
            {isAnalyzing ? 'PIPELINE: PROCESSING INFERENCE' : 'TELEMETRY STREAM: ACTIVE'}
          </span>
        </div>

        {/* Engine Status */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-surface-low border border-outline-variant/30 rounded">
          {isHealthy ? (
            <>
              <ShieldCheck className="w-3.5 h-3.5 text-primary" />
              <span className="text-on-surface-variant font-medium">ENGINE: ONLINE</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-amber-400 font-medium">ENGINE: OFFLINE</span>
            </>
          )}
        </div>

        {/* Pipeline Latency */}
        <div className="hidden lg:flex items-center gap-1 text-on-surface-variant">
          <Activity className="w-3.5 h-3.5 text-outline" />
          <span className="text-outline">LATENCY:</span>
          <span className="text-on-surface font-semibold">8.4ms</span>
        </div>

        <div className="hidden lg:block h-3.5 w-[1px] bg-outline-variant/40" />

        {/* UTC Clock */}
        <div className="hidden md:flex items-center gap-1.5 text-on-surface-variant">
          <Clock className="w-3.5 h-3.5 text-outline" />
          <span className="text-on-surface">{timeString || '14:30:00 UTC'}</span>
        </div>
      </div>
    </header>
  );
}
