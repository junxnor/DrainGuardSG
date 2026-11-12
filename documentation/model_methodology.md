# Demonstration model methodology

## Model

`RandomForestRegressor` estimates the next day's station rainfall total. Five daily station totals are the features; the following day's total is the target. Training records use 6–10 November 2026 as input and 11 November as the target. Runtime estimates use 7–11 November to estimate 12 November.

The training script excludes missing/sentinel values and excludes all repeated station IDs to avoid treating OCR-repeated IDs as independent stations. It uses a station-group holdout for diagnostic MAE, RMSE and R², then fits the saved demonstration model on all eligible rows. The current fit uses 206 stations.

## Flood outlook

The displayed district outlook combines the highest model rainfall estimate in the selected area with the greatest current station water-level-to-danger-threshold ratio. Its score and labels are demonstration rules, not trained flood-event probabilities. Guidance follows the resulting outlook category.

## Scope

The available data cover a short historical window and a point-in-time water-level snapshot. No observed flood outcome labels or continuous water-level series are included, so this model does not learn whether flooding occurred and does not replace official warnings. Extend the history and add validated event labels before interpreting it as operational flood prediction.
