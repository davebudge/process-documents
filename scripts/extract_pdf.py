#!/usr/bin/env python3
"""
Extract a PDF process/refurb guide into per-page text + de-branded step photos.

Given a source PDF, produces under output/<slug>/:
  pagetext/pNN.txt   exact per-page text (form-feed split, so page N text == page N)
  pages/page-NN.jpg  full-page renders (to read layout while authoring)
  photos/pNN-i.jpg   the embedded content photos, reindexed per page, downscaled

Extracting the raw embedded photo bitmaps (rather than cropping page renders)
strips the source's logo / banner / watermark automatically, because those are
separate small images we filter out by size. That is what makes the output
"our own thing" instead of a rebrand of someone else's page.

Requires poppler (`brew install poppler`) for pdftotext/pdftoppm/pdfimages,
and macOS `sips` for downscaling (swap for ImageMagick on Linux).

Usage:
  python3 scripts/extract_pdf.py "source/<guide>.pdf" <slug> \
      [--min-side 800] [--max-px 1600] [--render-dpi 120]

Then read output/<slug>/pagetext/*.txt and pages/*.jpg to author the Notion page,
and use scripts/notion_upload_images.py to place the photos.
"""
import argparse, os, re, subprocess, sys, shutil


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def sips_dim(path, which):
    out = subprocess.run(["sips", "-g", which, path], capture_output=True, text=True).stdout
    m = re.search(rf"{which}:\s*(\d+)", out)
    return int(m.group(1)) if m else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("slug")
    ap.add_argument("--min-side", type=int, default=800,
                    help="drop embedded images whose smaller side is under this (logos/banners)")
    ap.add_argument("--max-px", type=int, default=1600, help="downscale photos' long edge to this")
    ap.add_argument("--render-dpi", type=int, default=120)
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        sys.exit(f"not found: {args.pdf}")
    base = f"output/{args.slug}"
    pagetext, pages, photos, tmp = (f"{base}/pagetext", f"{base}/pages",
                                    f"{base}/photos", f"{base}/_extract")
    for d in (pagetext, pages, photos):
        os.makedirs(d, exist_ok=True)
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)

    # 1. per-page text via form-feed split (keeps page N text aligned to page N)
    txt = subprocess.run(["pdftotext", "-layout", args.pdf, "-"],
                         capture_output=True, text=True).stdout
    parts = txt.split("\f")
    for i, pg in enumerate(parts, 1):
        with open(f"{pagetext}/p{i:02d}.txt", "w") as fh:
            fh.write(pg.strip())
    npages = len([p for p in parts if p.strip()])
    print(f"page text: {npages} pages")

    # 2. full-page renders for reading layout
    run(["pdftoppm", "-jpeg", "-r", str(args.render_dpi),
         "-jpegopt", "quality=82", args.pdf, f"{pages}/page"])
    print(f"page renders: {len(os.listdir(pages))}")

    # 3. embedded photos, page-tagged, filtered to content, reindexed + downscaled
    run(["pdfimages", "-p", "-j", args.pdf, f"{tmp}/img"])
    by_page = {}
    for f in sorted(os.listdir(tmp)):
        fp = os.path.join(tmp, f)
        if sips_dim(fp, "pixelWidth") >= args.min_side and sips_dim(fp, "pixelHeight") >= args.min_side:
            m = re.match(r"img-0*(\d+)-", f)
            if m:
                by_page.setdefault(int(m.group(1)), []).append(fp)
    total = 0
    for page, files in sorted(by_page.items()):
        for i, src in enumerate(files, 1):
            out = f"{photos}/p{page:02d}-{i}.jpg"
            shutil.copy(src, out)
            run(["sips", "-Z", str(args.max_px), out])
            total += 1
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"photos: {total} across {len(by_page)} pages -> {photos}")
    print("photos per page:", {p: len(f) for p, f in sorted(by_page.items())})


if __name__ == "__main__":
    main()
