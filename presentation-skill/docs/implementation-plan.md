# Claude Code development handoff

## Goal
A company-shared natural-language PPTX generator using purchased original designs, official CIS, and approved editable layout variants.

## Stage 0
Repository was PUBLIC when inspected on 2026-11-06. Confirm Private status before uploading licensed archives or restricted corporate assets. Verify multi-seat licensing and reuse rights. Use Git LFS for large PPTX, ZIP and POTX; watch quotas.

## Stage 1: inventory
Analyze 500頁.pptx and Aviation Slides.zip, preserving untouched source copies and source hashes.
Create a per-slide catalog: file, page, content type, use cases, editable objects, image count, animation status, preview, license notes and source branding.
Deduplicate using hashes and visual comparison.

## Stage 2: adaptation
Start with five representative slides; after visual acceptance expand to 30–50.
Replace sample company names, demo numbers and unwanted 旁門左道PPT labels, including slide layouts and masters, subject to licensing.
Create internal and external cover families and sector-sensitive variants.
Apply CIS brand assets and coherent typography. Leave native objects editable. Preserve animation when validated; PowerPoint COM or OOXML-preserving workflows may be needed since python-pptx can discard animations.

## Stage 3: generator
Natural-language brief -> accurate content plan -> layout retrieval -> brand compliant slide population -> editable PPTX -> render/visual QA -> delivery.
Provide a first pilot, before/after visuals, tests and known limitations.

## Acceptance
No clipped text, overlaps, empty placeholders, incorrect logo, unverified figures or unwanted source labels. Inspect every slide and verify file opening and editability. Source files unmodified.

## Git workflow
Use separate dev branches and PRs; do not merge main automatically.

## Slide Master acceptance requirement
The generator MUST create/use a real PowerPoint Slide Master and appropriate layouts for cover, section divider and content pages. Place approved corporate logo art in masters/layouts only, rather than copying the logo object into every slide. Use editable placeholders for slide-specific titles, page numbers and other copy. Validate that (a) logo is not baked into PNG backgrounds, (b) there is no duplicate logo on slides, (c) updating the layout/master logo affects every matching slide, (d) any sector-specific logo placement still follows CIS v3.2. Inspect inheritance and master visibility in native PowerPoint.
