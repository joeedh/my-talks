# Software Engineering With AI — Talk Notes

**~45 min · mixed technical audience · 18 slides**

Sourced from real artifacts in `path.ux` / `fairmotion` / `mathl` / `noise_fractal_stuff` /
`pigment-painter` / `sculptcore` / `webgl-app-framework`.
📄 = file:line source exists. ⚠️ = needs your confirmation.

---

## Personal History With Agentic AI

* First started using agentic AI in March of this year.
* JS to TS porting
* Sculptcore
* Visual novel creator

### JS to TS porting

*  My first experiences with AI (Claude Code) was porting JS code to TS. This was very painful:
  - Claude kept wanting to add types to each file individually, driving typechecking errors to zero
    each time.
  - This produced hilariously garbage code [CLAUDE: insert code snippet from path.ux's git history of
    absurd uses of any Record etc].
  - Told Claude Code to add types to all files at once with its own reasoning alone, and only
    then drive typechecking errors to zero.  This worked.

### Sculptccore 

* Sculptcore is a digital sculpting system I designed years ago
* Meant to be embedded in host 3D digital content creation (DCC) apps like Blender or Maya.
* Includes bits of original research I had done for the Blender foundation (but never made it into 
  Blender).
* Project stalled due to the sheer work involved

### TS<->C++ bridge

* I had already coded a basic API to bridge C++ and TS.  I had Claude Code:
  - Add method/constructor binding.  
  - Fix the code that generates typescript interface files.
  - Remove the bridge's prior dependence on clang's `-fdelayed-template-parsing` flag.
* A generic method binding system is a nasty bit of C++ template code.  No problem for Claude.

### Claude's Perspective

For what it's worth, when creating notes for this talk Claude had this to say:

#### Why it worked — and the honest reason
* Genuinely hard: type-erased thunks `void(*)(void*, void**, void*)` where every parameter kind is read differently from a variadic pack; class templates with **string-literal NTTPs** reflected into TS generics (`BuiltinAttr<float3, '.face.normal'>`)
* 📄 The whole thing compiled only under `-fdelayed-template-parsing` — a clang MSVC-compat extension papering over two-phase lookup against an open overload set. The fix migrated ~124 call sites to a `Binder<T>::bind()` customization point.
* **The AI wrote the method and constructor binders. Best result in the talk.**
* **Why:** verification is nearly free. It compiles or it doesn't. And the refactor shipped behind a **zero-diff regeneration gate** — descriptors must regenerate byte-identical.
* **The pattern:** leverage is highest where the problem is tedious-hard and the check is mechanical. Lowest where the check is taste.
* Counterexample from the same work: node-addon-api's `CallbackInfo::Length()` returned `6e-310` garbage under clang-on-Windows. No model finds that — a spike did.

### Eh, No.

* Frontier models are perfectly capable of creating incredibly sophisticated tests.  
* You may have to coax them into doing it (they prefer making headless tests) but they can do it.
* For example. . .

### SBrush DSL

* Sculptcore is designed to execute brush strokes on both the CPU and the GPU.  
* Some sculpt brushes have exponential falloffs that never hit zero anywhere in the mesh,
  running them on the GPU greatly improves performance.
* So like any good computer graphics engineer, I made a DSL! 

* Example: 

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

### I had Claude do it

Actually I had Claude create it:
* I asked Claude to redesign a DSL that supported autodiff and could (eventually)
  be extended to meet all of our compute needs for sculpt brush evaluation.
* No problem for Claude 

### What Claude did 

* Wrote a parser and code emitters for C++ and WGSL.
* Created--without me asking--a sophisticated testing framework to test 
  that all compute backends produce identical results.
* Made me install two separate WGSL compilers:
  - The one used by Google's WebGPU implementation
  - Another one more typically used for compiling to Vulkan
* This was done to be absolutely sure the testing environment was correct to real-world use.

### Claude Is Really Good At Math

* This is actually pretty unusual.  Anthropic's models are not *that* great at creating testing
  frameworks with such little (none!) developer input.
* Claude is really, really good at math, and the reason it's good is because Anthropic has trained
  their models to write really good *tests* for math-heavy code.

### Later Developments

* I had previously prototyped a system to dynamically subdivide meshes 
  during sculpting while preserving UVs.  Claude was able to do it with around ~1 page of prompts in total.
* I also used Claude to do a large number of other things:
  - implement catmull-clark multiresolution sculpting.
  - write a blender addon.
  - modify blender's source code to make writing said addon possible.
  - . . .and more!
  
## A Break For Engineering!

Enough history for now, time to discuss practical engineering takeaways

### Agent Harnesses 

* LLMS are useless by themselves, they require harnesses.
* When people say 'Claude' they almost always means an official Anthropic harness.
* An agent harness provides tools to the model it can use to do things on your computer.

### The Context Window

* All LLMs have context windows.  
* Range from 10s of thousands of tokens to millions.  
* Current conventional wisdom is to use a window that's less then 500k in size
  - Avoids the dreaded 'middle rot' where the model starts ignoring tokens in the 
  middle of the context window.
  - Claude Code can be configured to use smaller context windows 
    [CLAUDE: insert instructions on doing so here]

### Basic Mental Model For Context

* The context is something your AI builds for its specific task.  
* Starts out with a system prompt provided by the harness, this informs the model about:
  - Tools
  - Custom skills (usually just the descriptions of them, models will load full skill files later).
  - Other instructions.
* A root 'memory' file is appended to the system prompt.  Depending on the harness this might be:
  - CLAUDE.md
  - AGENTS.md
  - HERMES.md
  [CLAUDE: insert other examples if they exist]
* This is a simple markdown file with links to other documents the model can use to build its context for the specific task it is doing
* These documents might be code documentation, ai-generated plans, research reports, etc
* When the agent is asked to do a task it will read CLAUDE.md, and follow any relevent links to useful documentation.
* It may use a subagent to synthesize everything into a more detailed report 
* Claude Opus and Fable will double-check this context against the current state of the codebase.  I think most 
  frontier models are trained to do this but I've not tested it.

### Other Bits of AGENTS.md

Since AGENTS.md is simply appended to the system prompt it often has other useful bits for the model:
* How to build the project
* High-priority rules

### How to Edit Your AGENTS.md Equivalent

Make the harness do it, e.g.:

* 'Create a CLAUDE.MD' (first run)
* 'Make sure CLAUDE.md is up to date'
* 'Add this rule to CLAUDE.md'
* 'Make sure CLAUDE.md links to the documentation'
* 'Cleanup CLAUDE.md, extract verbose sections into their own linked documentation files`

### Write "High-Priority" Rules, Formatting is for Formatters
Use high priority rules sparingly, code formatting and linting is the proper 
purview of linters/formatters.

#### Code Comment Rules 
This is extremely important to prevent the models from cluttering your codebase 
with verbose out of date comments that will poisons your context window.

I recommend these rules:
* Do not use more then X lines for *permanent non-doc* comments except for extremely math-heavy comments.
* You will need an exception policy, e.g.:
  - You may write longer comments every X lines (e.g. 500).
  - Long comments must be approved by the user, you must keep track of them in 
    a file committed in the repo.
* Temp comments must start with `AGENTNOTE:` and be stripped before final PR submissions.
  - The single most important comment rule!  Agents love writing temporary code comments 
  in the course of executing a task, making them prepend a tag allows them to easily
  grep the codebase to strip them.
* Temp comments have no line limit.

#### Debugging

It's important the model writes down how it debugged something so it can remember later
without having to spend the (possibly hours, possibly requiring you the developer's help)
time re-discovering it.  For example:

'Update Claude.MD: create a running debugging guide/lessons-learned (in docs/debugging.md) that's updated after each plan'

#### Folder Structure

I like to tell Claude to save documentation under the following folder hierachy:

* docs/ - For design documents.
* docs/research - For research reports
* docs/plans - For plans 

Note that depending on the harness you may need to explicitly tell the model to save plans in the main repo;
Claude Code for some reason does not, even though there are real benefits to doing so.

### Plans -- What Are Plans?

Plans are well, that: plans created by agents.  

* Most harnesses have a dedicated 'plan mode', 
* You can also simply command the agent to create a plan. 
* Models will often use plan files to store state 
  - This is why saving them in your repo is a good idea, that state is 
    often useful context for future plans.

#### Task Lists 

For particularly large tasks that require multiple plans you can create a task list.
This is often done after a high-level discussion with the model, possibly after it has
created a research report.  For example:

* [User]: I want to support X feature.  How would that work.
* [Agent]: Maybe like this.  Should I write a report?
* [User]: Do that.  Also create a master task list to keep track 
          of plans in docs/plans/feature-task-list.md.

Claude Code unfortuntely has quirks surrounding task lists, but so long as you
tell it to save the task list in a specific place it should be fine (there's 
actually a task list *tool* that operates in a single claude session, it's a whole thing).

### Tests, Or Why You Should Not Use MCP Servers

* MCP servers are an API layer that sits between an LLM and an API, they were invented 
  back when models were stupid.
* Frontier models do not need this.
  - Note: if you're in a high-security environment you may want to use MCPs to avoid triggering 
    excessive AI model cleverness.
* Claude Code has a chrome devtools MCP server.  The model happily told me it preferred to drive 
  Chromium apps over the debugging CDP protocol directly.

#### Skills 

You do want to use skills.  A skill is a markdown file that tells the model what to do, often associated with a simple 
bash/python/JS script.  Skills come in two forms:

* Formal skills.  These are loaded by the agent harness and usually invoked with `/[skill-name]`.
* Informal skills.  Raw instructions to the model.  
  - Can live anywhere in the codebase, usually linked to (or occasionally lives in) AGENTS.md.
  - Multiple 'skills' can live in a single markdown file (e.g. the debugging.md guide).

For tests it's easier to use informal skills almost exclusively; this lets the agent 
fix bugs in the skill, clone it to make specialized variants, etc.

#### Creating Tests 

The models are trained to always produced tests, but they aren't always very good at writing or debugging them.

Tips for best results:

* Let the model figure out *what* to test.
  - you will add to that later :)
* Ask the model to design any debugging skills/tools it needs for the tests (do not use the word 'skill'
  however).
* Inform the model about any debuggers or performance profiling tools on your system (important for C/C++).
* Tell the model to set up a framework for full headed end-to-end integration tests, creating any mocking necassary.
  (and only that which is necasssary).  You can use playwright, Electron, NWJS, etc.
* The agent (or at least Claude Code) will prefer to write headless tests.  When these tests turn out to be useless
  tell the model to redo them as full integration tests.
* Remember that models (at least Claude Opus and Fable) are extremely good at writing 
  math tests.

#### Debugging Tests

Let me say that again: tell the model to design any debugging tools it needs for the tests.  You may have to give 
it ideas if it tries to give up (e.g. write an integration test with playwright that you can connect to over Devtools CDP).

### Refactoring

Models are fairly good at refactoring (including across git submodule boundaries!).

An example refactoring run:

* [User]: I've noticed there's a bunch of duplicate code inside the consumers of this API.
* [Model]: You're right.  Here are all the places this is happening

* [User]: The duplicated code really belongs in the API itself.  Write a plan to do this.

. . .Or:

* [User]: The duplicated code really belongs in the API itself.  Move it inside the API.

### You Don't Always Want To Plan

* If you want the agent to iterate more then it would with normal plans you can directly order it to 
  do a task.  
* Claude Code is extremely good at gauging the complexity and creating minimal plans when necassary.
* Other harnesses may require explicit instructions, e.g. 'do X refactor, work in an iterative manner 
  updating your plan as you go along, keep me in the loop.'
 








