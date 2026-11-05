"""One-off developer tool: builds the list bundled inside the app.

Reads the channel's public pages so a fresh install has content before the
scheduled sync has run. It is not part of the scheduled job, because this page
format can change at any time.
"""

import json
import re
import sys
import time
import urllib.request

from site_writer import write_site

HANDLE = "@mohabbattv"


def page_data(path):
    request = urllib.request.Request(
        f"https://www.youtube.com/{path}",
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US"},
    )
    html = urllib.request.urlopen(request, timeout=30).read().decode("utf-8")
    return json.loads(re.search(r"ytInitialData\s*=\s*(\{.*?\});</script>", html, re.S).group(1))


def find_all(node, key, found=None):
    found = [] if found is None else found
    if isinstance(node, dict):
        if key in node:
            found.append(node[key])
        for value in node.values():
            find_all(value, key, found)
    elif isinstance(node, list):
        for value in node:
            find_all(value, key, found)
    return found


def lockup_title(lockup):
    return lockup["metadata"]["lockupMetadataViewModel"]["title"]["content"]


def videos_from(path):
    data = page_data(path)
    videos = [
        {"id": l["contentId"], "title": lockup_title(l)}
        for l in find_all(data, "lockupViewModel")
        if l.get("contentType") == "LOCKUP_CONTENT_TYPE_VIDEO"
    ]
    for row in find_all(data, "playlistVideoRenderer"):
        title = row["title"]
        videos.append({"id": row["videoId"],
                       "title": title.get("simpleText") or "".join(r["text"] for r in title["runs"])})
    return videos


def shorts_from(path):
    shorts = []
    for lockup in find_all(page_data(path), "shortsLockupViewModel"):
        ids = find_all(lockup, "videoId")
        if ids:
            shorts.append({"id": ids[0], "title": lockup["overlayMetadata"]["primaryText"]["content"]})
    return shorts


def main(out):
    playlists = []
    for lockup in find_all(page_data(f"{HANDLE}/playlists"), "lockupViewModel"):
        playlist_id = lockup["contentId"]
        time.sleep(0.5)
        playlists.append({"id": playlist_id, "title": lockup_title(lockup),
                          "items": videos_from(f"playlist?list={playlist_id}")})
    model = {
        "videos": videos_from(f"{HANDLE}/videos"),
        "live": videos_from(f"{HANDLE}/streams"),
        "shorts": shorts_from(f"{HANDLE}/shorts"),
        "playlists": playlists,
    }
    write_site(model, out)
    print({k: len(v) for k, v in model.items()},
          "playlist items", sum(len(p["items"]) for p in playlists),
          "empty playlists", sum(1 for p in playlists if not p["items"]))


if __name__ == "__main__":
    main(sys.argv[1])
