# Routing comparison rules

- `GroupMean` is the primary baseline selected from validation metrics.
- Neural Network is always included in the routing comparison; it passed the validation improvement rule: True.
- The decision is stored in `routing_model_selection.json` before routing.
- Select routes using training-derived weights or model predictions only.
- Use test actual travel times only to score routes; predicted times are never used as routing evaluation truth. `Oracle` is an explicitly labeled lower-bound reference.
