PHASE 6 — FORECASTING / WORLD MODEL
NetVision-AI-SIH26153 — AI Based Network Attack Forecasting from Network Traffic Data
1. Phase Overview
Phase

Phase 6 — Forecasting / World Model

Objective

The objective of Phase 6 was to develop a temporal forecasting and world-modeling layer capable of representing how network security states evolve over time and forecasting possible future network states.

The phase focused on:

Network state representation
State-transition modeling
Temporal transition probabilities
Multi-step future-state forecasting
Monte Carlo simulation
K-step attack forecasting
Forecast evaluation
Visualization
Finalization of the World Model artifacts

The World Model developed in this phase is a first-order probabilistic Markov state-transition model.

It is a mathematical/probabilistic temporal model rather than a separately trained machine-learning classifier.

2. Phase 6 Architecture

The Phase 6 workflow was:

Phase 4 Temporal Representation
            │
            ▼
    Network State Analysis
            │
            ▼
    State Representation
    BENIGN / ATTACK
            │
            ▼
   State Transition Model
            │
            ▼
 Transition Probability Matrix
            │
            ▼
 Multi-Step Probability Analysis
            │
            ├───────────────┐
            ▼               ▼
 Monte Carlo Simulation   K-Step Forecasting
            │               │
            └───────┬───────┘
                    ▼
        Forecast Evaluation
                    │
                    ▼
        World Model Results
3. World Model Definition

The World Model represents the network environment using two discrete security states:

State	Meaning
0	BENIGN
1	ATTACK

The model learns the temporal relationship between consecutive network states.

For example:

BENIGN → BENIGN
BENIGN → ATTACK
ATTACK → BENIGN
ATTACK → ATTACK

The frequency of these transitions is used to estimate transition probabilities.

The model can then use the current state to estimate the probability of future states.

4. Dataset Used

The World Model was developed using the finalized Phase 4 temporal representation of CIC-IDS2018.

Phase 4 produced:

Temporal window: 5 minutes
Forecasting horizon: 10 minutes
Final temporal rows: 1,008
Current state: current_attack_state
Future state: future_attack_state

The Phase 6 state sequence was constructed from these temporal windows.

5. Phase 6.1 — Network State Investigation

The first step was to investigate whether a simple or more detailed network-state representation was appropriate.

The analysis showed:

BENIGN = 725 windows
ATTACK = 283 windows

Distribution:

BENIGN = 71.92%
ATTACK = 28.08%

The current-state to future-state relationship was:

Current State	Future BENIGN	Future ATTACK
BENIGN	685	40
ATTACK	40	243

Corresponding probabilities:

Current State	Future BENIGN	Future ATTACK
BENIGN	94.48%	5.52%
ATTACK	14.13%	85.87%

Consecutive 5-minute state transitions were also investigated.

There were:

989 valid consecutive state transitions.

The observed transitions were:

Previous State	Current BENIGN	Current ATTACK
BENIGN	689	21
ATTACK	19	260

Based on this investigation, a two-state representation was selected.

Final decision
0 = BENIGN
1 = ATTACK

A richer state representation was not introduced because the available temporal state information did not provide sufficient justification for additional states.

6. Phase 6.2 — State Transition Model

A first-order Markov transition model was constructed using consecutive network states.

The transition matrix was calculated as:

$$ P_{ij} = \frac{\text{Number of transitions from state }i\text{ to state }j} {\text{Total transitions originating from state }i} $$

The resulting matrix was:

Current State	BENIGN	ATTACK
BENIGN	0.970423	0.029577
ATTACK	0.068100	0.931900

Interpretation:

BENIGN state

A currently BENIGN network has:

97.04% probability of remaining BENIGN
2.96% probability of transitioning to ATTACK
ATTACK state

A currently ATTACK network has:

6.81% probability of recovering to BENIGN
93.19% probability of remaining in ATTACK

This demonstrates strong temporal persistence in both network states, particularly the ATTACK state.

7. Phase 6.3 — Multi-Step Transition Probability Analysis

The transition matrix was propagated using matrix powers:

$$ P^k $$

where:

\(P\) = transition matrix
\(k\) = number of future steps

Since one temporal step represents 5 minutes:

$$ \text{Forecast Horizon} = k \times 5 \text{ minutes} $$

The resulting attack probabilities were:

Horizon	Starting BENIGN	Starting ATTACK
5 min	2.96%	93.19%
10 min	5.63%	87.05%
15 min	8.03%	81.50%
20 min	10.21%	76.50%
25 min	12.17%	71.98%
30 min	13.94%	67.91%
35 min	15.53%	64.23%
40 min	16.97%	60.92%
45 min	18.27%	57.93%
50 min	19.45%	55.22%
55 min	20.51%	52.79%
60 min	21.46%	50.59%
Interpretation

For an initially BENIGN network, the probability of reaching an ATTACK state gradually increases as the forecast horizon increases.

For an initially ATTACK network, the probability of remaining in an ATTACK state gradually decreases over time.

Both trajectories move toward the long-run stationary distribution.

8. Stationary State Distribution

The long-run stationary distribution of the transition model was estimated as:

State	Probability
BENIGN	69.72%
ATTACK	30.28%

This represents the long-run state distribution implied by the transition dynamics under the assumptions of the model.

It should not be interpreted as a guaranteed real-world attack rate.

9. Expected Attack Duration

The transition model estimated an expected ATTACK-state duration of approximately:

14.68 temporal steps

Since each step represents 5 minutes:

$$ 14.68 \times 5 \approx 73.42\text{ minutes} $$

Therefore, under the learned transition dynamics, an ATTACK state is expected to persist for approximately:

73.42 minutes

This is a model-derived temporal characteristic rather than a guaranteed duration for individual attacks.

10. Phase 6.4 — Future-State Monte Carlo Simulation

A Monte Carlo simulation was performed to validate the theoretical transition probabilities.

Simulation configuration
Number of simulations: 10,000
Random seed: 42
Forecast steps: 12
Temporal step: 5 minutes
Maximum horizon: 60 minutes

The simulated probabilities closely followed the theoretical probabilities.

The maximum absolute difference between simulated and theoretical probabilities was approximately:

Starting BENIGN: 0.00655
Starting ATTACK: 0.00947

This provided an implementation-level validation of the transition and simulation logic.

11. Probability of Future Attack Within 60 Minutes

The simulation estimated the probability of observing at least one future ATTACK state within 60 minutes.

Starting from BENIGN

30.72%

Starting from ATTACK

95.52%

This demonstrates the strong persistence of an existing ATTACK state in the learned temporal dynamics.

12. Expected Attack Windows During 60 Minutes

The simulation also estimated the expected number of ATTACK windows over the 60-minute period.

Starting from BENIGN

Expected attack windows:

1.6605 windows

Equivalent duration:

8.30 minutes

Starting from ATTACK

Expected attack windows:

8.2679 windows

Equivalent duration:

41.34 minutes

These values are expectations produced by the stochastic model and should not be interpreted as deterministic attack durations.

13. Phase 6.5 — K-Step Attack Forecasting

A reusable K-step forecasting procedure was implemented.

One step corresponds to:

5 minutes

Therefore:

1 step  = 5 minutes
2 steps = 10 minutes
3 steps = 15 minutes
...
12 steps = 60 minutes

The forecast probabilities were categorized for interpretation using:

Probability	Category
< 0.30	LOW
0.30 – < 0.60	MEDIUM
≥ 0.60	HIGH

These categories are interpretation categories only.

They are not the same as the Phase 5 ML ensemble classification threshold of 0.40.

14. K-Step Forecast Results
Starting from BENIGN

The attack probability increased from:

2.96% at 5 minutes

to:

21.46% at 60 minutes

All evaluated horizons remained in the LOW category.

Starting from ATTACK

The attack probability decreased from:

93.19% at 5 minutes

to:

50.59% at 60 minutes

The forecast remained HIGH until 40 minutes and moved into the MEDIUM category at 45 minutes.

This illustrates the gradual decay of attack-state probability as the forecast horizon increases.

15. Phase 6.6 — Forecast Evaluation

The primary forecasting horizon was:

10 minutes

An evaluation threshold of:

0.50

was used for classification-based evaluation.

This threshold is independent of the Phase 5 ML model's 0.40 threshold.

The primary 10-minute World Model results were:

Metric	Result
Accuracy	92.06%
Precision	85.87%
Recall	85.87%
F1-score	85.87%
ROC-AUC	90.17%
Brier Score	0.0716
16. Primary 10-Minute Confusion Matrix
	Predicted BENIGN	Predicted ATTACK
Actual BENIGN	685	40
Actual ATTACK	40	243

Therefore:

True Negatives: 685
False Positives: 40
False Negatives: 40
True Positives: 243

The model correctly classified 685 BENIGN windows and 243 ATTACK windows.

17. Conditional Forecast Behaviour

The conditional analysis showed:

Current State	Samples	Actual Attack Rate	Mean Forecast Attack Probability
BENIGN	725	5.52%	5.63%
ATTACK	283	85.87%	87.05%

The predicted probabilities were reasonably close to the corresponding observed future attack rates.

This provides evidence that the transition probabilities capture useful temporal persistence in the observed data.

18. Forecasting Across Horizons

The classification metrics remained the same across the evaluated horizons because the current two-state Markov model produces state-conditioned probabilities that remain on the same side of the 0.50 classification threshold over the evaluated 5–60 minute range.

However, the probability quality changes with the horizon.

The Brier scores were:

Horizon	Brier Score
5 min	0.0735
10 min	0.0716
15 min	0.0726
20 min	0.0756
30 min	0.0857
45 min	0.1052
60 min	0.1248

The increasing Brier score at longer horizons indicates increasing uncertainty in the probabilistic forecasts.

19. Important Methodological Interpretation

The Phase 6 World Model should not be considered a replacement for the Phase 5 machine-learning forecasting model.

The two layers have different purposes.

Phase 5 — Machine Learning
Traffic-derived features
        ↓
XGBoost + Random Forest-SMOTE
        ↓
Future attack prediction

The Phase 5 model learns relationships between traffic characteristics and the future attack state.

Phase 6 — World Model
Current network state
        ↓
State-transition probabilities
        ↓
Future-state evolution
        ↓
K-step forecast

The Phase 6 model represents temporal state dynamics and simulates how the network state may evolve.

Therefore, the World Model acts as a temporal dynamics layer rather than another conventional ML classifier.

20. Relationship Between Phase 5 and Phase 6

The overall research architecture can be represented as:

                 Network Traffic
                       │
                       ▼
              Phase 4 Temporal Data
                       │
             ┌─────────┴─────────┐
             │                   │
             ▼                   ▼
       Phase 5 ML            Phase 6 World
        Forecasting              Model
             │                   │
             │             State Dynamics
             │                   │
             └─────────┬─────────┘
                       ▼
             Future Attack Forecast

The integration of these components into the actual backend application is intentionally deferred to Phase 7 — System Integration.

21. Phase 6 Artifacts

The following artifacts were generated during Phase 6.

State Investigation
network_state_sequence.csv
current_to_future_transition_matrix.csv
consecutive_state_transition_matrix.csv
phase6_1_state_investigation_summary.csv
State Transition Model
state_transition_matrix.csv
state_transition_counts.csv
state_transition_model.json
Multi-Step Forecasting
multi_step_transition_probabilities.csv
stationary_state_distribution.csv
multi_step_forecasting_config.json
Monte Carlo Simulation
future_state_simulation_results.csv
future_state_simulation_config.json
example_future_state_trajectories.csv
K-Step Forecasting
k_step_attack_forecasts.csv
selected_attack_forecast_horizons.csv
k_step_forecasting_config.json
Forecast Evaluation
world_model_forecast_evaluation_by_horizon.csv
world_model_primary_10min_forecasts.csv
world_model_conditional_forecast_analysis.csv
world_model_primary_metrics.csv
Final Configuration
phase6_final_configuration.json
phase6_artifact_validation.csv
22. Visualization Artifacts

The following visualizations were generated:

multi_step_attack_probability.png
future_state_simulation_vs_theoretical.png
world_model_forecast_performance_by_horizon.png
world_model_10min_attack_probability.png

These visualizations support analysis of:

Multi-step attack probability
Theoretical vs simulated probabilities
Forecast performance across horizons
10-minute attack probability evolution
23. Final World Model Configuration

The finalized World Model configuration is:

Parameter	Value
Model	First-order Markov state-transition model
States	BENIGN / ATTACK
Temporal window	5 minutes
Primary horizon	10 minutes
Maximum evaluated horizon	60 minutes
Transition estimation	Consecutive temporal states
Multi-step method	Matrix powers
Simulation	Monte Carlo
Simulations	10,000
Random seed	42
24. Limitations

The current World Model has several important limitations.

1. Two-state representation

The model represents the network using only:

BENIGN
ATTACK

It does not currently distinguish individual attack types or detailed attack stages.

2. State-conditioned dynamics

The current Markov model primarily uses the current network state rather than the full set of traffic features.

Therefore, it does not capture every possible traffic-specific change in network behaviour.

3. Historical transition dynamics

The transition probabilities are estimated from CIC-IDS2018 temporal data.

They therefore represent the dynamics observed in this dataset and may not directly generalize to every real-world network.

4. Longer-horizon uncertainty

Forecast uncertainty increases as the forecast horizon becomes longer, which is reflected in the increasing Brier score.

5. Evaluation interpretation

The Phase 6 World Model evaluation is a validation of the temporal state-transition layer. It should not be directly compared with the held-out Phase 5 ML test performance as though they were identical experiments.

25. Phase 6 Final Outcome

Phase 6 successfully established a temporal/world-model forecasting layer for NetVision-AI-SIH26153.

The completed work includes:

Two-state network representation
First-order Markov transition model
Transition probability estimation
Multi-step future-state forecasting
Monte Carlo future-state simulation
K-step attack forecasting
10-minute primary forecast evaluation
Forecast probability analysis
Visualization
Final configuration and artifact validation

The primary 10-minute World Model evaluation achieved:

Accuracy: 92.06%

Precision: 85.87%

Recall: 85.87%

F1-score: 85.87%

ROC-AUC: 90.17%

Brier Score: 0.0716

Most importantly, the phase establishes a mathematical representation of network-state temporal dynamics, which can subsequently be integrated with the Phase 5 machine-learning forecasting layer.

26. Phase Status
======================================================================
PHASE 6 — FORECASTING / WORLD MODEL
======================================================================

6.1 Network State Investigation              ✓ COMPLETE
6.2 State Transition Model                  ✓ COMPLETE
6.3 Multi-Step Transition Probability       ✓ COMPLETE
6.4 Future-State Monte Carlo Simulation     ✓ COMPLETE
6.5 K-Step Attack Forecasting               ✓ COMPLETE
6.6 Forecast Evaluation & Visualization     ✓ COMPLETE
6.7 Finalization & Artifact Validation      ✓ COMPLETE

======================================================================
PHASE 6 STATUS: COMPLETE
======================================================================