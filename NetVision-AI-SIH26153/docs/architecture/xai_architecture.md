# NetVision AI — Explainable AI (XAI) & Probability-Space SHAP Architecture

## 1. Executive Summary

In cybersecurity operations, high predictive accuracy without explainability leads to analyst alert fatigue and distrust in AI-driven automation. NetVision AI incorporates **Explainable AI (XAI)** at the core of every forecast using **SHAP (SHapley Additive exPlanations)**.

Crucially, rather than presenting raw, uncalibrated log-odds (margin values) typical of tree-based models, NetVision AI implements **Probability-Space SHAP Attribution**. Every feature attribution reflects an exact **percentage delta ($\Delta P$)** that directly explains why the current 5-minute traffic window exceeded or stayed below the $0.40$ decision threshold.

```mermaid
flowchart LR
    A["Raw Traffic Profile"] --> B["Runtime Transformer"]
    B --> C["XGBoost + RF Ensemble"]
    C --> D["TreeExplainer Inference"]
    D --> E["Probability-Space Transform<br>Log-Odds ➔ Delta P"]
    E --> F["Top Risk Drivers / Mitigators"]
    F --> G["SOC Waterfall Visualizer"]
```

---

## 2. The Theoretical Problem: Margin Space vs Probability Space

Standard tree ensembles produce predictions in **raw margin space (log-odds)**:

$$f(x) = \ln \left( \frac{P(\text{Attack})}{1 - P(\text{Attack})} \right)$$

While default TreeExplainer algorithms satisfy Shapley efficiency in margin space:

$$\sum_{i=1}^{M} \phi_i^{\text{margin}} = f(x) - \mathbb{E}[f(x)]$$

These values are unintelligible to human SOC analysts:
- An analyst cannot easily understand what $+1.84 \text{ logits}$ means in terms of operational threat level.
- Nonlinear logit saturation means a $+1.0$ logit increase at $P=0.50$ produces a massive probability shift ($+0.231$), while the same $+1.0$ logit increase at $P=0.95$ produces an almost imperceptible probability change ($+0.031$).

### 2.1 The NetVision Probability-Space Transformation

NetVision AI calibrates margin SHAP contributions into intuitive probability deltas $\phi_i^{\text{prob}}$:

$$\phi_i^{\text{prob}} = \phi_i^{\text{margin}} \times \left( \frac{P(\text{Attack}) - P_{\text{base}}}{\sum_{j=1}^{M} \phi_j^{\text{margin}}} \right)$$

Where:
- $P(\text{Attack}) \in [0, 1]$ is the final ensemble attack probability.
- $P_{\text{base}} = \mathbb{E}[P(\text{Attack})] = 0.3631$ is the empirical expectation over the background dataset.
- $\sum_{i=1}^{M} \phi_i^{\text{prob}} = P(\text{Attack}) - P_{\text{base}}$ satisfies the **Efficiency Axiom directly in probability space**.

---

## 3. Background Reference Dataset (`shap_background.csv`)

TreeExplainer requires a background reference distribution $\mathcal{D}_{\text{bg}}$ to estimate expected marginal values $\mathbb{E}[f(x) \mid S]$.

### 3.1 Selection Methodology
- **Size**: 50 representative 5-minute observation windows (50 rows $\times$ 138 canonical features).
- **Stratification**: Sampled across genuine Phase 4 temporal windows containing both nominal corporate activity and multi-vector intrusion phases from **CSE-CIC-IDS2018**.
- **Performance Trade-Off**:
  - Background size of $N=50$ maintains high fidelity with the true continuous distribution while keeping inference latency strictly **under 200 ms** per forecast.

```
Baseline Expected Attack Probability (P_base): 0.3631 (36.31%)
```

---

## 4. Top SHAP Risk Drivers & Interpretations

Empirical SHAP analysis across genuine cyber attack profiles identifies five dominant behavioral feature families:

| Canonical Model Feature | Domain Meaning | Direction of Risk Impact | Cyber Phenomenon |
| :--- | :--- | :---: | :--- |
| **`Bwd Pkts/s_mean`** | Backward Packet Rate | Positive ($\uparrow$) | Rapid response generation during port scans or DoS reflections |
| **`Fwd Seg Size Min_mean`** | Minimum Segment Size | Negative ($\downarrow$) or Positive | Anomalous TCP segment headers (e.g. 20-byte empty SYN/ACK probes) |
| **`TotLen Fwd Pkts_sum`** | Forward Byte Volume | Positive ($\uparrow$) | Data exfiltration, bulk automated HTTP POST floods |
| **`Pkt Len Max_max`** | Maximum Packet Length | Positive ($\uparrow$) | Large payload fragmentation or buffer overflow attempts |
| **`Flow Duration_max`** | Longest Connection Duration | Positive ($\uparrow$) | Slowloris stealth attacks or persistent C2 beaconing |
| **`PSH Flag Cnt_sum`** | Push Flag Count | Positive ($\uparrow$) | Immediate buffer flush requests during interactive command injection |

---

## 5. Software Architecture & Implementation

The XAI engine is encapsulated in [`src/xai/shap_explainer.py`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/src/xai/shap_explainer.py):

```python
class SHAPExplainer:
    """
    Computes calibrated probability-space SHAP feature contributions
    for the NetVision AI ensemble.
    """
    def __init__(self, model, background_data: pd.DataFrame, feature_names: list[str]):
        self.feature_names = feature_names
        self.explainer = shap.TreeExplainer(
            model,
            data=background_data,
            feature_perturbation="interventional",
            model_output="probability"
        )
        self.base_value = float(self.explainer.expected_value)

    def explain_instance(self, instance_df: pd.DataFrame, top_k: int = 5) -> list[dict]:
        shap_values = self.explainer.shap_values(instance_df)[0]
        
        # Sort by absolute impact
        ranked_indices = np.argsort(np.abs(shap_values))[::-1][:top_k]
        
        explanations = []
        for idx in ranked_indices:
            feat_name = self.feature_names[idx]
            val = float(instance_df.iloc[0, idx])
            sv = float(shap_values[idx])
            explanations.append({
                "feature": feat_name,
                "value": val,
                "shap_value": sv,
                "impact": "Increases Attack Risk" if sv > 0 else "Decreases Attack Risk"
            })
        return explanations
```

---

## 6. UI Integration: SOC Waterfall & Radar

In the frontend dashboard ([`frontend/src/components/analysis/AnalysisView.jsx`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/frontend/src/components/analysis/AnalysisView.jsx)):
- **Waterfall Chart**: Displays base probability ($36.3\%$) sequentially modified by positive (red) and negative (emerald green) feature contributions leading to the final probability.
- **Top Drivers List**: Translates technical column names (`Fwd Seg Size Min_mean`) into plain-English analyst descriptors (*"Minimum Forward Segment Size"*).
