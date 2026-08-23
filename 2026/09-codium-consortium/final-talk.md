---
title: "Software Engineering With AI"
author: "Joe Eagar"
date: "Codium Consortium · September 2026"
title-slide-attributes:
  data-background-image: "slide-front-page.jpg"
  data-background-size: "contain"
  data-background-color: "#0b1020"
---

<!-- PREP NOTES AND TODOS ARE AT THE BOTTOM OF THIS FILE.
     Don't put them up here: anything between the YAML block and the first
     header becomes a blank slide, and YAML rejects freeform text like "[ ]:". -->

## Backstory

* First started using agentic AI in March of this year.
* JS to TS porting

### Things Did Not Start Well

* My first task for Claude was to port a large amount of Javascript code to Typescript.
* Anthropic's models are trained to port JS->TS one file at a time, driving all type errors to zero 
before going onto the next one.
* This produced hilariously garbage code (see next slide).

#### Hilariously Garbage Code 

```ts 
class Bleh {
	declare one: any 
	declare two: Record<string, any>
	three: unknown
	four: Bleh & { childClassThing: unknown }
}
```

### The solution
* I had Claude Code create a Javascript to Typescript conversion skill that worked in stages:
	- Adds types to all files with the model's own reasoning; it is not allowed to invoke the typechecker.
	- Read the files again to double check its work.
	- Finally drive typecheck errors to zero.

### Sculptcore

* Sculptcore: digital sculpting system I designed years ago.
* Meant to be embedded in host 3D digital content creation (DCC) apps like Blender or Maya.
* Includes bits of original research I had done for the Blender foundation (but never made it into 
  Blender).
* Project stalled due to the sheer work involved.
* Used Claude Code heavily to finish the work 

## Briefly Demo Sculptcore 

### Example of What Frontiers Model Can Do: SBrush DSL

* Sculptcore is designed to execute brush strokes on both the CPU and the GPU.  
* Some sculpt brushes have exponential falloffs that never hit zero anywhere in the mesh,
  running them on the GPU greatly improves performance.
* So like any good computer graphics engineer, I made a domain specific language (DSL)! 

### SBrush DSL — example

```hlsl
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

### SBrush DSL [contd]
* I've implemented enough compilers in my life
* So I asked Claude to design a DSL that supported autodiff and could (eventually)
  be extended to meet all of our compute needs for sculpt brush evaluation.
* The result was impressive.

### Claude

* Wrote a parser and code emitters for C++ and WGSL.
* Created--without me asking--a sophisticated testing framework to test 
  that all compute backends produce identical results.
* This was done to be absolutely sure the testing environment was correct to real-world use.

### Sadly This Is Not Normal

* Anthropic's models are not *that* great at creating testing
  frameworks with such little developer input.
* Math-heavy tasks (including math-heavy language compilers) are an exception.
* We'll come back to this later.

## Visual Novel Creator

Generative AI pipeline for creating visual novels, created from scratch with Claude Code. 

A user (or an AI agent) writes:
* Story notes (e.g. locations, characters, history)
* Scene scripts

The app generates AI artwork with google gemini.  Artwork 
form a tree of reference images, prior reference images are 
fed to gemini for reference (e.g. portrat -> character model sheet -> shot).

Human review of assets is built into the app. 

## Briefly Demo Visual Novel Creator

## Practical Software Engineering

Enough history for now.  Time for the good part.

There's a basic ai project template generator at:

https://github.com/joeedh/ai-quicktests

![](qr-ai-quicktests.png){width=40%}

### Terminology:

* Agent Harness - the software that interfaces with the AI model.
* AGENTS.md: the root context memory file, may also be called CLAUDE.MD 
             GEMINI.MD etc depending on your specific harness.
* The model: the active large language model 

### Interrupting The Model

* You can interrupt coding agents with 'escape' or by pressing a stop button.
* Ask the model questions, or give it further instructions.
* Type 'continue'

### Agent Harnesses 

* LLMs are useless by themselves, they require harnesses.
* When people say 'Claude' they almost always mean an official Anthropic harness.
* An agent harness provides tools to the model it can use to do things on your computer.

## Resuming Sessions 

* Your agent session should have a way to resume sessions 
* Claude Code has `claude --resume`{.text} that lets you pick a session to resume.

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

### The 'House Style'
* Anthropic's models derive a 'house' prose style from CLAUDE.md.
* Other models likely do the same
* If you find the model starts writing strangely-worded prose start at 
  your AGENTS.md equivalent.

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

* Coding agents by default will tend to clutter the codebase with temporary comments.
* These poison the context.
* Easy to prevent in AGENTS.md:

Do not use more than X lines for *permanent non-doc* comments except for extremely math-heavy comments.

<p style="text-align: left;">
**User**: Add these rules to AGENTS.md: permanent non-doc comments cannot be more then 4 lines except every 500 lines; temporary comments must start with AGENTNOTE: for later stripping.  Doc comments (e.g. jsdoc /** */) should be kept reasonably concise. 
</p>

#### Code Comment Rule Exceptions 
  
* You will need an exception policy, e.g.:
  - You may write longer comments every X lines (e.g. 500).
  - Long comments must be approved by the user, you must keep track of them in 
    a file committed in the repo.

#### Code Comment Rules (cont.)

* Temp comments must start with `AGENTNOTE:`{.text} and be stripped before final PR submissions.
  - The single most important comment rule!  Agents love writing temporary code comments 
  in the course of executing a task, making them prepend a tag allows them to easily
  grep the codebase to strip them.
* Temp comments have no line limit.

#### Comment Prose 

* If you have an existing codebase Claude will use the prose 
  style of its comments.
* If not the prose style may drift into Yoda-like statements the model
  finds more convientent but are unreadable to humans.
* There is a comment prose style guide in talk notes (CommentStyle.md).
  You can:
  - Drop it into AGENTS.md 
  - Or tell your agent to create a skill from it, e.g. 'create a skill that enforces the prose style in CommentStyle.md'
  - You can also use it to clean up your AGENTS.md's style:
    - **User:** 'Make AGENTS.md follow the prose style rules in CommentStyle.md (we are changing to house style)'
	- note how we tell the agent our goal.
* CommentStyle.md is fairly large; you shouldn't need to embedd the whole thing into AGENTS.md 
  unless things are already broken.

#### Comments For From Scratch Projects
* Work out a comment prose style early if creating a project 
  from scratch, since the model has no examples in the codebase 
  to work from.
* I had to have claude fix all the comments in a from-scratch project 
  - Used claude code's ultracode feature to use lots of agents in parallel.
  - Burned through 13 million tokens.
  - Cost about $150
  - Note: this was full unsubsidized token cost (I had run out of my max plan 
          usage for that week).

#### Debugging

It's important the model writes down how it debugged something so it can remember later
without having to spend the (possibly hours, possibly requiring you the developer's help)
time re-discovering it.  For example:

<p style="text-align: left;">
**User:** Update Claude.MD: create a running debugging guide/lessons-learned (in docs/debugging.md) that's updated after each plan'
</p>

#### Folder Structure

I like to tell Claude to save documentation under the following folder hierarchy:

* docs/ - For design documents.
* docs/research - For research reports
* docs/plans - For plans 

Note that depending on the harness you may need to explicitly tell the model to save plans in the main repo;
Claude Code for some reason does not, even though there are real benefits to doing so.

### DEMO

Create an empty git repo, start claude.

### Prompt 

<p style="text-align: left;">
Create a CLAUDE.md with the following rules:
</p>

* permanent non-doc code comments cannot be more then 4 lines except every 500 lines.
* temporary code comments have no limit but must start with AGENTNOTE: for later stripping.
* create a running debugging guide/lessons-learned in docs/debugging.md.
* design documentation go in docs/
* research and reports go in docs/research 
* plans should always be saved to the repo and go in docs/plans
* plans should be pressure tested with an agent and the results folded back into the plan 
  after creation.

### Plans

Plans are well, that: plans created by agents.  

* Most harnesses have a dedicated 'plan mode', 
* You can also simply command the agent to create a plan. 
* Models will often use plan files to store state 
  - This is why saving them in your repo is a good idea, that state is 
    often useful context for future plans.

### DEMO 

Prompt:


<p style="text-align: left;">
Create a plan to write a tetris game:
</p>

* Use native typescript tsgo, pnpm, eslint, prettier
* serve with esbuild's http server.  
* Create an Electron shell.  
* plan should make sure CLAUDE.md is up to date when it's done. 
* You may use either Playwright or the Electron shell for integration tests.
When the plan is done, execute the plan

#### Pressure Testing Plans 

* Rigourously attempts to falsify plans/documents
* Can be used to find and detect errors
* Worth running inside of subagents
* Worth creating a skill for this if your model doesn't support it natively
  - To test, just ask your model how it interprets the phrase 'pressure test X plan'.

For example:

<p style="text-align: left;">
**User:** Use an agent to pressure test plan at X
</p>
<p style="text-align: left;">
...model works 
</p>
<p style="text-align: left;">
**Model:** Agent found X errors.  Want me to fold them into the plan?
</p>
<p style="text-align: left;">
**User:** Yes
</p>

#### Pressure Testing Plans 

Claude Code doesn't always ask you if you want to apply the pressure testing results.
Do not assume it has done so, e.g.:

<p style="text-align: left;">
**User:** Did you fold the pressure testing results into the plan?
</p>

#### Task Lists 

For particularly large tasks that require multiple plans you can create a task list.
This is often done after a high-level discussion with the model, possibly after it has
created a research report.  For example:

<p style="text-align: left;">
**User:** I want to support X feature.  How would that work.
</p>
<p style="text-align: left;">
**Agent:** Maybe like this.  Should I write a report?
</p>
<p style="text-align: left;">
**User:** Do that.  Also create a master task list to keep track 
  of plans in docs/plans/feature-task-list.md.
</p>

Make sure to tell the agent to save the task list to a file, some harnesses 
support a temporary in-memory task list.

### Task List Example:

Prompt (we won't be running this now to save time):  

* Use an agent to pressure test the plan.
* Create a task list in docs/plans/tasklist.md:
  - Add the first plan to it.
  - Add a plan to write any necassary debugging code needed for you to drive the Electron
    shell over CDP.
* Write the second Plan.
* Execute the tasklist until completion.

### Tests 

* Frontier models are trained to always produce tests.
* Getting them to reliably produce *useful* tests can be a challenge.
* Let the model figure out *what* to test.
  - you will add to it later.
* Inform the model about any debuggers or performance profiling tools on your system
  (important for C/C++).
* Models (at least Claude Opus and Fable) are extremely good at writing 
  math tests.

### Tests [Contd]

* Make the model design a full integration test system early.
  - Can use Playwright, Electron, NWJS, etc.
* Models (or at least Anthropic ones) prefer to write headless tests.
  - These are often useless.
  - When this happens have the model convert them to full integration tests.
    - It's better to do this on a case by case basis instead of making the model only generate 
	  integration tests.
	- Full Chromium integration tests (whether Playwright or a shell like Electron) use quite a bit more system resources then headless ones.

### Build Debugging Tools

* Make the model think through and write the debugging tools it needs for its integration tests.
  - You may have to give it ideas if it tries to give up (e.g. "write an integration test with
    playwright that you can connect to over Devtools CDP").
  - Do not use the word 'skill' when you ask, more on that later.
* The 'keep a running lessons-learned guide in debugging.md' CLAUDE.md rule comes in handy here.
* But don't build them as MCP servers. . .

#### Do Not Write Debugging Tools as MCP Servers

* MCP servers are an API layer that sits between an LLM and an API, they were invented 
  back when models were stupid.
* Frontier models do not need this.  They can write the tools they need directly in a variety of ways.
* It's better to let the models write their own debugging tools as either formal or informal skills (more on that in a bit).
* Note: some organizations require MCP servers to be used for security reasons.
  
#### Skills 

A skill is a markdown file that tells the model what to do, often associated with a simple 
bash/python/JS script.  Skills come in two forms:

* Formal skills.  These are loaded by the agent harness and usually invoked with `/[skill-name]`{.text}.
* Informal skills.
  - Can live anywhere in the codebase, usually linked to (or occasionally lives in) AGENTS.md.
  - Raw instructions to the model.
  - May also have an associated script.  
  - Multiple 'skills' can live in a single markdown file (e.g. the debugging.md guide).
* The running debugging guide from earlier slides is a collection of informal skills

#### Skills (cont.)

When you tell an agent to create a tool for some task it will either:

* Write an informal skill in some existing doc (e.g. AGENT.md or debugging.md) possibly 
  including a helper script.
* Ask you if you want it to create a formal skill.  You can usually force this by saying 'create this skill'
* Never use the word 'skill' when asking the model to create tools unless you want it 
  to create a formal skill.

### Refactoring

* Agents are fairly good at refactoring
* Can handle git submodules

### Refactoring - Example

<p style="text-align: left;">
**User:** I've noticed there's a bunch of duplicate code inside the consumers of this API.
</p>
<p style="text-align: left;">
**Model:** You're right.  Here are all the places this is happening
</p>
<p style="text-align: left;">
**User:** The duplicated code really belongs in the API itself.  Write a plan to do this.
</p>

### Refactoring - Example 2

You can also simply command the model to do it directly:

<p style="text-align: left;">
**User:** The duplicated code really belongs in the API itself.  Move it inside the API.
</p>

### You Don't Always Want To Use Plan Mode

* Not using plan mode is sometimes easier to iterate on
* Claude is more reliable at following planning rules in CLAUDE.md if you 
  command it to create a plan outside of plan mode itself.
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

<p style="text-align: left;">
**User:** In a new worktree do X
</p>
<p style="text-align: left;">
**User:** In a new worktree execute the plan at docs/plans/XXX.md
</p>

When done:

<p style="text-align: left;">
**User:** merge into master and tear down the worktree
</p>
<p style="text-align: left;">
**User:** push to git and open a PR in github, then tear down the worktree
</p>

### DEMO 

Prompt:

In a new worktree do the items in todo.md 

### NWJS 

If you find yourself needing to use NWJS (basically single-process Electronjs, it's easier to debug)
you will have to tell Claude to jump through some hoops to allow multiple independent nwjs instances
(e.g. for tests):

<p style="text-align: left;">
**User:** I want to be able to run multiple instances of the nwjs shell at once.  This will require 
creating temporary lightweight Chromium profile directories.  Be absolutely sure those directories 
are deleted on exit as they can add up to quite a lot of disk space.
</p>

#### NWJS/Electron crashpad 

You can also have Claude set up Chromium's automated crashpad system:

<p style="text-align: left;">
**User:** Make sure NWJS crashpad works and you are able to read its dump files.
</p>







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
