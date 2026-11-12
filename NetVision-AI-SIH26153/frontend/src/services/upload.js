/**
 * NetVision AI — capture upload service
 *
 * Talks to the backend preprocessing endpoint. Raw CICFlowMeter flow CSVs,
 * PCAP/PCAPNG captures and pre-aggregated profile CSVs all go through the
 * same multipart route; the backend detects the format.
 */

import { API_BASE_URL } from './api';

export const MAX_UPLOAD_BYTES = 200 * 1024 * 1024;

export const UPLOAD_ACCEPT = [
  '.csv',
  '.pcap',
  '.pcapng',
  '.cap',
  'text/csv',
  'application/vnd.tcpdump.pcap',
  'application/x-pcap',
  'application/x-pcapng',
].join(',');

export const SOURCE_LABELS = {
  cicflowmeter_csv: 'CICFlowMeter CSV',
  pcap: 'PCAP capture',
  pcapng: 'PCAPNG capture',
  profile_csv: '40-field profile CSV',
  feature_csv: '138-feature model CSV',
};

export function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatCount(value) {
  if (!Number.isFinite(value)) return '—';
  return Math.round(value).toLocaleString();
}

/** Display a naive-UTC ISO timestamp without applying a local timezone shift. */
export function formatWindowTime(iso) {
  if (!iso || typeof iso !== 'string') return null;
  const [date, time] = iso.split('T');
  if (!time) return date;
  return `${date} ${time.slice(0, 5)}`;
}

/**
 * Round backend profile values for display in the 40-field form.
 *
 * The API returns full float precision; six significant digits preserve every
 * meaningful traffic statistic while keeping the inputs readable.
 */
export function profileToFormValues(profile) {
  const values = {};
  for (const [key, value] of Object.entries(profile || {})) {
    const numeric = Number(value);
    values[key] = Number.isFinite(numeric) ? Number(numeric.toPrecision(6)) : 0;
  }
  return values;
}

export async function preprocessCaptureFile(file, { signal } = {}) {
  if (!file) {
    throw new Error('Choose a capture file first.');
  }

  if (file.size > MAX_UPLOAD_BYTES) {
    throw new Error(
      `This file is ${formatBytes(file.size)}; the upload limit is ${formatBytes(MAX_UPLOAD_BYTES)}. Split the capture into smaller files.`
    );
  }

  const formData = new FormData();
  formData.append('file', file);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/preprocess/file`, {
      method: 'POST',
      body: formData,
      signal,
    });
  } catch (error) {
    if (error?.name === 'AbortError') throw error;
    throw new Error(
      'Could not reach the preprocessing service. Confirm the FastAPI backend is running and try again.'
    );
  }

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = payload?.detail;
    throw new Error(
      typeof detail === 'string'
        ? detail
        : `Preprocessing failed with status ${response.status}.`
    );
  }

  if (!payload || !Array.isArray(payload.windows) || payload.windows.length === 0) {
    throw new Error('The preprocessing service returned no observation windows.');
  }

  return payload;
}
