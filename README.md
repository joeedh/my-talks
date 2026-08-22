# talks

Talk slideshows. Markdown in, reveal.js out, via pandoc.

Published site: https://joeedh.github.io/my-talks/

```
python build.py --serve         # build + open at localhost:8080
python build.py --pdf           # also emit dist/<talk>.pdf
python build.py --standalone    # one self-contained .html to hand to organizers
python build.py --site --pdf    # every talk + an index, i.e. what CI publishes
python build.py --talk 2027/03-somewhere --theme white
```

First run installs `reveal.js` into `node_modules/` automatically. Requires
pandoc on PATH; PDF export additionally requires Chrome.

Pushing to master publishes the site to GitHub Pages
(`.github/workflows/pages.yml`). Every `<year>/*/` directory containing a
`final-talk.md` is picked up automatically.

## Slide model

**Every `###` / `####` header starts a new slide.** `##` is an act divider.
Pandoc's `--slide-level=4` does this natively — there are no explicit slide
separators to maintain.

Nothing auto-paginates, so a section with more content than fits one slide is
continued with a `(cont.)` header:

```markdown
#### Code Comment Rules

...first slide's worth...

#### Code Comment Rules (cont.)

...the rest...
```

## Speaker notes

Prose that should be spoken but not projected goes in a `notes` div. Press
**S** during the talk for the speaker window (notes, timer, next slide):

```markdown
### Some Slide

* terse bullet
* another one

::: notes
The full paragraph you actually say out loud goes here.
:::
```

The speaker window needs a real origin, so present via `--serve`, not `file://`.

## Gotchas

- `* [User]: some text` is a **link reference definition** in CommonMark and
  silently renders as an empty bullet. Use `* **User:** some text`.
- Metadata (title/author/date) is the YAML block at the top of the deck file;
  it becomes the title slide. Keep freeform prep notes and TODOs in an HTML
  comment at the *bottom* of the deck instead — YAML rejects things like
  `[ ]: todo`, and anything between the YAML block and the first header
  renders as a blank slide.
- Pandoc turns each `##` act into a vertical stack, so `reveal-after.html`
  sets `navigationMode: 'linear'` to keep the arrow keys walking every slide.

## Layout

```
build.py                      the build
reveal-after.html             reveal config pandoc's template won't forward
.github/workflows/pages.yml   build + deploy to GitHub Pages
2026/09-codium-consortium/
  final-talk.md               the deck
  ai-swe-talk-notes.md        earlier draft, kept for source material
dist/                         build output (gitignored)
```
