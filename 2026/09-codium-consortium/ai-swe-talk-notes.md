# Software Engineering With AI — Talk Notes

**~45 min · mixed technical audience · 18 slides**

Sourced from real artifacts in `path.ux` / `fairmotion` / `mathl` / `noise_fractal_stuff` /
`pigment-painter` / `sculptcore` / `webgl-app-framework`.
📄 = file:line source exists. ⚠️ = needs your confirmation.

**Proposed thesis** (cut or replace):
> AI didn't change what makes engineering hard. It changed the *price* of the artifacts
> that manage that hardness — specs, gates, measurement harnesses. Things that used to be
> overhead you skipped are now the highest-leverage thing you write.

---

### 1. Title / the six cases
- Software Engineering With AI — six case studies from my own codebases
- A 3D sculpting engine (C++20 → WASM + native), a UI toolkit, an animation program, three others
- **Ports** · **Templates** · **Spec** · **Research** · **Context** · **Guardrails**
- Everything here is on disk and greppable. The failures are in the same docs as the wins.

---

## ACT 1 — THE PORTS (4 slides, ~11 min)
*Theme: the apparatus scales with coupling, not with the word "port"*

### 2. Five ports and a control group
| repo | size | port | apparatus | when |
|---|---|---|---|---|
| **mathl** | 10.4k TS + 2.5k JS left | ~80%, stalled | none — 2 commits, 4.5 hrs | May 20 |
| **path.ux** | 44.2k lines | complete | `.port-scratch/` — 1,074 lines of survey | May–Jun |
| **noise_fractal** | 24.5k lines | complete, `strict` | **none** — one commit | May 31 |
| **fairmotion** | 88.6k lines | complete | phase plan + **843-line debugging log** | **Aug 2–10** |
| **pigment-painter** | 34.9k lines JS | **never touched** | none | dormant since Apr |

- Same author, same stack, same decade. **Ceremony didn't track size — it tracked coupling.**
- noise_fractal: a leaf app, nothing downstream → complete `strict` port, one commit, no ladder
- **mathl stalled at 80%** and it's an island — no submodules, nothing downstream. Nothing forced it to finish. 📄 Its own `CLAUDE.md` calls the still-`.js` 1,118-line lexer a "legacy stub re-export." The doc rotted in 3 months.
- pigment-painter is an accidental control: same stack, comparable size, dormant since two months before any of this
- **Cost:** path.ux ran **~$400** metered, most of it before the porting workflow existed and much of it producing garbage. fairmotion — twice the size — was flat-rate. ⚠️ *Not comparable numbers; say so before someone asks.*

### 3. path.ux: make the survey a committed artifact
- 📄 `.port-scratch/` — `ARCHITECTURE.md` (556 lines: read the whole app before fixing anything), `ERROR_CATEGORIES.md` (9 categories A–I, by error code *and* root cause), `errors-raw.txt`
- Fix order written down and justified: mechanical first, **because it cascades**. 📄 *"Re-run typecheck after each batch; counts cascade down."*
- 📄 `tsconfig.json`: `allowJs: true, checkJs: false` — unported `.js` stays in the program but is never checked. **The build never has to be green all at once.**
- **The best moment: the error count went UP.** Checking against emitted `.d.ts` rather than library source; the declarations were degraded (`util` → `{}`), so the checker was silently under-reporting.
  - 📄 *"The earlier `.tmp-types/` emitted declarations were low quality … **and hid errors — do NOT use them.** Count rose 593→635 because real source types surfaced more genuine errors."*
  - **The number getting worse was the evidence the setup had gotten better.** 593 → 635 → 139 → 0.
- What came out of the pain: 📄 `.agents/workflows/refactor-js-to-ts.md`, a per-file recipe naming the traps — *"vectors do not have a simple string-to-number index signature beyond `LEN`"* (`v[i] = i` failing is **deliberate**, it stops Vector3/Vector4 mixing), every `UIBase` subclass MUST take a `CTX` generic, `tooldef()` must perfectly match the ToolOp generics. **None of that is inferable from the code. It's design intent, and it reads like a bug to be worked around.**

### 4. fairmotion: the interesting one — it wasn't JavaScript
- Written in a **non-standard dialect** compiled by my own PLY-based Python transpiler, with a custom lazy module loader. 266 C-style type annotations, `static` locals in method bodies, `global x;` declarations.
- 📄 *"extjs_cc has no `async`/`await` support at all… **The whole codebase is Promise-chain style because the transpiler forced it to be.**"*
- The transpiler dependency was never recorded — the legacy build **couldn't run on a clean machine**
- **Why it breaks the playbook:** `allowJs: true`, the gradual escape hatch, is unavailable when the `.js` doesn't parse as `.js`. Everything unusual follows from that one fact.
- 📄 So: **annotate blind.** *"**Do not run the typechecker in this phase.** Errors are expected and ignored. The goal is getting reasonable types down fast; **fighting the checker now produces defensive `any`s**."*
- Pass 1: 145 files, checker off. Pass 2: turn it on. **Peak 7,226 errors** → 0, ladder visible in the commit subjects. Final: **2 `any`** against a budget of 10.
- With no checker in pass 1, phase 6 built **four custom Python coherence checkers** as substitute oracles

### 5. A green typecheck is not a working app
- 📄 *"Nothing in tsgo catches a removed library global, a changed upstream API, a shader that fails to compile, or a 'behavior-preserving' refactor that wasn't."*
- The transpiler was **load-bearing at runtime**:
  - It emitted the class registry nstructjs deserialization needed. Nothing in the *source* ever filled it.
  - 📄 esbuild renames `class Foo` → `var Foo = class _Foo`, and *"**`cls.name` is part of the on-disk file format here**, so a bundler rename would silently change what files are written"*
  - Sloppy → strict mode: 📄 *"look for every sloppy-mode silent no-op, **because renaming to `.ts` turned all of them into throws**"*
- 📄 **193 latent bugs surfaced and recorded, not fixed.** A tool-argument idiom that had never worked, in 20 places. A whole file wrapped in backticks — inert, never declared anything.
- 📄 And: v0.052 wrote **zeros for every vector field**. *"The geometry in those six example files was **destroyed at save time**. Nobody noticed because the screen-layout bug above made the same files open to a blank window."* Two recovered from 2015/2017 blobs. **Four are gone.**
- **So verify with something that has no memory of doing the work:** 📄 path.ux ran a *fresh-context agent* over the finished port hunting fake zeros — found 5 hacks masking real gaps. fairmotion captured a full baseline oracle (927 datapaths, 17 Playwright tests, 11 screenshots) **before touching anything**. 📄 *"**Trust the baseline run over the claim.**"*

---

## ACT 2 — THE TEMPLATES (2 slides, ~5 min)
*Theme: AI is best where a human is slow but verification is cheap*

### 6. `litestl::binding`
- Hand-rolled C++20 reflection. One descriptor set, three consumers: TS type generator (**11,082 lines emitted**), WASM runtime, native N-API runtime (3,150 lines of C++)
- 📄 309 member bindings, 248 methods, 68 `defineBindings()` sites across 39 files
```cpp
BIND_STRUCT_CONSTRUCTOR(st, "main", SpatialTree *, Brush *);
BIND_STRUCT_METHOD(st, execBrush, MARGS("mesh","brushType","nodes","origin","normal"));
```
```ts
export interface SpatialTree {
  [Symbol.dispose](): void
  node_from_id(id: int32): SpatialNode | undefined
}
```

### 7. Why it worked — and the honest reason
- Genuinely hard: type-erased thunks `void(*)(void*, void**, void*)` where every parameter kind is read differently from a variadic pack; class templates with **string-literal NTTPs** reflected into TS generics (`BuiltinAttr<float3, '.face.normal'>`)
- 📄 The whole thing compiled only under `-fdelayed-template-parsing` — a clang MSVC-compat extension papering over two-phase lookup against an open overload set. The fix migrated ~124 call sites to a `Binder<T>::bind()` customization point.
- **The AI wrote the method and constructor binders. Best result in the talk.**
- **Why:** verification is nearly free. It compiles or it doesn't. And the refactor shipped behind a **zero-diff regeneration gate** — descriptors must regenerate byte-identical.
- **The pattern:** leverage is highest where the problem is tedious-hard and the check is mechanical. Lowest where the check is taste.
- Counterexample from the same work: node-addon-api's `CallbackInfo::Length()` returned `6e-310` garbage under clang-on-Windows. No model finds that — a spike did.

---

## ACT 3 — THE SPEC (3 slides, ~7 min)
*Theme: the spec doc is the product*

### 8. sbrush
- A statically-typed DSL for sculpt brushes. One source → **seven** backends: C++, WGSL, SPIR-V, CUDA, HIP, OpenCL, C99/TinyCC
- **895 lines of DSL → 11,132 lines of compiler**
- 📄 *"The C++ emitter is the reference, so the semantics of any construct are 'what `emit_cpp.cc` produces' — every other backend matches it **bit-for-bit modulo floating point**."*
```
@brush("draw")
brush Draw {
  ctx float3 surfaceNo;
  uniform float radius;
  vertex void apply(inout Vertex v) {
    float s = strength(v.co) * masks();
    if (s == 0.0) { continue; }
    v.co += surfaceNo * s * radius * 0.5;
  }
}
```
- This is byte-for-byte the example in the spec. **The spec's example is the shipped kernel.**

### 9. The spec was written before any code, and is revised in place
- 📄 The design doc still carries its banner: *"Status: design only. … **nothing under `source/brush/` has been touched yet**."*
- Pre-specified before implementation and shipped under these exact names: CMake option names, build verb names, golden-file layout, numeric tolerances (`VERIFY_ATOL 1e-5`), a ~20-path critical-files list. Plus a rejected alternative with reasons.
- Revised in place with **realization notes**, not rewritten: 📄 *"**Realization (as of the falloff-shape slice):** the tagged union above was realized as **two orthogonal axes** … The per-arm `axisCurve` the union proposed for `Cube` is **not implemented**."*
- Doc-only commits bracket the work — plan committed one day, implementation T1–T5 the next, then a doc-only "mark T3/T4 done; record open gaps"
- Deferred items get a register with `Source:` back-citations and a **"Done when:"** exit criterion

### 10. What the discipline buys
- **Autodiff for free.** 📄 `grad(expr, var)` *"needs no grammar support — it parses as an ordinary `Call` and is intercepted by name in the emitters."* Same rewrite on all seven backends → bit-identical gradients. An intrinsic with no derivative rule is a **compile error, not a wrong derivative**.
- **Policy by construction.** 📄 `@paint`/`@unbounded`/`@incremental` each emit `def.accumulable = false`, so the ACCUMULATE flag is inert for those kernels *"**by construction rather than by convention**."*
- **It crosses a repo boundary.** The app queries per-kernel policy from the engine: *"never hardcode a tool-name conditional; **adding a brush should not require a host edit**."*
- **Takeaway:** a spec precise enough for a machine is a spec precise enough to prevent drift. Same document, two jobs.

---

## ACT 4 — THE RESEARCH (3 slides, ~7 min)
*Theme: AI as research associate, with a measurement harness bolted on*

### 11. What AI-assisted literature review actually looks like
- Raw multi-model transcripts committed verbatim — 📄 one research doc has exactly two headers, `## Claude` and `## Gemini`, both answers pasted unedited **including their trailing follow-up questions**
- AI reading **third-party source as literature**: CoMISo's `MISolver.cc` / `ConstrainedSolver.cc`, exact line refs, structured into Lessons 1–8
- Paper notes with DOIs and **license diligence**: 📄 *"no license file as of 2026-06 — read as reference, **do not vendor until clarified**"*
- **Epistemic tagging** — every claim marked `[measured]` / `[literature]` / `[hypothesis]` / `[code]`
- Contrast: the human-maintained `UsefulPapers.md` is **three lines long**

### 12. The AI was wrong, and the harness caught it
- It read CoMISo, produced 8 lessons, recommended "eliminate the integer lock exactly" as the top experiment
- 📄 The plan **inverted its ordering**: *"the report recommends the exact integer lock first. **We invert** — Q1 is cheap, formulation-preserving, and its convergence measurement is exactly the evidence that tells us whether the Q5 rewrite is worth its cost."*
- 📄 Our own A/B **falsified its headline causal claim**, annotated on top of the preserved original:
  > *"One causal claim below is **corrected by measurement**… the folds are **constraint-induced, not penalty-induced**… **The report text below is preserved unedited.**"*
- Lesson→verdict table: 2 landed, 1 measured and **rejected** (the rejected parameter is still in the code), 1 inverted in priority
- 📄 It also downgraded our own marketing: *"The 'provably free of spiraling iso-lines' guarantee in the docs is really **'no spirals if the residual happened to land under 1e-4.'**"*

### 13. Now the honest part
- 📄 **The headline test asset fails.** *"no preset rescues anime-girl — at L=0.05 a folded parametrization yields **O(100) usable quads from 148k input tris** … the asset stays the torture case, not a v1 success."*
- **The corpus is 4/6 placeholders.** Two assets resolve: a trivial control and a known failure. Every "run over the corpus" is really two meshes.
- 📄 **2–3 orders off the commercial benchmark:** *"953 s of a 962 s quantize"* vs ZRemesher's 10–20 s on 800k tris
- 📄 **Prefiltering: tried and reverted.** *"Geometry prefiltering is the wrong lever here — the folds are a property of the field-aligned parametrization, not of the input tessellation."*
- 📄 Two surveys reached **no decision at all** — explicitly labelled *"Brainstorm/survey report — no decisions adopted yet."*
- **The rigor and the hollowness are in the same artifact.** That's the real picture.

---

## ACT 5 — CONTEXT (3 slides, ~7 min)
*Theme: the model's memory is a filesystem you maintain on purpose*

### 14. A context system is a hierarchy of markdown files
- **Start by asking Claude to write it.** `CLAUDE.md` / `AGENTS.md` are cheap to generate from a codebase and cheap to correct — then tell it to keep them updated as part of the work, not as a chore afterward.
- **The root file is a hub, not a manual.** 📄 Mine is ~20KB: a paragraph per subsystem, each pointing at the real doc. It links out to ~25 of them.
- **It resolves like an include graph:**
  - 📄 `sculptcore/AGENTS.MD`, in its entirety: *"Read the contents of CLAUDE.md"*
  - 📄 `.claude/CLAUDE.MD`, one line: *"Include contents of ../CLAUDE.md."*
  - 📄 The submodule's own 30KB `CLAUDE.md` defers upward: *"The repo-wide rules in the root `CLAUDE.md` … apply here"* — then adds C++ specifics
- **One file is the map.** 📄 `documentation/projectIndex.md` — a table of every directory and what lives in it. `CLAUDE.md:6` opens with *"See `documentation/projectIndex.md` for the full source-tree map."*
- **Docs come in families, and each one states its own role.** One design doc split into five as the system shipped — a language reference, a compiler/build doc, a runtime doc, a task guide, a durable reference — each pointing at the others. 📄 *"[that] is the original design doc / deferred-work record."*
- **Some docs are generated *for* the model.** 📄 `API_PATHS.md` — a catalog of every valid data-path string, regenerated with one command, described in `CLAUDE.md` as *"the human/LLM path reference."* A custom lint rule checks path strings against it. **That's a hallucination check.**
- And the inverse: 📄 `.claudeignore` hides `eslint.config.js`, `.prettierrc`, `.clang-format`. Tell it the rules in prose; don't let it negotiate with the enforcement config.

### 15. Ask for a running log — of what happened, not what you expected
- **Debugging log.** fairmotion's `docs/debugging.md` is **843 lines** of symptom → cause → how-it-was-found → fix, appended at the end of every phase. The plan mandated it up front, and the instruction is the good part:
  - 📄 *"Create `docs/debugging.md` at the start of phase 0. **Leave it empty until something is actually run — it records observed behavior, not anticipated behavior.**"*
  - That's where every quote in Act 1 came from. Without it, eight days of hard-won findings would have died with the sessions that produced them.
- **Lessons-learned doc.** 📄 `lessons-learned-vulkan.md` was written for a WebGPU port **that hadn't happened yet** — each native-backend footgun translated forward into its WebGPU equivalent. *"These are about the shape of the GPU↔CPU interaction, not API trivia — that shape is what bites, and it bites the same way (or worse) on WebGPU."*
- **`plans/` and `research/` as an archive.** 67 plan docs, 26 research docs. 📄 The convention is three sentences: *"Write all plans to `documentation/plans` … add the current date and time to the name."*
- **The reason all of this exists, stated outright in a plan's own cleanup phase:**
  > 📄 *"Write the list to `documentation/plans/post-webgpu-cleanup-followups.md` **so it survives outside the chat context**."*
  - **Context loss treated as an engineering constraint with a mitigation, not as a complaint.**

### 16. Two conventions that provably hold
- **`CLAUDENOTE:`** — 📄 *"Refactor / implementation / temp comments: no length limit, but prefix them `CLAUDENOTE:` … **The final step of any plan is to remove them**"* — replacing the ones still worth keeping with permanent ≤3-line comments.
  - Grep the entire source tree today: **zero hits.** Every surviving mention is a cleanup checklist item inside a plan doc.
  - **A convention is only real if you can prove it's honored. This one greps.** It also makes the agent's own scaffolding a first-class, disposable category instead of sediment.
- **`approvedLongComments.md`** — comments are capped at 3 lines, but some code needs a paragraph, and the next comment audit (also run by an agent) will happily delete it. So: a human-approval registry granting **exemptions from a rule the agent enforces on itself.**
  - 📄 *"Entries here are exempt from the per-file length budget — **do not flag or shorten them during a comment audit**."*
  - **The syntax is the enforcement handle.** Non-doc comments must be `//`. Approved long ones are the one exception — `/* … */` with no leading `*`. An unregistered violation is greppable.
  - All 7 entries come from one file. Six of seven start with "why." Every one is undo/redo ordering. **It's a list of the seven places where a human signed off on a paragraph aimed at a future refactoring agent.**

---

## ACT 6 — THE GUARDRAILS (1 slide, ~3 min)
*Theme: rules are scars; gates turn judgment into arithmetic*

### 17. The rules file is an incident log
- 📄 *"The WASM build step deletes `build/sculptcore.{js,wasm}` before linking because emcc can silently succeed on compile errors otherwise — **don't "optimize" that away**."*
  - Scare-quotes on *optimize*. **That rule exists because an agent deleted it.**
- 📄 The arms race in a single rule: *"do not turn `set.filter(...)` into `[...set].filter(...)`. **Also do not transform into an `Array.from` pattern either.**"* — first loophole closed, agent found the next, second clause added
- The rules that matter aren't style — they're where **wrong code looks like working code**: 📄 *"a new `extern "C"` function compiles and links cleanly and is simply invisible at runtime — **which looks like a load or ABI failure, not a missing export**."*
- **And then gates, so the decisions aren't mine to make in the moment.** Plan status lines are a state machine: `awaiting G3 review — no code until approved` → `M4 slab built, measured, and **reverted at its gate**`
  - 📄 Stop rules written *before* the work: *"if the triangle-only lower bound is within noise of current, stop. **Publish the negative result — it is genuinely useful.**"*
  - The slab rewrite passed every correctness gate and cut memory 20% — and measured **+4–6% slower.** Reverted, preserved on a named branch, documented against re-trying.
  - 📄 *"Pre-registered keep/revert rules made the two big reverts **mechanical rather than judgment calls**."*
  - 📄 And the profiler lied: *"Per-event timers lie 2–3× at 50–700 ns granularity — the figure that motivated a whole plan was **~2× inflated by the profiler's own wrapper timers**."*

---

### 18. Close — what to steal
- **Not** "AI writes the code now." What changed is that the cost of **precision** collapsed: a spec detailed enough to generate from is now cheaper to write than the code it replaces. What didn't change is knowing what to build, and knowing when you're fooling yourself.
1. **Separate surveying from fixing.** The first pass produces an inventory, not a green build.
2. **Point it where verification is mechanical.** Compilers and validators are better reviewers than you are.
3. **Write the spec first; revise it in place.** Annotate where reality diverged — don't rewrite history.
4. **Treat context as a filesystem you maintain.** A hub file, an index, doc families, and a running log of what actually happened.
5. **Tag your scaffolding so you can delete it.** Then prove it's gone with grep.
6. **Pre-register your keep/revert rules.** Turns a judgment call into arithmetic.
- The instinct underneath all of it, 📄 from a corpus-runner comment header:
  > *"Assets that can't be resolved are SKIPPED with a logged reason — **never silently dropped, so the table never reads as 'covered everything' when it didn't**."*

---

## Open items
- ⚠️ **Slide 2** — the ~$400 is billing-only; nothing in the repo records it
- **Resolved:** the "checker off for a pass" memory is **fairmotion**, not path.ux. path.ux did the opposite — survey-first, checker on throughout. Both are in the talk now.
- Decide whether to name the projects / show the apps
- Slides 6, 8: consider a live demo instead of code screenshots

## Cut for length — pull back in if you get 60 min
- **Guardrails as two slides** — scars and gates each get their own, with the `NO_DEBUG_ALLOC` and `calcHashKey` rules restored, plus the full measurement-discipline quote (*"same-session A/B only … any drift is a bug, not noise"*)
- **The ts-migration agent spec exists in two versions** — path.ux's, and webgl-app-framework's *after the incidents*, which adds a hard-case verdict table (*"Casts to Function → is almost always wrong"*) and *"you must get explicit permission to use any or Record."* Diffing them is Act 5's thesis applied to Act 1.
- **Plan inflation:** noise_fractal has a 194-line Claude plan-mode doc for a GLSL double-emulation transpiler that leaked its own tool constraint into the commit (*"plan mode restricts edits to this plan file"*), written to conventions established 24 hours earlier — and **never built**. Superseded by ~40 lines of hand-written GLSL.
- The `type_decisions` map, the `🛑 HARD CASE` pause protocol, `// TYPED-BY: human` stamps
- The CLAUDE.md layering (repo root → submodule → per-domain subagents), and the custom lint rule that validates data-path strings against a generated catalog — a hallucination check
