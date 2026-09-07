PHASE 4 — TEMPORAL REPRESENTATION REPORT

Project

SIH26153 — AI based Network Attack Forecasting from Network Traffic Data

Dataset: CIC-IDS2018
Phase: 4 — Temporal Representation
Status: COMPLETE

1. Objective

Phase 4 introduced the temporal dimension into the cleaned and feature-engineered CIC-IDS2018 data.

The project is intended to forecast future network attacks rather than only classify the current traffic. Therefore, individual flow records were transformed into time-based network states.

Final design:

5-minute observation window

10-minute forecasting horizon

Window-level aggregation of network traffic features

Current network-state information

Future attack-state target

Missingness indicators where required

Chronological ordering

Leakage prevention

2. Why Temporal Representation Was Required

Before Phase 4, one row represented an individual network flow:

One row = One network flow

That representation is useful for conventional traffic classification, but forecasting requires information about how network activity changes over time.

Phase 4 changes the representation to:

One row = One 5-minute network state

This allows the ML stage to learn the relationship between the current network condition and a future attack state.

Conceptually:

Current network state
        ↓
     ML model
        ↓
Future network attack state

3. Temporal Window Investigation

Candidate window sizes investigated:

1 minute

5 minutes

10 minutes

30 minutes

The 1-minute window was relatively noisy and sparse. The 30-minute window was too coarse for capturing shorter state changes. A 10-minute window provided more aggregation but reduced finer temporal resolution.

The 5-minute window was selected as the primary experimental configuration because it provided a practical balance between temporal resolution and sufficient traffic information.

This is an experimental design choice and will be validated further during model development.

4. Forecast Horizon Investigation

Using the 5-minute representation, candidate future horizons were investigated:

Horizon

State Persistence

Attack Emergence

State Change

5 min

92.632%

2.865%

4.126%

10 min

85.866%

5.517%

7.937%

15 min

79.004%

8.089%

11.723%

The 5-minute horizon had very high persistence, while the 15-minute horizon produced more state changes but lower persistence.

The 10-minute horizon was selected as a balance between temporal continuity and meaningful future-state changes.

Therefore:

5-minute observation window → 10-minute forecasting horizon

5. Network State Representation

Each 5-minute window contains many individual network flows.

Instead of treating every flow as a separate ML observation, traffic characteristics within the window are aggregated to represent the overall network condition.

Examples include:

packet and byte totals

flow counts

traffic-rate statistics

packet-length statistics

inter-arrival-time statistics

TCP flag statistics

destination-port diversity

protocol diversity

other engineered CICFlowMeter-derived features

Conceptually:

Individual flow records
        ↓
Group into 5-minute windows
        ↓
Aggregate traffic characteristics
        ↓
5-minute network state

6. Forecasting Target

The main future target is:

future_attack_state

It represents whether the future temporal state contains attack activity according to the selected forecasting horizon.

The dataset also contains:

current_attack_state

attack_flow_count

total_flow_count

current_attack_ratio

The current state is separated from the future target to support leakage-free modelling.

7. Final Dataset Structure

Each Phase 4 file contains 198 columns.

Important fields include:

Temporal fields

window_start

dataset_day

Network-state features

Window-level aggregated traffic features derived from the Phase 3 feature set.

State/diagnostic fields

current_attack_state

attack_flow_count

total_flow_count

current_attack_ratio

Forecasting target

future_attack_state

Missingness indicators

Six indicators were retained for affected TCP initial-window features:

Init Fwd Win Byts_mean_missing

Init Fwd Win Byts_min_missing

Init Fwd Win Byts_max_missing

Init Bwd Win Byts_mean_missing

Init Bwd Win Byts_min_missing

Init Bwd Win Byts_max_missing

These indicators preserve information about the availability of the corresponding source measurements.

8. Dataset Transformation

Phase 4 transformed the Phase 3 flow-level dataset:

Input: 15,822,221 cleaned and feature-engineered flow records

Output: 1,008 temporal network-state observations

This reduction was performed through temporal aggregation, not random deletion.

15,822,221 flow records
          ↓
5-minute temporal grouping
          ↓
1,008 network states
          ↓
10-minute future target

9. Final File-Level Results

Dataset File

Temporal Rows

Columns

Friday-02-03-2018

104

198

Friday-16-02-2018

63

198

Friday-23-02-2018

110

198

Thuesday-20-02-2018

142

198

Thursday-01-03-2018

113

198

Thursday-15-02-2018

113

198

Thursday-22-02-2018

109

198

Wednesday-14-02-2018

108

198

Wednesday-21-02-2018

33

198

Wednesday-28-02-2018

113

198

Total

1,008

198 per file

The original source filename Thuesday-20-02-2018 was preserved.

10. Final Validation

The final validation checked:

Expected row counts

Expected column count

Required temporal columns

Timestamp validity

Chronological ordering

5-minute alignment

Duplicate temporal windows

NaN values

Infinite values

Future target validity

Current-state validity

Flow-count consistency

Current attack-ratio validity

Missingness indicators

Predictor schema consistency

Data leakage

All 10 files passed.

Validation Check

Result

Files

10/10 PASS

Temporal rows

1,008/1,008 PASS

Columns

198 PASS

NaN values

0 PASS

Infinite values

0 PASS

Duplicate windows

0 PASS

Ordering violations

0 PASS

Alignment failures

0 PASS

Invalid future targets

0 PASS

Invalid current states

0 PASS

Flow-count issues

0 PASS

Invalid indicators

0 PASS

Leakage issues

0 PASS

The final validation explicitly reported:

FINAL PHASE 4 VALIDATION: PASS

and confirmed that the dataset was ready for Hugging Face upload. fileciteturn64file0L197-L225

Individual files also passed all validation checks. fileciteturn64file0L13-L27

11. Hugging Face Upload

After validation, the final Phase 4 dataset was uploaded to the private project dataset repository:

PrakulShetty/NetVision-AI-SIH26153

Location:

processed/phase4/final/

Upload verification confirmed:

Phase 4 files: 10/10

Temporal rows: 1,008

Columns per file: 198

Phase 2 preserved: YES

Phase 3 preserved: YES

Phase 4 uploaded and verified: YES

12. Overall Phase 4 Pipeline

CIC-IDS2018
Raw Flow Records
        ↓
Phase 2
Cleaning & Chronological Ordering
        ↓
Phase 3
Feature Engineering
        ↓
Phase 4
Temporal Representation
        ↓
5-Minute Network States
        ↓
Current Network State
        +
Future State Target
        ↓
10-Minute Forecasting Horizon
        ↓
Phase 5 — ML Modelling

13. What Phase 4 Does and Does Not Do

Phase 4 DOES

Introduce time into the dataset

Group flows into 5-minute windows

Create network-state representations

Create a future attack-state target

Preserve chronological ordering

Prepare data for forecasting models

Validate temporal integrity and leakage

Phase 4 DOES NOT

Train an ML model

Predict attacks by itself

Select the final ML algorithm

Build the ensemble

Perform SHAP/XAI analysis

Those activities belong to later phases.

14. Key Methodological Decisions

5-minute window

Selected after comparing candidate temporal resolutions.

10-minute horizon

Selected after comparing 5-, 10-, and 15-minute future horizons.

Future target

future_attack_state is used as the forecasting target.

Leakage prevention

Current and future state information were separated, and the final validation included a leakage check.

Aggregation

Multiple flow records within a temporal window are summarized into one network-state observation.

15. Final Phase 4 Status

PHASE 4 — TEMPORAL REPRESENTATION: COMPLETE

Final result:

15,822,221 flow records
          ↓
5-minute temporal aggregation
          ↓
1,008 temporal network states
          ↓
198 columns per file
          ↓
10-minute future attack-state target
          ↓
Final validation: PASS
          ↓
Hugging Face upload: VERIFIED

The Phase 4 dataset is now ready for:

Phase 5 — ML Modelling + Ensemble Development

The next phase will establish the temporal train/validation/test strategy, separate predictors from the future target, establish the Logistic Regression reference model, evaluate individual ML models, and then experiment with ensemble approaches.