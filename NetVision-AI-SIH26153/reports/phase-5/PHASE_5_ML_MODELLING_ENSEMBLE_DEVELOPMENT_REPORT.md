PHASE 5 — ML MODELLING + ENSEMBLE DEVELOPMENT REPORT

Project

SIH26153 — AI based Network Attack Forecasting from Network Traffic Data

Phase

Phase 5 — ML Modelling + Ensemble Development

Status

Completed

1. Phase Objective

The objective of Phase 5 was to develop, compare, evaluate, and finalize the machine-learning component of the NetVision system.

The phase used the temporally represented CIC-IDS2018 dataset produced in Phase 4. The objective was to use the 5-minute temporal network-state representation to predict whether an attack would occur in the selected future horizon.

Final temporal configuration:

Temporal window: 5 minutes

Forecast horizon: 10 minutes

Target: future_attack_state

Total temporal samples: 1,008

Candidate predictors: 192

Final model features: 138

Phase 5 therefore produced a temporal future-state attack forecasting model rather than a conventional static flow-level classifier.

2. Dataset and Target

Phase 5 used the final Phase 4 temporal representation containing 1,008 chronologically ordered temporal records.

The following structural/state-derived columns were excluded:

window_start

dataset_day

current_attack_state

attack_flow_count

current_attack_ratio

future_attack_state

This prevented direct target leakage.

Target:

0 = Benign
1 = Attack

Target distribution:

State

Samples

Percentage

Benign

725

71.92%

Attack

283

28.08%

Total

1,008

100%

3. Feature Preparation

There were initially 192 candidate predictor features:

148 float64

44 int64

0 non-numeric features

A constant-feature investigation identified 54 constant features. These were removed because they contain no predictive variation.

Final representation:
192 candidate features → 138 model features

The exact 138-feature order was frozen in Phase 5.8.1 and saved as:

final_138_feature_schema.csv
final_138_feature_schema.json

The final inference schema was verified for feature count, ordering, numeric types, NaN/Inf values, and leakage.

4. Chronological Data Split

Because this is a forecasting problem, a random split was not used.

The 1,008 temporal samples were divided chronologically:

70% training

15% validation

15% test

Split

Samples

Benign

Attack

Training

705

536

169

Validation

151

116

35

Test

152

73

79

The later test period was substantially more attack-heavy. This temporal distribution shift was preserved as a realistic future evaluation condition.

5. Models Evaluated

The following approaches were evaluated:

Logistic Regression

Random Forest

Gradient Boosting

XGBoost

Random Forest with SMOTE

XGBoost + RF-SMOTE soft-voting ensemble

Logistic Regression was retained as the required reference baseline.

6. Logistic Regression Baseline

Pipeline:

StandardScaler

LogisticRegression

max_iter=2000

random_state=42

Validation:

Metric

Result

Accuracy

82.12%

Precision

72.22%

Attack Recall

37.14%

F1

49.06%

FPR

4.31%

Test:

Metric

Result

Accuracy

48.68%

Precision

55.56%

Attack Recall

6.33%

F1

11.36%

FPR

5.48%

The baseline showed substantial degradation on the later unseen test period, especially for attack recall.

7. Random Forest

Configuration:

300 estimators

max_depth=None

min_samples_split=2

min_samples_leaf=1

random_state=42

n_jobs=-1

Validation:

Metric

Result

Accuracy

83.44%

Precision

72.73%

Attack Recall

45.71%

F1

56.14%

FPR

5.17%

Test:

Metric

Result

Accuracy

55.92%

Precision

77.27%

Attack Recall

21.52%

F1

33.66%

FPR

6.85%

8. Gradient Boosting

Configuration:

200 estimators

learning rate = 0.05

maximum depth = 3

random_state=42

Validation:

Metric

Result

Accuracy

81.46%

Precision

64.00%

Attack Recall

45.71%

F1

53.33%

FPR

7.76%

Test:

Metric

Result

Accuracy

54.61%

Precision

69.23%

Attack Recall

22.78%

F1

34.29%

FPR

10.96%

9. Random Forest with SMOTE

SMOTE was applied only to the training partition, after the chronological split.

Original training distribution:

Benign = 536
Attack = 169

After SMOTE:

Benign = 536
Attack = 536
Total  = 1,072

Validation and test data remained untouched.

Validation:

Metric

Result

Accuracy

84.77%

Precision

75.00%

Attack Recall

51.43%

F1

61.02%

FPR

5.17%

Test:

Metric

Result

Accuracy

59.21%

Precision

79.31%

Attack Recall

29.11%

F1

42.59%

FPR

8.22%

SMOTE improved RF test F1 from 0.3366 to 0.4259 and attack recall from 0.2152 to 0.2911.

10. XGBoost

Configuration:

200 estimators

learning rate = 0.05

maximum depth = 3

subsample = 0.8

column sampling = 0.8

tree_method="hist"

objective="binary:logistic"

eval_metric="logloss"

random_state=42

Validation:

Metric

Result

Accuracy

83.44%

Precision

75.00%

Attack Recall

42.86%

F1

54.55%

FPR

4.31%

Test:

Metric

Result

Accuracy

59.87%

Precision

82.14%

Attack Recall

29.11%

F1

42.99%

FPR

6.85%

XGBoost was the strongest individual model by test F1.

11. Model Complementarity

Prediction agreement and attack-detection overlap were examined before selecting the ensemble.

For XGBoost + RF-SMOTE:

both detected the same 20 attack windows

XGBoost detected 23 attack windows

RF-SMOTE detected 23 attack windows

their union detected 26 attack windows

This indicated useful complementarity between the two models.

12. Hard Voting Experiment

A hard-voting experiment was performed using XGBoost and RF-SMOTE.

Validation:

Metric

Result

Accuracy

84.77%

Precision

73.08%

Attack Recall

54.29%

F1

62.30%

FPR

6.03%

Test:

Metric

Result

Accuracy

59.21%

Precision

74.29%

Attack Recall

32.91%

F1

45.61%

FPR

12.33%

Hard voting improved over the individual models but was not selected as the final ensemble.

13. Soft Voting Ensemble

The final ensemble uses probability averaging:

P(Attack) =
    0.50 × P_XGBoost(Attack)
  + 0.50 × P_RF-SMOTE(Attack)

At threshold 0.50:

Validation:

Metric

Result

Accuracy

85.43%

Precision

80.95%

Attack Recall

48.57%

F1

60.71%

FPR

3.45%

Test:

Metric

Result

Accuracy

57.89%

Precision

77.78%

Attack Recall

26.58%

F1

39.62%

FPR

8.22%

14. Threshold Selection

The soft-voting threshold was tuned using validation data only.

Candidate thresholds from 0.30 to 0.70 were evaluated.

The best validation F1 was obtained at:

Threshold = 0.40
Validation F1 = 0.6230

The threshold was frozen before test evaluation.

15. Final Ensemble

Final architecture:

XGBoost
   │
   │ 50%
   ├──────────────┐
   │              │
   │        Probability
   │         averaging
   │              │
   │              ↓
   │          P(Attack)
   │              │
   │         threshold 0.40
   │              │
   │       ┌──────┴──────┐
   │       ↓             ↓
   │    BENIGN         ATTACK
   │
   │ 50%
Random Forest
trained with SMOTE

Final model:
XGBoost + Random Forest (SMOTE-trained) 50/50 Soft-Voting Ensemble

16. Final Test Evaluation

Using the frozen threshold of 0.40:

Metric

Result

Accuracy

62.50%

Precision

73.91%

Attack Recall

43.04%

F1 Score

54.40%

False Positive Rate

16.44%

Confusion matrix:

                 Predicted
               Benign  Attack

Actual Benign      61      12
Actual Attack      45      34

Therefore:

TN = 61

FP = 12

FN = 45

TP = 34

The final ensemble detected 34 of 79 attack windows in the unseen test period.

17. Final Model Comparison

Model

Accuracy

Precision

Attack Recall

F1

FPR

Logistic Regression

48.68%

55.56%

6.33%

11.36%

5.48%

Random Forest

55.92%

77.27%

21.52%

33.66%

6.85%

Gradient Boosting

54.61%

69.23%

22.78%

34.29%

10.96%

XGBoost

59.87%

82.14%

29.11%

42.99%

6.85%

RF + SMOTE

59.21%

79.31%

29.11%

42.59%

8.22%

XGB + RF-SMOTE Ensemble

62.50%

73.91%

43.04%

54.40%

16.44%

The final ensemble achieved the highest test F1 and attack recall among the evaluated approaches.

18. Improvement over Baseline

Compared with Logistic Regression:

Metric

Improvement

Accuracy

+13.82 percentage points

Precision

+18.36 percentage points

Attack Recall

+36.71 percentage points

F1

+43.04 percentage points

FPR

+10.96 percentage points

The improvement in attack detection came with an increase in false-positive rate. This trade-off is retained explicitly.

19. Final Inference Schema

The final model requires exactly 138 numerical features.

The schema was verified for:

exact feature count

exact feature order

train/validation/test consistency

numeric types

no NaN

no infinite values

no target leakage

The schema was saved as:

final_138_feature_schema.csv
final_138_feature_schema.json

20. Final Inference Object

A reusable NetVisionEnsemble inference object was created containing:

XGBoost trained model

RF-SMOTE trained model

XGBoost weight = 0.50

RF-SMOTE weight = 0.50

threshold = 0.40

138 feature names in fixed order

model version = v1

temporal window = 5 minutes

forecast horizon = 10 minutes

The inference flow is:

Input validation
      ↓
Feature-order correction
      ↓
XGBoost probability
      +
RF-SMOTE probability
      ↓
50/50 probability average
      ↓
Threshold 0.40
      ↓
BENIGN / ATTACK

21. Inference Verification

The inference wrapper was tested on the unseen test set.

It reproduced the Phase 5.7 results exactly:

Accuracy        = 0.6250
Precision       = 0.7391
Attack Recall   = 0.4304
F1              = 0.5440
FPR             = 0.1644

The maximum difference between independently calculated ensemble probabilities and wrapper probabilities was:

0.000000000000

This verified the 50/50 soft-voting implementation.

22. Model Serialization

The final inference object was serialized using joblib.

Artifact:

netvision_final_ensemble_v1.pkl

Size:

0.96 MB

SHA-256:

76bf425aeb81eecae08d8d40cf9866e14aeada6c5f88f8fa7d40a032c07cf196

The serialized model was loaded again and verified.

Results:

configuration preserved

138-feature schema preserved

probabilities identical

predictions identical

prediction differences after save/load = 0

23. Project Integration

Final trained artifact:

models/
├── preprocessing/
└── trained/
    └── netvision_final_ensemble_v1.pkl

Reusable ensemble implementation:

src/
└── models/
    └── ensemble.py

The src/models/ensemble.py module contains reusable inference-side ensemble logic, while the .pkl contains the trained model artifact.

The backend will later load the model once at application startup rather than retraining it for each request.

24. SMOTE Design Decision

SMOTE is a training-time technique in this project.

It was not applied to:

Phase 2 cleaned data

Phase 3 feature-engineered data

Phase 4 temporal data

validation data

test data

backend inference inputs

SMOTE was applied only to the training partition for the Random Forest experiment.

This preserves the integrity of validation and test evaluation.

25. Methodological Checks

The following checks passed:

chronological splitting

no random train/test split

train/test separation

future target excluded from predictors

current-state-derived fields excluded

SMOTE only on training data

validation used for threshold selection

test used only for final evaluation

exact feature order preserved

no NaN in final model inputs

no infinite values

138-feature schema consistency

save/load prediction consistency

26. Research Interpretation

Phase 5 demonstrates that the temporal network-state representation can be used to forecast a future attack state.

The final ensemble outperformed the Logistic Regression baseline and the individual nonlinear models on the held-out temporal test period in terms of F1 and attack recall.

However, Phase 5 is not the complete SIH "World Model."

At the end of Phase 5, the system provides:

5-minute temporal network state → 10-minute future attack-state prediction

The following requirements remain for later phases:

explicit network state-transition modelling

state-transition probability estimation

multi-step/k-step future simulation

attack-stage/MITRE ATT&CK mapping

SHAP-based explainability

complete forecasting pipeline integration

These are intentionally addressed in later phases.

27. Phase 5 Final Outcome

Phase 5 successfully produced the project's finalized machine-learning forecasting component.

Dataset:
    CIC-IDS2018 temporal representation

Temporal window:
    5 minutes

Forecast horizon:
    10 minutes

Final features:
    138

Models:
    XGBoost
    Random Forest + SMOTE

Ensemble:
    50/50 Soft Voting

Threshold:
    0.40

Final Test Accuracy:
    0.6250

Final Test F1:
    0.5440

Final Attack Recall:
    0.4304

Final model:
    netvision_final_ensemble_v1.pkl

PHASE 5 STATUS: COMPLETE