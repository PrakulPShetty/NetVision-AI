Phase 1 Report — CIC-IDS2018 Dataset Investigation

Project: SIH26153 — AI based Network Attack Forecasting from Network Traffic Data
Phase: Phase 1 — CIC-IDS2018 Dataset Investigation
Status: COMPLETE
Primary Dataset: CSE-CIC-IDS2018 / CIC-IDS2018
Private Repository: PrakulShetty/NetVision-AI-SIH26153

1. Purpose

Phase 1 was conducted to investigate and validate CIC-IDS2018 before using it for SIH26153.
The investigation covered dataset discovery, source verification, raw inspection, data quality, labels, traffic features, temporal structure, forecasting suitability, directional traffic, final suitability, and preservation of the verified original files.

No preprocessing or modelling was applied to the original dataset during this phase.

2. Dataset Discovery

The public Hugging Face dataset repository c01dsnap/CIC-IDS2018 was identified.

It contains 10 daily CICFlowMeter CSV files:

Friday-02-03-2018_TrafficForML_CICFlowMeter.csv

Friday-16-02-2018_TrafficForML_CICFlowMeter.csv

Friday-23-02-2018_TrafficForML_CICFlowMeter.csv

Thuesday-20-02-2018_TrafficForML_CICFlowMeter.csv

Thursday-01-03-2018_TrafficForML_CICFlowMeter.csv

Thursday-15-02-2018_TrafficForML_CICFlowMeter.csv

Thursday-22-02-2018_TrafficForML_CICFlowMeter.csv

Wednesday-14-02-2018_TrafficForML_CICFlowMeter.csv

Wednesday-21-02-2018_TrafficForML_CICFlowMeter.csv

Wednesday-28-02-2018_TrafficForML_CICFlowMeter.csv

Approximate total size: 6.9 GB.


3. Source Verification

The dataset source and redistribution information were verified using the available CIC-IDS2018 documentation and official dataset information.

The associated paper is:

Iman Sharafaldin, Arash Habibi Lashkari, Ali A. Ghorbani, “Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization”, ICISSP, 2018.

The dataset provides raw traffic/PCAP information, event information, and processed CICFlowMeter traffic-flow CSV files containing more than 80 traffic features.

The available dataset documentation permits redistribution, republication, and mirroring subject to the required citation and AWS dataset link.

Decision: Source verified.


4. Access from Google Colab

The dataset was successfully accessed from Google Colab using the Hugging Face Hub.

A representative file, Friday-16-02-2018_TrafficForML_CICFlowMeter.csv, was successfully accessed.

Google Colab was used as a temporary working and transfer environment.

The verified original files were then copied to the project's private Hugging Face repository:

PrakulShetty/NetVision-AI-SIH26153

Colab is not treated as permanent dataset storage.


5. Raw Dataset Inspection

The common CICFlowMeter representation contains 80 columns.

Important feature groups include:

Destination port

Protocol

Timestamp

Flow duration

Forward/backward packet counts

Forward/backward packet lengths

Flow byte and packet rates

Forward/backward IAT statistics

TCP flag counts

Packet-length statistics

Down/Up ratio

Forward/backward segment statistics

Subflow statistics

Initial TCP window information

Active/idle statistics

Label

The initial sample contained:

57 integer columns

21 floating-point columns

2 object columns: Timestamp and Label

No missing values in the initial five-row sample

A critical observation was that raw CSV row order is not chronological.

Therefore:

Timestamp is the authoritative basis for temporal ordering.

Chronological sorting will be performed during later preprocessing/temporal preparation.


6. Cross-File Structure

Nine files followed the common 80-column schema.

Thuesday-20-02-2018_TrafficForML_CICFlowMeter.csv contains 84 columns.

It has four additional endpoint fields:

Flow ID

Src IP

Src Port

Dst IP

The common traffic features are still present.

No columns were deleted during Phase 1.

The final treatment of endpoint-identifying fields will be decided during preprocessing based on leakage, generalization, and modelling considerations.


7. Data Quality Investigation

The dataset was investigated for missing values, duplicates, infinite values, data types, invalid timestamps, non-numeric values, negative values, and malformed/header-like records.

7.1 Missing Values
Missing values were found in Flow Byts/s in 7 files:

File

Missing values

Friday-02-03-2018

2,558

Friday-16-02-2018

0

Friday-23-02-2018

3,754

Thuesday-20-02-2018

36,767

Thursday-01-03-2018

1,834

Thursday-15-02-2018

4,921

Thursday-22-02-2018

3,569

Wednesday-14-02-2018

2,277

Wednesday-21-02-2018

0

Wednesday-28-02-2018

4,041

No imputation was performed in Phase 1.


7.2 Duplicate Rows
Duplicate records were observed.

Notable percentages:

Friday-16-02-2018: approximately 14.07%

Wednesday-14-02-2018: approximately 21.52%

Wednesday-21-02-2018: approximately 1.67%

Wednesday-28-02-2018: approximately 1.00%

Duplicates were not automatically removed because their effect on temporal forecasting must be considered during preprocessing.


7.3 Infinite Values
Infinite values occurred mainly in:

Flow Byts/s

Flow Pkts/s

These will be handled during Phase 2.


7.4 Malformed/Header-Like Rows
Three files contained malformed/header-like records:

Friday-16-02-2018: 1

Thursday-01-03-2018: 25

Wednesday-28-02-2018: 33

Total: 59 rows.

These records correspond to the label Label and will be removed during Phase 2.


7.5 Suspicious Timestamps
Suspicious timestamps around 1970 were observed in:

Thursday-22-02-2018

Wednesday-14-02-2018

These require timestamp validation during preprocessing.


7.6 Negative Values
A small number of negative values were found in features such as:

Flow Duration

Flow Pkts/s

Flow IAT Mean

Flow IAT Max

Flow IAT Min

Some initial TCP window features also contain -1.

These require domain-aware handling during preprocessing.


7.7 Data Types
The investigation did not identify genuine mixed Python data types across the files.


8. Attack Labels and Class Distribution
Total records investigated: 16,233,002

There were 16 unique label values, including the malformed Label value.

Label

Records

Approx. %

Benign

13,484,708

83.07%

DDOS attack-HOIC

686,012

4.23%

DDoS attacks-LOIC-HTTP

576,191

3.55%

DoS attacks-Hulk

461,912

2.85%

Bot

286,191

1.76%

FTP-BruteForce

193,360

1.19%

SSH-Bruteforce

187,589

1.16%

Infilteration

161,934

1.00%

DoS attacks-SlowHTTPTest

139,890

0.86%

DoS attacks-GoldenEye

41,508

0.26%

DoS attacks-Slowloris

10,990

0.07%

DDOS attack-LOIC-UDP

1,730

0.01%

Brute Force -Web

611

<0.01%

Brute Force -XSS

230

<0.01%

SQL Injection

87

<0.01%

Label

59

<0.01%

Excluding the 59 malformed rows:

Benign: 13,484,708

Attack: 2,748,235

Benign: approximately 83.07%

Attack: approximately 16.93%

Benign-to-attack ratio: approximately 4.91:1

Significant class imbalance exists.

Rare classes include SQL Injection, Brute Force-XSS, and Brute Force-Web.

SMOTE is not automatically selected. Later experiments may compare no resampling, class weights, SMOTE, Borderline-SMOTE, or another appropriate strategy. For temporal modelling, any resampling will be restricted to training data to avoid leakage.


9. Network-Traffic Feature Investigation

A 10,000-row sample was investigated.

The dataset contains rich information about:

Flow volume

Packet behaviour

Byte behaviour

Inter-arrival timing

TCP flags

Directional traffic

Active/idle behaviour

TCP window behaviour

9.1 Constant/Sparse Features

The following 12 features were constant at zero in the investigated sample:

Bwd PSH Flags

Fwd URG Flags

Bwd URG Flags

FIN Flag Cnt

URG Flag Cnt

CWE Flag Count

Fwd Byts/b Avg

Fwd Pkts/b Avg

Fwd Blk Rate Avg

Bwd Byts/b Avg

Bwd Pkts/b Avg

Bwd Blk Rate Avg

They were not deleted during Phase 1.

9.2 Feature Correlation

The sample contained 126 feature pairs with |r| >= 0.90.

Examples of perfect/high correlation included:

RST Flag Cnt ↔ ECE Flag Cnt

TotLen Bwd Pkts ↔ Subflow Bwd Byts

Fwd Pkt Len Mean ↔ Fwd Seg Size Avg

Tot Bwd Pkts ↔ Subflow Bwd Pkts

Tot Fwd Pkts ↔ Subflow Fwd Pkts

TotLen Fwd Pkts ↔ Subflow Fwd Byts

Bwd Pkt Len Mean ↔ Bwd Seg Size Avg

Flow Duration ↔ Fwd IAT Tot

Flow Pkts/s ↔ Fwd Pkts/s

Flow Pkts/s ↔ Bwd Pkts/s

This indicates substantial redundancy.

Feature selection will be investigated later using training data.


10. Temporal Information and Forecasting Suitability

Temporal analysis was essential because SIH26153 is a forecasting problem rather than only a static classification problem.

10.1 Timestamp

All files contain a Timestamp field.

Most daily files cover approximately 12 hours of traffic. Wednesday-21-02-2018 covers approximately 8 hours and 48 minutes in the investigated data.

10.2 Chronological Ordering

Raw row order is not chronological.

Therefore:

Timestamp, not CSV row order, must be used for temporal ordering.

10.3 Temporal Attack Activity

Five-minute aggregation showed attack activity across all 10 files.

Strong attack concentration was observed in several periods, including:

DoS activity on Friday-16-02-2018

DDOS-HOIC activity on Wednesday-21-02-2018

Infilteration activity on Thursday-01-03-2018

SSH-Bruteforce activity on Wednesday-14-02-2018

10.4 State Transitions

One-minute investigation on Friday-16-02-2018 showed observable transitions including:

Benign → DoS attacks-Hulk

DoS attacks-Hulk → Benign

Benign → DoS attacks-SlowHTTPTest

DoS attacks-SlowHTTPTest → Benign

This provides evidence of temporal state changes.

10.5 Forecasting Suitability

Final assessment: MODERATE–STRONG

The dataset provides timestamped records, attack labels, temporal attack activity, observable state transitions, and traffic features suitable for investigating future-state and attack forecasting.

However:

CIC-IDS2018 is not claimed to be a dedicated attack-forecasting benchmark.

Forecasting performance must be experimentally validated in later phases.


11. Directional Traffic Investigation

CIC-IDS2018 provides forward and backward traffic statistics.

Investigated directional features included:

Tot Fwd Pkts

Tot Bwd Pkts

TotLen Fwd Pkts

TotLen Bwd Pkts

Fwd Pkts/s

Bwd Pkts/s

Forward/backward header lengths

Forward/backward IAT statistics

Forward/backward initial TCP window values

Down/Up Ratio

11.1 Bidirectional Structure

In a 10,000-row sample:

Category

Count

Percentage

Both directions

9,947

99.47%

Forward only

53

0.53%

Backward only

0

0.00%

Neither

0

0.00%

The sample therefore shows strong bidirectional representation.

11.2 Directional Ratios

Forward/backward packet, byte, and rate ratios were investigated.

Raw ratios can become extremely large when the backward value is zero. Therefore, raw ratios should not automatically be used as final model features.

Later feature engineering may investigate directional shares, bounded ratios, log-ratios, or other robust representations.

11.3 Down/Up Ratio

In the investigated sample:

0: 81 records

1: 9,918 records

4: 1 record

Therefore, Down/Up Ratio alone should not be treated as the complete representation of directional behaviour.

11.4 Directional Decision

Directional traffic support: STRONG

CIC-IDS2018 provides sufficient forward/backward information for SIH26153.

The project will not impose a unidirectional-only traffic assumption.


12. Overall Dataset Suitability Decision

CIC-IDS2018 — SELECTED

CIC-IDS2018 is selected as the primary dataset for SIH26153 because it provides:

Verified source

Large-scale network traffic

Rich flow-level features

Multiple attack categories

Timestamp information

Observable temporal attack activity

Observable attack/benign state transitions

Forward/backward traffic information

Reproducible access

Strong alignment with SIH26153 requirements

Known limitations will be addressed in later phases:

Class imbalance

Missing values

Infinite values

Duplicate records

Malformed/header-like rows

Suspicious timestamps

Feature redundancy

Schema difference in one daily file

Potential endpoint-related leakage

Unknown optimal temporal window and forecasting horizon

These limitations do not reject the dataset. They define the preprocessing and modelling work required next.


13. Fixed Phase 1 Decisions

Dataset

CIC-IDS2018 is the primary dataset.

Temporal ordering

Timestamp is authoritative. Raw row order is not chronological.

Traffic direction

The system will use bidirectional flow information. It will not assume all traffic is unidirectional.

Forecasting

Forecasting suitability is currently moderate–strong, pending experimental validation.

Class imbalance

Imbalance exists. SMOTE is not automatically selected and will only be considered after appropriate temporal splitting.

Feature selection

Constant and highly correlated features will be evaluated during later preprocessing/feature engineering.

Data preservation

The original verified files are preserved separately from future processed datasets.


14. Private Repository Copy
All 10 original CIC-IDS2018 CSV files were successfully copied to:

PrakulShetty/NetVision-AI-SIH26153

The transfer path was:

Public Hugging Face Dataset
        ↓
Google Colab temporary cache
        ↓
Private Hugging Face Repository
PrakulShetty/NetVision-AI-SIH26153

Google Colab acted as the temporary transfer/work environment.

The private Hugging Face repository is the persistent project copy.

The original files were not preprocessed during this transfer.


15. Phase 1 Completion

Step

Status

1. Find dataset

✅ COMPLETE

2. Verify source

✅ COMPLETE

3. Access from Colab

✅ COMPLETE

4. Raw dataset inspection

✅ COMPLETE

5. Data quality investigation

✅ COMPLETE

6. Attack labels & class distribution

✅ COMPLETE

7. Network-traffic feature investigation

✅ COMPLETE

8. Temporal information & forecasting suitability

✅ COMPLETE

9. Directional traffic investigation

✅ COMPLETE

10. Dataset suitability decision

✅ COMPLETE

11. Copy verified dataset to private HF

✅ COMPLETE

PHASE 1 — COMPLETE

16. Transition to Phase 2

Phase 1 answered:

Is CIC-IDS2018 a suitable foundation for SIH26153, and what problems exist in the raw dataset?

Answer:

Yes. CIC-IDS2018 is selected as the primary dataset, with the identified data-quality, imbalance, redundancy, temporal, and schema issues carried forward into preprocessing.

Phase 2 will focus on building a complete preprocessing pipeline that cleans and prepares the data while maintaining temporal integrity and preventing data leakage.

Planned Phase 2 work:

Define preprocessing strategy

Load data efficiently

Remove malformed/header-like rows

Convert and validate timestamps

Handle suspicious timestamps

Handle missing values

Handle infinite values

Handle invalid numerical values

Handle duplicates

Resolve schema differences

Establish chronological ordering

Perform temporal train/validation/test splitting

Handle class imbalance appropriately

Save processed dataset

Validate the final preprocessing pipeline

Final Statement

CIC-IDS2018 has been investigated and selected as the primary dataset for SIH26153 — AI based Network Attack Forecasting from Network Traffic Data. It provides large-scale labelled network traffic, temporal information, observable attack-state transitions, and bidirectional flow features. The raw dataset contains several quality and modelling challenges, which will be addressed systematically in Phase 2 while preserving temporal integrity and preventing data leakage.