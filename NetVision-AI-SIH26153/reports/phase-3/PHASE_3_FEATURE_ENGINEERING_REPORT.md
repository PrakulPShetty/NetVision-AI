PHASE 3 REPORT — FEATURE ENGINEERING & FEATURE SELECTION

Project

SIH26153 — AI Based Network Attack Forecasting from Network Traffic Data

Phase

Phase 3 — Feature Engineering + Feature Selection

Status

COMPLETED AND VALIDATED

1. Objective

The objective of Phase 3 was to transform the cleaned and chronologically ordered Phase 2 CIC-IDS2018 datasets into a reduced, consistent, model-ready feature representation.

The phase focused on:

Preparing numerical network-traffic features.

Investigating anomalous numerical values.

Defining appropriate treatment for special values.

Investigating feature redundancy.

Selecting a reduced feature set.

Creating the final Phase 3 datasets.

Preserving Timestamp and Label for subsequent temporal modelling.

Validating the final datasets stored in the Hugging Face dataset repository.

Phase 3 did not perform temporal aggregation or forecasting. Those tasks belong to Phase 4 and later phases.

2. Input Dataset

Phase 3 used the outputs of Phase 2.

The Phase 2 datasets contained 15,822,221 records across 10 files and were cleaned, chronologically ordered, and validated before entering Phase 3.

3. Phase 3 Workflow

Phase 2 Cleaned Dataset
        ↓
Numeric Feature Preparation
        ↓
Numerical Value Quality Investigation
        ↓
Anomalous Feature Interpretation
        ↓
Special-Value Treatment
        ↓
Feature Redundancy Analysis
        ↓
Redundancy-Based Feature Selection
        ↓
Final 68 Model Features
        ↓
Final Phase 3 Dataset
        ↓
Hugging Face Validation

4. Numerical Feature Preparation

The Phase 2 schema was investigated to determine the model-input columns.

The common CIC-IDS2018 schema contained:

Timestamp

Label

78 model-input features

The Tuesday dataset also contained additional identity-related fields:

Flow ID

Src IP

Src Port

Dst IP

These identity fields were not included in the common model feature set.

Timestamp was retained for temporal representation, and Label was retained as the target information for later modelling.

5. Numerical Value Quality Investigation

An optimized DuckDB-based investigation was performed across all 10 datasets.

Four features contained special numerical conditions:

Feature

Condition

Affected values

Flow Byts/s

Invalid/non-numeric values

36,005

Flow Pkts/s

Invalid/non-numeric values

94,348

Init Fwd Win Byts

Value = -1

4,432,096

Init Bwd Win Byts

Value = -1

8,192,276

No infinite numerical values were detected.

The affected values occurred across multiple dataset files rather than being isolated to a single file.

6. Special-Value Treatment

The verified treatment was:

Flow Byts/s
Invalid values → NaN

Flow Pkts/s
Invalid values → NaN

Init Fwd Win Byts
-1 → NaN

Init Bwd Win Byts
-1 → NaN

These treatments affected feature values but did not remove network-flow records.

Total affected feature values:

12,754,725

Missing-value imputation and model-specific handling were deferred to later modelling stages so that the strategy can be selected according to the temporal split and model requirements.

7. Feature Redundancy Analysis

Feature redundancy was investigated using:

10,000 sampled rows per file

100,000 total sampled rows

78 model-input features

Correlation threshold: |r| >= 0.95

The analysis identified:

46 highly correlated feature pairs

42 features appearing in at least one highly correlated pair

The analysis identified redundant relationships between features; it did not represent a count of duplicate individual values.

No features were automatically deleted during the redundancy analysis.

8. Feature Selection

The redundancy findings were used to define candidate features for removal while retaining representative features from correlated groups.

The final 10 removed features were:

Subflow Fwd Pkts

Subflow Fwd Byts

Fwd Act Data Pkts

Subflow Bwd Pkts

Subflow Bwd Byts

Flow IAT Min

Fwd IAT Min

Fwd Seg Size Avg

Bwd Seg Size Avg

Fwd Pkts/s

Feature-count reduction

Original model features : 78
Removed features        : 10
Final model features    : 68

No dataset rows were removed during feature selection.

9. Final 68 Model Features

The final model feature set contains:

Dst Port

Protocol

Flow Duration

Tot Fwd Pkts

Tot Bwd Pkts

TotLen Fwd Pkts

TotLen Bwd Pkts

Fwd Pkt Len Max

Fwd Pkt Len Min

Fwd Pkt Len Mean

Fwd Pkt Len Std

Bwd Pkt Len Max

Bwd Pkt Len Min

Bwd Pkt Len Mean

Bwd Pkt Len Std

Flow Byts/s

Flow Pkts/s

Flow IAT Mean

Flow IAT Std

Flow IAT Max

Fwd IAT Tot

Fwd IAT Mean

Fwd IAT Std

Fwd IAT Max

Bwd IAT Tot

Bwd IAT Mean

Bwd IAT Std

Bwd IAT Max

Bwd IAT Min

Fwd PSH Flags

Bwd PSH Flags

Fwd URG Flags

Bwd URG Flags

Fwd Header Len

Bwd Header Len

Bwd Pkts/s

Pkt Len Min

Pkt Len Max

Pkt Len Mean

Pkt Len Std

Pkt Len Var

FIN Flag Cnt

SYN Flag Cnt

RST Flag Cnt

PSH Flag Cnt

ACK Flag Cnt

URG Flag Cnt

CWE Flag Count

ECE Flag Cnt

Down/Up Ratio

Pkt Size Avg

Fwd Byts/b Avg

Fwd Pkts/b Avg

Fwd Blk Rate Avg

Bwd Byts/b Avg

Bwd Pkts/b Avg

Bwd Blk Rate Avg

Init Fwd Win Byts

Init Bwd Win Byts

Fwd Seg Size Min

Active Mean

Active Std

Active Max

Active Min

Idle Mean

Idle Std

Idle Max

Idle Min

10. Final Phase 3 Dataset Creation

The final feature-selected datasets were created separately from the Phase 3 intermediate datasets.

Each final dataset contains:

68 model features
+
Timestamp
+
Label
=
70 total columns

The feature-selection operation selected columns only and preserved all network-flow records.

Final dataset size:

15,822,221 records across 10 files.

11. Hugging Face Storage

The final Phase 3 datasets were uploaded to the project's Hugging Face dataset repository:

PrakulShetty/NetVision-AI-SIH26153

under:

processed/phase3/final/

All 10 final files were successfully uploaded.

Phase 2 datasets and Phase 3 intermediate datasets were preserved separately.

12. Final Hugging Face Validation

The final datasets were validated directly from the Hugging Face repository.

The validation confirmed:

Validation

Result

Final files

10/10 PASS

Total records

15,822,221

Expected records

15,822,221

Columns per file

70

Model features

68

Timestamp

Present

Label

Present

Invalid timestamps

0

Empty labels

0

Schema validation

PASS

Row-count validation

PASS

All ten datasets passed final validation.

13. Phase 3 Final Dataset Structure

CIC-IDS2018 Original
        ↓
Phase 2
Cleaned + Chronologically Ordered
        ↓
Phase 3
Feature Engineering
        ↓
78 Model Features
        ↓
Redundancy Analysis
        ↓
10 Features Removed
        ↓
68 Final Model Features
        ↓
Timestamp + Label Retained
        ↓
70 Columns
        ↓
15,822,221 Records
        ↓
Hugging Face
processed/phase3/final/
        ↓
FINAL VALIDATION: PASS

14. Scope Boundary

Phase 3 does not yet create the temporal forecasting representation.

The current final dataset remains flow-level network traffic data with timestamps.

The following tasks belong to Phase 4:

Time-window construction

Temporal aggregation

Lag features

Rolling statistics

Network-state representation

Forecast-target construction

Temporal train/validation/test splitting

Final temporal dataset preparation

Therefore, the validated Phase 3 datasets are now locked as the input to Phase 4.

15. Final Status

PHASE 3 — COMPLETED

Phase 3 successfully reduced the CIC-IDS2018 model input from 78 to 68 features while preserving all 15,822,221 network-flow records.

The final dataset contains 70 columns:

68 model features

Timestamp

Label

The 10 final datasets were stored under:

processed/phase3/final/

in the project Hugging Face dataset repository and directly validated successfully.

Phase 3 is officially complete.

Next Phase: Phase 4 — Temporal Representation.