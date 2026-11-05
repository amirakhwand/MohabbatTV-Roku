"""Reads the channel through the official YouTube Data API v3."""

import json
import urllib.error
import urllib.parse
import urllib.request

API = "https://www.googleapis.com/youtube/v3/"
HIDDEN_TITLES = {"Private video", "Deleted video"}


class YouTubeClient:
    def __init__(self, api_key, opener=urllib.request.urlopen):
        self.api_key = api_key
        self.opener = opener

    def _get(self, endpoint, **params):
        query = urllib.parse.urlencode({**params, "key": self.api_key})
        with self.opener(f"{API}{endpoint}?{query}", timeout=30) as response:
            return json.load(response)

    def latest_upload_id(self, channel_id):
        """Costs 1 quota unit, so it can run on every scheduled check."""
        body = self._get("playlistItems", part="snippet", maxResults=1,
                         playlistId=_uploads(channel_id, "UU"))
        items = body.get("items", [])
        return items[0]["snippet"]["resourceId"]["videoId"] if items else ""

    def playlist_videos(self, playlist_id):
        videos, token = [], None
        while True:
            params = {"part": "snippet", "maxResults": 50, "playlistId": playlist_id}
            if token:
                params["pageToken"] = token
            try:
                body = self._get("playlistItems", **params)
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    return videos
                raise
            for item in body.get("items", []):
                snippet = item["snippet"]
                if snippet["title"] not in HIDDEN_TITLES:
                    videos.append({"id": snippet["resourceId"]["videoId"], "title": snippet["title"]})
            token = body.get("nextPageToken")
            if not token:
                return videos

    def channel_playlists(self, channel_id):
        playlists, token = [], None
        while True:
            params = {"part": "snippet", "maxResults": 50, "channelId": channel_id}
            if token:
                params["pageToken"] = token
            body = self._get("playlists", **params)
            for item in body.get("items", []):
                playlists.append({"id": item["id"], "title": item["snippet"]["title"]})
            token = body.get("nextPageToken")
            if not token:
                return playlists

    def fetch_model(self, channel_id):
        playlists = self.channel_playlists(channel_id)
        for playlist in playlists:
            playlist["items"] = self.playlist_videos(playlist["id"])
        return {
            # YouTube's automatic per-type upload lists. The prefixes are widely
            # used but not formally documented; a missing one counts as empty.
            "videos": self.playlist_videos(_uploads(channel_id, "UULF")),
            "live": self.playlist_videos(_uploads(channel_id, "UULV")),
            "shorts": self.playlist_videos(_uploads(channel_id, "UUSH")),
            "playlists": playlists,
        }


def _uploads(channel_id, prefix):
    return prefix + channel_id[2:]
