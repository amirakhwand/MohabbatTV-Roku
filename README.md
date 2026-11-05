# MohabbatTV for Roku

A Roku app laid out like the [@mohabbattv](https://www.youtube.com/@mohabbattv) YouTube channel, with Videos, Live, Shorts and Playlists tabs. Selecting a video opens it in the official YouTube app on the Roku.

## How updates work

```
YouTube API -> scheduled GitHub job -> published data files -> Roku app
```

Every 15 minutes, a GitHub job asks YouTube for the newest upload. If it has changed, the job rebuilds the data files. The job also does a full rebuild once a day to pick up renamed videos and playlist changes. The app loads fresh data when it starts and checks again every 5 minutes while open. GitHub can delay scheduled jobs, so allow up to about an hour for a new video to appear.

If the data can't be reached, the app shows its last saved copy, or the list bundled with it.

## Setup

### 1. Get a YouTube API key

1. In the [Google Cloud console](https://console.cloud.google.com/), create a project.
2. Enable **YouTube Data API v3**.
3. Create an **API key** and restrict it to that API.

The channel's normal use should stay well inside the free daily quota of 10,000 units.

### 2. Publish the sync job on GitHub

1. Put this folder in a **public** GitHub repository. Free GitHub Pages needs a public repository, and the key stays private in step 3.
2. Go to **Settings > Secrets and variables > Actions** and add a secret named `YOUTUBE_API_KEY`.
3. Go to **Actions > Sync YouTube channel > Run workflow**. This creates the `docs` folder.
4. Go to **Settings > Pages** and publish from the main branch's `/docs` folder.

Never put the API key in this code or commit it to the repository.

### 3. Point the app at your data

In `components/Config.brs`, set the address from GitHub Pages, including the final `/`:

```
return "https://YOUR-NAME.github.io/YOUR-REPO/"
```

Until this is set, the app only shows its bundled list and never updates.

### 4. Install on your Roku

1. On the Roku remote, press **Home 3 times, Up 2 times, Right, Left, Right, Left, Right**, then enable the developer installer and set a password.
2. In **Settings > System > Advanced system settings > Control by mobile apps**, make sure network access isn't turned off or limited. The app uses this to open YouTube.
3. Make sure the YouTube app is installed on the Roku.
4. Run:

```bash
ROKU_IP=192.168.1.50 ROKU_PASSWORD=your-dev-password scripts/install.sh
```

A Roku holds one developer app at a time. This install method is for your own devices, not for other viewers.

## Publishing on the Roku store

This build isn't suitable for the store. Roku's certification rules are reported to forbid one app opening another this way. A store version would need to play videos inside the app, from files you host outside YouTube.

## Project layout

| Path | Purpose |
| --- | --- |
| `source/`, `components/` | The Roku app |
| `data/`, `images/` | Bundled video list and artwork |
| `sync/` | The scheduled job and image tools |
| `tests/` | Tests for the job: `python -m unittest discover tests` |

To refresh the bundled list, run `python sync/snapshot_public.py data`, then rebuild the app.

The Vazirmatn font is used under the SIL Open Font License (`sync/fonts/OFL.txt`).
