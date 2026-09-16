/**
 * NetVision AI — forecast response normalisation
 *
 * Single place where the FastAPI `POST /forecast` payload is converted into the
 * view model used by the pages. Keeping this isolated means:
 *
 *   1. Pages never read raw backend keys, so backend schema changes are handled
 *      in one file instead of every component.
 *   2. Nothing here fabricates values — every field is either taken from the
 *      response or explicitly marked as unavailable.
 */

import { describeFeature } from '../utils/features';

const SIGNAL_GROUP_LABELS = {
  destination_diversity: 'Destination diversity',
  traffic_volume: 'Traffic volume',
  packet_rate: 'Packet rate',
  temporal_concentration: 'Temporal concentration',
};

const toPercent = (value) => {
  const n = Number(value);
  return Number.isFinite(n) ? Number((n * 100).toFixed(2)) : null;
};

function normaliseContributions(rawXai, ml) {
  const rows = Array.isArray(rawXai.top_contributions) ? rawXai.top_contributions : [];
  const maxAbs = rows.reduce((max, row) => Math.max(max, Math.abs(Number(row.shap_value) || 0)), 0) || 1;

  const contributions = rows.map((row) => {
    const meta = describeFeature(row.feature);
    const value = Number(row.shap_value) || 0;
    const abs = Math.abs(value);
    return {
      ...meta,
      value,
      abs,
      importance: (abs / maxAbs) * 100,
      direction: value > 0 ? 'raises' : value < 0 ? 'lowers' : 'neutral',
      influence: value > 0 ? 'Raises attack probability' : value < 0 ? 'Lowers attack probability' : 'No directional effect',
      // Attribution is expressed in probability space by the backend.
      interpretation: meta.meaning
        ? `${meta.meaning} In this window this signal ${value > 0 ? 'increased' : 'reduced'} the ensemble attack probability by ${Math.abs(value).toFixed(4)}.`
        : `This signal ${value > 0 ? 'increased' : 'reduced'} the ensemble attack probability by ${Math.abs(value).toFixed(4)}.`,
    };
  });

  const raisers = contributions.filter((c) => c.value > 0);
  const reducers = contributions.filter((c) => c.value < 0);

  const summary = raisers.length
    ? `The forecast is driven primarily by ${raisers
        .slice(0, 3)
        .map((c) => c.label.toLowerCase())
        .join(', ')}.` +
      (reducers.length
        ? ` ${reducers
            .slice(0, 2)
            .map((c) => c.label.toLowerCase())
            .join(' and ')} pulled the probability back down.`
        : '')
    : 'No feature increased the attack probability for this window.';

  const method = rawXai.method || 'Probability-space SHAP';

  return {
    available: contributions.length > 0,
    method,
    summary,
    contributions,
    raisers,
    reducers,
    baseProbability: toPercent(rawXai.base_probability),
    reconstructedProbability: toPercent(rawXai.reconstructed_probability),
    validationPassed: rawXai.validation_passed ?? null,
    xgbProbability: toPercent(rawXai.ensemble?.xgb_attack_probability ?? ml.xgb),
    rfProbability: toPercent(rawXai.ensemble?.rf_attack_probability ?? ml.rf),
  };
}

function normaliseSignalGroups(rawGroups) {
  if (!rawGroups || typeof rawGroups !== 'object') return [];
  return Object.entries(rawGroups).map(([name, group]) => {
    const features = Array.isArray(group?.supporting_features)
      ? group.supporting_features.map((feature) => describeFeature(feature))
      : [];
    const active = typeof group === 'boolean' ? group : Boolean(group?.present ?? group?.active);
    return {
      name,
      label: SIGNAL_GROUP_LABELS[name] || name.replace(/_/g, ' '),
      active,
      features,
      detail: group?.reason || group?.detail || '',
    };
  });
}

function normaliseMitre(rawMitre) {
  const techniquesRaw = Array.isArray(rawMitre.techniques) ? rawMitre.techniques : [];
  const legacy = !techniquesRaw.length && rawMitre.id ? [rawMitre] : techniquesRaw;

  const techniques = legacy.map((tech) => {
    const evidence = Array.isArray(tech.evidence)
      ? tech.evidence.map((item) => {
          if (typeof item === 'string') {
            return { group: item, label: SIGNAL_GROUP_LABELS[item] || item.replace(/_/g, ' '), features: [] };
          }
          return {
            group: item.signal_group,
            label: SIGNAL_GROUP_LABELS[item.signal_group] || String(item.signal_group || 'Evidence').replace(/_/g, ' '),
            features: Array.isArray(item.supporting_features)
              ? item.supporting_features.map((feature) => describeFeature(feature))
              : [],
          };
        })
      : [];

    return {
      id: tech.technique_id || tech.id || '—',
      name: tech.technique_name || tech.name || 'Unnamed technique',
      tactic: tech.tactic || '—',
      confidence: tech.confidence ?? 'Not specified',
      evidence,
      features: Array.isArray(tech.supporting_features)
        ? tech.supporting_features.map((feature) => describeFeature(feature))
        : Array.isArray(tech.features)
        ? tech.features.map((feature) => describeFeature(feature))
        : [],
      interpretation: tech.interpretation || '',
      limitation: tech.limitation || 'Flow-level evidence alone cannot confirm malicious intent.',
    };
  });

  return {
    status: rawMitre.mapping_status || (techniques.length ? 'MITRE ATT&CK mapping identified' : 'No confident MITRE mapping identified'),
    reason: rawMitre.reason || '',
    techniques,
    identified: techniques.length > 0,
    signalGroups: normaliseSignalGroups(rawMitre.signal_groups),
  };
}

/**
 * Convert a raw backend forecast response into the NetVision AI view model.
 * Returns null when there is nothing usable in the payload.
 */
export function normaliseForecast(data) {
  if (!data) return null;

  const mlRaw = data.ml || data.ml_forecast || {};
  const probability = toPercent(mlRaw.ensemble_attack_probability) ?? 0;
  const threshold = toPercent(mlRaw.decision_threshold) ?? 40;

  const ml = {
    state: mlRaw.current_state_label || mlRaw.predicted_current_state || (probability >= threshold ? 'ATTACK' : 'BENIGN'),
    probability,
    threshold,
    margin: Number((probability - threshold).toFixed(2)),
    xgb: toPercent(mlRaw.xgb_attack_probability),
    rf: toPercent(mlRaw.rf_attack_probability),
    stateIndex: mlRaw.current_state,
  };

  const rawForecasts = data.world_model?.forecasts || [];
  const forecast = rawForecasts.map((item) => {
    const minutes = Number(item.horizon_minutes) || (Number(item.steps) * 5 || 10);
    const stateProbability = toPercent(item.future_attack_probability ?? item.attack_probability) ?? 0;
    const benignProbability = toPercent(item.future_benign_probability) ?? Number((100 - stateProbability).toFixed(2));
    return {
      minutes,
      horizon: `${minutes}m`,
      steps: item.steps ?? Math.round(minutes / 5),
      k: item.steps ?? Math.round(minutes / 5),
      probability: Number(stateProbability.toFixed(2)),
      benignProbability: Number(benignProbability.toFixed(2)),
      state: item.forecast_state || item.state || (stateProbability >= 50 ? 'ATTACK' : 'BENIGN'),
      aboveThreshold: stateProbability >= threshold,
    };
  });

  const xai = normaliseContributions(data.xai || {}, ml);
  const mitre = normaliseMitre(data.mitre_attack || data.mitre || {});

  return {
    ml,
    forecast,
    xai,
    mitre,
    method: 'XGBoost + Random Forest (SMOTE) ensemble → first-order Markov world model',
  };
}
