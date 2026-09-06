PHASE 2 — CIC-IDS2018 DATA PREPROCESSING REPORT

Project: SIH26153 — AI Based Network Attack Forecasting from Network Traffic Data
Project Name: NetVision-AI-SIH26153
Dataset: CSE-CIC-IDS2018
Phase: Phase 2 — Data Preprocessing & Dataset Preparation
Status: ✅ COMPLETED

1. Phase Overview

Phase 2 focused on preparing the verified CIC-IDS2018 network traffic dataset for subsequent feature engineering, temporal representation, machine learning, and attack forecasting.

The objective of this phase was to perform data cleaning and structural preparation without prematurely making modelling decisions.

The preprocessing pipeline addressed:

Dataset metadata and provenance
Timestamp conversion
Malformed/header-like records
Suspicious timestamps
Chronological ordering
Missing values
Infinite values
Duplicate records
Invalid numerical values
Schema and data-type consistency
Missing-rate features
Final chronological ordering
Final dataset validation

The resulting dataset is stored locally in the Colab environment at:

/content/phase2_final
2. Input Dataset

The input to Phase 2 was the verified CIC-IDS2018 dataset copied from the public source to the project's private Hugging Face repository.

The dataset consists of 10 CICFlowMeter CSV files corresponding to different traffic-capture days.

The Phase 2 input contained:

16,233,002 rows

across the 10 files.

The dataset contains flow-level network traffic features together with:

Timestamp
Label
Protocol information
Forward traffic statistics
Backward traffic statistics
Packet statistics
Inter-arrival-time features
TCP flag information
Active/idle statistics
Flow-rate features
3. Phase 2 Objectives

The main objectives were:

Establish dataset metadata and provenance.
Convert timestamps into a usable datetime representation.
Identify and remove malformed/header-like records.
Investigate suspicious timestamp values.
Establish chronological ordering using Timestamp.
Investigate and handle missing and infinite numerical values.
Identify and remove exact duplicate records.
Investigate invalid negative numerical values.
Preserve valid special values where their meaning is dataset-specific.
Verify schema consistency.
Investigate missing values in flow-rate features.
Produce a final chronologically ordered dataset.
Validate the final dataset before entering Feature Engineering.
4. Phase 2 Processing Pipeline

The final preprocessing workflow was:

CIC-IDS2018 Verified Dataset
            ↓
Dataset Metadata & Provenance
            ↓
Timestamp Conversion
            ↓
Malformed Row Removal
            ↓
Suspicious Timestamp Investigation
            ↓
Timestamp Cleaning
            ↓
Chronological Ordering
            ↓
Missing & Infinite Value Handling
            ↓
Duplicate Investigation & Removal
            ↓
Invalid Numerical Value Investigation
            ↓
Invalid Record Removal
            ↓
Schema & Data-Type Investigation
            ↓
Missing-Rate Investigation
            ↓
Final Chronological Re-Sort
            ↓
Final Validation
            ↓
/content/phase2_final
5. Dataset Metadata & Provenance

A metadata and provenance stage was added at the beginning of Phase 2.

The metadata investigation recorded:

Dataset source
Source files
File names
Row counts
Column counts
Column names
Presence of Timestamp
Presence of Label
Basic schema information
Dataset structure

The investigation confirmed that:

All 10 files contain Timestamp.
All 10 files contain Label.
9 files contain 80 columns.
The Tuesday file contains 84 columns.

The Tuesday file contains four additional endpoint-related fields:

Flow ID
Src IP
Src Port
Dst IP

These fields were not removed during Phase 2, because their usefulness and potential modelling implications belong to later feature engineering decisions.

6. Timestamp Conversion

The original dataset contained timestamps represented as text.

The timestamp format was:

%d/%m/%Y %H:%M:%S

For example:

16/02/2018 08:27:23

The timestamps were converted into a datetime representation.

Timestamp was treated as the authoritative basis for temporal ordering.

This decision is important because the original CSV row order cannot be assumed to represent chronological order.

7. Malformed/Header-Like Row Handling

During timestamp conversion and validation, several files contained malformed rows resembling repeated header records.

These rows contained invalid/non-numeric values across the traffic-feature columns and malformed timestamp values.

The affected files were:

Friday-16-02-2018
Thursday-01-03-2018
Wednesday-28-02-2018

A total of:

59 malformed/header-like rows

were identified and removed.

These rows were not treated as genuine network traffic records.

8. Suspicious Timestamp Investigation

During temporal validation, suspicious timestamps from the year 1970 were identified in:

Thursday-22-02-2018
Wednesday-14-02-2018

Investigation showed:

9 suspicious rows in Thursday-22-02-2018
5 suspicious rows in Wednesday-14-02-2018

Total:

14 suspicious timestamp records

The suspicious records were associated with:

1970 timestamps
Benign labels
Implausible numerical traffic values
Negative/non-positive traffic-rate characteristics

Because these timestamps were inconsistent with the corresponding 2018 traffic-capture period, the records were removed rather than having their timestamps artificially corrected.

9. Chronological Ordering

Chronological ordering is particularly important for this project because SIH26153 requires network-state evolution and future attack forecasting.

Therefore:

Timestamp
   ↓
Chronological ordering
   ↓
Temporal representation
   ↓
State transition
   ↓
Future-state prediction

The dataset was sorted using the cleaned Timestamp field.

The final chronological re-sort was performed after all row-level cleaning operations.

This was necessary because operations such as duplicate removal can change physical row ordering.

10. Missing and Infinite Value Handling

The initial data-quality investigation identified missing and infinite values primarily in:

Flow Byts/s
Flow Pkts/s

Before infinite-value conversion:

59,721 missing cells

were identified.

A total of:

131,799 infinite cells

were identified.

Infinite values were converted to:

NaN

After this conversion:

191,520 missing cells

were present before later duplicate and invalid-record removal.

Importantly, no rows were blindly deleted simply because these rate features were missing.

The final modelling treatment of these missing values is intentionally deferred to the ML preprocessing stage so that any imputation parameters can be learned from training data only and temporal/data leakage can be avoided.

11. Duplicate Record Investigation

Exact duplicate records were investigated after the initial numerical cleaning.

The investigation covered all 10 files.

Total rows investigated:

16,232,929

Exact duplicate records identified:

410,707

Overall duplicate percentage:

2.5301%

The duplicate rate varied considerably between files.

The largest duplicate concentrations occurred in:

Friday-16-02-2018
Wednesday-14-02-2018

Both benign and attack records were present among duplicates.

Exact duplicates were removed while retaining the first occurrence.

Near-duplicates or similar traffic records were not automatically removed, because they may represent legitimate repeated network behaviour.

12. Invalid Numerical Value Investigation

Negative-value investigation was performed on the cleaned dataset.

Two groups of values required different treatment.

12.1 Initial TCP Window Features

The following features contained -1 values:

Init Fwd Win Byts
Init Bwd Win Byts

The counts were:

Init Bwd Win Byts: 8,192,276 negative values
Init Fwd Win Byts: 4,432,096 negative values

All negative values in these two features were exactly:

-1

Therefore, they were treated as a dataset-specific special value rather than automatically classified as invalid.

They were preserved for later feature-engineering decisions.

13. Actual Invalid Negative Record

Two IAT features contained one genuinely invalid negative record:

Fwd IAT Min
Flow IAT Min

The invalid record contained:

Flow IAT Min = -2228
Fwd IAT Min  = -2171

The record occurred in:

Friday-23-02-2018

with:

Timestamp: 2018-02-23 10:22:22
Label: Benign

This record was removed because the negative IAT values were not consistent with valid inter-arrival-time measurements.

Total records removed at this stage:

1

14. Schema & Data-Type Investigation

The final schema investigation confirmed that:

9 files contain the common 80-column CICFlowMeter structure.
The Tuesday file contains 84 columns.
All files contain Timestamp.
All files contain Label.
Common traffic features are numerically represented.
No unexpected mixed-type column issue was identified during validation.

The four additional Tuesday fields are:

Flow ID
Src IP
Src Port
Dst IP

No feature was physically removed during this phase based solely on redundancy or correlation.

Feature selection is reserved for Phase 3.

15. Missing-Rate Feature Investigation

The missing values in:

Flow Byts/s
Flow Pkts/s

were investigated to determine whether they could safely be reconstructed.

The investigation showed that affected records could not be reliably reconstructed from the available flow information in the examined cases.

Therefore, the decision was:

Do not fabricate or blindly reconstruct the missing flow-rate values.

The remaining missing values will be handled during the model-preparation stage using a leakage-safe strategy.

16. Final Chronological Re-Sort

After all row-level preprocessing operations were completed, the dataset was re-sorted chronologically one final time.

The final output directory is:

/content/phase2_final

All 10 files were processed.

The final chronological verification produced:

Ordering Violations: 0
Chronological: True

for every file.

This confirms that the final datasets are chronologically ordered according to Timestamp.

17. Final Dataset Statistics
File	Final Rows
Friday-02-03-2018	1,043,116
Friday-16-02-2018	900,988
Friday-23-02-2018	1,045,960
Thuesday-20-02-2018	7,948,746
Thursday-01-03-2018	331,027
Thursday-15-02-2018	1,046,154
Thursday-22-02-2018	1,045,288
Wednesday-14-02-2018	822,942
Wednesday-21-02-2018	1,031,018
Wednesday-28-02-2018	606,982
Total	15,822,221
18. Records Removed During Phase 2

The total reduction from the original dataset was:

Original rows:
16,233,002

Final rows:
15,822,221

Total rows removed:
410,781

The main removals were:

Reason	Records Removed
Malformed/header-like rows	59
Suspicious 1970 timestamp records	14
Exact duplicate records	410,707
Invalid negative numerical record	1
Total	410,781
19. Final Validation

The final Phase 2 dataset was validated for:

Validation	Result
Files processed	10/10
Final rows	15,822,221
Invalid timestamps	0
Ordering violations	0
Chronologically ordered files	10/10
Infinite values	0
Invalid IAT negatives	0
Empty labels	0
Required Timestamp field	Present
Required Label field	Present

The final chronological verification confirmed:

All files chronological: True

Therefore, the final dataset is ready to enter the feature-engineering and temporal-representation stages.

20. Decisions Deferred to Later Phases

Some operations were deliberately not finalized during Phase 2 because they depend on the modelling strategy.

These include:

Feature removal

Constant and highly correlated features will be evaluated during Feature Engineering.

Missing-value imputation

Remaining NaN values in flow-rate features will be handled using a leakage-safe ML preprocessing strategy.

-1 values

The meaning and treatment of Init Fwd Win Byts and Init Bwd Win Byts will be evaluated during feature engineering.

Feature scaling

Scaling will be determined by the requirements of the selected models.

SMOTE

SMOTE will not be applied automatically.

If class imbalance requires resampling, it will be applied only after the appropriate train/validation/test split and only to the training data.

Temporal window size

The final temporal window size will be determined during Temporal Representation rather than being fixed during preprocessing.

Forecast horizon

The forecasting horizon will be defined experimentally during the temporal modelling stage.

21. Phase 2 Final Output

The primary output of Phase 2 is:

/content/phase2_final

It contains the cleaned and chronologically ordered CIC-IDS2018 CSV files.

This directory should be treated as the final Phase 2 dataset for the current Colab workflow.

22. Phase 2 Completion Status
============================================================
PHASE 2 — DATA PREPROCESSING
============================================================

Dataset Metadata & Provenance       ✅
Timestamp Conversion                ✅
Malformed Row Handling              ✅
Suspicious Timestamp Handling      ✅
Chronological Ordering              ✅
Missing/Infinite Investigation      ✅
Infinite Value Handling             ✅
Duplicate Investigation             ✅
Duplicate Removal                   ✅
Invalid Numerical Investigation    ✅
Invalid Record Removal              ✅
Schema Investigation                ✅
Missing-Rate Investigation          ✅
Final Chronological Re-Sort         ✅
Final Validation                    ✅

STATUS: COMPLETE
============================================================
23. Transition to Phase 3

With Phase 2 completed, the project now moves from data cleaning to feature and temporal representation.

The next pipeline is:

/content/phase2_final
          ↓
Feature Engineering
          ↓
Feature Selection
          ↓
Feature Transformation
          ↓
Temporal Window Construction
          ↓
Network State Representation
          ↓
Forecasting Dataset

The next phase will therefore focus on creating a compact, modelling-ready temporal representation of the 15.8 million cleaned network-flow records.

24. Final Statement

Phase 2 successfully transformed the verified CIC-IDS2018 dataset into a cleaned, validated, and chronologically ordered dataset suitable for the subsequent stages of the NetVision-AI-SIH26153 system.

The final dataset contains 15,822,221 records across 10 traffic-capture files.

All final files have:

Valid timestamps
No infinite values
No identified invalid IAT negatives
Valid labels
Verified chronological ordering

The remaining modelling-dependent decisions have intentionally been deferred to Feature Engineering and Temporal Representation to prevent premature assumptions and potential temporal/data leakage.

Phase 2 — Data Preprocessing & Dataset Preparation is officially COMPLETE.