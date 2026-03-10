# Manuscript

The manuscript `.docx` files are excluded from this repository during peer review.

To regenerate them from source:

```bash
npm install          # install docx dependencies
node scripts/create_manuscript.js
node scripts/create_supplement.js
node scripts/create_cover_letter.js
```

This produces `manuscript.docx`, `supplement.docx`, and `cover_letter.docx` in this directory.

All content is fully determined by the scripts and the data in `outputs/` and `data/`.
