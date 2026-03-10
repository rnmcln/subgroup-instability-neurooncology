# Data directory

## Structure

```
data/
  extracted/
    indigo/                      INDIGO trial extracted data
      km_digitised_pfs.csv       Digitized PFS KM curves (arm, month, survival)
      km_digitised_tni.csv       Digitized TTNI KM curves (raw)
      km_digitised_tni_anchored.csv  TTNI curves anchored to text-reported probabilities
      forestplot_pfs.csv         PFS subgroup HRs from Figure 3
      forestplot_tni.csv         TTNI subgroup HRs from Figure 3
      tni_anchors.csv            Text-reported TTNI probabilities used for anchoring
    checkmate_blinded/           CheckMate 498 blinded phase
      km_digitised_os.csv        Digitized OS KM curves
      km_digitised_pfs.csv       Digitized PFS KM curves
      forestplot_os.csv          OS subgroup HRs from Figure 3
      table2_rates.csv           OS/PFS rates from Table 2
    checkmate_unblinded/         CheckMate 498 unblinded phase (with supplement)
      km_pdl1_s1ab_left.csv      OS by PD-L1 >= 1% (Fig S1a)
      km_pdl1_s1ab_right.csv     OS by PD-L1 < 1% (Fig S1b)
      km_pdl1_s1cd_left.csv      OS by PD-L1 >= 5% (Fig S1c)
      km_pdl1_s1cd_right.csv     OS by PD-L1 < 5% (Fig S1d)
      table2_rates_supplement.csv
```

## Column definitions

### KM curve files (km_digitised_*.csv)
- `arm`: treatment arm name
- `month`: time in months from randomization
- `survival`: Kaplan-Meier survival probability (0 to 1)

### Forest plot files (forestplot_*.csv)
- `group`: factor name (e.g., "Chromosome 1p/19q codeletion status")
- `subgroup`: subgroup level (e.g., "Codeleted")
- `events` / `events_nivo` / `events_tmz`: number of events
- `n` / `n_nivo` / `n_tmz`: number randomized
- `hr`: hazard ratio (treatment vs control)
- `ci_low`, `ci_high`: 95% CI bounds

## Data provenance

INDIGO data extracted from NEJMoa2304194.pdf (Mellinghoff et al., NEJM 2023) via PDF rendering at 200 dpi, HSV color-based pixel masking, and regex text parsing.

CheckMate 498 data extracted from noac099.pdf (Reardon et al., Neuro-Oncology 2020) with manual transcription fallback for forest plot data where PDF text parsing produced incorrect group assignments.

Supplement images digitized from provided PNG files using orange/gray color channels.
