"""One-off developer tool: renders the app's fixed Persian labels."""

import sys
from pathlib import Path

from titles import render_text

LABELS = {
    "tab_videos": "ویدیوها",
    "tab_live": "پخش زنده",
    "tab_shorts": "شورتز",
    "tab_playlists": "لیست‌های پخش",
}
ERROR = "یوتیوب باز نشد. لطفاً مطمئن شوید برنامه یوتیوب روی روکو نصب است."

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
for name, text in LABELS.items():
    (out / f"{name}.png").write_bytes(render_text(text, 280, 60, 36, max_lines=1, align="center"))
(out / "error_youtube.png").write_bytes(render_text(ERROR, 1500, 70, 38, max_lines=1, align="center"))
