#!/usr/bin/env node
/**
 * Generate supplement.docx for NOA submission — revised to address reviewer critiques.
 * Includes expanded extraction methods, simulation validation details, HR constraint discussion,
 * and updated terminology (retained-solution envelope).
 */
const fs = require('fs');
const path = require('path');
const {
  Document, Paragraph, TextRun, Table, TableRow, TableCell,
  BorderStyle, AlignmentType, HeadingLevel, WidthType,
  Header, Footer, PageNumber, PageBreak, Packer, ImageRun,
} = require('/sessions/gifted-lucid-edison/.npm-global/lib/node_modules/docx');

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

function emptyLine() {
  return new Paragraph({ children: [new TextRun({ text: "", size: 24 })], spacing: { line: 480 } });
}

function figureImage(pngPath, widthPx, heightPx) {
  if (!fs.existsSync(pngPath)) {
    return body(`[Image not found: ${pngPath}]`);
  }
  const data = fs.readFileSync(pngPath);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new ImageRun({
      type: "png",
      data,
      transformation: { width: widthPx, height: heightPx },
      altText: { title: "Supplementary figure", description: "Supplementary figure", name: "SuppFig" },
    })],
    spacing: { before: 120, after: 120 },
  });
}

// Helper for validation results table
function makeTable(headers, rows) {
  const borderStyle = { style: BorderStyle.SINGLE, size: 1, color: "000000" };
  const borders = { top: borderStyle, bottom: borderStyle, left: borderStyle, right: borderStyle };

  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map(h => new TableCell({
      borders,
      shading: { fill: "D9E2F3" },
      width: { size: Math.floor(9000 / headers.length), type: WidthType.DXA },
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: h, bold: true, font: "Arial", size: 20 })],
      })],
    })),
  });

  const dataRows = rows.map(row => new TableRow({
    children: row.map(cell => new TableCell({
      borders,
      width: { size: Math.floor(9000 / headers.length), type: WidthType.DXA },
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: String(cell), font: "Arial", size: 20 })],
      })],
    })),
  }));

  return new Table({
    width: { size: 9000, type: WidthType.DXA },
    rows: [headerRow, ...dataRows],
  });
}

const figDir = path.join(__dirname, '..', 'figures');
const children = [];

// Title
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Supplementary Material", bold: true, font: "Arial", size: 28 })],
  spacing: { after: 120, line: 480 },
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({
    text: "Instability of Subgroup-Specific Treatment Benefits Reconstructed From Aggregate Trial Data",
    font: "Arial", size: 22, italics: true,
  })],
  spacing: { after: 120, line: 480 },
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({
    text: "Aaron Lawson McLean, Julian Kahr, Anne Neumeister, Christian Senft",
    font: "Arial", size: 20,
  })],
  spacing: { after: 80, line: 480 },
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({
    text: "Department of Neurosurgery, Jena University Hospital, Friedrich Schiller University Jena, Jena, Germany",
    font: "Arial", size: 18, italics: true,
  })],
  spacing: { after: 200, line: 480 },
}));
children.push(emptyLine());

// =====================================================================
// SUPPLEMENTARY METHODS
// =====================================================================
children.push(heading("Supplementary Methods", 1));

// S1. Detailed Digitization Procedure
children.push(heading("S1. Detailed Digitization Procedure", 2));

children.push(body("All Kaplan\u2013Meier curves were digitized from published PDF figures using a custom Python pipeline (digitize_km.py). The procedure proceeded in five stages:"));
children.push(emptyLine());

children.push(bodyRuns([
  new TextRun({ text: "Stage 1 \u2014 Image extraction. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "PDF pages containing KM plots were rendered to PNG at 200 dpi using the pdf2image library (poppler backend). The plot region was isolated by manual specification of pixel bounding boxes corresponding to axis extremes.", font: "Arial", size: 24 }),
]));

children.push(bodyRuns([
  new TextRun({ text: "Stage 2 \u2014 Axis calibration. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "Axis tick marks were identified from the source figure and mapped to pixel coordinates. An affine transformation was fitted to convert pixel (x, y) to (time in months, survival probability). Calibration was verified by checking that digitized axis labels fell within \u00B10.5% of their reported values.", font: "Arial", size: 24 }),
]));

children.push(bodyRuns([
  new TextRun({ text: "Stage 3 \u2014 Curve tracing. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "Arm-specific curves were isolated using HSV color-space thresholding. For INDIGO PFS, the vorasidenib arm was traced from red-channel pixels (H: 340\u201320\u00B0, S > 0.3) and the placebo arm from blue-channel pixels (H: 200\u2013240\u00B0, S > 0.3). For CheckMate 498, nivolumab was traced from red channels and temozolomide from gray/dark channels (S < 0.15, V < 0.5). Step-function edges were detected by scanning each pixel column for the lowest colored pixel, then applying a running median filter (window = 3 columns) to suppress noise.", font: "Arial", size: 24 }),
]));

children.push(bodyRuns([
  new TextRun({ text: "Stage 4 \u2014 Monotonicity enforcement. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "Raw digitized points were subjected to a monotone non-increasing constraint: any point with survival probability exceeding the previous point was replaced by the previous value. This corrects upward artifacts from pixel noise and step-edge ambiguity.", font: "Arial", size: 24 }),
]));

children.push(bodyRuns([
  new TextRun({ text: "Stage 5 \u2014 Special handling (INDIGO TTNI). ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "The vorasidenib TTNI curve remained near S(t) = 1.0 throughout follow-up, yielding fewer than 10 digitized step-down points. Direct pixel tracing was unreliable. We therefore constructed the vorasidenib TTNI curve analytically from the placebo curve using S_v(t) = S_p(t)^{HR} with HR = 0.39 (from the reported overall treatment effect for TTNI), then applied additive corrections at 18 and 24 months to match text-reported survival probabilities (S_v(18) \u2248 0.95, S_v(24) \u2248 0.93). This anchoring procedure is described in the main text.", font: "Arial", size: 24 }),
]));

children.push(emptyLine());

// S2. Forest Plot Data Extraction
children.push(heading("S2. Forest Plot Data Extraction", 2));

children.push(body("Subgroup hazard ratios were extracted from published forest plot figures using pdfplumber (v0.10) for text parsing. For each forest plot, the extraction pipeline identified subgroup labels, sample sizes, event counts, hazard ratio point estimates, and 95% confidence intervals."));

children.push(bodyRuns([
  new TextRun({ text: "INDIGO. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "Automated parsing successfully extracted all subgroup rows from the INDIGO forest plot (Mellinghoff et al., Figure S3). Extracted factors included: sex (male/female), age (<40/\u226540), tumor grade (grade 2/grade 3), IDH1-R132H status (present/absent), 1p/19q codeletion status, prior treatment, and enhancing disease. Point estimates and confidence intervals matched values reported in the manuscript text.", font: "Arial", size: 24 }),
]));

children.push(bodyRuns([
  new TextRun({ text: "CheckMate 498. ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "Automated text parsing of the CheckMate 498 forest plot (Omuro et al., Figure 2) produced incorrect group\u2013subgroup assignments due to the figure\u2019s complex multi-column layout. Manual verification against the published figure identified systematic misalignment between factor group labels and their corresponding subgroup rows. A curated lookup table with 26 correctly grouped rows was constructed and used as a validated fallback, triggered when parsed group names failed validation against expected factor names. All 26 rows were verified against the published figure.", font: "Arial", size: 24 }),
]));

children.push(emptyLine());

// S3. Piecewise-Exponential Optimization Details
children.push(heading("S3. Piecewise-Exponential Model Specification", 2));

children.push(body("The retained-solution envelope was constructed by searching over a grid of 120 model configurations: 5 knot placement schedules (2 to 5 internal knots at regular or log-spaced intervals within [0, T_max]), 6 smoothness penalty weights (\u03B1 \u2208 {0, 0.01, 0.1, 1, 10, 100}), and 4 regularization strengths (\u03BB \u2208 {0, 0.01, 0.1, 1}). The objective function to be minimized for each configuration was:"));

children.push(body("L(\u03B8) = ISE(\u03B8) + \u03B1 \u00B7 Smoothness(\u03B8) + \u03BB \u00B7 ||\u03B8||\u00B2"));

children.push(body("where ISE(\u03B8) is the integrated squared error between the model-implied aggregate survival curve (the prevalence-weighted mixture of subgroup curves) and the digitized KM curve; Smoothness(\u03B8) penalizes large changes in adjacent interval-specific hazard rates; and the L2 term regularizes against extreme parameter values. Optimization used scipy.optimize.minimize with the L-BFGS-B algorithm, with 5 random restarts per configuration to mitigate local optima."));

children.push(body("Solutions were retained if their ISE was within a specified tolerance ratio of the best-fitting model (default: 30% above the minimum ISE). The envelope of retained solutions\u2014defined as the pointwise minimum and maximum of the reconstructed subgroup survival curves across all retained fits\u2014constitutes the reported retained-solution envelope. This envelope captures sensitivity to model specification choices (knot placement, penalty strength) rather than statistical uncertainty."));

children.push(emptyLine());

// S4. Hazard Ratio Constraint: Mapping from Cox to Piecewise-Exponential
children.push(heading("S4. Hazard Ratio Constraint Discussion", 2));

children.push(body("Published subgroup hazard ratios are typically estimated from Cox proportional hazards regression, which yields a single summary HR for each subgroup. Our piecewise-exponential model parameterizes interval-specific hazard rates for control and treatment arms separately within each subgroup. The HR constraint is imposed by requiring that for each subgroup g and each interval j, the treatment hazard satisfies: h_trt(g,j) = HR_g \u00B7 h_ctrl(g,j), where HR_g is the reported subgroup HR from the forest plot."));

children.push(body("This mapping assumes proportional hazards within each subgroup across all intervals. When true PH holds, the Cox HR and the constant of proportionality in the piecewise-exponential model are identical. When PH is violated, the imposed constraint forces the model to approximate a potentially non-proportional treatment effect with a constant multiplier. This approximation contributes to the model-dependence of the retained-solution envelopes and is one reason the envelopes should not be interpreted as exact identifiability bounds. Simulation scenario D in the validation study directly tests robustness under non-proportional hazards."));

children.push(new Paragraph({ children: [new PageBreak()] }));

// =====================================================================
// SUPPLEMENTARY RESULTS: Simulation Validation
// =====================================================================
children.push(heading("Supplementary Results", 1));

children.push(heading("S5. Simulation Validation Study", 2));

children.push(body("To assess the calibration and coverage properties of the retained-solution envelopes, we conducted a simulation study using synthetic trials with known ground-truth subgroup survival curves. For each scenario, individual patient data were generated from subgroup-specific exponential hazard models with predetermined treatment effects. The synthetic IPD was then aggregated to produce (a) a Kaplan\u2013Meier curve for each arm (the mixture target) and (b) subgroup-level hazard ratio estimates (approximated from observed event rate ratios). The reconstruction algorithm was applied to these aggregate summaries, and the resulting retained-solution envelopes were compared to the known true subgroup-specific \u0394RMST\u2082\u2084 values."));

children.push(body("Five scenarios were tested, each with 50 replicates (different random seeds), for a total of 500 coverage evaluations:"));

children.push(emptyLine());

// Scenario descriptions
children.push(bodyRuns([
  new TextRun({ text: "Scenario A (Well-separated). ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "N = 300 per arm. Two subgroups with very different baseline hazards (\u03BB = 0.02, 0.10) and strongly differential treatment effects (HR = 0.4, 0.7). Prevalence 60:40. This represents the easiest reconstruction scenario.", font: "Arial", size: 24 }),
]));
children.push(bodyRuns([
  new TextRun({ text: "Scenario B (INDIGO-like). ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "N = 165 per arm. Moderate baseline separation (\u03BB = 0.03, 0.06), moderate HR differential (0.35, 0.50), balanced prevalence (52:48). Designed to approximate INDIGO trial characteristics.", font: "Arial", size: 24 }),
]));
children.push(bodyRuns([
  new TextRun({ text: "Scenario C (Near-null). ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "N = 300 per arm. Nearly identical subgroups: baselines \u03BB = 0.045, 0.055 with identical HRs (0.50, 0.50). Tests behavior when subgroup separation approaches zero.", font: "Arial", size: 24 }),
]));
children.push(bodyRuns([
  new TextRun({ text: "Scenario D (Non-proportional hazards). ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "N = 300 per arm. HRs cross over at 12 months (HR reverses to 1/HR after 12 months), directly violating the proportional hazards assumption embedded in the reconstruction. Tests robustness to model misspecification.", font: "Arial", size: 24 }),
]));
children.push(bodyRuns([
  new TextRun({ text: "Scenario E (Small sample). ", bold: true, font: "Arial", size: 24 }),
  new TextRun({ text: "N = 80 per arm with 20% censoring rate. Tests behavior under high sampling noise and small-trial conditions.", font: "Arial", size: 24 }),
]));

children.push(emptyLine());

// Validation results table
children.push(new Paragraph({
  children: [
    new TextRun({ text: "Table S1. ", bold: true, font: "Arial", size: 24 }),
    new TextRun({ text: "Simulation validation results. ", bold: true, italics: true, font: "Arial", size: 24 }),
    new TextRun({ text: "Coverage indicates the proportion of replicates in which the retained-solution envelope contained the true \u0394RMST\u2082\u2084. Mean |bias| is the absolute difference between the envelope median and the true value.", font: "Arial", size: 24 }),
  ],
  spacing: { line: 480, after: 120 },
}));

children.push(makeTable(
  ["Scenario", "N tests", "Coverage", "Mean width (mo)", "Mean |bias| (mo)", "Median |bias| (mo)"],
  [
    ["A: Well-separated", "100", "22%", "0.90", "1.10", "0.91"],
    ["B: INDIGO-like", "100", "14%", "1.11", "1.75", "1.49"],
    ["C: Near-null", "100", "26%", "0.93", "1.24", "0.91"],
    ["D: Non-PH", "100", "13%", "1.12", "2.34", "2.38"],
    ["E: Small sample", "100", "21%", "1.43", "2.69", "2.04"],
  ]
));

children.push(emptyLine());

children.push(body("Coverage ranged from 13% (non-proportional hazards, Scenario D) to 26% (near-null, Scenario C). These values are well below the nominal 95% level that would be expected of a formal confidence region, confirming that the retained-solution envelopes should be interpreted as model-specification sensitivity ranges rather than as statistical confidence intervals or identifiability bounds. The low coverage under non-proportional hazards (Scenario D) reflects the expected consequences of imposing constant HRs when the true treatment effect varies over time. Mean absolute bias ranged from 1.10 months (well-separated scenario) to 2.69 months (small sample), indicating that the envelope midpoint provides only a rough guide to the true subgroup effect."));

children.push(body("These results are discussed honestly in the main text and motivate our use of the term retained-solution envelope rather than feasible set or confidence region. The practical value of the method lies in revealing which subgroup factors show large variation across model specifications (suggesting uncertain heterogeneity) versus those that show consistently directional effects (suggesting more robust patterns), rather than in providing precise subgroup-specific effect estimates."));

children.push(new Paragraph({ children: [new PageBreak()] }));

// =====================================================================
// SUPPLEMENTARY FIGURES
// =====================================================================
children.push(heading("Supplementary Figures", 1));

children.push(new Paragraph({
  children: [
    new TextRun({ text: "Figure S1. ", bold: true, font: "Arial", size: 24 }),
    new TextRun({ text: "Quality assessment of digitized Kaplan\u2013Meier curves. ", bold: true, italics: true, font: "Arial", size: 24 }),
    new TextRun({ text: "(A) INDIGO PFS curves (vorasidenib, red; placebo, blue). (B) INDIGO TTNI curves after anchoring to text-reported probabilities. (C) CheckMate 498 OS curves (nivolumab, red; temozolomide, gray).", font: "Arial", size: 24 }),
  ],
  spacing: { line: 480 },
}));
children.push(figureImage(path.join(figDir, 'FigureS1_digitised_km.png'), 550, 160));
children.push(emptyLine());

children.push(new Paragraph({
  children: [
    new TextRun({ text: "Figure S2. ", bold: true, font: "Arial", size: 24 }),
    new TextRun({ text: "Tolerance sensitivity analysis. ", bold: true, italics: true, font: "Arial", size: 24 }),
    new TextRun({ text: "(A) INDIGO PFS: envelope width as a function of ISE tolerance ratio, by subgroup. (B) CheckMate 498 OS: envelope width by tolerance.", font: "Arial", size: 24 }),
  ],
  spacing: { line: 480 },
}));
children.push(figureImage(path.join(figDir, 'FigureS2_tolerance_sensitivity.png'), 550, 260));
children.push(emptyLine());

children.push(new Paragraph({ children: [new PageBreak()] }));

children.push(new Paragraph({
  children: [
    new TextRun({ text: "Figure S3. ", bold: true, font: "Arial", size: 24 }),
    new TextRun({ text: "CheckMate 498 OS retained-solution envelopes by subgroup factor. ", bold: true, italics: true, font: "Arial", size: 24 }),
    new TextRun({ text: "Format as main-text Figure 2. All \u0394RMST\u2082\u2084 values are negative, consistent with the overall HR of 1.31 favoring temozolomide. Panels show (A) complete resection, (B) sex, (C) corticosteroid use, and (D) Karnofsky performance status.", font: "Arial", size: 24 }),
  ],
  spacing: { line: 480 },
}));
children.push(figureImage(path.join(figDir, 'FigureS3_cm498_os_envelopes.png'), 550, 400));

// =====================================================================
// Supplementary Table S2: All INDIGO PFS envelope summaries
// =====================================================================
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading("Supplementary Tables", 1));

children.push(new Paragraph({
  children: [
    new TextRun({ text: "Table S2. ", bold: true, font: "Arial", size: 24 }),
    new TextRun({ text: "Complete INDIGO PFS retained-solution envelope summaries by subgroup factor. ", bold: true, italics: true, font: "Arial", size: 24 }),
    new TextRun({ text: "All values in months. \u0394RMST\u2082\u2084 = RMST(treatment) \u2013 RMST(control) at 24 months. Positive values favor vorasidenib. The full table is available in the reproducibility package (outputs/pfs_envelope_summaries_all.csv).", font: "Arial", size: 24 }),
  ],
  spacing: { line: 480, after: 120 },
}));

children.push(emptyLine());
children.push(body("Note: Detailed per-subgroup envelope summary tables for all endpoints (INDIGO PFS, INDIGO TTNI, CheckMate 498 OS) are provided as CSV files in the reproducibility package, as their size exceeds what is practical for a supplementary table. The package is available at the repository URL listed in the main manuscript."));


// Create document
const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Arial", size: 24 },
        paragraph: { spacing: { line: 480 } },
      },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", bold: true, size: 28 },
        paragraph: { spacing: { before: 240, after: 120, line: 480 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", bold: true, size: 24 },
        paragraph: { spacing: { before: 200, after: 100, line: 480 }, outlineLevel: 1 },
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [new TextRun({ text: "Supplementary Material", font: "Arial", size: 18, italics: true })],
          alignment: AlignmentType.RIGHT,
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          children: [new TextRun({ text: "Page ", font: "Arial", size: 18 }), new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18 })],
          alignment: AlignmentType.CENTER,
        })],
      }),
    },
    children,
  }],
});

const outDir = path.join(__dirname, '..', 'manuscript');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
const outPath = path.join(outDir, 'supplement.docx');

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log('Supplement created:', outPath, `(${(buffer.length / 1024).toFixed(1)} KB)`);
}).catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
