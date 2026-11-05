"""Renders text to transparent PNGs.

Roku's text labels are reported to draw Arabic-script text as separate,
unjoined letters, so every Persian string the app shows is drawn here instead.
"""

import io
import unicodedata
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = Path(__file__).parent / "fonts" / "Vazirmatn-Medium.ttf"
ZWNJ = "‌"
_reshaper = arabic_reshaper.ArabicReshaper(
    configuration={"delete_harakat": False, "support_ligatures": True}
)


def _font(size):
    return ImageFont.truetype(str(FONT_PATH), size, layout_engine=ImageFont.Layout.BASIC)


def _has_arabic_script(text):
    return any("ARABIC" in unicodedata.name(c, "") for c in text)


def _visual(text):
    """Converts logical text to shaped glyphs in left-to-right drawing order."""
    shaped = _reshaper.reshape(text).replace(ZWNJ, "")
    return get_display(shaped, base_dir="R") if _has_arabic_script(text) else shaped


def _clean(text):
    """Drops emoji and other symbols the font has no glyph for."""
    kept = [c for c in text if unicodedata.category(c) not in ("So", "Cs", "Co", "Cn")
            and c != "️"]
    return " ".join("".join(kept).split())


def _wrap(text, font, width, max_lines):
    def fits(candidate):
        return font.getlength(_visual(candidate)) <= width

    lines, current = [], ""
    words = text.split()
    for word in words:
        candidate = f"{current} {word}".strip()
        if fits(candidate):
            current = candidate
            continue
        if current and len(lines) < max_lines - 1:
            lines.append(current)
            current = word
            if fits(current):
                continue
        # Out of lines, or a single word wider than the card: cut and mark it.
        base = current or candidate
        while base and not fits(base + "…"):
            base = base[:-1]
        lines.append(base.rstrip() + "…")
        return lines
    if current:
        lines.append(current)
    return lines


def render_text(text, width, height, size, max_lines=2, align=None):
    """Returns PNG bytes of white text. align: "left", "right", "center" or
    None to follow the text's own direction."""
    text = _clean(text) or "-"
    font = _font(size)
    if align is None:
        align = "right" if _has_arabic_script(text) else "left"

    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    line_height = int(size * 1.45)
    for index, line in enumerate(_wrap(text, font, width, max_lines)):
        x = {"left": 0, "right": width, "center": width / 2}[align]
        anchor = {"left": "la", "right": "ra", "center": "ma"}[align]
        draw.text((x, index * line_height), _visual(line), font=font, fill="white", anchor=anchor)

    out = io.BytesIO()
    image.save(out, "PNG", optimize=True)
    return out.getvalue()
