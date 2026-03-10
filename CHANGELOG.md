# Changelog

## v1.0.0 (2026-03-09)

Initial release of the identifiability-aware subgroup reconstruction package.

### Features
- Piecewise-exponential hazard model with mixture constraint for two-level factor partitions
- Feasible-set characterization over 5 knot configurations, 6 smoothness penalties, 4 regularization levels
- Color-based KM curve digitization from PDF/image sources
- TTNI anchoring to text-reported probabilities when digitization is unreliable
- Four sensitivity analyses: tolerance thresholds (5% to 40%), time-varying HR, alternative parametric families (Weibull, Royston-Parmar), HR uncertainty propagation via bootstrap
- Synthetic identifiability demonstration
- INDIGO trial: PFS and TTNI reconstruction for 4 factors each
- CheckMate 498: OS reconstruction for 4 factors (blinded and unblinded phases)
- Blinded vs unblinded comparison with tolerance sensitivity
- Publication-quality figures (PDF + 300 dpi PNG)
- Formatted result tables (CSV)
- Manuscript, supplement, and cover letter (docx)
- Single-command reproducibility via run_all.py
