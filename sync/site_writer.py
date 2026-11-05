"""Writes the static files the Roku app reads.

Input model:
    {"videos": [{"id", "title"}], "live": [...], "shorts": [...],
     "playlists": [{"id", "title", "items": [{"id", "title"}]}]}

Output, relative to the output folder:
    feed.json                      version stamp the app polls
    tabs/<tab>-<page>.json         one page of a tab
    playlists/<id>-<page>.json     one page of a playlist
    titles/<hash>.png              rendered titles
"""

import hashlib
import json
import shutil
from pathlib import Path

from titles import render_text

PAGE_SIZE = 60
CARD = {"width": 420, "height": 92, "size": 30}
SHORT_CARD = {"width": 270, "height": 92, "size": 26}
RENDER_VERSION = "1"


def _title_image(title, card, out, used):
    key = f"{RENDER_VERSION}|{card['width']}|{card['size']}|{title}"
    name = hashlib.sha256(key.encode()).hexdigest()[:20] + ".png"
    used.add(name)
    path = out / "titles" / name
    if not path.exists():
        path.write_bytes(render_text(title, card["width"], card["height"], card["size"]))
    return f"titles/{name}"


def _write_pages(items, folder, prefix, out):
    pages = [items[i:i + PAGE_SIZE] for i in range(0, len(items), PAGE_SIZE)] or [[]]
    for number, page in enumerate(pages):
        has_next = number + 1 < len(pages)
        body = {"items": page, "next": f"{folder}/{prefix}-{number + 1}.json" if has_next else ""}
        (out / folder / f"{prefix}-{number}.json").write_text(
            json.dumps(body, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )


def _video_items(videos, kind, out, used):
    card = SHORT_CARD if kind == "short" else CARD
    return [
        {"id": v["id"], "kind": kind, "titleImage": _title_image(v["title"], card, out, used)}
        for v in videos
    ]


def write_site(model, out):
    out = Path(out)
    for folder in ("tabs", "playlists"):
        shutil.rmtree(out / folder, ignore_errors=True)
        (out / folder).mkdir(parents=True)
    (out / "titles").mkdir(parents=True, exist_ok=True)

    used = set()
    _write_pages(_video_items(model["videos"], "video", out, used), "tabs", "videos", out)
    _write_pages(_video_items(model["live"], "video", out, used), "tabs", "live", out)
    _write_pages(_video_items(model["shorts"], "short", out, used), "tabs", "shorts", out)

    playlists = []
    for playlist in model["playlists"]:
        if not playlist["items"]:
            continue
        prefix = playlist["id"]
        _write_pages(_video_items(playlist["items"], "video", out, used), "playlists", prefix, out)
        playlists.append({
            "id": playlist["id"],
            "kind": "playlist",
            "titleImage": _title_image(playlist["title"], CARD, out, used),
            "thumbId": playlist["items"][0]["id"],
            "list": f"playlists/{prefix}-0.json",
        })
    _write_pages(playlists, "tabs", "playlists", out)

    for image in (out / "titles").glob("*.png"):
        if image.name not in used:
            image.unlink()

    version = hashlib.sha256(
        json.dumps(model, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()[:16]
    (out / "feed.json").write_text(json.dumps({"version": version}), encoding="utf-8")
    return version
