#!/usr/bin/env python3
"""
Privately upload step photos into a Notion process-doc page, laid out 3-abreast.

Uses the Notion File Upload API (https://developers.notion.com/docs/uploading-small-files)
so the images live inside Notion, not on the public GitHub repo. Reads a steps.json
manifest (produced by the PDF-extraction run), uploads each photo, then appends the
images under their step heading as column rows (2-3 images wide) so the page stays
compact and each image click-expands.

Reusable for any future "PDF -> Jaunt process doc" run: point it at a different
manifest + photos dir + page.

Prereqs:
  1. A Notion internal integration token with content capabilities.
       export NOTION_TOKEN="ntn_xxx"
  2. The target page (or its parent database) shared with that integration
     (Notion page: ... > Connections > add your integration).

Usage:
  export NOTION_TOKEN="ntn_..."
  # First run (or re-run after --replace clears old media):
  python3 scripts/notion_upload_images.py \
      --manifest output/<slug>/steps.json \
      --photos   output/<slug>/photos \
      --page     <page_id> [--replace] [--toc] [--cols 3]

Flags:
  --replace  Archive existing step images / column layouts first (idempotent re-run).
  --toc      Add a collapsible "Table of contents" toggle near the top of the page.
  --cols     Max images per row (default 3).
  --dry-run  Print the plan without touching Notion.
"""
import argparse, json, os, sys, time, urllib.request, urllib.error

API = "https://api.notion.com/v1"
VERSION = "2022-06-28"


def _req(method, url, token, data=None, headers=None, raw=False):
    h = {"Authorization": f"Bearer {token}", "Notion-Version": VERSION}
    if headers:
        h.update(headers)
    body = data
    if data is not None and not raw:
        body = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} on {method} {url}\n{e.read().decode()}")


# ---------- file upload ----------

def upload_photo(token, filepath):
    filename = os.path.basename(filepath)
    up = _req("POST", f"{API}/file_uploads", token,
              {"mode": "single_part", "filename": filename})
    boundary = "----jauntupload7eb1e163"
    with open(filepath, "rb") as f:
        content = f.read()
    body = b"".join([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode(),
        b"Content-Type: image/jpeg\r\n\r\n", content,
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    _req("POST", up["upload_url"], token, data=body, raw=True,
         headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    return up["id"]


# ---------- block builders ----------

def img_block(fid):
    return {"object": "block", "type": "image",
            "image": {"type": "file_upload", "file_upload": {"id": fid}}}


def row_sizes(n, cols):
    """Chunk n images into rows of <=cols, each row 2..cols wide (no orphan of 1).
    A column_list needs >=2 columns, so we never leave a trailing single in a row."""
    if n <= 1:
        return [n] if n else []
    rows = []
    while n > 0:
        if n == cols + 1:          # e.g. 4 with cols=3 -> 2,2 (avoid 3,1)
            rows += [2, n - 2]
            n = 0
        elif n <= cols:
            rows.append(n)
            n = 0
        else:
            rows.append(cols)
            n -= cols
    return rows


def media_blocks(fids, cols):
    """Return a list of blocks (single images and/or column_lists) for one step."""
    blocks, i = [], 0
    for size in row_sizes(len(fids), cols):
        chunk = fids[i:i + size]
        i += size
        if size == 1:
            blocks.append(img_block(chunk[0]))
        else:
            blocks.append({
                "object": "block", "type": "column_list",
                "column_list": {"children": [
                    {"object": "block", "type": "column",
                     "column": {"children": [img_block(f)]}} for f in chunk]},
            })
    return blocks


# ---------- page ops ----------

def top_level_children(token, page_id):
    out, cursor = [], None
    while True:
        url = f"{API}/blocks/{page_id}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"
        res = _req("GET", url, token)
        out.extend(res["results"])
        if not res.get("has_more"):
            break
        cursor = res["next_cursor"]
    return out


def step_headings(children):
    out = {}
    for b in children:
        if b["type"] == "heading_2":
            txt = "".join(t["plain_text"] for t in b["heading_2"]["rich_text"])
            if txt.startswith("Step ") and ":" in txt:
                try:
                    out[int(txt.split("Step ", 1)[1].split(":", 1)[0])] = b["id"]
                except ValueError:
                    pass
    return out


def archive_media(token, children):
    n = 0
    for b in children:
        if b["type"] in ("image", "column_list"):
            _req("PATCH", f"{API}/blocks/{b['id']}", token, {"archived": True})
            n += 1
    return n


def add_toc(token, page_id, children):
    # skip if a toggle named "Table of contents" already exists
    for b in children:
        if b["type"] == "toggle":
            txt = "".join(t["plain_text"] for t in b["toggle"]["rich_text"]).lower()
            if "table of contents" in txt:
                return False
    toc = {"object": "block", "type": "toggle", "toggle": {
        "rich_text": [{"type": "text", "text": {"content": "Table of contents"}}],
        "children": [{"object": "block", "type": "table_of_contents",
                      "table_of_contents": {}}]}}
    # place after the first block (the AI-draft callout) to keep the convention
    after = children[0]["id"] if children else None
    payload = {"children": [toc]}
    if after:
        payload["after"] = after
    _req("PATCH", f"{API}/blocks/{page_id}/children", token, payload)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--photos", required=True)
    ap.add_argument("--page", required=True)
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--replace", action="store_true")
    ap.add_argument("--toc", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("NOTION_TOKEN")
    if not token and not args.dry_run:
        sys.exit("Set NOTION_TOKEN (internal integration token, shared with the page).")

    manifest = json.load(open(args.manifest))
    steps = manifest["steps"]
    total = sum(len(s["photos"]) for s in steps)
    print(f"{len(steps)} steps, {total} photos, cols={args.cols}")

    if args.dry_run:
        for s in steps:
            print(f"  Step {s['n']:>2}: {len(s['photos'])} photos -> rows {row_sizes(len(s['photos']), args.cols)}")
        return

    children = top_level_children(token, args.page)

    if args.replace:
        removed = archive_media(token, children)
        print(f"Archived {removed} existing media blocks.")
        children = top_level_children(token, args.page)  # refresh

    if args.toc:
        print("Added table of contents." if add_toc(token, args.page, children)
              else "Table of contents already present, skipped.")
        children = top_level_children(token, args.page)

    headings = step_headings(children)
    print(f"Matched {len(headings)} step headings.")

    done = 0
    for s in steps:
        n = s["n"]
        if n not in headings:
            print(f"  ! Step {n}: no heading, skipping")
            continue
        fids = []
        for p in s["photos"]:
            fp = os.path.join(args.photos, p)
            if not os.path.exists(fp):
                print(f"  ! missing {p}")
                continue
            fids.append(upload_photo(token, fp))
            done += 1
            time.sleep(0.1)
        if fids:
            _req("PATCH", f"{API}/blocks/{args.page}/children", token,
                 {"children": media_blocks(fids, args.cols), "after": headings[n]})
        print(f"  Step {n:>2}: +{len(fids)} images ({done}/{total})")

    print(f"Done. {done} images laid out {args.cols}-abreast in page {args.page}.")


if __name__ == "__main__":
    main()
