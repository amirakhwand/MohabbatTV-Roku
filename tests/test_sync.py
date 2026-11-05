"""Run from the project root: python -m unittest discover tests

The YouTube API responses here are hand-written stand-ins, so these tests check
this project's logic, not the live API.
"""

import io
import json
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sync"))

from site_writer import PAGE_SIZE, write_site
from sync import CHANNEL_ID, FULL_REBUILD_SECONDS, run
from titles import render_text
from youtube_api import YouTubeClient


def entry(video_id, title):
    return {"snippet": {"title": title, "resourceId": {"videoId": video_id}}}


class FakeYouTube:
    """Answers API URLs from a table and records what was requested."""

    def __init__(self, lists):
        self.lists = lists
        self.calls = []

    def __call__(self, url, timeout=None):
        query = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))
        self.calls.append(query)
        if "/playlists?" in url:
            body = {"items": [{"id": "PL1", "snippet": {"title": "محرم ۱۴۴۵"}}]}
        else:
            playlist = query["playlistId"]
            if playlist not in self.lists:
                raise urllib.error.HTTPError(url, 404, "not found", None, None)
            pages = self.lists[playlist]
            number = int(query.get("pageToken", 0))
            body = {"items": pages[number]}
            if number + 1 < len(pages):
                body["nextPageToken"] = str(number + 1)
        return _Response(json.dumps(body))


class _Response(io.StringIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def channel(newest="new1"):
    suffix = CHANNEL_ID[2:]
    return {
        "UU" + suffix: [[entry(newest, "x")]],
        "UULF" + suffix: [
            [entry(newest, "ویدیو جدید"), entry("gone", "Private video")],
            [entry("old1", "ویدیو قدیمی")],
        ],
        "UUSH" + suffix: [[entry("short1", "شورت")]],
        "PL1": [[entry("old1", "ویدیو قدیمی")]],
    }


class SyncTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.out = Path(folder.name)

    def client(self, fake):
        return YouTubeClient("KEY", opener=fake)

    def page(self, name):
        return json.loads((self.out / name).read_text(encoding="utf-8"))

    def test_builds_every_tab_and_follows_api_paging(self):
        run(self.client(FakeYouTube(channel())), self.out, now=1000)
        videos = self.page("tabs/videos-0.json")["items"]
        self.assertEqual([v["id"] for v in videos], ["new1", "old1"])
        self.assertEqual(self.page("tabs/live-0.json")["items"], [])
        self.assertEqual(self.page("tabs/shorts-0.json")["items"][0]["kind"], "short")
        playlist = self.page("tabs/playlists-0.json")["items"][0]
        self.assertEqual(playlist["thumbId"], "old1")
        self.assertEqual(self.page(playlist["list"])["items"][0]["id"], "old1")
        self.assertTrue((self.out / videos[0]["titleImage"]).exists())

    def test_quiet_check_costs_one_call_and_changes_nothing(self):
        run(self.client(FakeYouTube(channel())), self.out, now=1000)
        before = self.page("feed.json")
        fake = FakeYouTube(channel())
        self.assertEqual(run(self.client(fake), self.out, now=1900), "unchanged")
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(self.page("feed.json"), before)

    def test_new_upload_appears_and_changes_version(self):
        run(self.client(FakeYouTube(channel())), self.out, now=1000)
        before = self.page("feed.json")["version"]
        run(self.client(FakeYouTube(channel(newest="new2"))), self.out, now=1900)
        self.assertNotEqual(self.page("feed.json")["version"], before)
        self.assertEqual(self.page("tabs/videos-0.json")["items"][0]["id"], "new2")

    def test_daily_rebuild_runs_without_a_new_upload(self):
        run(self.client(FakeYouTube(channel())), self.out, now=1000)
        fake = FakeYouTube(channel())
        run(self.client(fake), self.out, now=1000 + FULL_REBUILD_SECONDS)
        self.assertGreater(len(fake.calls), 1)

    def test_empty_response_keeps_existing_data(self):
        run(self.client(FakeYouTube(channel())), self.out, now=1000)
        before = self.page("tabs/videos-0.json")
        empty = {"UU" + CHANNEL_ID[2:]: [[entry("new2", "x")]], "PL1": [[]]}
        with self.assertRaises(RuntimeError):
            run(self.client(FakeYouTube(empty)), self.out, now=1900)
        self.assertEqual(self.page("tabs/videos-0.json"), before)

    def test_large_lists_split_into_linked_pages(self):
        videos = [{"id": f"v{i}", "title": f"t{i}"} for i in range(PAGE_SIZE + 1)]
        write_site({"videos": videos, "live": [], "shorts": [], "playlists": []}, self.out)
        first = self.page("tabs/videos-0.json")
        self.assertEqual(len(first["items"]), PAGE_SIZE)
        self.assertEqual(self.page(first["next"])["next"], "")

    def test_titles_survive_long_text_and_emoji(self):
        for text in ["واژه‌ای " * 60, "🔥🔥", "x" * 500, ""]:
            self.assertTrue(render_text(text, 420, 92, 30).startswith(b"\x89PNG"))


if __name__ == "__main__":
    unittest.main()
