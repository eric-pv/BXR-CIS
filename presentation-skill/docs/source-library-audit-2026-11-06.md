# PPTX source library audit — initial pass (2026-11-06)

## Source: 500頁.pptx
- 604 native slide XML files inspected.
- 587 slides contain PowerPoint timing XML. This does NOT prove animations are functional when copied.
- Initial heuristic content classification: 245 image-layout, 148 map, 65 product, 39 people, 10 agenda, 6 section, 15 navigation/intro, 76 unclassified.
- For each slide, local CSV records page ID, text-run count, native shape count, picture count, group count, animation-timing flag and extracted text preview.
- The classification is provisional: labels inside master slides, images or artwork are not reliably detected from per-slide text only.
- The full CSV was prepared as `500pages_slide_catalog.csv` in the ChatGPT workspace; it has not yet been uploaded to GitHub.
- No slides have been CIS-recolored or visually approved.

## Source: Aviation Slides.zip
- Archive includes 498 PPTX entries.
- Detailed nested-file analysis has not yet completed and must not be represented as finished.

## Next for Claude Code
1. Run a tested, resumable PPTX parser to index all nested Aviation PPTX source decks.
2. Generate contact sheets / previews of the 604 slides.
3. Inspect masters, layout backgrounds and images for embedded source branding.
4. Check paid-source licensing before public distribution; current repository is Public.
5. Select five approved pilot slides to prove safe and editable BXR recoloring with visual comparison.
6. Validate native animation and editability on PowerPoint before promising preservation.

This document is an engineering audit and does not contain purchased source archives.
