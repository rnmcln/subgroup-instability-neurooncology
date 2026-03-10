#!/usr/bin/env node
/**
 * Generate cover_letter.docx for NOA submission — revision 2.
 * Framed as cautionary sensitivity analysis, not reconstruction tool.
 */
const fs = require('fs');
const path = require('path');
const {
  Document, Paragraph, TextRun, AlignmentType,
  Header, Footer, PageNumber, Packer,
} = require('/sessions/gifted-lucid-edison/.npm-global/lib/node_modules/docx');

function body(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 24 })],
    spacing: { line: 360, after: 120 },
  });
}

function emptyLine() {
  return new Paragraph({ children: [new TextRun({ text: "", size: 24 })], spacing: { line: 360 } });
}

const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

const children = [];

children.push(body(today));
children.push(emptyLine());

children.push(body("Editor-in-Chief"));
children.push(body("Neuro-Oncology Advances"));
children.push(emptyLine());

children.push(body("Dear Editor,"));
children.push(emptyLine());

children.push(body("We are pleased to submit our manuscript entitled \u201CInstability of Subgroup-Specific Treatment Benefits Reconstructed From Aggregate Trial Data\u201D for consideration as an Original Article in Neuro-Oncology Advances."));

children.push(body("Clinicians and guideline panels routinely infer subgroup-specific absolute treatment benefits from aggregate trial publications. However, these quantities are generally not uniquely determined by the published data, and the sensitivity of such inferences to modelling assumptions is rarely quantified. The result is a risk of false precision: seemingly exact subgroup benefit estimates that depend substantially on implicit modelling choices."));

children.push(body("Our manuscript demonstrates this instability through a systematic model-specification sensitivity analysis applied to two trials of direct relevance to your readership: the INDIGO trial of vorasidenib in IDH-mutant glioma (Mellinghoff et al., NEJM 2023) and CheckMate 498 of nivolumab in newly diagnosed MGMT-unmethylated glioblastoma (Omuro et al., Neuro-Oncology 2023). The paper is not a tool for estimating subgroup effects\u2014our simulation validation (50 replicates per scenario, 500 total coverage tests), reported transparently, shows that such estimation from aggregate data is unreliable. Rather, it is a cautionary framework that makes visible the degree to which standard subgroup benefit estimates rest on modelling assumptions rather than on the published evidence itself."));

children.push(body("We believe this contributes a needed perspective for the neuro-oncology community, where subgroup-specific treatment recommendations increasingly influence clinical practice. A complete reproducibility package accompanies this submission."));

children.push(body("We confirm that this manuscript has not been published previously, is not under consideration for publication elsewhere, and that all authors have read and approved the submitted version. We have no conflicts of interest to disclose at this time."));

children.push(emptyLine());
children.push(body("We look forward to your consideration."));
children.push(emptyLine());
children.push(body("Sincerely,"));
children.push(emptyLine());
children.push(body("Aaron Lawson McLean"));
children.push(body("Department of Neurosurgery, Jena University Hospital"));
children.push(body("Friedrich Schiller University Jena"));
children.push(body("Am Klinikum 1, 07747 Jena, Germany"));
children.push(body("Aaron.lawsonmclean@med.uni-jena.de"));

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Arial", size: 24 },
      },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    children,
  }],
});

const outDir = path.join(__dirname, '..', 'manuscript');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
const outPath = path.join(outDir, 'cover_letter.docx');

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log('Cover letter created:', outPath, `(${(buffer.length / 1024).toFixed(1)} KB)`);
}).catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
