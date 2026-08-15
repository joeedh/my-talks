#!/usr/bin/env python3
"""Build a talk deck: markdown -> reveal.js HTML (and optionally PDF).

    python build.py                          build the default talk
    python build.py --serve                  build, then serve on :8080
    python build.py --pdf                    also emit a PDF via headless Chrome
    python build.py --standalone             single self-contained .html for handoff
    python build.py --site                   every talk + an index, for GitHub Pages
    python build.py --talk 2027/03-somewhere --theme white
"""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import re
import shutil
import socketserver
import subprocess
import tempfile
import sys
import webbrowser
from html import escape
from pathlib import Path
from urllib.request import pathname2url

ROOT = Path(__file__).resolve().parent


class BuildError(Exception):
    pass


def say(msg: str, colour: str = "") -> None:
    codes = {"cyan": "36", "green": "32", "yellow": "33", "red": "31", "grey": "90"}
    if colour and sys.stdout.isatty():
        print(f"\033[{codes[colour]}m{msg}\033[0m")
    else:
        print(msg)


# ---------------------------------------------------------------- preflight
def ensure_reveal() -> Path:
    """reveal.js is a devDependency; install it on first run."""
    reveal = ROOT / "node_modules" / "reveal.js"
    if reveal.is_dir():
        return reveal

    say("reveal.js not vendored yet - installing...", "yellow")
    pm = shutil.which("pnpm") or shutil.which("npm")
    if not pm:
        raise BuildError("neither pnpm nor npm found on PATH")
    subprocess.run([pm, "install"], cwd=ROOT, check=True, shell=False)

    if not reveal.is_dir():
        raise BuildError(f"install did not produce {reveal}")
    return reveal


# ---------------------------------------------------------------- build
def build_html(args: argparse.Namespace, reveal: Path, talk: str) -> Path:
    src = ROOT / talk / args.deck
    if not src.is_file():
        raise BuildError(f"no such deck: {src}")

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)

    out = dist / f"{slug_of(talk)}.html"

    cmd = [
        "pandoc",
        str(src),
        "--to=revealjs",
        "--standalone",
        f"--slide-level={args.slide_level}",
        f"--syntax-highlighting={args.highlight}",
        f"--resource-path={ROOT / talk}",
        f"--variable=theme:{args.theme}",
        "--variable=transition:none",
        "--variable=controls:true",
        "--variable=progress:true",
        "--variable=hash:true",
        "--variable=history:true",
        "--variable=width:1280",
        "--variable=height:800",
        "--variable=margin:0.06",
        f"--include-after-body={ROOT / 'reveal-after.html'}",
        f"--output={out}",
    ]

    if args.standalone:
        # inline every asset so the deck is a single portable file
        cmd += ["--embed-resources", f"--variable=revealjs-url:{reveal}"]
    elif args.site:
        # the runtime is copied in beside the decks; see copy_reveal_runtime
        cmd += ["--variable=revealjs-url:reveal.js"]
    else:
        # resolved by the browser, relative to dist/
        cmd += ["--variable=revealjs-url:../node_modules/reveal.js"]

    say(f"pandoc {talk}/{args.deck} -> dist/{out.name}", "cyan")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    if proc.returncode != 0:
        raise BuildError(f"pandoc failed ({proc.returncode})")

    html = out.read_text(encoding="utf-8")
    say(f"  ok - {len(re.findall(r'<section', html))} sections", "green")
    warn_on_blank_slides(html)
    return out


def warn_on_blank_slides(html: str) -> None:
    """A section with a heading but no body is almost always an authoring slip."""
    body = html[html.find('<div class="slides">') :]
    blank = 0
    for chunk in re.split(r"(?=<section)", body)[1:]:
        chunk = chunk.split("<section", 1)[0]
        if re.search(r"<h[1-4]", chunk) and not re.sub(r"<[^>]+>", "", chunk).strip():
            blank += 1
    if blank:
        say(f"  warning: {blank} slide(s) render empty", "yellow")


# ---------------------------------------------------------------- site
def slug_of(talk: str) -> str:
    return talk.replace("\\", "-").replace("/", "-")


def discover_talks(deck: str) -> list[str]:
    """A <year>/<month-slug>/ directory holding a deck file is a talk.
    Newest first, which is the order the index wants."""
    found = [p.parent.relative_to(ROOT).as_posix() for p in ROOT.glob(f"[0-9][0-9][0-9][0-9]/*/{deck}")]
    return sorted(found, reverse=True)


def deck_meta(src: Path) -> dict[str, str]:
    """Just enough YAML for the index: top-level `key: value` in the frontmatter."""
    text = src.read_text(encoding="utf-8")
    m = re.match(r"---\s*\n(.*?)\n---\s*\n", text, re.S)
    meta: dict[str, str] = {}
    if m:
        for line in m.group(1).splitlines():
            if line[:1].isspace() or ":" not in line:
                continue
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip("\"'")
    return meta


def copy_reveal_runtime(reveal: Path) -> None:
    """One shared copy of reveal beside the decks, rather than --standalone's
    inlined copy per deck."""
    dest = ROOT / "dist" / "reveal.js"
    dest.mkdir(parents=True, exist_ok=True)
    for part in ("dist", "plugin"):  # everything pandoc's template references
        shutil.copytree(reveal / part, dest / part, dirs_exist_ok=True)
    say(f"  ok - dist/reveal.js ({sum(f.stat().st_size for f in dest.rglob('*') if f.is_file()) // 1024} KB)", "green")


INDEX_CSS = """
:root { color-scheme: dark }
body { margin: 0; padding: 4rem 1.5rem; background: #191919; color: #eee;
       font: 16px/1.6 -apple-system, "Segoe UI", system-ui, sans-serif; }
main { max-width: 46rem; margin: 0 auto }
h1 { font-weight: 600; letter-spacing: -.02em; margin: 0 0 .25rem }
.sub { color: #888; margin: 0 0 3rem }
.talk { padding: 1.25rem 0; border-top: 1px solid #333 }
.talk h2 { font-size: 1.15rem; font-weight: 600; margin: 0 0 .2rem }
.talk h2 a { color: #eee; text-decoration: none }
.talk h2 a:hover { color: #42affa }
.meta { color: #888; font-size: .9rem; margin: 0 0 .6rem }
.links a { color: #42affa; text-decoration: none; font-size: .9rem; margin-right: 1.25rem }
.links a:hover { text-decoration: underline }
"""


def write_index(built: list[tuple[str, Path, Path | None]], deck: str) -> Path:
    rows = []
    for talk, html, pdf in built:
        meta = deck_meta(ROOT / talk / deck)
        title = escape(meta.get("title") or talk)
        line = " · ".join(escape(meta[k]) for k in ("author", "date") if meta.get(k))
        links = [f'<a href="{html.name}">Slides</a>']
        if pdf:
            links.append(f'<a href="{pdf.name}">PDF</a>')
        rows.append(
            f'    <article class="talk">\n'
            f'      <h2><a href="{html.name}">{title}</a></h2>\n'
            f'      <p class="meta">{line}</p>\n'
            f'      <p class="links">{"".join(links)}</p>\n'
            f"    </article>"
        )

    out = ROOT / "dist" / "index.html"
    out.write_text(
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Talks</title>\n"
        f"<style>{INDEX_CSS}</style>\n</head>\n<body>\n  <main>\n"
        "    <h1>Talks</h1>\n"
        '    <p class="sub">Slide decks. Press <b>S</b> in a deck for speaker notes, '
        "<b>Esc</b> for the overview.</p>\n" + "\n".join(rows) + "\n  </main>\n</body>\n</html>\n",
        encoding="utf-8",
    )
    say(f"  ok - dist/index.html ({len(built)} talk(s))", "green")
    return out


# ---------------------------------------------------------------- pdf
CHROME_CANDIDATES = (
    r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
    r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
    r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
)


def find_chrome() -> str | None:
    for pat in CHROME_CANDIDATES:
        p = Path(os.path.expandvars(pat))
        if p.is_file():
            return str(p)
    for name in ("chrome", "google-chrome", "chromium", "msedge"):
        if (found := shutil.which(name)):
            return found
    return None


def build_pdf(html: Path) -> Path | None:
    chrome = find_chrome()
    if not chrome:
        say("  warning: Chrome not found; skipping PDF", "yellow")
        return None

    pdf = html.with_suffix(".pdf")
    uri = "file:" + pathname2url(str(html)) + "?print-pdf"

    say(f"chrome --headless -> dist/{pdf.name}", "cyan")
    with tempfile.TemporaryDirectory(prefix="talks-chrome-") as profile:
        subprocess.run(
            [
                chrome,
                "--headless=new",
                # --headless=new reuses the REAL profile by default, and a stale
                # file:// cache entry silently yields a one-page blank PDF. Always
                # print from a throwaway profile.
                f"--user-data-dir={profile}",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-extensions",
                # the file:// origin has to reach node_modules/reveal.js
                "--allow-file-access-from-files",
                # must match the deck's width/height, or reveal's print layout
                # collapses to a single blank page
                "--window-size=1280,800",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=60000",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}",
                uri,
            ],
            capture_output=True,
            text=True,
        )

    if not pdf.is_file():
        say("  warning: no PDF produced - open the deck with ?print-pdf and Ctrl-P", "yellow")
        return None

    data = pdf.read_bytes()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", data))
    if pages <= 1:
        say(f"  warning: PDF is {pages} page(s) - reveal's print layout did not apply", "yellow")
        return None

    say(f"  ok - dist/{pdf.name} ({len(data) // 1024} KB, {pages} pages)", "green")
    return pdf


# ---------------------------------------------------------------- serve
def serve(html: Path, port: int) -> None:
    """file:// works for a quick look, but the speaker-notes window (press S)
    needs a real origin. Serve the repo root so ../node_modules resolves."""
    url = f"http://localhost:{port}/dist/{html.name}"
    print()
    say(f"  {url}", "green")
    say("  S = speaker view + timer  |  ESC = overview  |  Ctrl-C to stop", "grey")
    print()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass  # a request log per asset is just noise while presenting

    handler = functools.partial(Handler, directory=str(ROOT))

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    webbrowser.open(url)
    with Server(("", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()


# ---------------------------------------------------------------- cli
def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--talk", default="2026/09-codium-consortium")
    p.add_argument("--deck", default="final-talk.md")
    p.add_argument("--theme", default="black", help="reveal theme (black, white, league, ...)")
    p.add_argument("--highlight", default="breezedark", help="pandoc syntax highlighting style")
    p.add_argument("--slide-level", type=int, default=4)
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--pdf", action="store_true", help="also emit a PDF")
    p.add_argument("--standalone", action="store_true", help="inline all assets into one file")
    p.add_argument("--site", action="store_true", help="build every talk plus an index (GitHub Pages)")
    p.add_argument("--serve", action="store_true", help="serve and open in a browser")
    args = p.parse_args()

    if not shutil.which("pandoc"):
        say("pandoc not found on PATH. https://pandoc.org/installing.html", "red")
        return 1

    if args.pdf and args.standalone:
        # reveal's print layout does not survive --embed-resources; the two
        # flags are for different handoffs anyway (one file vs. one PDF).
        say("--pdf and --standalone can't be combined; run them separately", "red")
        return 1

    try:
        reveal = ensure_reveal()

        talks = discover_talks(args.deck) if args.site else [args.talk]
        if not talks:
            raise BuildError(f"no talks found - looked for <year>/*/{args.deck}")

        # before the decks, not after: a --site deck loads reveal from
        # dist/reveal.js, and --pdf renders the deck as it stands on disk
        if args.site and not args.standalone:
            copy_reveal_runtime(reveal)

        built = []
        for talk in talks:
            html = build_html(args, reveal, talk)
            built.append((talk, html, build_pdf(html) if args.pdf else None))

        landing = write_index(built, args.deck) if args.site else built[-1][1]

        if args.serve:
            serve(landing, args.port)
    except BuildError as e:
        say(str(e), "red")
        return 1
    except subprocess.CalledProcessError as e:
        say(f"command failed: {e}", "red")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
