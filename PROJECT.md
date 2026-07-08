# Process Documents

## What this is

A pipeline that turns a workshop video into a polished Notion process documentation page. Drop an MP4 in `source/`, tell Claude to process it, and a Draft-status row appears in the existing **⚙️ Process Documentation and Instructions** database with: transcript-derived intro, numbered steps, screenshots pulled from the video, and a callout reminding you to upload the video to YouTube and paste the URL in.

Built to remove the friction between "shoot a 5-minute workshop demo" and "have a usable workshop manual in Notion." The SME shoots the video; everything else is automated except the YouTube upload and final review.

## Current status

- ✅ Pipeline scripts working ([scripts/](scripts/))
- ✅ Whisper large-v3 model downloaded (`models/ggml-large-v3.bin`, ~3GB, gitignored)
- ✅ Test video processed end-to-end ([output/dji-test/](output/dji-test/))
- ✅ Test Notion page created (see end of this file for URL)
- ⏳ YouTube upload still manual (no API automation in v1)
- ⏳ Frame selection is "midpoint of step" — works but could be smarter

## Key decisions

- **Destination database**: existing **⚙️ Process Documentation and Instructions** at https://www.notion.so/7a70100a43e64098b71cd6370f1ed398. Data source ID: `a4c0f0f9-6a4b-4d1b-88c9-0032db708e7d`. Default template: **Workshop Manual Template** (ID `23f02a43-0089-80db-9b90-d1d23dfd91d9`). Use this — don't create a parallel database.
- **Page format**: Workshop Manual Template structure (Intro / Before You Start / Required Parts / Tools and Bolts / Steps / Next Steps). The pipeline fills Intro + Steps (with screenshots). It leaves Required Parts and Tools and Bolts empty with a yellow SME callout — those tables need human input (torques, part numbers).
- **Transcription**: `whisper-cli` (whisper.cpp) with `large-v3` model, Metal GPU on M2 Max. About 8s for a 110s video. Big accuracy win on mechanical jargon ("ROPS", "rivet", "capping") and Aussie accent.
- **Frame extraction**: midpoint of each step's spoken timestamp via `ffmpeg -ss <t>`. Output as JPEG @ 1920px max, q=3. ~150KB per frame. Easy to host on GitHub.
- **Image hosting**: this repo, pushed to https://github.com/davebudge/process-documents (public, by design — Notion needs HTTP URLs and the frames are workshop technique stills, nothing proprietary). Notion images use `https://raw.githubusercontent.com/davebudge/process-documents/main/output/<slug>/frames/step-NN.jpg`.
- **YouTube**: manual upload (unlisted) to the "Process Library" playlist. The pipeline leaves a yellow callout at the top of the Notion page with a placeholder embed line ready to paste the URL into.
- **Source videos**: live in `source/`, gitignored (too big). The MP4 stays on the workstation only.

## Project rules

- Use **A4** and **AUD** in any generated docs (Dave's preferences).
- **Australian spelling**, no em dashes (—), short imperative sentences in Steps.
- Workshop-internal audience — jargon and acronyms (BMS, CCS, CAN, ROPS) are fine.
- Safety-critical step → yellow `<callout icon="⚠️" color="yellow_background">`.
- Frames go into `output/<slug>/frames/step-NN.jpg`, two-digit number, zero-padded.
- Per-video slug = lowercased video basename with non-alnum collapsed to `-`.

## File layout

```
process-documents/
├── source/                   # MP4s (gitignored)
├── output/<slug>/
│   ├── audio.wav             # gitignored
│   ├── transcript.json
│   ├── transcript.txt
│   ├── steps.json            # title, category, vehicle line, steps[] with timestamps
│   └── frames/step-NN.jpg
├── scripts/
│   ├── download_model.sh     # one-time
│   ├── transcribe.sh         # video → transcript
│   └── extract_frames.py     # steps.json → frames
└── models/ggml-large-v3.bin  # gitignored (3GB)
```

## How to do a new video

1. Drop the MP4 in `source/`.
2. Tell Claude Code: *"process source/<filename>.mp4"*.
3. Claude runs `scripts/transcribe.sh`, drafts `steps.json` + intro by reading the transcript, runs `scripts/extract_frames.py`, commits + pushes the frames, then creates the Notion page via the Notion MCP.
4. Claude also renames the source MP4 to a descriptive YouTube-ready filename (pattern: `YYYY-MM-DD-<slug>.MP4`) and outputs a **YouTube upload bundle**: title, description (with Notion page URL), tags, settings (Unlisted, Autos & Vehicles, Process Library playlist, comments off, embedding on), and the `<video src="https://youtu.be/..."></video>` snippet to paste into the top callout. Do this at the end of every run, automatically.
5. Dave uploads to YouTube, pastes the embed snippet into the Notion page replacing the yellow callout, and flips Status to In use.

## Known issues and gotchas

- **Frame quality**: midpoint extraction can land on motion-blur or an unhelpful angle. For v1, accept the trade-off; if a frame is bad, manually replace it in Notion. v2 idea: scene-detect candidates + let a vision model pick the best.
- **Parts and torques**: default is you can't derive them from audio, so leave those tables empty with an SME callout, and never invent a part number. **Exception (Dave's call, 05/07/2026):** when the SME narrates torques and fastener specs on-camera (some videos are pure torque/fastener tours), DO capture them, but tag every value `VERIFY` and put a loud "verify against spec before use" callout at the top. They go in as Draft for human sign-off. Still never invent part numbers, they're rarely spoken.
- **Whisper hallucination loop**: when the audio goes quiet/ambient (SME stops talking but keeps filming), large-v3 can lock into repeating one phrase for the rest of the clip (a whole minute of "they're going to be a little bit different than the old ones" on the 03/07 run). Spot the repeated-line tail in transcript.txt and cut it, the real content ends where the repetition starts.
- **DJI source files**: huge (~700MB for 2 minutes at 4K). Keep them out of git. If you ever need the source again, it's still on the workstation under `source/`.
- **Public repo**: image URLs are world-readable. Don't film anything you wouldn't put on the company YouTube. If a video has sensitive content, host frames elsewhere (Cloudflare R2, etc.).
- **Whisper proper-noun spelling**: even large-v3 will mis-spell uncommon Aussie names and supplier names. Spot-check the transcript before publishing.

## Test page

First end-to-end run, 2026-05-28:

- **Source video:** `source/2026-05-27-remove-rops-and-capping-perentie.MP4` (1:50, ROPS + body capping removal walkthrough on a Land Rover Perentie)
- **Generated Notion page:** https://www.notion.so/36e02a43008981a9a77fc910d6e93cb3 ("Remove ROPS and body capping [Perentie]")
- **GitHub frames:** https://github.com/davebudge/process-documents/tree/main/output/dji-test/frames

Quirks observed and worked around:

- Whisper large-v3 on M2 Max Metal transcribed a 1:50 video in ~8 seconds. Got "ROPS", "rivet", "capping", "fuel filler nozzle" all correct.
- Initial frame extraction wrote 4K 16-bit PNGs at 35MB each (too big for a repo). Updated `extract_frames.py` to write 1920px JPEG q=3 (~150KB).
- The Notion MCP `fetch` strips the `color="yellow_background"` attribute from callouts in the read-back, even though the colour is persisted on the page (confirmed by checking an existing page with known-yellow callouts). Don't trust the fetch view for callout colours, but the colour IS applied.
- Notion auto-linked `.MP4` in the Note field as if it were a URL. Worked around by writing the extension as `(MP4)` instead of `.MP4` in the Note.
- Em dashes (`—`) snuck into step headings on the first draft. Replaced with colons. Watch this in future runs — em dashes are a hard no.

Second run, 2026-07-05:

- **Source video:** `source/2026-07-03-perentie-chassis-component-assembly.MP4` (3:53, 4K, front chassis component assembly on a Perentie: shock mounts, bushes, steering box)
- **Generated Notion page:** https://app.notion.com/p/39402a43008981cab0e6c18d73cb7a3f ("Assemble chassis components, part 1: shock mounts, bushes, steering box [Perentie]")
- **GitHub frames:** https://github.com/davebudge/process-documents/tree/main/output/perentie-chassis-component-assembly/frames

Quirks and firsts on this run:

- First **torque/fastener-tour** video: not a sequential procedure, the SME walks the chassis calling out each bolt and torque. Filled the Tools and Bolts table (each value tagged VERIFY) per the exception above, kept Required Parts blank (no part numbers spoken).
- Whisper looped from ~2:53 to the end (see gotcha above). Cut the tail.
- Suppliers came through the transcript garbled and Dave corrected them: "just worth fasteners" = **Würth**, "pretty shorter parts" = **British Auto Parts**. Filed both to the wiki. SuperPro was correct.
- Frames were sharp this run, the SME's finger was on the relevant fastener at each midpoint.

Third run, 2026-07-09:

- **Source video:** `source/2026-07-09-perentie-chassis-component-assembly-part-2.MP4` (1:04, 4K, short follow-on to part 1: bash guard under the motor + the crossbar that replaces the old gearbox mount)
- **Generated Notion page:** not yet created (Notion MCP was unauthenticated this session). Page content drafted and saved to [output/perentie-chassis-component-assembly-part-2/notion-page.md](output/perentie-chassis-component-assembly-part-2/notion-page.md), ready to create once the connector is authorised.
- **GitHub frames:** https://github.com/davebudge/process-documents/tree/main/output/perentie-chassis-component-assembly-part-2/frames

Quirks and notes on this run:

- **New-file confusion:** the "new file" turned out to be the video in `source/` (dropped as a raw `DJI_...MP4`), not the whiteboard photos sitting untracked in `output/dev-meeting-2026-05-28/`. Those photos are an unrelated strategy-board capture, not pipeline output.
- Two clean steps only. The SME frames it as "part three, let's call it" (he's numbering the physical assembly steps), but as a document it's part 2 of the series (part 1 = shock mounts, bushes, steering box). Dave confirmed vehicle = Perentie and doc numbering = part 2.
- Fastener tour again: M8 x 25mm into rivnuts on the gearbox mount crossbar. Tagged `VERIFY` (SME said "I think they're M8 by 25mm"). No torque spoken, left blank with SME callout. No part numbers spoken.
- Both frames sharp, no motion blur or hallucination tail this run.
- **Notion MCP blocked:** connector not authenticated in this session, so the page couldn't be created. Everything up to that point (transcript, steps, frames, page draft, YouTube bundle) is ready.
