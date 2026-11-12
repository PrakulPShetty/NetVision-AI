import { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  FileText,
  Layers,
  Upload,
} from 'lucide-react';
import Panel from '../common/Panel';
import Callout from '../common/Callout';
import Chip from '../common/Chip';
import {
  MAX_UPLOAD_BYTES,
  SOURCE_LABELS,
  UPLOAD_ACCEPT,
  formatBytes,
  formatCount,
  formatWindowTime,
  preprocessCaptureFile,
} from '../../services/upload';

/**
 * Capture ingestion panel.
 *
 * Accepts raw CICFlowMeter flow CSVs, PCAP/PCAPNG captures and aggregated
 * profile CSVs. The backend extracts 5-minute windows; this panel lets the
 * analyst inspect the windows, load one into the existing 40-field form, or
 * run inference directly on the selected window.
 */

function windowTimeLabel(window, index, showDate) {
  const start = formatWindowTime(window.window_start);
  const end = formatWindowTime(window.window_end);
  const flowPart = `${formatCount(window.flow_count)} flow${window.flow_count === 1 ? '' : 's'}`;

  if (start && end) {
    const startText = showDate || !start.includes(' ') ? start : start.split(' ')[1];
    const endText = showDate || !end.includes(' ') ? end : end.split(' ')[1];
    return `${startText}–${endText} · ${flowPart}`;
  }

  return `Row ${index + 1} · ${flowPart}`;
}

export default function FileUploadPanel({
  status = 'ready',
  analyzingMode = null,
  onUseProfile,
  onAnalyzeProfile,
  onAnalyzeFeatures,
}) {
  const [phase, setPhase] = useState('idle'); // idle | working | ready | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [windowIndex, setWindowIndex] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  const startUpload = useCallback(async (file) => {
    if (!file) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setPhase('working');
    setError(null);
    setResult(null);
    setWindowIndex(0);

    try {
      const payload = await preprocessCaptureFile(file, {
        signal: controller.signal,
      });
      const firstNonEmpty = payload.windows.findIndex(
        (window) => window.flow_count > 0
      );
      setResult(payload);
      setWindowIndex(firstNonEmpty >= 0 ? firstNonEmpty : 0);
      setPhase('ready');
    } catch (uploadError) {
      if (uploadError?.name === 'AbortError') return;
      setError(uploadError.message || 'The capture could not be preprocessed.');
      setPhase('error');
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
    }
  }, []);

  const pickFile = (fileList) => {
    const file = fileList?.[0];
    if (!file) return;
    startUpload(file);
  };

  const onDrop = (event) => {
    event.preventDefault();
    setDragActive(false);
    if (phase === 'working') return;
    pickFile(event.dataTransfer.files);
  };

  const onDragOver = (event) => {
    event.preventDefault();
    if (phase !== 'working') setDragActive(true);
  };

  const onDragLeave = (event) => {
    event.preventDefault();
    setDragActive(false);
  };

  const windows = result?.windows || [];
  const selectedWindow = windows[windowIndex] || null;
  const selectedProfile = selectedWindow?.profile || null;
  const selectedFeatures = selectedWindow?.features || null;
  const sourceLabel = result
    ? SOURCE_LABELS[result.source_type] || result.source_type
    : '';
  const isPcap = result?.source_type === 'pcap' || result?.source_type === 'pcapng';
  const isWorking = phase === 'working' || status === 'analyzing';
  const analyzingLabel =
    analyzingMode === 'features' ? 'Analyzing features' : 'Analyzing window';

  const dates = new Set(
    windows.map((window) => window.window_start?.slice(0, 10)).filter(Boolean)
  );
  const showDate = dates.size > 1;

  const labels = Object.entries(result?.label_summary || {})
    .sort((left, right) => right[1] - left[1])
    .slice(0, 4);

  return (
    <Panel
      eyebrow="Capture ingestion"
      title="Upload network traffic"
      tone={phase === 'error' ? 'critical' : 'default'}
      aside={<span className="panel-note">CSV · PCAP · PCAPNG</span>}
      footer={
        <p className="panel-footnote">
          Raw flows are aggregated into 5-minute windows with the same Phase 4
          semantics used to train the model, then expanded by the existing
          runtime transformer. Labels, when present, are shown for context
          only — they are never sent to the model.
        </p>
      }
    >
      <div
        className={`upload-drop${dragActive ? ' dragging' : ''}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
      >
        <span className="upload-drop-icon" aria-hidden="true">
          {phase === 'working' ? <Clock size={26} /> : <Upload size={26} />}
        </span>
        <p className="upload-title">
          {phase === 'working'
            ? 'Preprocessing capture…'
            : 'Drop a capture file here'}
        </p>
        <p className="upload-hint">
          {phase === 'working'
            ? 'Parsing flows and building 5-minute observation windows. Large captures can take a moment.'
            : 'CICFlowMeter flow CSV, PCAP/PCAPNG capture, or an aggregated 40-field profile CSV.'}
        </p>
        <button
          type="button"
          className="button small"
          disabled={phase === 'working'}
          onClick={() => inputRef.current?.click()}
        >
          <FileText size={14} /> Choose file
        </button>
        <input
          ref={inputRef}
          className="upload-input"
          type="file"
          accept={UPLOAD_ACCEPT}
          onChange={(event) => {
            pickFile(event.target.files);
            event.target.value = '';
          }}
        />
        <p className="upload-limit">
          Up to {formatBytes(MAX_UPLOAD_BYTES)} · the server also enforces a
          5-minute window and row/packet limit.
        </p>
      </div>

      {phase === 'error' && (
        <div className="upload-error">
          <Callout tone="critical" title="Could not read this capture">
            {error}
          </Callout>
        </div>
      )}

      {result && (
        <div className="upload-summary">
          <div className="upload-summary-head">
            <Chip tone={isPcap ? 'info' : 'normal'}>{sourceLabel}</Chip>
            <span className="upload-file">{result.filename}</span>
            <span className="upload-size">{formatBytes(result.file_size_bytes)}</span>
          </div>

          <div className="upload-stats">
            <div className="upload-stat">
              <span>Windows</span>
              <strong>{formatCount(result.window_count)}</strong>
            </div>
            <div className="upload-stat">
              <span>{isPcap ? 'Packets' : 'Flows'}</span>
              <strong>
                {formatCount(
                  isPcap ? result.packet_count : result.row_count
                )}
              </strong>
            </div>
            <div className="upload-stat">
              <span>Window length</span>
              <strong>{Math.round(result.window_seconds / 60)} min</strong>
            </div>
            <div className="upload-stat">
              <span>Profile</span>
              <strong>{result.has_features ? '138 features' : '40 fields'}</strong>
            </div>
          </div>

          {labels.length > 0 && (
            <div className="upload-labels">
              <span className="upload-label-title">Source labels</span>
              <div className="upload-label-chips">
                {labels.map(([label, count]) => (
                  <Chip
                    key={label}
                    tone={label.trim().toLowerCase() === 'benign' ? 'normal' : 'critical'}
                    title={`${formatCount(count)} flow(s) labelled ${label}`}
                  >
                    {label} · {formatCount(count)}
                  </Chip>
                ))}
              </div>
            </div>
          )}

          <label className="upload-window">
            <span>
              Observation window ({windowIndex + 1} of {windows.length})
            </span>
            <select
              value={windowIndex}
              onChange={(event) => setWindowIndex(Number(event.target.value))}
            >
              {windows.map((window, index) => (
                <option key={window.index ?? index} value={index}>
                  {windowTimeLabel(window, index, showDate)}
                </option>
              ))}
            </select>
          </label>

          {selectedWindow && (
            <div className="upload-window-detail">
              <span>
                <strong>{formatCount(selectedWindow.flow_count)}</strong> flows
              </span>
              {selectedWindow.window_start && (
                <span>{formatWindowTime(selectedWindow.window_start)}</span>
              )}
              {selectedWindow.attack_flow_count !== null &&
                selectedWindow.attack_flow_count !== undefined && (
                  <span>
                    <strong>{formatCount(selectedWindow.attack_flow_count)}</strong>{' '}
                    labelled attack flows
                  </span>
                )}
              {selectedProfile && (
                <span>
                  <strong>40</strong> profile fields ready
                </span>
              )}
              {selectedFeatures && (
                <span>
                  <strong>138</strong> model features ready
                </span>
              )}
            </div>
          )}

          <div className="upload-actions">
            {selectedProfile && (
              <>
                <button
                  type="button"
                  className="button primary small"
                  disabled={isWorking}
                  onClick={() => {
                    onUseProfile?.(selectedProfile);
                    onAnalyzeProfile?.(selectedProfile);
                  }}
                >
                  {status === 'analyzing' ? (
                    <>
                      <i className="spinner" /> {analyzingLabel}
                    </>
                  ) : (
                    <>
                      Analyze selected window <ArrowRight size={14} />
                    </>
                  )}
                </button>
                <button
                  type="button"
                  className="text-button"
                  disabled={isWorking}
                  onClick={() => onUseProfile?.(selectedProfile)}
                >
                  <Layers size={14} /> Load into form
                </button>
              </>
            )}

            {selectedFeatures && (
              <button
                type="button"
                className="button primary small"
                disabled={isWorking}
                onClick={() => onAnalyzeFeatures?.(selectedFeatures)}
              >
                {status === 'analyzing' ? (
                  <>
                    <i className="spinner" /> {analyzingLabel}
                  </>
                ) : (
                  <>
                    Analyze feature row <ArrowRight size={14} />
                  </>
                )}
              </button>
            )}

            {phase === 'ready' && (
              <span className="upload-ready">
                <CheckCircle2 size={14} /> Preprocessing complete
              </span>
            )}
          </div>

          {result.warnings?.length > 0 && (
            <details className="upload-warnings">
              <summary>
                <AlertTriangle size={13} /> {result.warnings.length}{' '}
                preprocessing note{result.warnings.length === 1 ? '' : 's'}
              </summary>
              <ul>
                {result.warnings.map((warning, index) => (
                  <li key={`${index}-${warning.slice(0, 24)}`}>{warning}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </Panel>
  );
}
