"""Spec 003, V3 (AC8, AC9): the design rules of the page, as a check that can fail.

`problems` reads the source of the page and lists what breaks a rule of specs/003-visual-pass/spec.md (design rules, FR7).
The tests run it on the page itself and, so that it is known to be able to fail, on copies of the page that are wrong in
one way each.
"""

import hashlib
import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest

from kube_agent import view
from kube_agent.controller import TACTICS

PAGE = (view.PAGE_DIR / "index.html").read_text()
ALLOWED_FAMILIES = {"plex sans", "plex mono", "sans-serif", "monospace"}
MARKETING = ("magic", "revolutionary", "game-changing", "game changing", "ai-powered", "unleash", "supercharge", "seamless",
             "cutting-edge", "thinking", "next-level", "blazing", "powered by")
NAMED_COLOURS = {"red", "green", "blue", "white", "black", "gray", "grey", "yellow", "orange", "purple", "pink", "cyan", "magenta",
                 "silver", "navy", "teal", "lime", "maroon", "olive", "aqua", "fuchsia", "gold", "brown", "violet", "indigo",
                 "crimson", "coral", "salmon"}
# The ranges of Unicode's Extended_Pictographic that matter here (the standard library has no property for it).
PICTOGRAPHIC = re.compile("[©®‼⁉™ℹ↔-↪⌚-⏿Ⓜ▪-◾☀-➿"
                          "⤴⤵⬅-⭕〰〽㊗㊙\U0001f000-\U0001faff]")
MIN_TEXT_PX, MIN_TACTIC_PX, MIN_CARD_ROW_PX = 28, 96, 64
FONT_SHA256 = {
    "IBMPlexMono-Regular.woff2": "ba204497f16b6d334cee9d1e963a831b73e3a56e1d6300a8489d18df7214b350",
    "IBMPlexMono-SemiBold.woff2": "6a825b4824c01cbb401e829e5a066a1818411bcb3538b5a5792c5ca9b82343c3",
    "IBMPlexSans-Regular.woff2": "ba711a3085ff9f27440b6b9c4550cfc47c97bf36591d5da958b975bb3add8c1a",
    "IBMPlexSans-SemiBold.woff2": "f78048030eab62e860efa39a0df79e2e5581bf122eb95b9bc42c0b8a4988d205",
}
OFL_SHA256 = "7e6b2818edbd8f6a01ae80641cc8f16a51080d08fb4e532be3a0b6f74adb07da"
# Validated on this background, all pairs, dark mode, with the dataviz skill's validate_palette.js (2026-10-10).
TACTIC_COLOURS = {"--bg": "#121212", "--engage": "#3987e5", "--kite": "#c98500", "--retreat": "#d55181", "--search": "#008300"}


class _Text(HTMLParser):
    """The text a visitor can see in the markup: everything outside <script> and <style>."""

    def __init__(self):
        super().__init__()
        self.skipping, self.texts = 0, []

    def handle_starttag(self, tag, attrs):
        self.skipping += tag in ("script", "style")

    def handle_endtag(self, tag):
        self.skipping -= tag in ("script", "style")

    def handle_data(self, data):
        if not self.skipping and data.strip():
            self.texts.append(data.strip())


def _flatten(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _flatten(item)
    elif isinstance(value, list):
        for item in value:
            yield from _flatten(item)


def string_problems(strings) -> list[str]:
    found = []
    for text in strings:
        if "!" in text:
            found.append(f"an exclamation mark in {text!r}")
        if PICTOGRAPHIC.search(text):
            found.append(f"an emoji or pictograph in {text!r}")
        found += [f"the marketing word {word!r} in {text!r}" for word in MARKETING if word in text.lower()]
    return found


def _rule(css: str, selector: str) -> str:
    match = re.search(r"(?:^|\})\s*" + re.escape(selector) + r"\s*\{([^}]*)\}", css)
    return match.group(1) if match else ""


def _px(body: str, prop: str) -> int | None:
    match = re.search(rf"(?<![\w-]){prop}:\s*(\d+)px", body)
    return int(match.group(1)) if match else None


def problems(html: str) -> list[str]:
    """What is wrong with the page for the design rules. An empty list means nothing is."""
    found = []
    style = "\n".join(re.findall(r"<style>(.*?)</style>", html, re.S))
    root = re.search(r":root\s*\{(.*?)\}", style, re.S)
    css = re.sub(r"/\*.*?\*/", "", style.replace(root.group(0), "") if root else style, flags=re.S)

    if PICTOGRAPHIC.search(html):
        found.append("an emoji or pictograph")
    for token in ("gradient(", "box-shadow", "text-shadow", "blur(", "backdrop-filter", "@keyframes", "animation", "@import", "filter:"):
        if token in css:
            found.append(f"{token} in the style")
    for value in re.findall(r"transition:\s*([^;]+);", css):
        for number, unit in re.findall(r"(\d+(?:\.\d+)?)(ms|s)\b", value):
            if float(number) * (1000 if unit == "s" else 1) > 200:
                found.append(f"a transition of {number}{unit}, over 200 ms")
    for value in re.findall(r"font-family:\s*([^;]+);", css):
        for family in (name.strip().strip("\"'").lower() for name in value.split(",")):
            if family not in ALLOWED_FAMILIES:
                found.append(f"the font family {family!r}, not one of the bundled ones")
    if re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", css):
        found.append("a colour literal outside :root")
    for _, value in re.findall(r"([\w-]+)\s*:\s*([^;{}]+);", css):
        for word in re.findall(r"[a-z]+", value.lower()):
            if word in NAMED_COLOURS:
                found.append(f"the named colour {word!r} outside :root")
    defined = set(re.findall(r"(--[\w-]+)\s*:", style))
    found += [f"var({name}) is not defined" for name in sorted(set(re.findall(r"var\((--[\w-]+)\)", style)) - defined)]

    if re.search(r"https?:|//[\w.-]+\.\w|<link|<img|<iframe|<script[^>]*\ssrc=", html):
        found.append("an external or extra resource")
    for target in re.findall(r"url\(\s*[\"']?([^\"')]+)", css):
        if target not in {f"/fonts/{name}" for name in view.FONT_FILES}:
            found.append(f"url({target}) is not a bundled font")

    sizes = [int(size) for size in re.findall(r"font-size:\s*(\d+)px", css)]
    if sizes and min(sizes) < MIN_TEXT_PX:
        found.append(f"text under {MIN_TEXT_PX} px ({min(sizes)} px)")
    if (_px(_rule(css, ".tactic"), "font-size") or 0) < MIN_TACTIC_PX:
        found.append(f".tactic under {MIN_TACTIC_PX} px")
    if (_px(_rule(css, ".card .row"), "font-size") or 0) < MIN_CARD_ROW_PX:
        found.append(f".card .row under {MIN_CARD_ROW_PX} px")

    text_block = re.search(r'<script type="application/json" id="text">(.*?)</script>', html, re.S)
    if text_block is None:
        found.append("no TEXT table")
    else:
        text = json.loads(text_block.group(1))
        found += string_problems(_flatten(text))
        if set(text.get("tactics", {})) != set(TACTICS):
            found.append("the tactics of the TEXT table are not the agent's")
    visible = _Text()
    visible.feed(html)
    found += string_problems(visible.texts)

    listed = re.search(r"const TACTICS = \[(.*?)\];", html)
    if listed is None or tuple(re.findall(r'"(\w+)"', listed.group(1))) != TACTICS:
        found.append("the page's TACTICS are not the agent's, in the agent's order")
    ids = set(re.findall(r'\sid="([\w-]+)"', html))
    found += [f"the script asks for the element {name!r}, which is not in the page"
              for name in sorted(set(re.findall(r'\$\("([\w-]+)"\)', html)) - ids)]
    return found


# --- the page that is in the repository ---------------------------------------------------------------------------------


def test_the_page_follows_the_design_rules():
    assert problems(PAGE) == []


def test_the_conclusion_card_follows_the_same_rules_on_its_words():
    assert string_problems(_flatten(json.loads(view.CONCLUSION_PATH.read_text()))) == []


def test_the_game_corner_is_left_empty():
    css = re.sub(r"/\*.*?\*/", "", "\n".join(re.findall(r"<style>(.*?)</style>", PAGE, re.S)), flags=re.S)
    panel, bottom, stage = _rule(css, ".panel"), _rule(css, ".bottom"), _rule(css, ".stage")

    assert (_px(stage, "width"), _px(stage, "height")) == (1920, 1080)
    assert _px(panel, "left") >= 1280 and _px(panel, "left") + _px(panel, "width") == 1920 and _px(panel, "height") == 720
    assert _px(bottom, "top") >= 720 and _px(bottom, "top") + _px(bottom, "height") == 1080 and _px(bottom, "width") == 1920


def test_the_four_tactic_colours_are_the_validated_ones():
    root = re.search(r":root\s*\{(.*?)\}", PAGE, re.S).group(1)
    found = dict(re.findall(r"(--[\w-]+):\s*(#[0-9a-fA-F]{6})", root))
    assert {name: found[name].lower() for name in TACTIC_COLOURS} == TACTIC_COLOURS


@pytest.mark.parametrize("name, digest", sorted(FONT_SHA256.items()))
def test_each_font_is_the_file_that_was_downloaded_from_the_ibm_release(name, digest):
    assert hashlib.sha256((view.PAGE_DIR / "fonts" / name).read_bytes()).hexdigest() == digest


def test_the_license_of_the_fonts_travels_with_them():
    license_text = (view.PAGE_DIR / "fonts" / "OFL.txt").read_bytes()
    assert hashlib.sha256(license_text).hexdigest() == OFL_SHA256
    assert b"SIL Open Font License" in license_text and set(view.FONT_FILES) == set(FONT_SHA256)


def test_every_font_face_points_to_a_file_that_is_there():
    targets = re.findall(r'src:\s*url\("/fonts/([\w.-]+)"\)', PAGE)
    assert sorted(targets) == sorted(FONT_SHA256) and all((view.PAGE_DIR / "fonts" / name).is_file() for name in targets)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed here")
def test_the_script_of_the_page_has_no_syntax_error(tmp_path):
    script = re.findall(r"<script>(.*?)</script>", PAGE, re.S)[-1]
    (tmp_path / "page.js").write_text(script)

    result = subprocess.run(["node", "--check", str(tmp_path / "page.js")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


# --- the check can fail: one wrong thing at a time --------------------------------------------------------------------------


BREAKS = [
    ("an emoji in a text", '"waiting": "waiting for a game"', '"waiting": "waiting for a game \U0001f642"', "emoji"),
    ("a star in a text", '"waiting": "waiting for a game"', '"waiting": "★ waiting for a game"', "emoji"),
    ("a gradient", ".card.on { opacity: 1; }", ".card.on { opacity: 1; background: linear-gradient(var(--bg), var(--rule)); }", "gradient("),
    ("a shadow", ".seg, .fill { background: var(--c); }", ".seg, .fill { background: var(--c); box-shadow: 0 0 8px var(--c); }", "box-shadow"),
    ("a text shadow", ".hidden { display: none; }", ".hidden { display: none; text-shadow: 0 0 4px var(--fg); }", "text-shadow"),
    ("a blur", ".hidden { display: none; }", ".hidden { display: none; filter: blur(4px); }", "blur("),
    ("a glass panel", ".hidden { display: none; }", ".hidden { display: none; backdrop-filter: blur(8px); }", "backdrop-filter"),
    ("a keyframes animation", ".hidden { display: none; }", "@keyframes pulse { to { opacity: 0.5; } }\n.hidden { display: none; }", "@keyframes"),
    ("an animation property", ".hidden { display: none; }", ".hidden { display: none; animation: pulse 1s infinite; }", "animation"),
    ("a slow transition", "transition: width 150ms linear;", "transition: width 400ms linear;", "over 200 ms"),
    ("a slow transition in seconds", "transition: opacity 200ms linear;", "transition: opacity 1s linear;", "over 200 ms"),
    ("another font", "font-family: \"Plex Mono\", monospace; font-weight: 600; font-size: 112px;",
     "font-family: Inter, sans-serif; font-weight: 600; font-size: 112px;", "font family"),
    ("a hex colour outside :root", ".prob.chosen { color: var(--fg); }", ".prob.chosen { color: #ffffff; }", "colour literal"),
    ("an rgb colour outside :root", ".prob.chosen { color: var(--fg); }", ".prob.chosen { color: rgb(255, 0, 0); }", "colour literal"),
    ("a named colour", ".prob.chosen { color: var(--fg); }", ".prob.chosen { color: white; }", "named colour"),
    ("a variable that does not exist", ".prob.chosen { color: var(--fg); }", ".prob.chosen { color: var(--fgg); }", "--fgg"),
    ("an external stylesheet", "<title>Jev plays cub3D</title>", '<title>Jev plays cub3D</title><link rel="stylesheet" href="x.css">', "external or extra"),
    ("an external address", "<title>Jev plays cub3D</title>", "<title>Jev plays cub3D (https://example.org)</title>", "external or extra"),
    ("an image", "<title>Jev plays cub3D</title>", '<title>Jev plays cub3D</title><img src="/logo.png">', "external or extra"),
    ("a font that is not bundled", 'url("/fonts/IBMPlexSans-Regular.woff2")', 'url("/other/x.woff2")', "not a bundled font"),
    ("small text", "font-size: 28px; line-height: 44px; padding-left: 10px;", "font-size: 20px; line-height: 44px; padding-left: 10px;", "text under 28"),
    ("a small tactic name", "font-size: 112px; line-height: 128px;", "font-size: 80px; line-height: 128px;", ".tactic under"),
    ("small card lines", "font-size: 64px; line-height: 84px;", "font-size: 48px; line-height: 84px;", ".card .row under"),
    ("an exclamation mark", '"waiting": "waiting for a game"', '"waiting": "waiting for a game!"', "exclamation"),
    ("a marketing word", "The code aims, fires and walks.\",\n    \"scripted\"", "The code aims, fires and walks, seamless.\",\n    \"scripted\"", "marketing"),
    ("text in the markup", '<div class="does" id="does"></div>', '<div class="does" id="does"></div><p>Amazing results!</p>', "exclamation"),
    ("a tactic missing from the page", 'const TACTICS = ["ENGAGE", "KITE", "RETREAT", "SEARCH"];', 'const TACTICS = ["ENGAGE", "KITE", "RETREAT"];', "TACTICS"),
    ("a tactic in another order", 'const TACTICS = ["ENGAGE", "KITE", "RETREAT", "SEARCH"];', 'const TACTICS = ["KITE", "ENGAGE", "RETREAT", "SEARCH"];', "TACTICS"),
    ("a tactic with no description", '    "SEARCH": "walk to the nearest zombie"', '    "SEARC": "walk to the nearest zombie"', "tactics of the TEXT"),
    ("an element the script cannot find", '$("does")', '$("doess")', "doess"),
    ("no TEXT table", '<script type="application/json" id="text">', '<script type="application/x" id="text">', "no TEXT table"),
]


@pytest.mark.parametrize("name, old, new, expected", BREAKS, ids=[item[0] for item in BREAKS])
def test_the_check_catches_it(name, old, new, expected):
    assert PAGE.count(old) == 1, f"the break {name!r} does not find its place in the page"

    found = problems(PAGE.replace(old, new))

    assert any(expected in problem for problem in found), found


def test_a_conclusion_with_an_exclamation_mark_or_a_marketing_word_is_refused():
    assert string_problems(["Jev won 40 of 40 games!"]) and string_problems(["A seamless result"]) and string_problems(["\U0001f525 fast"])
    assert string_problems(["Jev won 40 of 40 games."]) == []
