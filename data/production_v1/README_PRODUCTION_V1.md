# PhD Research Intelligence — Production Snapshot V1

Generated: 2026-09-17T20:44:02

## Production Components
- CANONICAL_REPRODUCIBILITY_MANIFEST_V1.txt (1670 bytes)
- canonical_explanations_v1.csv (964596 bytes)
- canonical_literature_v1.csv (620352 bytes)
- canonical_objective_features_v1.csv (51526 bytes)
- human_preference_calibration_v1_metrics.csv (221 bytes)
- human_preference_calibration_v1_oof.csv (13110 bytes)
- human_preference_calibrator_v1_params.csv (93 bytes)
- human_preference_layer_v1.csv (666909 bytes)
- scientific_priority_v1_1.csv (643264 bytes)

## Canonical Flow
Raw PubMed → Canonical Literature → Evidence → Semantic/Hybrid → Objective Features → Scientific Priority → Human Preference Layer → Explanation → Streamlit

## Validation State
250 unique papers; 110 informatively sampled human labels; 5-fold ordinal calibration retained as secondary probability layer only.

## Important Scientific Constraint
Human preference calibration does not replace the scientific evidence/ranking engine.

## Runtime
Run: streamlit run app.py