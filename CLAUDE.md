# CLAUDE.md

Repo of talk slideshows. Each talk is a single markdown file; `build.py` turns
it into a reveal.js deck.

## The pipeline

```
2026/09-codium-consortium/final-talk.md
      |  pandoc --to=revealjs --slide-level=4
      v
dist/2026-09-codium-consortium.html   +  ../node_modules/reveal.js  (runtime, vendored by pnpm)
      |  headless Chrome ?print-pdf --print-to-pdf
      v
dist/2026-09-codium-consortium.pdf
```

There is no intermediate format and no per-slide files. `build.py` shells out to
pandoc once, optionally to Chrome once, and that is the whole build.

```
python build.py                 build dist/<slug>.html
python build.py --serve         build, serve repo root on :8080, open browser
python build.py --pdf           also emit dist/<slug>.pdf
python build.py --standalone    inline every asset into one portable .html
python build.py --site --pdf    every talk + index.html, exactly what CI publishes
python build.py --talk 2027/03-somewhere --theme black --slide-level 4
```

Requires `pandoc` on PATH. First run installs `reveal.js` into `node_modules/`
via pnpm (falls back to npm). PDF export additionally requires Chrome.

`--pdf` and `--standalone` are mutually exclusive and `build.py` rejects the
combination — `--embed-resources` breaks reveal's print layout, and the two
flags serve different handoffs anyway (one PDF vs. one HTML file).

## Slide model

**Every `###` and `####` header starts a new slide.** That is `--slide-level=4`
doing its job; there are no `---` separators to maintain. `##` is an act
divider and gets its own title slide.

Nothing auto-paginates. A section with more content than fits 1280x800 is split
by hand with a `(cont.)` header:

```markdown
#### Code Comment Rules

...first slide's worth...

#### Code Comment Rules (cont.)

...the rest...
```

Speaker notes go in a `::: notes` div (press **S** during the talk). The
speaker window needs a real origin, so present via `--serve`, not `file://`.

## Publishing (GitHub Pages)

`.github/workflows/pages.yml` runs `python build.py --site --pdf` on every push
to master and uploads `dist/` as the Pages artifact. Pages source is already set
to GitHub Actions, so there is no `gh-pages` branch and nothing to commit.

`--site` differs from a normal build in three ways:

- it builds **every** talk it discovers — any `<year>/*/` directory holding a
  `final-talk.md`. Adding a talk needs no workflow or `build.py` change.
- reveal is copied once to `dist/reveal.js/` and the decks point at it, instead
  of `../node_modules/` (outside the artifact) or `--standalone`'s inlined copy
  per deck. **The copy happens before the decks are built**, because `--pdf`
  renders the deck as it stands on disk — get the order wrong and Chrome prints
  an unstyled 7-page dump instead of the 41-page deck.
- it writes `dist/index.html`, a listing whose titles and dates come from each
  deck's YAML frontmatter.

CI pins pandoc to the same release as local (`3.9.0.2`); apt's is old enough to
reject `--syntax-highlighting`. Chrome comes from the runner image — if it ever
goes missing the site still builds, just without PDFs.

## Files

```
.github/workflows/pages.yml   build + deploy to GitHub Pages
build.py              the whole build; argparse CLI, no config file
reveal-after.html     reveal config + print fixes, injected via --include-after-body
syntax/*.xml          extra skylighting language definitions, auto-loaded
filters/inline-cpp.lua  highlights single-backtick spans as C++
package.json          pins reveal.js; npm scripts just call build.py
2026/09-codium-consortium/
  final-talk.md       the deck (YAML frontmatter -> title slide)
  ai-swe-talk-notes.md  earlier evidence-dense draft, kept as source material
dist/                 build output (gitignored)
```

## reveal-after.html

Pandoc's reveal template only forwards a fixed allowlist of options, so
anything else has to be applied after `Reveal.initialize()`. Two distinct jobs,
branched on `?print-pdf`:

- **Presenting:** `navigationMode: 'linear'`. Pandoc turns each `##` act into a
  reveal *vertical stack*, so without this the arrow keys jump act-to-act and
  skip their contents. Also sets `slideNumber: 'c/t'`.
- **Printing:** `requestAnimationFrame` is redirected onto `setTimeout`, and the
  `Reveal.configure()` call above is skipped entirely. Both are load-bearing —
  see below.
- **Appearance:** the palette and type overrides live here too, in a `<style>`
  block, because pandoc's reveal template forwards only `theme` and won't carry
  arbitrary CSS.

## Look and feel

The deck is `--theme white` (reveal's, self-hosting Source Sans Pro) with the
palette and fonts overridden in `reveal-after.html`:

- **Paper, not a lightbox.** `#faf8f5` ground with `#33383d` ink, ~11:1. Reveal's
  own white theme pairs `#fff` with `#222`, which is close to as harsh as the
  white-on-black it replaced. Pure black on pure white is 21:1 and glares.
- **System font stack** — Segoe UI Variable / Segoe UI / `-apple-system` /
  `system-ui` for prose, and `ui-monospace` / Cascadia Code / SF Mono / Consolas
  for code. Nothing is downloaded, so nothing degrades when presenting offline.
  The tradeoff is that a Mac podium renders a different face than your laptop.
- **`--highlight` must stay a light style** (`tango`, `pygments`, `kate`) to match.
  `breezedark` is a dark syntax theme and is unreadable on this ground.
- The title slide keeps its dark cover art (`data-background-color` in the deck's
  frontmatter) — that is deliberate, not a leftover from the dark theme.

Only reveal's `white`, `white-contrast`, `black`, `black-contrast` and `serif`
themes work offline. **`simple`, `solarized`, `beige` and `sky` `@import` Lato and
friends from Google Fonts** and silently fall back to a system face with no
network — exactly the condition you present in. Don't reach for them.

## Syntax highlighting

Fenced blocks are highlighted by pandoc/skylighting (`--syntax-highlighting`,
default `tango`). ```` ```ts ````, ```` ```cpp ````, ```` ```python ```` and
anything else `pandoc --list-highlight-languages` lists just work.

For a language skylighting doesn't ship, drop a KDE-format definition in
`syntax/`. `build.py` passes every `syntax/*.xml` as `--syntax-definition`, so a
new language needs no code change. `syntax/hlsl.xml` is the worked example — it
also carries the SBrush DSL's own keywords (`brush`, `ctx`, `vertex`, `@brush`).

**Inline single-backtick spans are lexed as C++** by `filters/inline-cpp.lua`,
which pandoc otherwise leaves as plain text. It renders each span through
skylighting and splices the token markup back in, so inline and fenced code share
one theme and it survives `--pdf` and `--standalone` with no client-side JS.

Give a span any class to opt out or pick another language:

```markdown
`claude --resume`{.text}      plain
`x = 1`{.python}              highlighted as python
```

Reach for `{.text}` whenever C++ lexing misreads something — `-fdelayed-template-parsing`
colors `template` as a keyword, and a `'...'` inside a span reads as an unterminated
char literal.

## Gotchas (each one cost real debugging time)

- **`* [User]: text` is a link reference definition** in CommonMark and renders
  as an empty bullet — silent content loss. Write `* **User:** text`. This is a
  markdown-level trap, not a pandoc one; every markdown deck tool has it.
- **Nothing goes between the YAML block and the first header.** It becomes a
  blank slide. And YAML rejects freeform text like `[ ]: todo` ("Non-string keys
  are not supported"). Prep notes and TODOs therefore live in an HTML comment at
  the *bottom* of the deck file, where nothing parses them.
- **`Reveal.configure()` breaks PDF export.** It re-evaluates the view mode and
  drops the deck back out of the print layout, leaving `loading-scroll-mode` on
  the body and printing one blank page.
- **Headless Chrome stalls reveal's print setup.** `Print.activate()` sequences
  itself with `await new Promise(requestAnimationFrame)`; under
  `--virtual-time-budget` those frames may never arrive, so activation hangs
  with every slide still hidden. Timers *are* driven by virtual time, hence the
  rAF-to-setTimeout shim. Symptom to recognize: a 1079-byte, 1-page PDF.
- **Print from a throwaway `--user-data-dir`.** `--headless=new` reuses the real
  Chrome profile by default.
- **`--window-size` must match the deck's width/height** (1280x800), or reveal's
  print layout collapses.
- **Pandoc only emits the highlighting stylesheet when the AST holds a highlighted
  *block*.** A deck with inline code and no fences would get colorless spans, so
  `inline-cpp.lua` appends a hidden empty `cpp` block in that case. It has to be a
  real `CodeBlock` — a `RawBlock` of pre-rendered HTML does not trigger it.
- **Framing `div.sourceCode` *and* `pre` draws a box inside a box.** Pandoc wraps
  every highlighted block in `div.sourceCode > pre.sourceCode`, so the background
  and border belong on the wrapper only — `pre:not(.sourceCode)` catches the
  unhighlighted ones.
- `build.py` warns on slides that render with a heading and no body — usually an
  authoring slip like the one above, worth investigating rather than ignoring.

## Verifying a change

`python build.py` prints the section count (currently 62) and any blank-slide
warnings. For PDF changes check page count, not just exit status:
`python build.py --pdf` should report ~59 pages / ~2.9 MB. A 1-page PDF means
the print layout silently failed. (The deck was ~185 KB before the cover image
went in; the bulk is that one JPEG.)

For highlighting changes, check the emitted classes rather than eyeballing:

```
grep -o 'class="sourceCode[^"]*"' dist/2026-09-codium-consortium.html | sort | uniq -c
```

A bare `class="sourceCode"` on a `<pre>` means the language was not recognized
and the block rendered unstyled.
