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
python build.py --talk 2027/03-somewhere --theme white --slide-level 4
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
- `build.py` warns on slides that render with a heading and no body — usually an
  authoring slip like the one above, worth investigating rather than ignoring.

## Verifying a change

`python build.py` prints the section count (currently 43) and any blank-slide
warnings. For PDF changes check page count, not just exit status:
`python build.py --pdf` should report ~41 pages / ~185 KB. A 1-page PDF means
the print layout silently failed.
