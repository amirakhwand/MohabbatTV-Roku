"""Scheduled job: rebuilds the app's data when the channel changes.

A new upload triggers a full rebuild right away. Edits that a new-upload check
can't see (renamed videos, changed playlists) are picked up by a daily rebuild.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from site_writer import write_site
from youtube_api import YouTubeClient

CHANNEL_ID = "UCPscc-OAnGpsvNAbHhLhkGA"
FULL_REBUILD_SECONDS = 24 * 60 * 60


def run(client, out, now=None):
    now = time.time() if now is None else now
    out = Path(out)
    state_path = out / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}

    latest = client.latest_upload_id(CHANNEL_ID)
    is_due = now - state.get("lastFullSync", 0) >= FULL_REBUILD_SECONDS
    if latest == state.get("latestUpload") and not is_due:
        return "unchanged"

    model = client.fetch_model(CHANNEL_ID)
    if not (model["videos"] or model["live"] or model["shorts"]):
        raise RuntimeError("YouTube returned no videos; keeping the existing data")

    version = write_site(model, out)
    state_path.write_text(json.dumps({"latestUpload": latest, "lastFullSync": now}))
    return f"rebuilt {version}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="docs")
    args = parser.parse_args()

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        sys.exit("YOUTUBE_API_KEY is not set")
    print(run(YouTubeClient(api_key), args.out))


if __name__ == "__main__":
    main()
