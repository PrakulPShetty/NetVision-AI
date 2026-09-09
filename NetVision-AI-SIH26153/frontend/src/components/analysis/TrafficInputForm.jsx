import React, { useState } from 'react';
import { TRAFFIC_PRESETS } from '../../mocks/phase1/mockData';
import { Play, RotateCcw, Sliders, CheckCircle2, Loader2, Info } from 'lucide-react';

export default function TrafficInputForm({ onAnalyze, isAnalyzing }) {
  const [selectedPresetId, setSelectedPresetId] = useState('elevated_scanning');
  const [formData, setFormData] = useState(TRAFFIC_PRESETS[1].data);

  const handlePresetChange = (presetId) => {
    setSelectedPresetId(presetId);
    const preset = TRAFFIC_PRESETS.find((p) => p.id === presetId);
    if (preset) {
      setFormData({ ...preset.data });
    }
  };

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: parseFloat(value) || 0
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onAnalyze(formData);
  };

  return (
    <div className="bg-surface-low border border-surface-border rounded-lg p-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-5 border-b border-surface-border">
        <div>
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-primary" />
            <h2 className="text-base font-semibold text-content-primary">Network Traffic Telemetry Profile</h2>
          </div>
          <p className="text-xs text-content-muted mt-0.5">
            Configure observed traffic parameters to evaluate security state forecast and explainability outputs.
          </p>
        </div>

        {/* Preset Selector */}
        <div className="flex items-center gap-2 bg-surface-container p-1 rounded-md border border-surface-border">
          <span className="text-xs font-mono text-content-muted px-2">Presets:</span>
          {TRAFFIC_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => handlePresetChange(preset.id)}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
                selectedPresetId === preset.id
                  ? 'bg-primary text-background font-semibold shadow-sm'
                  : 'text-content-secondary hover:text-content-primary hover:bg-surface-high'
              }`}
            >
              {preset.name}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-6">
        {/* Fieldsets */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Section 1: Traffic Overview */}
          <div className="bg-surface-container border border-surface-border rounded-lg p-4">
            <h3 className="text-xs font-mono font-semibold text-primary uppercase tracking-wider mb-4 pb-2 border-b border-surface-border">
              1. TRAFFIC OVERVIEW
            </h3>
            <div className="space-y-3.5">
              <div>
                <label className="block text-xs text-content-secondary mb-1">Flow Count</label>
                <input
                  type="number"
                  value={formData.flowCount}
                  onChange={(e) => handleInputChange('flowCount', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-xs text-content-secondary mb-1">Unique Destination Ports</label>
                <input
                  type="number"
                  value={formData.uniqueDstPorts}
                  onChange={(e) => handleInputChange('uniqueDstPorts', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-xs text-content-secondary mb-1">Unique Protocols</label>
                <input
                  type="number"
                  value={formData.uniqueProtocols}
                  onChange={(e) => handleInputChange('uniqueProtocols', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Forward & Backward Volume */}
          <div className="bg-surface-container border border-surface-border rounded-lg p-4">
            <h3 className="text-xs font-mono font-semibold text-primary uppercase tracking-wider mb-4 pb-2 border-b border-surface-border">
              2. FORWARD / BACKWARD TRAFFIC
            </h3>
            <div className="space-y-3.5">
              <div>
                <label className="block text-xs text-content-secondary mb-1">Total Forward Packets</label>
                <input
                  type="number"
                  value={formData.totalFwdPackets}
                  onChange={(e) => handleInputChange('totalFwdPackets', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-xs text-content-secondary mb-1">Total Forward Bytes</label>
                <input
                  type="number"
                  value={formData.totalFwdBytes}
                  onChange={(e) => handleInputChange('totalFwdBytes', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-xs text-content-secondary mb-1">Total Backward Packets</label>
                <input
                  type="number"
                  value={formData.totalBwdPackets}
                  onChange={(e) => handleInputChange('totalBwdPackets', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
            </div>
          </div>

          {/* Section 3: Flow Dynamics */}
          <div className="bg-surface-container border border-surface-border rounded-lg p-4">
            <h3 className="text-xs font-mono font-semibold text-primary uppercase tracking-wider mb-4 pb-2 border-b border-surface-border">
              3. FLOW CHARACTERISTICS
            </h3>
            <div className="space-y-3.5">
              <div>
                <label className="block text-xs text-content-secondary mb-1">Flow Duration (ms)</label>
                <input
                  type="number"
                  value={formData.flowDurationMs}
                  onChange={(e) => handleInputChange('flowDurationMs', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-xs text-content-secondary mb-1">Flow Bytes/sec</label>
                <input
                  type="number"
                  value={formData.flowBytesPerSec}
                  onChange={(e) => handleInputChange('flowBytesPerSec', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-xs text-content-secondary mb-1">Flow Packets/sec</label>
                <input
                  type="number"
                  value={formData.flowPacketsPerSec}
                  onChange={(e) => handleInputChange('flowPacketsPerSec', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
            </div>
          </div>

          {/* Section 4: TCP Flags */}
          <div className="bg-surface-container border border-surface-border rounded-lg p-4 md:col-span-2 lg:col-span-3">
            <h3 className="text-xs font-mono font-semibold text-primary uppercase tracking-wider mb-4 pb-2 border-b border-surface-border">
              4. TCP FLAG ACTIVITY
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs text-content-secondary mb-1 font-mono">SYN Flags</label>
                <input
                  type="number"
                  value={formData.synCount}
                  onChange={(e) => handleInputChange('synCount', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-xs text-content-secondary mb-1 font-mono">ACK Flags</label>
                <input
                  type="number"
                  value={formData.ackCount}
                  onChange={(e) => handleInputChange('ackCount', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-xs text-content-secondary mb-1 font-mono">RST Flags</label>
                <input
                  type="number"
                  value={formData.rstCount}
                  onChange={(e) => handleInputChange('rstCount', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-xs text-content-secondary mb-1 font-mono">FIN Flags</label>
                <input
                  type="number"
                  value={formData.finCount}
                  onChange={(e) => handleInputChange('finCount', e.target.value)}
                  className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-content-primary focus:outline-none focus:border-primary"
                />
              </div>
            </div>
          </div>

        </div>

        {/* Actions & Explanatory Context */}
        <div className="pt-4 border-t border-surface-border flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-content-muted">
            <Info className="w-4 h-4 text-primary shrink-0" />
            <span>
              Phase 1 runs analysis simulation. In Phase 2, this form will send structured JSON vectors directly to FastAPI.
            </span>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              type="button"
              onClick={() => handlePresetChange('nominal')}
              className="px-4 py-2 rounded bg-surface-container hover:bg-surface-high border border-surface-border text-xs text-content-secondary font-medium transition-colors flex items-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Nominal</span>
            </button>

            <button
              type="submit"
              disabled={isAnalyzing}
              className="w-full sm:w-auto px-6 py-2.5 rounded bg-primary hover:bg-primary-light text-background font-semibold text-xs transition-colors flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Evaluating Model Pipeline...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Run Traffic Forecast Model</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
