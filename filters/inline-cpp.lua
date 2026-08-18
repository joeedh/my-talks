-- Pandoc never highlights single-backtick spans, in any language. The decks are
-- mostly about C++ APIs, so `CallbackInfo::Length()` and `Binder<T>::bind()`
-- should read as code, not as flat body text.
--
-- Every bare inline span is lexed as C++. A span opts out by naming its own
-- class: `claude --resume`{.text} stays plain, `x = 1`{.python} picks another
-- language. That is also the fix when C++ lexing misreads something -- e.g.
-- `-fdelayed-template-parsing` colors "template" as a keyword.

local DEFAULT_LANG = 'cpp'

local used_inline = false   -- did we emit any highlighted span?
local saw_code_block = false -- ...and did pandoc already highlight a real block?

local function highlight_style()
  local opts = PANDOC_WRITER_OPTIONS
  return opts and opts.highlight_style or nil
end

--- Render `text` as a highlighted one-liner and return just the token spans.
local function highlight_inline(text, lang)
  local block = pandoc.CodeBlock(text, pandoc.Attr('', {lang}))
  local ok, html = pcall(pandoc.write, pandoc.Pandoc({block}), 'html',
                         {highlight_style = highlight_style()})
  if not ok then return nil end

  local inner = html:match('<code[^>]*>(.-)</code>')
  if not inner then return nil end

  -- Drop the per-line wrapper pandoc adds for line numbering: an outer
  -- <span id="cb1-1"> plus its anchor. Without this the anchor renders as a
  -- stray link inside running text.
  inner = inner:gsub('<a href="#[^"]*"[^>]*></a>', '')
  inner = inner:gsub('^%s*<span id="[^"]*">', '')
  inner = inner:gsub('</span>%s*$', '')
  return inner
end

function Code(el)
  -- An explicit class means the author already chose (or declined) a language.
  if #el.classes > 0 then return nil end

  local inner = highlight_inline(el.text, DEFAULT_LANG)
  if not inner then return nil end

  used_inline = true
  return pandoc.RawInline('html',
    '<code class="sourceCode ' .. DEFAULT_LANG .. '">' .. inner .. '</code>')
end

function CodeBlock(el)
  -- Pandoc emits the highlighting stylesheet only when the document contains a
  -- highlighted *block*. Track whether one exists so we know if we have to
  -- supply the CSS ourselves.
  if #el.classes > 0 then saw_code_block = true end
  return nil
end

function Pandoc(doc)
  if not used_inline or saw_code_block then return nil end

  -- Inline-only document: pandoc would emit no stylesheet at all, leaving the
  -- spans uncolored. Smuggle in a real (hidden) highlighted block so pandoc's
  -- own `code span.*` rules get written out. A RawBlock won't do -- the writer
  -- keys off the AST, not the rendered HTML.
  doc.blocks:insert(pandoc.Div(
    {pandoc.CodeBlock('', pandoc.Attr('', {DEFAULT_LANG}))},
    pandoc.Attr('', {}, {style = 'display:none'})))
  return doc
end

-- Inlines are rewritten before the finalizer needs to know about them, and
-- CodeBlock has to run before Pandoc too, so order the passes explicitly.
return {
  {CodeBlock = CodeBlock, Code = Code},
  {Pandoc = Pandoc},
}
