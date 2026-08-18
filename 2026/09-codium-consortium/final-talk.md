---
title: "Software Engineering With AI"
author: "Joe Eagar"
date: "Codium Consortium · September 2026"
---

<!-- PREP NOTES AND TODOS ARE AT THE BOTTOM OF THIS FILE.
     Don't put them up here: anything between the YAML block and the first
     header becomes a blank slide, and YAML rejects freeform text like "[ ]:". -->

## Title Page 
[CLAUDE: insert slide-front-page.jpg here]

## About the Front Page 

I uploaded this talk to Google Gemini and told it to "create a diagram inspired by this talk".

## Personal History With Agentic AI

* First started using agentic AI in March of this year.
* JS to TS porting
* Sculptcore
* Visual novel creator

## Briefly Demo Sculptcore 

## Briefly Demo Visual Novel Creator

### JS to TS porting

*  My first experiences with AI (Claude Code) were porting JS code to TS. This was very painful:
  - Claude kept wanting to add types to each file individually, driving typechecking errors to zero
    each time.
  - This produced hilariously garbage code [CLAUDE: insert code snippet from path.ux's git history of
    absurd uses of any Record etc].
  - Told Claude Code to add types to all files at once with its own reasoning alone, and only
    then drive typechecking errors to zero.  This worked.

### Sculptcore

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
* The whole thing compiled only under `-fdelayed-template-parsing` — a clang MSVC-compat extension papering over two-phase lookup against an open overload set. The fix migrated ~124 call sites to a `Binder<T>::bind()` customization point.
* **The AI wrote the method and constructor binders. Best result in the talk.**

#### Why it worked (cont.)

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

### SBrush DSL — example

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

### Sadly This Is Not Normal

* Anthropic's models are not *that* great at creating testing
  frameworks with such little (none!) developer input.
* They are great at writing math tests however.

### Later Developments

* I had previously prototyped a system to dynamically subdivide meshes 
  during sculpting while preserving UVs.  Claude was able to do it with around ~1 page of prompts in total.
* I also used Claude to do a large number of other things:
  - implement catmull-clark multiresolution sculpting.
  - write a blender addon.
  - modify blender's source code to make writing said addon possible.
  - . . .and more!
  
## Practical Software Engineering

Enough history for now, time to discuss practical engineering takeaways

There's a basic ai project template generator at:

https://github.com/joeedh/ai-quicktests

CLAUDE: create and embedd a QR code for the above link 
the demo QR code should be shown on the bottom right corner 
of all successive slides along with the caption 'Demo'.

### Set up demo 

I'll be setting up a demo making a simple puzzle fighter game.  Note: for the sake 
of speed I'll being Sonnet with low effort level, a frontier model like Opus or even
Sonnet on high effort will give much (much!) better results.

### A Note On Chromium debugging

* Claude has multiple means of debugging JS-based apps served in a chromium shell.
* If you don't like the solution it's using, you can press escape to interrupt it
  and tell it to use another approach.

### Agent Harnesses 

* LLMs are useless by themselves, they require harnesses.
* When people say 'Claude' they almost always mean an official Anthropic harness.
* An agent harness provides tools to the model it can use to do things on your computer.

## Resuming Sessions 

* Your agent session should have a way to resume sessions 
* Claude Code has `claude --resume` that lets you pick a session to resume.

### The Context Window

* All LLMs have context windows.  
* Range from 10s of thousands of tokens to millions.  
* Current conventional wisdom is to use a window that's less than 500k in size
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

### Basic Mental Model For Context (cont.)

Most context (or memory) files are simple markdown file with links to other documents, important information the 
model might, etc.  The context hierachy typically looks like this (in order of insertion into the prompt):

* A root 'memory' file is appended to the system prompt.  Depending on the harness this might be
  AGENTS.md, CLAUDE.md, GEMINI.md, etc
* Some kind of external memory store associated with this project.  In Claude Code this is a markdown file:
  - Flat list of links to other 'memory' markdown files
  - Lives in the user's home folder
  - Is associated with a specific repo
* Basically there's context memory that's committed to the repo (AGENTS.md) and memory that's not.

### Basic Mental Model For Context (cont.)

* When the agent is asked to do a task it will read AGENTS.md, and follow any relevant links to useful documentation.
* It may use a subagent to synthesize everything into a more detailed report 
* Claude Opus and Fable will double-check this context against the current state of the codebase.  I think most 
  frontier models are trained to do this but I've not tested it.

### How to Edit Your AGENTS.md Equivalent

Make the harness do it, e.g.:

* 'Create a AGENTS.MD' (first run)
* 'Make sure AGENTS.md is up to date'
* 'Add this rule to AGENTS.md'
* 'Make sure AGENTS.md links to the documentation'
* 'Cleanup AGENTS.md, extract verbose sections into their own linked documentation files`

Replace 'AGENTS.md' with the proper name for your agent harness (many actually support AGENTS.md in addition
to their own special filenames).

### Write "High-Priority" Rules, Formatting is for Formatters

Use high priority rules sparingly, code formatting and linting is the proper 
purview of linters/formatters.

#### Code Comment Rules 

This is extremely important to prevent the models from cluttering your codebase 
with verbose out of date comments (and poison your agent's ability to accurately build context).

I recommend these rules:

* Do not use more than X lines for *permanent non-doc* comments except for extremely math-heavy comments.
* You will need an exception policy, e.g.:
  - You may write longer comments every X lines (e.g. 500).
  - Long comments must be approved by the user, you must keep track of them in 
    a file committed in the repo.

#### Code Comment Rules (cont.)

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

I like to tell Claude to save documentation under the following folder hierarchy:

* docs/ - For design documents.
* docs/research - For research reports
* docs/plans - For plans 

Note that depending on the harness you may need to explicitly tell the model to save plans in the main repo;
Claude Code for some reason does not, even though there are real benefits to doing so.

### DEMO

Create an empty git repo, start claude.

Prompt: 

Create a CLAUDE.md with the following rules:
permanent non-doc code comments cannot be more then 4 lines except every 500 lines;
temporary code comments have no limit but must start with AGENTNOTE: for later 
stripping; create a running debugging guide/lessons-learned in docs/debugging.md; 
design documentation goes in docs/ research/reports in docs/research plans in 
docs/plans; always write plans into the repo.

### Plans

Plans are well, that: plans created by agents.  

* Most harnesses have a dedicated 'plan mode', 
* You can also simply command the agent to create a plan. 
* Models will often use plan files to store state 
  - This is why saving them in your repo is a good idea, that state is 
    often useful context for future plans.

### DEMO 

Prompt:

Create a plan to write a puzzle fighter game.  Use native typescript tsgo,
pnpm, eslint, prettier, serve with esbuild's http server.  Create an Electron
shell.  The plan should make sure CLAUDE.md is up to date when it's done. 
You may use either Playwright or the Electron shell for integration tests.

#### Pressure Testing Plans 

* Rigourously attempts to falsify plans/documents
* Can be used to find and detect errors
* Worth running inside of subagents
* Worth creating a skill for this if your model doesn't support it natively
  - To test, just ask your model how it interprets the phrase 'pressure test X plan'.

For example:

[User]: Use an agent to pressure test plan at X
...model works 
[Model]: Agent found X errors.  Want me to fold them into the plan?
[User]: Yes

#### Task Lists 

For particularly large tasks that require multiple plans you can create a task list.
This is often done after a high-level discussion with the model, possibly after it has
created a research report.  For example:

* **User:** I want to support X feature.  How would that work.
* **Agent:** Maybe like this.  Should I write a report?
* **User:** Do that.  Also create a master task list to keep track 
  of plans in docs/plans/feature-task-list.md.

Make sure to tell the agent to save the task list to a file, some harnesses 
support a temporary in-memory task list.

### DEMO:
Prompt: 

* Use an agent to pressure test the plan, fold its recommendations into the plan.
* Create a task list in docs/plans/tasklist.md:
  - Add the first plan to it.
  - Add a plan to write any necassary debugging code needed for you to drive the Electron
    shell over CDP.
* Write the second Plan
* Execute the tasklist until completion

### Tests 

* Frontier models are trained to always produce tests.
* Getting them to reliably produce *useful* tests can be a challenge.
* Let the model figure out *what* to test.
  - you will add to that later :)
* Inform the model about any debuggers or performance profiling tools on your system
  (important for C/C++).
* Remember that models (at least Claude Opus and Fable) are extremely good at writing 
  math tests.

### Tests — Headed, Not Headless

* Make the model design a full integration test system early.
  - Can use Playwright, Electron, NWJS, etc.
* Models (or at least Anthropic ones) prefer to write headless tests.
  - These are often useless.
  - When this happens have the model convert them to full integration tests.
    - It's better to do this on a case by case basis instead of making the model only generate 
	  integration tets.
	- Full Chromium integration tests (whether Playwright or a shell like Electron) use quite a bit more system resources then headless ones.

### Tests — Make It Build Its Own Debugging Tools

* Make the model think through and write the debugging tools it needs for its integration tests.
  - You may have to give it ideas if it tries to give up (e.g. "write an integration test with
    playwright that you can connect to over Devtools CDP").
  - Do not use the word 'skill' when you ask — see *Skills*, two slides on.
* The 'keep a running lessons-learned guide in debugging.md' CLAUDE.md rule comes in handy here.
* But don't build them as MCP servers. . .

#### Do Not Write Debugging Tools as MCP Servers

* MCP servers are an API layer that sits between an LLM and an API, they were invented 
  back when models were stupid.
* Frontier models do not need this.  They can write the tools they need directly in a variety of ways.

#### Do Not Write Debugging Tools as MCP Servers (cont.)

* Note: there are reasons to use MCP servers (like security)
  - If you need to use an MCP server for your app make the testing framework use it.
  - Do not *write* MCP servers specifically for your testing framework unless 
    your security policies require it.
* Claude Code has a chrome devtools MCP server.  The model happily told me it preferred to drive 
  Chromium apps over the debugging CDP protocol directly.

#### Skills 

You do want to use skills.  A skill is a markdown file that tells the model what to do, often associated with a simple 
bash/python/JS script.  Skills come in two forms:

* Formal skills.  These are loaded by the agent harness and usually invoked with `/[skill-name]`.
* Informal skills.  Raw instructions to the model.  
  - Can live anywhere in the codebase, usually linked to (or occasionally lives in) AGENTS.md.
  - Multiple 'skills' can live in a single markdown file (e.g. the debugging.md guide).
* The running debugging guide from earlier slides is a collection of informal skills

#### Skills (cont.)

When you tell an agent to create a tool for some task it will either:

* Write an informal skill in some existing doc (e.g. AGENT.md or debugging.md) possibly 
  including a helper script.
* Ask you if you want it to create a formal skill.  You can usually force this by saying 'create this skill'
  which is why you should never use the word 'skill' when asking the model to create tools unless you want it 
  to create a formal skill.
  
For tests it's easier to use informal skills almost exclusively; this lets the agent 
fix bugs in the skill, clone it to make specialized variants, etc.

### Refactoring

Models are fairly good at refactoring (including across git submodule boundaries!).

An example refactoring run:

**User:** I've noticed there's a bunch of duplicate code inside the consumers of this API.
**Model:** You're right.  Here are all the places this is happening
**User:** The duplicated code really belongs in the API itself.  Write a plan to do this.

You can also simply command the model to do it directly:

**User:** The duplicated code really belongs in the API itself.  Move it inside the API.

Note: modern agent harnesses will automatically create plans for complex tasks.

### You Don't Always Want To Use Plan Mode

* Not using plan mode is sometimes easier to iterate on
* Not needed for the immediate todo list workflow 

### Immediate Todo Workflow 

* Test your app.
* Write a todo list of things to be done immediately
* Have your agent execute it.
* Repeat 

### Immediate Todo Workflow [Contd]

Use a checked markdown list.

Example:
```markdown 
[ ]: Do X 
[ ]: Do Y
```

### DEMO: 

Create a todo list for the demo.

### Working in Parallel: Git Worktrees

Git worktrees are a lightway way to clone branches into new folders:

* Let's you work on multiple things at once.
* A branch can only be checked out in one worktree at a time
* Claude's worktree support has a few simple but dire bugs 
* To fix, write a prompt like so:

### Worktree Fix prompt

Update the global CLAUDE.md: 
* worktrees must be created in sibling folders of the repo, NOT .claude/worktrees
* if the exit worktree skill cannot delete a worktree directory it should check for any git file 
watchers, typecheck servers or dev servers that hold the directory's lock and kill them.

### Using worktrees (Claude Code)

 [User]: In a new worktree do X
 [User]: In a new worktree execute the plan at docs/plans/XXX.md

When done:

 [User]: merge into master and tear down the worktree
 [User]: push to git and open a PR in github, then tear down the worktree

### DEMO 

Prompt:

In a new worktree do the items in todo.md 

### NWJS 

If you find yourself needing to use NWJS (basically single-process Electronjs, it's easier to debug)
you will have to tell Claude to jump through some hoops to allow multiple independent nwjs instances
(e.g. for tests):

  [User]: I want to be able to run multiple instances of the nwjs shell at once.  This will require 
creating temporary lightweight Chromium profile directories.  Be absolutely sure those directories 
are deleted on exit as they can add up to quite a lot of disk space.

#### NWJS/Electron crashpad 

You can also have Claude set up Chromium's automated crashpad system:

  [User]: Make sure NWJS crashpad works and you are able to read its dump files.







<!-- ===========================================================================
PREP NOTES — not rendered. Freeform; nothing parses this block.

Sections starting with DEMO cannot be split into multiple slides

~45 min · mixed technical audience · ~41 slides (31 sections, 10 split for overflow)

Sourced from real artifacts in path.ux / fairmotion / mathl / noise_fractal_stuff /
pigment-painter / sculptcore / webgl-app-framework.

Slide model: every ### / #### header starts a new slide (pandoc --slide-level=4).
Sections too long for one slide are continued with a "(cont.)" header.

TODO:
[ ] add section on selecting models and model effort.
[ ] add example/demo section.
[ ] explain out-of-repo memory files that live in the user folder's .claude folder
[ ] fill the three [CLAUDE: ...] placeholders.
[ ] write a closing slide — the talk currently stops rather than ends.
[ ] mention pressure testing plans 
[ ] make section headers have a consistent title case style, use whatever the 
    most common case styling.
=========================================================================== -->
