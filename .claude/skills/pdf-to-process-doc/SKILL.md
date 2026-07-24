---
name: pdf-to-process-doc
description: >-
  Turn a PDF process/refurb/assembly guide into a Jaunt Notion process document
  in the "Process Documentation and Instructions" database. Use this whenever Dave
  drops a PDF guide in the process-documents `source/` folder and wants it rebuilt
  in our own format, or says things like "extract the steps and images from this
  PDF and build a process doc", "turn this Fellten/supplier guide into our style",
  or "make a Notion manual from this PDF". Handles the whole pipeline: per-page text
  and photo extraction (de-branded), rewriting into Jaunt voice, pushing to Notion,
  and uploading photos privately laid out 3-abreast with a collapsible table of
  contents. This is the PDF counterpart to the existing video pipeline.
---

# PDF to Jaunt process document

Rebuild a PDF guide (often a supplier's, e.g. Fellten) as a Jaunt Notion process
doc: same Workshop Manual structure as the video pipeline, but the input is a
photo-heavy PDF instead of a video. The source is usually one logical step per
page (text on the left/middle, photos on the right), sometimes with photo-only
continuation pages.

The whole point is to make it **ours**: rewrite the prose in Jaunt voice and pull
the raw photos out (which drops the source's logo/watermark), rather than
re-hosting their branded pages.

## The pipeline

### 1. Extract
```
python3 scripts/extract_pdf.py "source/<guide>.pdf" <slug>
```
`<slug>` = lowercase-hyphenated short name. This writes `output/<slug>/`:
- `pagetext/pNN.txt` exact per-page text (page N text really is page N)
- `pages/page-NN.jpg` full-page renders, to read layout
- `photos/pNN-i.jpg` the de-branded content photos, per page

Read the page renders and page text to understand the procedure. `pdfinfo` gives
the page count; the first few pages are usually title / disclaimer / tools /
parts, and photos typically start a few pages in.

### 2. Author the page content
Write `output/<slug>/notion-page.md` in Jaunt's Workshop Manual format. Follow
Dave's global rules: Australian spelling, **no em dashes**, short imperative
steps, workshop-internal jargon is fine. Match the structure of an existing
pipeline page (see references below). Sections:

- Top callouts: the AI-draft disclaimer (`🤖`, per the Notion convention in
  CLAUDE.md), a provenance/confidentiality note if the source is a partner's IP,
  a torque-verify warning, and any HV/safety warning.
- `# Intro`, `## Steps which must be completed before beginning this task`
- `# Before You Start`
- `# Parts` (if the source lists them) + `## Consumables`
- `# Tools and Bolts` table (Description / Dimensions / Torque (Nm) / Tools)
- `# Steps` with `## Step N: <title>` headings, numbered sub-steps under each
- `# Updates to make to this page`, `## Next Step(s)`

**One step per source page.** Photo-only continuation pages (a page with photos
but no text) merge into the preceding step. Carry across every safety callout the
source flags (trapped fingers, burn risk, fragile cables, HV) as
`<callout icon="⚠️">`.

**Torques and part numbers.** Transcribe every torque from the guide into the
Tools table, tagged `(verify)` — they're documented specs, but still confirm
against current spec before anyone works to them. If the source leaves a value
blank ("??Nm"), flag it loudly (top callout + in the step + Tools table + an
Updates checkbox). Never invent a part number.

Write a `output/<slug>/steps.json` manifest mapping each step to its title,
source pages, and photo filenames (used by the uploader). See the LDU run's
`steps.json` for the shape.

### 3. Push text to Notion
The target is the **Process Documentation and Instructions** database
(data source `a4c0f0f9-6a4b-4d1b-88c9-0032db708e7d`). Dave usually creates the
empty page from the Workshop Manual Template first and gives you the URL; if not,
create one under that data source.

Use the Notion MCP (the "Jaunt Claude extension"):
`update-page` with `command: replace_content`, `allow_deleting_content: true`,
passing the markdown. Then `update-page` `update_properties` to set:
`Category` (multi, e.g. `["DR - Drivetrain","HV - HV Electrical"]`),
`Category ` (select, e.g. `⚡️ Motor Transmission & Driveline`),
`Work Type` (e.g. `🛠 Repair & Rebuild`), and a `Note` recording provenance.
Leave Status as Concept / Draft for human review.

Callout, table, image and step syntax that works: see `references/notion-format.md`.

### 4. Upload photos (private, 3-abreast, with ToC)
```
export NOTION_TOKEN="ntn_..."          # internal integration, shared with the page
python3 scripts/notion_upload_images.py \
  --manifest output/<slug>/steps.json \
  --photos   output/<slug>/photos \
  --page     <page_id> --toc --cols 3
```
This uploads each photo via the Notion File Upload API (so they live inside
Notion, not on the public repo), lays them 2-3 wide under each step so the page
stays compact and each image click-expands, and adds a collapsible "Table of
contents" toggle near the top. Re-running? Add `--replace` to clear old media
first (fresh file uploads are needed each time; upload IDs are single-use).

**Why a token is needed:** the Notion MCP can only ingest images from a public
URL, so it can't do a private local upload. The File Upload API can, but needs an
internal integration token (notion.so/my-integrations) shared with the page
(page ... > Connections). Ask Dave for one if it isn't set.

## Hosting / confidentiality (important)

This repo is **public** (Notion needs public URLs for the video pipeline's
frames). A supplier's proprietary guide must NOT land here — not the photos, page
renders, extracted text, or the rewritten procedure. For such a source:
- Upload photos privately into Notion (step 4), never the public repo.
- Gitignore the whole `output/<slug>/` and the source PDF (`source/*.pdf`).
- Backups are local + CCC + OneDrive.
Only the generic `scripts/` code is safe to commit. Confirm the confidentiality
call with Dave if unsure (a partner's teardown is more sensitive than Jaunt's own
workshop demos).

## References
- `references/notion-format.md` — working Notion markdown syntax (callouts, image
  columns, tables, ToC) and the database property values.
- Worked example: the Fellten LDU refurb run (`output/ldu-reduction-gearset-quaife-lsd-refurb/`,
  gitignored) and PROJECT.md's "PDF -> process doc workflow" section.
- Scripts: `scripts/extract_pdf.py`, `scripts/notion_upload_images.py`.
