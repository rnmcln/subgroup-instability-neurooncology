#!/usr/bin/env node
/**
 * Generate manuscript.docx compliant with Neuro-Oncology Advances (NOA) guidelines.
 * REVISION 3: Further tightened per round-3 critique.
 * - Leaner title: dropped subtitle, signals instability directly
 * - 120-spec grid language tightened: "investigator-defined" not "plausible"
 * - TTNI demoted to secondary/corroborative throughout (including abstract)
 * - Discussion further restrained; no drift toward estimation
 * - Validation expanded to 50 replicates per scenario (500 total tests)
 * - Figures reinforce instability, not subgroup discovery
 */
const fs = require('fs');
const path = require('path');
const {
  Document, Paragraph, TextRun, Table, TableRow, TableCell,
  BorderStyle, AlignmentType, HeadingLevel, WidthType, ShadingType,
  Header, Footer, PageNumber, PageBreak, Packer,
} = require('/sessions/gifted-lucid-edison/.npm-global/lib/node_modules/docx');

// ── Helper functions ─────────────────────────────────────────────────

function heading(text, level = 1) {
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    children: [new TextRun({ text, bold: true, font: "Arial", size: level === 1 ? 24 : 22 })],
    spacing: { before: 240, after: 120, line: 480 },
  });
}

function body(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 24 })],
    spacing: { line: 480 },
    alignment: AlignmentType.JUSTIFIED,
  });
}

function bodyRuns(runs) {
  return new Paragraph({
    children: runs,
    spacing: { line: 480 },
    alignment: AlignmentType.JUSTIFIED,
  });
}

function superRef(num) {
  return new TextRun({ text: String(num), font: "Arial", size: 16, superScript: true });
}

function emptyLine() {
  return new Paragraph({ children: [new TextRun({ text: "", font: "Arial", size: 24 })], spacing: { line: 480 } });
}

function centered(text, bold = false, size = 24) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text, bold, font: "Arial", size })],
    spacing: { line: 480, after: 80 },
  });
}

function italicBody(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 24, italics: true })],
    spacing: { line: 480 },
  });
}

function noaTable(headers, rows, colWidths) {
  const totalWidth = colWidths.reduce((a, b) => a + b, 0);
  const hBorder = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
  const noBorder = { style: BorderStyle.NONE, size: 0 };

  function makeCell(text, isHeader, width) {
    return new TableCell({
      width: { size: width, type: WidthType.DXA },
      borders: { top: isHeader ? hBorder : noBorder, bottom: hBorder, left: noBorder, right: noBorder },
      margins: { top: 40, bottom: 40, left: 80, right: 80 },
      children: [new Paragraph({
        children: [new TextRun({ text: String(text), bold: isHeader, font: "Arial", size: 20 })],
        alignment: AlignmentType.CENTER,
        spacing: { line: 276 },
      })],
    });
  }

  const headerRow = new TableRow({ children: headers.map((h, i) => makeCell(h, true, colWidths[i])) });
  const dataRows = rows.map(row => new TableRow({ children: row.map((cell, i) => makeCell(cell, false, colWidths[i])) }));
  return new Table({ width: { size: totalWidth, type: WidthType.DXA }, columnWidths: colWidths, rows: [headerRow, ...dataRows] });
}

// ── Read CSV data ────────────────────────────────────────────────────

function readCSV(fp) {
  const lines = fs.readFileSync(fp, 'utf8').trim().split('\n');
  const hdr = lines[0].split(',');
  return lines.slice(1).map(line => {
    const vals = line.split(',');
    const obj = {};
    hdr.forEach((h, i) => { obj[h] = vals[i]; });
    return obj;
  });
}

const pfsData = readCSV(path.join(__dirname, '..', 'outputs', 'pfs_envelope_summaries_all.csv'));
const tniData = readCSV(path.join(__dirname, '..', 'outputs', 'tni_envelope_summaries_all.csv'));
const cmData = readCSV(path.join(__dirname, '..', 'outputs', 'cm_blinded_os_envelope_summaries.csv'));

// Read validation data
let valSummary = [];
try {
  valSummary = readCSV(path.join(__dirname, '..', 'outputs', 'validation_summary.csv'));
} catch(e) { console.log("Warning: no validation_summary.csv found"); }

function fmt(v) { return parseFloat(v).toFixed(2); }
function fmtRange(row) { return `${fmt(row.dRMST24_med)} [${fmt(row.dRMST24_min)}, ${fmt(row.dRMST24_max)}]`; }

// ── Build document sections ──────────────────────────────────────────
const children = [];

// ═══ TITLE PAGE ═══
children.push(centered("Instability of Subgroup-Specific Treatment Benefits", true, 28));
children.push(centered("Reconstructed From Aggregate Trial Data", true, 28));
children.push(emptyLine());
children.push(centered("Running title: Instability of reconstructed subgroup benefits", false, 20));
children.push(emptyLine());
children.push(centered("Aaron Lawson McLean, Julian Kahr, Anne Neumeister, Christian Senft", false, 22));
children.push(emptyLine());
children.push(centered("Department of Neurosurgery, Jena University Hospital,", false, 20));
children.push(centered("Friedrich Schiller University Jena, Jena, Germany", false, 20));
children.push(emptyLine());
children.push(centered("Corresponding author: Aaron Lawson McLean", false, 20));
children.push(centered("Department of Neurosurgery, Jena University Hospital,", false, 20));
children.push(centered("Friedrich Schiller University Jena, Am Klinikum 1, 07747 Jena, Germany", false, 20));
children.push(centered("Email: Aaron.lawsonmclean@med.uni-jena.de", false, 20));
children.push(emptyLine());
children.push(emptyLine());

children.push(new Paragraph({
  children: [new TextRun({ text: "Word count (text body): approximately 5,400", font: "Arial", size: 20, italics: true })],
  spacing: { line: 480 },
}));
children.push(new Paragraph({
  children: [new TextRun({ text: "Display items: 4 figures, 2 tables (6 total)", font: "Arial", size: 20, italics: true })],
  spacing: { line: 480 },
}));
children.push(new Paragraph({
  children: [new TextRun({ text: "References: 33", font: "Arial", size: 20, italics: true })],
  spacing: { line: 480 },
}));
children.push(new Paragraph({
  children: [new TextRun({ text: "Simulation replicates: 50 per scenario (500 total coverage tests)", font: "Arial", size: 20, italics: true })],
  spacing: { line: 480 },
}));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ═══ STRUCTURED ABSTRACT ═══
children.push(heading("Abstract", 1));
children.push(bodyRuns([
  new TextRun({ text: "Background. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "Clinicians routinely infer subgroup-specific absolute treatment benefits from aggregate trial publications, yet these quantities are generally not uniquely determined by published data. The sensitivity of such inferences to modelling assumptions is rarely quantified, creating a risk of false precision.", font: "Arial", size: 24 }),
]));
children.push(bodyRuns([
  new TextRun({ text: "Methods. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "We developed a sensitivity analysis framework that characterizes how subgroup-specific restricted mean survival time (RMST) differences vary across a structured grid of piecewise-exponential model specifications fitted to published aggregate Kaplan\u2013Meier curves and subgroup hazard ratios. We evaluated coverage and calibration using synthetic trials with known ground truth across five scenarios (50 replicates each; 500 total tests), then applied the framework to progression-free survival (PFS) in the INDIGO trial (vorasidenib in IDH-mutant glioma; N=331) and overall survival (OS) in CheckMate 498 (nivolumab in newly diagnosed glioblastoma; N=560). Time to next intervention (TTNI) in INDIGO was analysed as a secondary, corroborative endpoint.", font: "Arial", size: 24 }),
]));
children.push(bodyRuns([
  new TextRun({ text: "Results. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "Retained-solution envelopes contained the true subgroup effect in 14\u201326% of well-specified scenarios and 13% under model misspecification, confirming that the envelopes capture model-specification sensitivity rather than statistical uncertainty. For INDIGO PFS, subgroup \u0394RMST\u2082\u2084 varied by 0.45\u20132.06 months across model specifications depending on the subgroup factor. CheckMate 498 OS showed similar instability. A secondary analysis of INDIGO TTNI produced corroborative subgroup ordering but with additional model dependence due to analytical curve construction. Supplementing with additional published subgroup data narrowed envelopes by 5\u201317%.", font: "Arial", size: 24 }),
]));
children.push(bodyRuns([
  new TextRun({ text: "Conclusions. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "Subgroup-specific absolute treatment benefits reconstructed from aggregate trial data are substantially less determinate than point estimates imply. The instability revealed by systematic model-specification variation argues against treating such reconstructions as precise estimates and supports reporting sensitivity ranges when subgroup absolute benefits are used in clinical interpretation or evidence synthesis.", font: "Arial", size: 24 }),
]));
children.push(emptyLine());

// ═══ KEYWORDS ═══
children.push(bodyRuns([
  new TextRun({ text: "Keywords: ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "subgroup analysis; restricted mean survival time; model sensitivity; false precision; glioma; aggregate data", font: "Arial", size: 24 }),
]));
children.push(emptyLine());

// ═══ KEY POINTS ═══
children.push(heading("Key Points", 2));
children.push(body("1. Subgroup-specific absolute benefits derived from aggregate trial data are sensitive to modelling assumptions in ways that standard reporting does not acknowledge."));
children.push(body("2. Systematic variation of model specifications exposes this instability and reveals which subgroup contrasts are robust versus fragile."));
children.push(body("3. The approach is a tool for quantifying false precision, not for recovering true subgroup effects."));
children.push(emptyLine());

// ═══ IMPORTANCE OF THE STUDY ═══
children.push(heading("Importance of the Study", 2));
children.push(body("When clinicians, guideline panels, or health technology assessment bodies interpret subgroup treatment effects from published trials, they typically work from point estimates that convey more certainty than the data warrant. The fundamental issue is that subgroup-specific absolute benefits are not uniquely determined by aggregate Kaplan\u2013Meier curves and subgroup hazard ratios. We provide a practical sensitivity analysis that makes this instability visible. Applied to two neuro-oncology trials\u2014INDIGO and CheckMate 498\u2014the framework shows that varying model specifications across an investigator-defined grid yields meaningfully different subgroup benefit estimates. This is not a limitation of our method; it is a property of the data. The primary contribution is to equip readers and decision-makers with a tool for recognising when subgroup claims rest on implicit modelling choices rather than on information in the published evidence."));
children.push(emptyLine());

children.push(new Paragraph({ children: [new PageBreak()] }));

// ═══ INTRODUCTION ═══
children.push(heading("Introduction", 1));

children.push(bodyRuns([
  new TextRun({ text: "Subgroup analysis is central to treatment individualisation in neuro-oncology, where landmark trials of temozolomide,", font: "Arial", size: 24 }),
  superRef(26),
  new TextRun({ text: " PCV chemotherapy,", font: "Arial", size: 24 }),
  superRef(25),
  new TextRun({ text: " and targeted agents such as vorasidenib", font: "Arial", size: 24 }),
  superRef(5),
  new TextRun({ text: " have reported subgroup-stratified outcomes that inform EANO guideline recommendations.", font: "Arial", size: 24 }),
  superRef(24),
  new TextRun({ text: " Additional neuro-oncology trials such as CATNON", font: "Arial", size: 24 }),
  superRef(23),
  new TextRun({ text: " further illustrate the reliance on subgroup-level inference. Randomised trials routinely report aggregate Kaplan\u2013Meier survival curves together with subgroup-level hazard ratios, and clinicians commonly use these to infer absolute treatment benefits for specific patient groups. The interpretive hazards of subgroup analyses\u2014including risks of overinterpretation, multiplicity, and misleading inference\u2014are well recognised in the general trial-methodology literature", font: "Arial", size: 24 }),
  superRef(1),
  superRef(","),
  superRef(2),
  superRef(","),
  superRef(3),
  superRef(","),
  superRef(16),
  superRef(","),
  superRef(30),
  new TextRun({ text: " and have recently been reiterated specifically for neuro-oncology.", font: "Arial", size: 24 }),
  superRef(31),
  new TextRun({ text: " However, a distinct limitation is less often discussed: subgroup-specific ", font: "Arial", size: 24 }),
  new TextRun({ text: "absolute", italics: true, font: "Arial", size: 24 }),
  new TextRun({ text: " benefits\u2014expressed, for example, as differences in restricted mean survival time (RMST)", font: "Arial", size: 24 }),
  superRef(10),
  superRef(","),
  superRef(14),
  new TextRun({ text: "\u2014are generally not uniquely determined by the published data.", font: "Arial", size: 24 }),
  superRef(4),
]));

children.push(bodyRuns([
  new TextRun({ text: "This indeterminacy arises because multiple distinct configurations of subgroup-level survival curves can produce identical aggregate Kaplan\u2013Meier curves when mixed according to subgroup prevalences. Reported subgroup hazard ratios constrain the problem further\u2014linking treatment and control hazards within each subgroup\u2014but do not resolve it. The practical consequence is that point estimates of subgroup absolute benefit implicitly assume a unique solution exists when, in general, it does not. This creates a risk of false precision: clinical and policy decisions may be based on estimates whose apparent exactness obscures the degree to which they depend on arbitrary modelling choices.", font: "Arial", size: 24 }),
]));

children.push(bodyRuns([
  new TextRun({ text: "Existing approaches to subgroup analysis address estimation efficiency and multiplicity but not the underlying identifiability limitation: they improve the precision of an estimate without questioning whether the estimand is uniquely recoverable from the available data. A related body of work reconstructs individual patient-level survival from published Kaplan\u2013Meier curves", font: "Arial", size: 24 }),
  superRef(7),
  superRef(","),
  superRef(32),
  new TextRun({ text: " or elicits unreported subgroup-specific survival from aggregate trial reports,", font: "Arial", size: 24 }),
  superRef(33),
  new TextRun({ text: " but these methods inherit the same identifiability constraint and their performance is sensitive to structural assumptions, particularly in real-world trial settings.", font: "Arial", size: 24 }),
]));

children.push(bodyRuns([
  new TextRun({ text: "Against this background, our aim is not to propose a more accurate recovery of true subgroup effects from aggregate data\u2014our validation shows that no such recovery is reliable from aggregate data alone. Rather, we ask a different question: how unstable are subgroup-specific absolute benefit estimates when reconstructed from published aggregate survival data under alternative, reasonable model specifications? To our knowledge, this model-specification instability\u2014and its implications for false precision in neuro-oncology trial interpretation\u2014has not been systematically foregrounded as the primary object of analysis. We present a sensitivity analysis framework that characterises the resulting range of retained solutions across a structured grid of piecewise-exponential model specifications, and apply it to two neuro-oncology trials: INDIGO (vorasidenib in IDH-mutant glioma)", font: "Arial", size: 24 }),
  superRef(5),
  new TextRun({ text: " and CheckMate 498 (nivolumab plus radiotherapy in newly diagnosed MGMT-unmethylated glioblastoma).", font: "Arial", size: 24 }),
  superRef(6),
]));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ═══ METHODS ═══
children.push(heading("Methods", 1));

children.push(heading("Data Sources and Extraction", 2));
children.push(bodyRuns([
  new TextRun({ text: "INDIGO (NCT04164901) randomised 331 patients with residual or recurrent grade 2 IDH1- or IDH2-mutant glioma to vorasidenib (40 mg daily) or placebo.", font: "Arial", size: 24 }),
  superRef(5),
  new TextRun({ text: " We digitised progression-free survival (PFS; overall HR 0.39, 95% CI 0.27\u20130.56) and time to next intervention (TTNI; overall HR 0.26, 95% CI 0.15\u20130.45) Kaplan\u2013Meier curves from the primary publication. Subgroup hazard ratios with 95% confidence intervals and sample sizes were extracted from forest plot figures for four two-level factors: chromosome 1p/19q codeletion status (codeleted, n=172 vs non-codeleted, n=159), tumour location (frontal, n=222 vs non-frontal, n=109), longest tumour diameter (<2 cm, n=62 vs \u22652 cm, n=269), and number of previous surgeries (1, n=260 vs \u22652, n=71).", font: "Arial", size: 24 }),
]));

children.push(bodyRuns([
  new TextRun({ text: "CheckMate 498 (NCT02617589) randomised 560 patients with newly diagnosed glioblastoma with unmethylated MGMT promoter to nivolumab plus radiotherapy or temozolomide plus radiotherapy.", font: "Arial", size: 24 }),
  superRef(6),
  new TextRun({ text: " The control arm received the standard Stupp protocol.", font: "Arial", size: 24 }),
  superRef(26),
  new TextRun({ text: " We digitised overall survival (OS; HR 1.31, 95% CI 1.09\u20131.58) Kaplan\u2013Meier curves and extracted subgroup hazard ratios for four factors: complete surgical resection, sex, baseline corticosteroid use, and Karnofsky performance status.", font: "Arial", size: 24 }),
]));

children.push(heading("Digitisation Procedure", 2));
children.push(bodyRuns([
  new TextRun({ text: "Kaplan\u2013Meier curves were digitised from publication PDF figures rendered at 200 dots per inch. Arm-specific curves were separated using HSV colour-space thresholding with manually tuned hue ranges (details in Supplementary Methods S1). Pixel coordinates were converted to survival\u2013time pairs via affine transformation against axis tick marks, and monotone non-increasing constraints were enforced.", font: "Arial", size: 24 }),
  superRef(7),
  new TextRun({ text: " We emphasise that this extraction pipeline introduces multiple sources of imprecision: colour-threshold tuning, step-edge detection, and the absence of censoring-mark extraction. These are inherent to any KM digitisation approach and contribute to the overall model dependence of downstream estimates.", font: "Arial", size: 24 }),
]));

children.push(body("For INDIGO TTNI, the vorasidenib arm remained near S(t)=1.0 throughout follow-up, yielding sparse and imprecise digitised points. We therefore constructed the vorasidenib TTNI curve analytically using S_vorasidenib(t) = S_placebo(t)^{HR} under proportional hazards, then anchored to text-reported survival probabilities at 18 and 24 months. This construction adds an additional layer of model dependence to the TTNI endpoint: the vorasidenib TTNI curve is itself a modelling assumption, not a directly digitised quantity. We report TTNI results for completeness but interpret them with additional caution."));

children.push(body("Forest plot hazard ratios were parsed from PDF text layers using pdfplumber, with manual verification against source publications. For CheckMate 498, automatic parsing produced incorrect subgroup\u2013factor assignments due to complex multi-column layout; a manually curated lookup was used as fallback (Supplementary Methods S2)."));

children.push(heading("Reconstruction Model", 2));
children.push(bodyRuns([
  new TextRun({ text: "For each two-level subgroup factor, we modelled arm-specific survival using piecewise-exponential hazards,", font: "Arial", size: 24 }),
  superRef(13),
  superRef(","),
  superRef(17),
  new TextRun({ text: " a flexible parametric family that accommodates non-monotone hazard trajectories without imposing a specific distributional form. Within subgroup g and treatment arm k, the hazard function is h(t|g,k) = \u03BBg,k,j for t \u2208 [\u03C4j, \u03C4j+1). The model is fitted under two constraints. The mixture constraint requires that the prevalence-weighted combination of subgroup curves equals the digitised aggregate Kaplan\u2013Meier curve. The hazard ratio constraint requires h(t|g,treatment)/h(t|g,control) = HR_g, where HR_g is the reported subgroup-specific Cox hazard ratio.", font: "Arial", size: 24 }),
  superRef(15),
]));

children.push(body("The HR constraint warrants explicit discussion. Published subgroup HRs are typically estimated from Cox proportional hazards regression, which yields a single average HR over the observed time horizon. Our model maps this directly onto interval-specific hazard ratios, imposing proportional hazards within each subgroup. When the true treatment effect is non-proportional, this mapping is an approximation. We assess the consequences of this approximation in our validation study (Scenario D)."));

children.push(bodyRuns([
  new TextRun({ text: "Model parameters were estimated by minimising the mean integrated squared error (ISE) between model-implied and digitised aggregate survival curves across both arms, plus smoothness penalties on adjacent log-hazard differences and L2 regularisation.", font: "Arial", size: 24 }),
  superRef(18),
  new TextRun({ text: " Optimisation used L-BFGS-B with multiple random initialisations.", font: "Arial", size: 24 }),
]));

children.push(heading("Retained-Solution Envelope", 2));
children.push(body("To characterise model-specification sensitivity, we systematically varied three classes of modelling choices over an investigator-defined grid: 5 knot placement configurations (2 to 5 internal knots at regular or log-spaced intervals), 6 smoothness penalty levels (\u03B1 \u2208 {0, 0.01, 0.1, 1, 10, 100}), and 4 regularisation strengths (\u03BB \u2208 {0, 0.01, 0.1, 1}), yielding 120 candidate specifications per factor. This grid is not exhaustive and does not claim to represent all reasonable modelling choices; it is a structured sample designed to expose instability, not to bound it. Solutions were retained if their total ISE was within a tolerance threshold (default: 30% above the minimum ISE). For each retained solution, we computed subgroup-specific 24-month RMST and between-arm RMST differences (\u0394RMST\u2082\u2084). Results are reported as the envelope (minimum, median, maximum) across retained solutions."));

children.push(bodyRuns([
  new TextRun({ text: "We call this range the ", font: "Arial", size: 24 }),
  new TextRun({ text: "retained-solution envelope", italics: true, font: "Arial", size: 24 }),
  new TextRun({ text: ". The name is chosen to avoid connotations of rigorous bounds or coverage guarantees. The envelope represents the variation in output across the 120 model specifications that we explored; it does not characterise the full set of subgroup trajectories consistent with the published data, it is not a confidence interval, and expanding the specification grid could widen or shift it. Its value lies in making visible the instability of estimates that would otherwise be reported as single numbers.", font: "Arial", size: 24 }),
]));

children.push(heading("Information Sources and Their Roles", 2));
children.push(body("Three information sources contribute to the analysis, each with a distinct inferential role. The aggregate Kaplan\u2013Meier curves define the mixture target: any valid subgroup decomposition must reproduce these observed curves when combined according to subgroup prevalences. The subgroup prevalences (from reported sample sizes) determine the mixture weights. The subgroup hazard ratios add between-arm constraints. No single source renders the problem identified; together they constrain the solution space to a region that our model-specification search samples. The retained-solution envelope reflects the portion of this region explored by our parametric framework."));

children.push(heading("Simulation Validation", 2));
children.push(bodyRuns([
  new TextRun({ text: "To assess the calibration of retained-solution envelopes, we conducted a simulation study following standard principles of trial simulation.", font: "Arial", size: 24 }),
  superRef(27),
  superRef(","),
  superRef(28),
  new TextRun({ text: " Synthetic two-subgroup trials with known ground-truth survival curves were generated. For each scenario, individual patient data were generated from subgroup-specific exponential hazards, aggregated to produce Kaplan\u2013Meier curves and subgroup HR estimates (from observed event-rate ratios), and then processed through the reconstruction framework. Coverage was defined as the proportion of replicates in which the retained-solution envelope for \u0394RMST\u2082\u2084 contained the true value computed from the generating model.", font: "Arial", size: 24 }),
]));

children.push(body("Five scenarios were designed to span a range of conditions:"));

children.push(bodyRuns([
  new TextRun({ text: "Scenario A (well-separated): ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "N=300/arm, two subgroups with baseline hazards \u03BB=0.02 and 0.10, treatment HRs 0.4 and 0.7, prevalence 60:40. Represents favourable reconstruction conditions with strong subgroup separation.", font: "Arial", size: 24 }),
]));
children.push(bodyRuns([
  new TextRun({ text: "Scenario B (INDIGO-like): ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "N=165/arm, moderate baseline separation (\u03BB=0.03, 0.06), moderate HR differential (0.35, 0.50), balanced prevalence (52:48). Designed to approximate INDIGO trial characteristics.", font: "Arial", size: 24 }),
]));
children.push(bodyRuns([
  new TextRun({ text: "Scenario C (near-null): ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "N=300/arm, nearly identical subgroups (\u03BB=0.045, 0.055; identical HRs 0.50). Tests behaviour when subgroup separation approaches zero.", font: "Arial", size: 24 }),
]));
children.push(bodyRuns([
  new TextRun({ text: "Scenario D (non-proportional hazards): ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "N=300/arm, HRs cross over at 12 months (reversing to 1/HR), directly violating the proportional hazards assumption imposed by the reconstruction. Tests robustness to model misspecification.", font: "Arial", size: 24 }),
]));
children.push(bodyRuns([
  new TextRun({ text: "Scenario E (small sample): ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "N=80/arm with 20% censoring. Tests behaviour under high sampling variability.", font: "Arial", size: 24 }),
]));

children.push(body("Each scenario was run with 50 independent replicates (100 tests per scenario: two subgroups per replicate), for a total of 500 coverage evaluations. The default 30% ISE tolerance was used throughout. We additionally assessed tolerance sensitivity by varying the threshold from 10% to 50% on a subset of scenarios."));

children.push(heading("Sensitivity Analyses", 2));
children.push(bodyRuns([
  new TextRun({ text: "Four additional sensitivity analyses assessed robustness on the real trial data. Tolerance sensitivity examined how envelope width changed across ISE thresholds (20\u201340% for INDIGO; 5\u201330% for CheckMate 498). Time-varying HR sensitivity allowed piecewise-constant HR(t) with an anchoring penalty. Parametric family sensitivity compared piecewise-exponential results with Weibull and Royston\u2013Parmar restricted cubic spline alternatives.", font: "Arial", size: 24 }),
  superRef(12),
  new TextRun({ text: " HR uncertainty was propagated via log-normal bootstrap (200 replicates).", font: "Arial", size: 24 }),
]));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ═══ RESULTS ═══
children.push(heading("Results", 1));

// Validation first — central to the paper's identity
children.push(heading("Simulation Validation", 2));

let valText = "";
if (valSummary.length > 0) {
  const scA = valSummary.find(r => r.scenario === "A_well_separated");
  const scB = valSummary.find(r => r.scenario === "B_moderate_indigo_like");
  const scC = valSummary.find(r => r.scenario === "C_near_null");
  const scD = valSummary.find(r => r.scenario === "D_non_proportional_hazards");
  const scE = valSummary.find(r => r.scenario === "E_small_sample");
  if (scA && scB && scD) {
    valText += `Under well-separated conditions (Scenario A), retained-solution envelopes contained the true \u0394RMST\u2082\u2084 in ${Math.round(parseFloat(scA.coverage)*100)}% of tests (mean envelope width ${parseFloat(scA.mean_width).toFixed(2)} months, mean absolute bias ${parseFloat(scA.mean_abs_bias).toFixed(2)} months). Under INDIGO-like conditions (Scenario B), coverage was ${Math.round(parseFloat(scB.coverage)*100)}% with mean width ${parseFloat(scB.mean_width).toFixed(2)} months. `;
    if (scC) valText += `Near-null separation (Scenario C) yielded ${Math.round(parseFloat(scC.coverage)*100)}% coverage. `;
    valText += `Under deliberate model misspecification with non-proportional hazards (Scenario D), coverage fell to ${Math.round(parseFloat(scD.coverage)*100)}% with mean bias ${parseFloat(scD.mean_abs_bias).toFixed(2)} months\u2014the largest of any scenario. `;
    if (scE) valText += `Small-sample conditions (Scenario E) showed ${Math.round(parseFloat(scE.coverage)*100)}% coverage with the widest mean envelopes at ${parseFloat(scE.mean_width).toFixed(2)} months. `;
  }
}

valText += "These coverage values\u2014well below 95%\u2014confirm the central premise of this paper: retained-solution envelopes do not reliably contain the true subgroup effect, and should not be interpreted as confidence intervals. Their value is different: they quantify the degree to which subgroup benefit estimates are unstable across the investigator-defined specification grid. A wide envelope indicates that modelling assumptions, not the data, are driving the estimate. A narrow envelope in which all retained solutions agree on direction, while not constituting proof of a subgroup effect, suggests that the finding is at least robust to the specifications explored. Expanding the grid could alter these ranges.";

children.push(body(valText));

children.push(body("Tolerance sensitivity analysis showed that coverage was insensitive to the ISE threshold over the range 10\u201350%: envelope widths increased modestly with more permissive thresholds, but the qualitative pattern\u2014low coverage, informative directional consistency\u2014was stable."));

// INDIGO PFS
children.push(heading("INDIGO: Progression-Free Survival", 2));

const pfsCodel = pfsData.filter(r => r.factor === "Chromosome 1p/19q codeletion status");
const pfsLoc = pfsData.filter(r => r.factor === "Location of tumor at initial diagnosis");
const pfsDiam = pfsData.filter(r => r.factor === "Longest diameter of tumor at baseline");
const pfsSurg = pfsData.filter(r => r.factor === "No. of previous surgeries");

children.push(body(`Table 1 and Figure 2 present retained-solution envelopes for INDIGO PFS \u0394RMST\u2082\u2084 by subgroup factor. All \u0394RMST\u2082\u2084 values were positive across all factors and retained solutions, consistent with the overall HR of 0.39 favouring vorasidenib. However, the magnitude of estimated benefit varied across model specifications in ways that standard reporting would not reveal.`));

children.push(body(`For 1p/19q codeletion status, the median \u0394RMST\u2082\u2084 was ${fmt(pfsCodel[0].dRMST24_med)} months (envelope: ${fmt(pfsCodel[0].dRMST24_min)}\u2013${fmt(pfsCodel[0].dRMST24_max)}) for codeleted patients and ${fmt(pfsCodel[1].dRMST24_med)} months (${fmt(pfsCodel[1].dRMST24_min)}\u2013${fmt(pfsCodel[1].dRMST24_max)}) for non-codeleted patients. Tumour location showed wider envelopes: frontal ${fmt(pfsLoc[0].dRMST24_med)} months (${fmt(pfsLoc[0].dRMST24_min)}\u2013${fmt(pfsLoc[0].dRMST24_max)}) versus non-frontal ${fmt(pfsLoc[1].dRMST24_med)} months (${fmt(pfsLoc[1].dRMST24_min)}\u2013${fmt(pfsLoc[1].dRMST24_max)}).`));

children.push(body(`Tumour diameter showed the most notable instability: patients with tumours <2 cm (n=62) showed \u0394RMST\u2082\u2084 of ${fmt(pfsDiam[0].dRMST24_med)} months (${fmt(pfsDiam[0].dRMST24_min)}\u2013${fmt(pfsDiam[0].dRMST24_max)}), while patients with tumours \u22652 cm (n=269) showed ${fmt(pfsDiam[1].dRMST24_med)} months (${fmt(pfsDiam[1].dRMST24_min)}\u2013${fmt(pfsDiam[1].dRMST24_max)}). This contrast was consistent across all retained solutions, but whether it reflects genuine biological heterogeneity, prevalence-related constraints on the reconstruction (62 vs 269 patients), or a parametric artefact cannot be determined from aggregate data alone. This is precisely the kind of finding where false precision is a risk: a single point estimate would mask the modelling dependence.`));

children.push(body(`For prior surgeries, patients with \u22652 surgeries showed \u0394RMST\u2082\u2084 of ${fmtRange(pfsSurg[1])} months versus ${fmtRange(pfsSurg[0])} months for single-surgery patients.`));

children.push(heading("INDIGO: Time to Next Intervention (Secondary Endpoint)", 2));

const tniCodel = tniData.filter(r => r.factor === "Chromosome 1p/19q codeletion status");
const tniDiam = tniData.filter(r => r.factor === "Longest diameter of tumor at baseline");
const tniSurg = tniData.filter(r => r.factor === "No. of previous surgeries");

children.push(body(`TTNI envelopes showed broadly similar subgroup ordering to PFS but with larger absolute magnitudes, consistent with the stronger overall treatment effect. Codeleted patients showed \u0394RMST\u2082\u2084 of ${fmtRange(tniCodel[0])} months; patients with \u22652 prior surgeries showed ${fmtRange(tniSurg[1])} months. Tumour diameter <2 cm again showed the narrowest estimated benefit (${fmtRange(tniDiam[0])} months), though the same caveats regarding identifiability apply.`));

children.push(body("The parallel subgroup ordering between PFS and TTNI provides some internal consistency, though these endpoints share the same aggregate data constraints and are not independent. Moreover, the TTNI vorasidenib curve was analytically constructed rather than directly digitised, adding model dependence specific to this endpoint. We interpret the TTNI results as corroborative rather than as an independent confirmation."));

children.push(heading("CheckMate 498: Overall Survival", 2));

const cmRes = cmData.filter(r => r.factor === "Complete resection (CRF)");
const cmSex = cmData.filter(r => r.factor === "Sex");
const cmKPS = cmData.filter(r => r.factor.includes("Karnofsky"));

children.push(body(`All CheckMate 498 OS \u0394RMST\u2082\u2084 values were negative, consistent with the overall HR of 1.31 favouring temozolomide plus radiotherapy. Complete resection showed \u0394RMST\u2082\u2084 of ${fmtRange(cmRes[1])} months (with resection) versus ${fmtRange(cmRes[0])} months (without). The Karnofsky performance status factor yielded the widest envelope at ${fmt(cmKPS.length > 0 ? cmKPS[0].dRMST24_max - cmKPS[0].dRMST24_min : 0)} months, consistent with greater instability for smaller subgroups.`));

children.push(heading("Effect of Additional Published Data", 2));
children.push(body("Supplementing CheckMate 498 data with PD-L1 subgroup information from the trial supplement narrowed retained-solution envelopes by 5\u201317% (Figure 4). The largest reductions occurred for baseline corticosteroid use (17.2%) and sex (14.1\u201314.5%). This demonstrates that additional published subgroup information\u2014even from supplementary appendices\u2014measurably reduces model-specification sensitivity, supporting thorough data extraction in evidence synthesis."));

children.push(heading("Sensitivity Analyses", 2));
children.push(body("INDIGO PFS envelope widths were stable across ISE tolerance thresholds of 20\u201340%, with mean width of approximately 0.56 months. CheckMate 498 showed modest sensitivity, with mean width increasing from 0.67 to 0.73 months between 5% and 30% tolerance. Time-varying HR sensitivity and alternative parametric families (Weibull, Royston\u2013Parmar) yielded results within the primary piecewise-exponential envelopes. Bootstrap HR uncertainty expanded envelopes by approximately 15\u201325%."));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ═══ DISCUSSION ═══
children.push(heading("Discussion", 1));

children.push(body("The central finding of this paper is negative: subgroup-specific absolute treatment benefits reconstructed from aggregate trial data are substantially less determinate than standard reporting implies. Systematic variation of model specifications\u2014a routine sensitivity check that is almost never performed in published subgroup analyses\u2014reveals that the apparent precision of subgroup benefit estimates is largely an artefact of choosing a single model specification. This finding is relevant to any setting where subgroup absolute benefits are inferred from aggregate data, including clinical interpretation of trial results, guideline development, health technology assessment, and indirect evidence synthesis."));

// Primary use case
children.push(bodyRuns([
  new TextRun({ text: "The primary use case of this framework is to warn against false precision in clinical interpretation. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "When a clinician reads that vorasidenib PFS benefit differs between codeleted and non-codeleted IDH-mutant glioma patients, the natural assumption is that the published data determine this comparison with reasonable specificity. Our analysis shows that the comparison is sensitive to how the model is specified: varying choices across our investigator-defined grid yields meaningfully different estimates. This does not invalidate subgroup analysis\u2014it argues for honesty about the modelling dependence that is inherent to any reconstruction from aggregate data. A secondary application is in evidence synthesis and health technology assessment, where subgroup-specific survival estimates are often needed for cost-effectiveness modelling; retained-solution envelopes provide a structured way to propagate modelling uncertainty into downstream analyses.", font: "Arial", size: 24 }),
]));

children.push(body("Our simulation validation results require careful interpretation. Across 500 coverage tests (50 replicates \u00d7 5 scenarios \u00d7 2 subgroups), retained-solution envelopes contained the true subgroup effect in 14\u201326% of well-specified scenarios and 13% under non-proportional hazards. Low coverage is consistent with the manuscript\u2019s central claim: these envelopes are not inferential intervals and should not be interpreted as such. They are model-specification sensitivity ranges derived from a finite, investigator-defined grid. The tool does not claim to estimate the true subgroup effect. Its purpose is to make visible the degree to which reconstructed absolute benefit depends on modelling choices that are ordinarily implicit. A wide envelope tells the reader that this subgroup comparison is unstable across explored specifications. An envelope in which all retained solutions agree on direction tells the reader that the directional finding is robust to the specifications explored, even if the magnitude is not precisely determined. Expanding the specification grid could widen or shift these ranges."));

children.push(body("The hazard ratio constraint contributes to the model dependence. Published subgroup HRs are Cox proportional hazards estimates\u2014summary measures that average over the observed time horizon. Our model imposes these as constant hazard multipliers across all time intervals, which is exact under proportional hazards but approximate otherwise. Scenario D in our validation, which deliberately violates this assumption, shows the expected degradation: coverage falls to 13% with the largest mean bias of any scenario (2.34 months). Future work should explore time-varying HR constraints that better accommodate the Cox estimand."));

children.push(bodyRuns([
  new TextRun({ text: "The data extraction layer deserves candid discussion. The digitisation pipeline involves multiple fragile preprocessing steps: HSV colour-thresholding with manually tuned hue ranges, step-edge detection with running-median filtering, affine axis calibration, and monotonicity enforcement. For INDIGO TTNI, the vorasidenib arm was too flat to digitise reliably, and the analytical construction (S_placebo(t)^{HR} with textual anchoring) adds a layer of model dependence on top of the reconstruction model itself. These preprocessing steps are common to all KM digitisation approaches", font: "Arial", size: 24 }),
  superRef(7),
  new TextRun({ text: " but are worth making explicit because the reconstructed quantities depend on them. We partially characterise digitisation quality through comparison with text-reported survival probabilities (Supplementary Methods S1), but a full uncertainty propagation from the digitisation layer through reconstruction was not performed.", font: "Arial", size: 24 }),
]));

children.push(bodyRuns([
  new TextRun({ text: "Our framework addresses a gap between standard subgroup analysis methods and the clinical need for absolute benefit estimates. Interaction tests", font: "Arial", size: 24 }),
  superRef(8),
  new TextRun({ text: " and Bayesian hierarchical models", font: "Arial", size: 24 }),
  superRef(9),
  superRef(","),
  superRef(20),
  new TextRun({ text: " improve estimation but assume identifiability. RMST-based approaches", font: "Arial", size: 24 }),
  superRef(10),
  superRef(","),
  superRef(11),
  superRef(","),
  superRef(21),
  superRef(","),
  superRef(22),
  new TextRun({ text: " provide clinically interpretable endpoints but do not address the aggregate-to-subgroup recovery problem. IPD reconstruction methods such as that of Guyot et al.", font: "Arial", size: 24 }),
  superRef(7),
  new TextRun({ text: " and Liu et al.", font: "Arial", size: 24 }),
  superRef(32),
  new TextRun({ text: " recover individual-level data from aggregate curves but do not address subgroup-level identifiability. Our approach complements these methods by explicitly quantifying the instability that they leave implicit.", font: "Arial", size: 24 }),
]));

// Positioning against near-neighbour subgroup-recovery literature
children.push(bodyRuns([
  new TextRun({ text: "Our work should be read as complementary to, rather than in competition with, the literature on reconstructing survival information from published Kaplan\u2013Meier data. Existing methods have shown that individual-level or subgroup-level survival can sometimes be usefully approximated from aggregate reporting, particularly under strong structural assumptions.", font: "Arial", size: 24 }),
  superRef(33),
  new TextRun({ text: " Our emphasis is different: rather than asking whether unreported subgroup survival can be recovered, we ask how much the resulting subgroup-specific absolute benefit estimates move when the model specification moves. The answer\u2014that estimates are substantially less determinate than point values imply\u2014is relevant regardless of which reconstruction method is used, because the underlying identifiability limitation is a property of the data, not of any particular algorithm. We note that reconstruction approaches may nonetheless be practically useful for certain purposes\u2014such as populating cost-effectiveness models or generating hypotheses for future trials\u2014even when the absolute subgroup benefit they produce is sensitive to modelling choices; our results quantify rather than preclude that sensitivity.", font: "Arial", size: 24 }),
]));

children.push(body("We deliberately refrain from interpreting the subgroup-specific estimates as discoveries of biological heterogeneity. That non-frontal tumour location and larger tumour diameter are associated with greater estimated vorasidenib PFS benefit may reflect genuine treatment-effect heterogeneity, prevalence-related constraints on the reconstruction, or parametric artefacts. The appropriate conclusion is that these patterns are stable across explored model specifications\u2014not that they represent established subgroup effects."));

// Limitations
children.push(heading("Limitations", 2));
children.push(bodyRuns([
  new TextRun({ text: "Several limitations warrant emphasis. The framework depends on accurate aggregate data; digitisation error is partially characterised but not fully propagated. We analyse only two-level factor partitions, not joint strata. The 120-specification grid is an investigator-defined sample; it does not exhaustively characterise the space of admissible solutions, even within our parametric family, and different grid choices could yield wider or narrower envelopes. The Cox-HR-to-piecewise-hazard mapping is approximate. The framework does not address competing risks,", font: "Arial", size: 24 }),
  superRef(19),
  new TextRun({ text: " which may be relevant for endpoints such as PFS where non-cancer events could alter the estimand. The TTNI analytical construction introduces endpoint-specific model dependence that is difficult to separate from the reconstruction model dependence. Digitisation does not recover censoring patterns, numbers at risk, or individual event times. Finally, computational cost, while moderate (~10 minutes per trial), may limit integration into rapid decision-making.", font: "Arial", size: 24 }),
]));

children.push(bodyRuns([
  new TextRun({ text: "In summary, the instability of subgroup-specific absolute benefit estimates reconstructed from aggregate trial data is a property of the data, not a deficiency of any particular method. Making this instability visible\u2014through systematic model-specification sensitivity analysis\u2014serves clinical honesty and better-calibrated decision-making.", font: "Arial", size: 24 }),
  superRef(29),
  new TextRun({ text: " We advocate for reporting retained-solution envelopes alongside conventional subgroup analyses, with transparent acknowledgement of their model-dependent nature.", font: "Arial", size: 24 }),
]));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ═══ REQUIRED STATEMENTS ═══
children.push(heading("Ethics Statement", 2));
children.push(body("This study used only published aggregate data from previously reported clinical trials. No individual patient data were accessed and no ethical approval was required."));
children.push(emptyLine());

children.push(heading("Funding", 2));
children.push(body("This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors."));
children.push(emptyLine());

children.push(heading("Conflict of Interest Statement", 2));
children.push(body("The authors declare no conflicts of interest."));
children.push(emptyLine());

children.push(heading("Authorship Statement", 2));
children.push(body("ALM conceived the study, developed the methodological framework, performed the analyses, interpreted the data, and drafted the manuscript. JK and AN contributed to data interpretation and critical revision of the manuscript. CS contributed to interpretation of the findings and critically revised the manuscript. All authors approved the final manuscript."));
children.push(emptyLine());

children.push(heading("Data Availability Statement", 2));
children.push(body("All source code, extracted data, and simulation validation scripts required to reproduce the analyses are available at https://github.com/rnmcln/subgroup-instability-neurooncology. The framework was applied to published data from Mellinghoff et al. (N Engl J Med 2023) and Omuro et al. (Neuro-Oncology 2023)."));
children.push(emptyLine());

children.push(new Paragraph({ children: [new PageBreak()] }));

// ═══ REFERENCES ═══
// Cleaned: Guyot deduplicated, CheckMate 143 orphan removed
children.push(heading("References", 1));

const refs = [
  /*  1 */ "Rothwell PM. Subgroup analyses in randomised controlled trials: importance, indications, and interpretation. Lancet. 2005;365(9454):176-186.",
  /*  2 */ "Wang R, Lagakos SW, Ware JH, Hunter DJ, Drazen JM. Statistics in medicine\u2014reporting of subgroup analyses in clinical trials. N Engl J Med. 2007;357(21):2189-2194.",
  /*  3 */ "Assmann SF, Pocock SJ, Enos LE, Kasten LE. Subgroup analysis and other (mis)uses of baseline data in clinical trials. Lancet. 2000;355(9209):1064-1069.",
  /*  4 */ "Gail M, Simon R. Testing for qualitative interactions between treatment effects and patient subsets. Biometrics. 1985;41(2):361-373.",
  /*  5 */ "Mellinghoff IK, van den Bent MJ, Blumenthal DT, et al. Vorasidenib in IDH1- or IDH2-mutant low-grade glioma. N Engl J Med. 2023;389(7):589-601.",
  /*  6 */ "Omuro A, Brandes AA, Carpentier AF, et al. Radiotherapy combined with nivolumab or temozolomide for newly diagnosed glioblastoma with unmethylated MGMT promoter: an international randomized phase III trial. Neuro-Oncology. 2023;25(1):123-134.",
  /*  7 */ "Guyot P, Ades AE, Ouwens MJNM, Welton NJ. Enhanced secondary analysis of survival data: reconstructing the data from published Kaplan-Meier survival curves. BMC Med Res Methodol. 2012;12:9.",
  /*  8 */ "Lagakos SW. The challenge of subgroup analyses\u2014reporting without distorting. N Engl J Med. 2006;354(16):1667-1669.",
  /*  9 */ "Dixon DO, Simon R. Bayesian subset analysis. Biometrics. 1991;47(3):871-881.",
  /* 10 */ "Uno H, Claggett B, Tian L, et al. Moving beyond the hazard ratio in quantifying the between-group difference in survival analysis. J Clin Oncol. 2014;32(22):2380-2385.",
  /* 11 */ "Royston P, Parmar MKB. Restricted mean survival time: an alternative to the hazard ratio for the design and analysis of randomized trials with a time-to-event outcome. BMC Med Res Methodol. 2013;13:152.",
  /* 12 */ "Royston P, Parmar MKB. Flexible parametric proportional-hazards and proportional-odds models for censored survival data. Stat Med. 2002;21(15):2175-2197.",
  /* 13 */ "Klein JP, Moeschberger ML. Survival Analysis: Techniques for Censored and Truncated Data. 2nd ed. Springer; 2003.",
  /* 14 */ "Zhao L, Tian L, Uno H, et al. Utilizing the integrated difference of two survival functions to quantify the treatment contrast for designing, monitoring, and analyzing a comparative clinical study. Clin Trials. 2012;9(5):570-577.",
  /* 15 */ "Cox DR. Regression models and life-tables. J R Stat Soc Series B. 1972;34(2):187-220.",
  /* 16 */ "Brookes ST, Whitely E, Egger M, et al. Subgroup analyses in randomized trials: risks of subgroup-specific analyses. J Clin Epidemiol. 2004;57(3):229-236.",
  /* 17 */ "Collett D. Modelling Survival Data in Medical Research. 3rd ed. Chapman and Hall/CRC; 2015.",
  /* 18 */ "Harrell FE Jr. Regression Modeling Strategies. 2nd ed. Springer; 2015.",
  /* 19 */ "Fine JP, Gray RJ. A proportional hazards model for the subdistribution of a competing risk. J Am Stat Assoc. 1999;94(446):496-509.",
  /* 20 */ "Ibrahim JG, Chen MH, Sinha D. Bayesian Survival Analysis. Springer; 2001.",
  /* 21 */ "Wei Y, Royston P, Tierney JF, Parmar MKB. Meta-analysis of time-to-event outcomes from randomized trials using restricted mean survival time: application to individual participant data. Stat Med. 2015;34(21):2881-2898.",
  /* 22 */ "Liang F, Zhang S, Wang Q, Li W. Treatment effects measured by restricted mean survival time in trials with nonproportional hazards. J Natl Cancer Inst. 2020;112(12):1222-1228.",
  /* 23 */ "van den Bent MJ, Tesileanu CMS, Wick W, et al. Adjuvant and concurrent temozolomide for 1p/19q non-co-deleted anaplastic glioma (CATNON). Lancet Oncol. 2021;22(6):813-823.",
  /* 24 */ "Weller M, van den Bent M, Preusser M, et al. EANO guidelines on the diagnosis and treatment of diffuse gliomas of adulthood. Nat Rev Clin Oncol. 2021;18(3):170-186.",
  /* 25 */ "Buckner JC, Shaw EG, Pugh SL, et al. Radiation plus procarbazine, CCNU, and vincristine in low-grade glioma. N Engl J Med. 2016;374(14):1344-1355.",
  /* 26 */ "Stupp R, Mason WP, van den Bent MJ, et al. Radiotherapy plus concomitant and adjuvant temozolomide for glioblastoma. N Engl J Med. 2005;352(10):987-996.",
  /* 27 */ "Peto R, Pike MC, Armitage P, et al. Design and analysis of randomized clinical trials requiring prolonged observation of each patient, I. Br J Cancer. 1976;34(6):585-612.",
  /* 28 */ "Friedman LM, Furberg CD, DeMets DL. Fundamentals of Clinical Trials. 5th ed. Springer; 2015.",
  /* 29 */ "Louis TA, Zeger SL. Effective communication of standard errors and confidence intervals. Biostatistics. 2009;10(1):1-2.",
  /* 30 */ "Schandelmaier S, Guyatt G. Same old challenges in subgroup analysis. JAMA Netw Open. 2024;7(3):e243339.",
  /* 31 */ "Gerritsen JKW, Weng S, Ardon H, et al. Practical and statistical aspects of subgroup analyses in surgical neuro-oncology: a narrative review. Neuro-Oncology. 2025;27(5):1149-1164.",
  /* 32 */ "Liu N, Zhou Y, Lee JJ. IPDfromKM: reconstruct individual patient data from published Kaplan-Meier survival curves. BMC Med Res Methodol. 2021;21(1):111.",
  /* 33 */ "Alagoz O, Singh P, Dixon M, Kurt M. Eliciting unreported subgroup-specific survival from aggregate randomized controlled trial data. Med Decis Making. 2025;46(2):250-264.",
];

refs.forEach((ref, i) => {
  children.push(new Paragraph({
    children: [
      new TextRun({ text: `${i + 1}. `, bold: true, font: "Arial", size: 20 }),
      new TextRun({ text: ref, font: "Arial", size: 20 }),
    ],
    spacing: { line: 360, after: 40 },
    indent: { left: 360, hanging: 360 },
  }));
});

children.push(new Paragraph({ children: [new PageBreak()] }));

// ═══ TABLES ═══
children.push(heading("Tables", 1));

// Table 1: INDIGO PFS + TTNI combined
children.push(bodyRuns([
  new TextRun({ text: "Table 1. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "INDIGO trial: retained-solution envelopes for PFS and TTNI \u0394RMST", font: "Arial", size: 24 }),
  new TextRun({ text: "24", font: "Arial", size: 16, subScript: true }),
  new TextRun({ text: " (months) by subgroup factor.", font: "Arial", size: 24 }),
]));
children.push(emptyLine());

const t1headers = ["Factor", "Subgroup", "N", "PFS \u0394RMST\u2082\u2084 [min, max]", "TTNI \u0394RMST\u2082\u2084 [min, max]"];
const t1widths = [1800, 1500, 600, 2700, 2700];
const t1rows = [];

const factorN = {
  "Chromosome 1p/19q codeletion status": { "Codeleted": "172", "Non-codeleted": "159" },
  "Location of tumor at initial diagnosis": { "Frontal lobe": "222", "Nonfrontal lobe": "109" },
  "Longest diameter of tumor at baseline": { "<2 cm": "62", "\u22652 cm": "269" },
  "No. of previous surgeries": { "1": "260", "\u22652": "71" },
};

const shortFactor = {
  "Chromosome 1p/19q codeletion status": "1p/19q codeletion",
  "Location of tumor at initial diagnosis": "Tumour location",
  "Longest diameter of tumor at baseline": "Tumour diameter",
  "No. of previous surgeries": "Prior surgeries",
};

for (const [factor, subs] of Object.entries(factorN)) {
  for (const [sub, n] of Object.entries(subs)) {
    const pfs_row = pfsData.find(r => r.factor === factor && r.subgroup === sub);
    const tni_row = tniData.find(r => r.factor === factor && r.subgroup === sub);
    let tni_match = tni_row;
    if (!tni_match) {
      const tniSub = sub === "Frontal lobe" ? "Frontal" : sub === "Nonfrontal lobe" ? "Nonfrontal" : sub;
      tni_match = tniData.find(r => r.subgroup === tniSub || r.subgroup === sub);
    }
    const pfsStr = pfs_row ? `${fmt(pfs_row.dRMST24_med)} [${fmt(pfs_row.dRMST24_min)}, ${fmt(pfs_row.dRMST24_max)}]` : "\u2014";
    const tniStr = tni_match ? `${fmt(tni_match.dRMST24_med)} [${fmt(tni_match.dRMST24_min)}, ${fmt(tni_match.dRMST24_max)}]` : "\u2014";
    const displaySub = sub.replace("Nonfrontal", "Non-frontal");
    t1rows.push([shortFactor[factor], displaySub, n, pfsStr, tniStr]);
  }
}

children.push(noaTable(t1headers, t1rows, t1widths));
children.push(italicBody("Values are median [minimum, maximum] of retained-solution envelope across 120 investigator-defined model specifications. \u0394RMST\u2082\u2084, difference in restricted mean survival time at 24 months; PFS, progression-free survival (primary); TTNI, time to next intervention (secondary, corroborative). TTNI vorasidenib curves were analytically constructed (see Methods); TTNI results carry additional model dependence."));
children.push(emptyLine());

children.push(new Paragraph({ children: [new PageBreak()] }));

// Table 2: CheckMate 498 OS
children.push(bodyRuns([
  new TextRun({ text: "Table 2. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "CheckMate 498 trial: retained-solution envelopes for OS \u0394RMST", font: "Arial", size: 24 }),
  new TextRun({ text: "24", font: "Arial", size: 16, subScript: true }),
  new TextRun({ text: " (months) by subgroup factor.", font: "Arial", size: 24 }),
]));
children.push(emptyLine());

const t2headers = ["Factor", "Subgroup", "\u0394RMST\u2082\u2084 median", "\u0394RMST\u2082\u2084 [min, max]", "Width"];
const t2widths = [2000, 1400, 1600, 2600, 1000];
const t2rows = [];

const cmShort = {
  "Complete resection (CRF)": "Complete resection",
  "Sex": "Sex",
  "Baseline corticosteroid use": "Corticosteroid use",
  "Baseline performance status (Karnofsky scale)": "Karnofsky PS",
};

for (const row of cmData) {
  const width = (parseFloat(row.dRMST24_max) - parseFloat(row.dRMST24_min)).toFixed(2);
  t2rows.push([cmShort[row.factor] || row.factor, row.subgroup, fmt(row.dRMST24_med), `[${fmt(row.dRMST24_min)}, ${fmt(row.dRMST24_max)}]`, width]);
}

children.push(noaTable(t2headers, t2rows, t2widths));
children.push(italicBody("Negative values indicate temozolomide + RT superiority. Width is the range of the retained-solution envelope. \u0394RMST\u2082\u2084, difference in restricted mean survival time at 24 months; OS, overall survival; PS, performance status."));
children.push(emptyLine());

children.push(new Paragraph({ children: [new PageBreak()] }));

// ═══ FIGURE LEGENDS ═══
children.push(heading("Figure Legends", 1));

children.push(bodyRuns([
  new TextRun({ text: "Figure 1. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "Synthetic demonstration of non-identifiability. ", bold: true, italics: true, font: "Arial", size: 24 }),
  new TextRun({ text: "(A) Two distinct subgroup hazard configurations produce the same observed aggregate control-arm survival curve. (B) When a common treatment hazard ratio is applied, the configurations yield different treatment-arm aggregate curves, with the shaded region indicating the identifiability gap. (C) Resulting subgroup-specific \u0394RMST\u2082\u2084 differs between configurations, demonstrating that a single point estimate is not uniquely determined by aggregate data.", font: "Arial", size: 24 }),
]));
children.push(emptyLine());

children.push(bodyRuns([
  new TextRun({ text: "Figure 2. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "INDIGO PFS retained-solution envelopes. ", bold: true, italics: true, font: "Arial", size: 24 }),
  new TextRun({ text: "Horizontal bars show the range of \u0394RMST\u2082\u2084 values across retained model specifications for each subgroup, quantifying estimation instability. Red diamonds indicate the median. Panels show (A) 1p/19q codeletion status, (B) tumour location, (C) tumour diameter, and (D) prior surgeries. Bar width reflects model-specification sensitivity: wider bars indicate greater dependence on modelling choices. All values are positive across all specifications, but magnitudes are model-dependent.", font: "Arial", size: 24 }),
]));
children.push(emptyLine());

children.push(bodyRuns([
  new TextRun({ text: "Figure 3. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "INDIGO TTNI retained-solution envelopes (secondary, corroborative endpoint). ", bold: true, italics: true, font: "Arial", size: 24 }),
  new TextRun({ text: "Format as Figure 2. TTNI envelopes show larger absolute benefits, consistent with the stronger overall treatment effect. Vorasidenib TTNI curves were analytically constructed (see Methods), adding a layer of model dependence beyond the reconstruction model itself. These results are presented as corroborative evidence of subgroup ordering, not as independent estimates.", font: "Arial", size: 24 }),
]));
children.push(emptyLine());

children.push(bodyRuns([
  new TextRun({ text: "Figure 4. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "CheckMate 498: effect of supplementary data on envelope width. ", bold: true, italics: true, font: "Arial", size: 24 }),
  new TextRun({ text: "Grey bars show envelopes from main-paper data only; blue bars show envelopes after supplementing with PD-L1 subgroup information. Percentage annotations indicate envelope width reduction.", font: "Arial", size: 24 }),
]));

// ═══ CREATE DOCUMENT ═══
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Arial", size: 24 }, paragraph: { spacing: { line: 480 } } },
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", bold: true, size: 28 }, paragraph: { spacing: { before: 240, after: 120, line: 480 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", bold: true, size: 24 }, paragraph: { spacing: { before: 200, after: 100, line: 480 }, outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } },
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        children: [new TextRun({ text: "Instability of reconstructed subgroup benefits", font: "Arial", size: 18, italics: true })],
        alignment: AlignmentType.RIGHT,
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        children: [new TextRun({ text: "Page ", font: "Arial", size: 18 }), new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18 })],
        alignment: AlignmentType.CENTER,
      })] }),
    },
    children,
  }],
});

const outDir = path.join(__dirname, '..', 'manuscript');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
const outPath = path.join(outDir, 'manuscript.docx');

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log('Manuscript created:', outPath, `(${(buffer.length / 1024).toFixed(1)} KB)`);
}).catch(err => {
  console.error('Error creating manuscript:', err);
  process.exit(1);
});
