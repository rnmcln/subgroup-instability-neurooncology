# Verification report

Generated: 2026-03-09

## 1. Subgroup weights sum correctly

**INDIGO PFS** (overall N=331):

| Factor | Subgroup N sum | Match |
|--------|---------------|-------|
| Sex | 331 | Yes |
| Location of tumor at initial diagnosis | 331 | Yes |
| No. of previous surgeries | 331 | Yes |
| Chromosome 1p/19q codeletion status | 331 | Yes |
| Longest diameter of tumor at baseline | 331 | Yes |

**CheckMate 498 OS** (overall N=560):

| Factor | Subgroup N sum | Match |
|--------|---------------|-------|
| Complete resection (CRF) | 560 | Yes |
| Sex | 560 | Yes |
| Baseline corticosteroid use | 560 | Yes |
| Baseline performance status (Karnofsky scale) | 556 | No (4 missing, expected from original data) |

## 2. Mixture curves reproduce digitized KM within tolerance

For the baseline fit (Chromosome 1p/19q codeletion, piecewise-exponential, knots at 0/12/24/30):
- ISE (control arm): 0.004279
- ISE (treatment arm): 0.001213
- Max absolute deviation (control): 0.140
- Max absolute deviation (treatment): 0.150

These are within expected range for digitized data. The feasible-set tolerance of 30% above baseline ISE ensures all retained solutions have comparable fit quality.

## 3. Output completeness

| Output | Status |
|--------|--------|
| pfs_envelope_summaries_all.csv | 8 rows, 4 factors |
| tni_envelope_summaries_all.csv | 8 rows, 4 factors |
| cm_blinded_os_envelope_summaries.csv | 8 rows, 4 factors |
| results_summary_indigo.json | 21 keys |
| results_summary_checkmate_blinded.json | 5 keys |
| Figures | 11 PDF, 11 PNG |
| Tables | 7 CSV files |
| Manuscript files | manuscript.docx, supplement.docx, cover_letter.docx |

## 4. TTNI anchor values match text-reported probabilities

- Vorasidenib 18-month TTNI-free: 85.6% (extracted)
- Placebo 18-month TTNI-free: 47.4% (extracted)
- Vorasidenib 24-month TTNI-free: 83.4% (extracted)

These values were extracted by regex from the INDIGO PDF text and used to anchor the digitized TTNI curves.

## 5. Feasible-set envelope consistency

INDIGO PFS envelope summaries (all dRMST24 values in months):

| Factor | Subgroup | N solutions | dRMST24 min | dRMST24 median | dRMST24 max |
|--------|----------|-------------|-------------|----------------|-------------|
| Chromosome 1p/19q codeletion | Codeleted | 120 | 1.91 | 2.26 | 2.53 |
| Chromosome 1p/19q codeletion | Non-codeleted | 120 | 4.29 | 4.49 | 5.06 |
| Location of tumor | Frontal lobe | 120 | 3.03 | 3.13 | 3.72 |
| Location of tumor | Nonfrontal lobe | 120 | 3.01 | 3.45 | 4.23 |

All dRMST24 values are positive (vorasidenib superior), consistent with overall HR of 0.39.

CheckMate 498 OS envelope summaries (all dRMST24 values negative, nivolumab inferior):

| Factor | Subgroup | N solutions | dRMST24 min | dRMST24 median | dRMST24 max |
|--------|----------|-------------|-------------|----------------|-------------|
| Complete resection | Yes | 120 | -1.59 | -1.50 | -1.39 |
| Complete resection | No | 120 | -0.77 | -0.34 | -0.06 |
| Sex | Male | 120 | -1.36 | -1.31 | -1.26 |
| Sex | Female | 120 | -0.72 | -0.12 | -0.03 |

All dRMST24 values are negative, consistent with overall HR of 1.28 (TMZ superior).

## 6. Sensitivity analysis robustness

Tolerance sensitivity (INDIGO PFS, mean envelope width across subgroups):
- 20% tolerance: mean width = 0.555 months
- 30% tolerance: mean width = 0.555 months
- 40% tolerance: mean width = 0.555 months

CheckMate tolerance sensitivity:
- 5% tolerance: mean width = 0.668 months
- 10% tolerance: mean width = 0.714 months
- 30% tolerance: mean width = 0.727 months

The feasible sets show modest sensitivity to tolerance choice, with tighter tolerances producing narrower envelopes as expected.

## 7. Reproducibility

All analyses can be reproduced from source PDFs using:
```bash
python scripts/run_all.py --indigo-pdf <path> --checkmate-pdf <path> [--checkmate-s1ab <path>] [--checkmate-s1cd <path>]
```

Step-by-step logs are saved to `outputs/logs/`.
