# Translation brief — SMART EDC user manual, screen-by-screen volumes (화면별 분권)

Product: SMART EDC, an electronic data capture (EDC) system for clinical trials by DH Soft (Korean UI). These volumes explain the application screens (login, my account, projects, subjects, visits, data entry, queries, locks, audit trail, export, roles, …) for clinical data managers, CRAs, investigators and site staff. Register: precise technical manual.
Repository: /Users/khy/dhsoft_261016/dhsoft-manuals

## Input
`manuals/<VOL>/data/units_ko.json` — array of {key, kind, ko}. `ko` is an HTML fragment. `kind`:
- `title` document title · `cover` cover title / subtitle · `h1` chapter title (TOC + divider) · `h2` section title (TOC + page header; keys `secX.Y.title` and `pN.title` with the SAME Korean text must get the SAME translation) · `h3` tab title of an extra section · `path` one breadcrumb item · `overview` overview paragraph · `desc` numbered screen description (may start with `<b>label</b> — …`) · `caption` figure caption · `notice` precaution card item · `list` plain list item · `th` table header cell · `td` table cell.
Shared reference material (read first):
- `glossary/<lang>.json` — UI terms already used in the 16 CRF volumes ({ko, tr, type, …}). Reuse the same translation for the same Korean term whenever it appears.
- `template/fixed.json` — fixed design labels per language (Overview / Screen guide / Precautions, Setting / Result / Note, Must check …). These are NOT in the units, but your body text must use the same words when it mentions them.

## Output (all under `manuals/<VOL>/`)
1. `data/<lang>.json` — JSON object {key: translated HTML string} containing EVERY key of units_ko.json. Valid JSON (escape quotes). No extra keys.
2. `i18n/glossary_<lang>.json` — array of {"ko", "tr", "type": "button|tab|menu|label|field|value|status|term|message|path", "note": ""} for every UI label / button / tab / menu / screen text / status value / example value you translated that is NOT already in glossary/<lang>.json, plus recurring domain terms. One translation per Korean term.
3. `i18n/<lang>_notes.md` — written in Korean for the designer (hy0909): short list of places where the meaning was unclear, where a real localized UI wording is unknown, or where you made a judgement call. Do NOT put "[확인 필요]" or any note inside the translated text.

`<lang>` is `en`, `de` or `ja`.

## Hard rules (fidelity — from the design prompt, section 1)
- Translate meaning faithfully. Do not add, drop, soften or strengthen anything: no new steps, conditions, warnings, examples, numbers. Keep negations, must/only/always/never, quantities, units, dates and decimals exactly. You may reorder words or split a long sentence for natural reading, but keep all information.
- Keep every HTML tag with the same count and nesting: `<b>…</b>`, `<code>…</code>`, `<span class="ref">…</span>`, `<span class="lcir …">…</span>` (never change the inside of an lcir span). Bold may move with word order but must cover the same meaning. Do not add tags. Do not use HTML entities except `&amp; &lt; &gt;` where the source has them.
- References `<span class="ref">2.1</span>`, `<span class="ref">2.1 · 2.3</span>` stay digits unchanged; chapter refs `<span class="ref">2장</span>` become en `Ch. 2`, de `Kap. 2`, ja `第2章`. Nothing else goes inside the span. The source keeps a trailing period or text after the span — keep that too.
- Never translate code identifiers, enum values, screen codes, field keys, file names or Latin input values: SCR-ACC-001, HARD_LOCK, FREEZE, SOFT_LOCK, OPEN, ANSWERED, CLEAN, NOT_CREATED, IN_PROGRESS, COMPLETED, PI, CRC, CRA, DM, AUDITOR, SDV, AE, SAE, CRF, Query, Lock, UUID, entryRef, VisitGroup, mg/dL … Keep them exactly. `Query`, `Lock`, `Audit Trail`, `Site` are product terms used in Latin letters inside Korean text — keep them as-is (ja: keep Latin, half-width).
- Korean UI labels (button/tab/menu/screen names, status badges such as 미처리 · 답변됨, example values) ARE translated, consistently, using the glossary; add new ones to your glossary file.
- Bracket conventions: `[ ]` around buttons stays `[ ]`. Korean corner quotes 「X」 → en “X”, de „X“, ja 「X」. Korean “X” / ‘X’ → en “X” / ‘X’, de „X“ / ‚X‘, ja 「X」 / 『X』.
- Em dash ` — ` separators, middle dots ` · ` between list-like items, and the `<b>label</b> — description` pattern at the start of desc items are layout conventions: keep them (ja: keep ` — ` and ` · ` with the surrounding half-width spaces as in the source).
- Section titles must be translated identically everywhere they occur (`secX.Y.title`, `pN.title`, cover subtitle mentions). Chapter titles likewise.
- Output must contain NO Hangul at all (U+AC00–U+D7A3 etc.). No "[확인 필요]", no Korean in parentheses next to the translation.
- Leading/trailing spaces in `ko` must be preserved.

## Style per language (single source of truth — the design prompt 1절 points here; revised 2026-11-09)
Common rules (all languages):
- Procedure sentences: the action comes first and its condition stays in the same sentence. Keep the source's number and order of steps; only word order inside a sentence may change.
- Precaution cards: the hazard, its consequence and how to avoid it must all survive translation. Keep the source sentence structure. After translating, compare every must / never / only / cannot against the source — same strength, nothing softened or sharpened.
- Terminology: same function, same term. Reuse `glossary/<lang>.json` and `template/fixed.json`; one Korean UI label gets one translation, identical in body text and in screenshot text.
- Review sheet (append to `i18n/<lang>_notes.md`): read the finished volume once against six questions — perceptibility (readable in the layout), simplicity (plain wording), structure (order and grouping intact), correctness (facts, numbers, references), concision (no padding), motivation (the reader can tell why a step matters). Record only the problems found; no scores.
- Reader check (optional, decided by hy0909): one or two native users per language perform a task from the volume. Note here anything a reviewer could not judge alone.
Per language:
- en: US English, concise manual style, imperative for instructions, "you" for the reader, sentence case for headings. Keep the source's item count and grouping; do not split items or add abbreviation explanations. Do not split sentences by default — only when the meaning would otherwise blur. After translating, list procedure sentences longer than 20 words in `i18n/en_notes.md` (a checklist for review; do not rewrite them automatically).
- de: formal "Sie", clear technical German. Render source conditions as German conditional clauses and keep the result in the same paragraph; split a sentence only when the meaning would otherwise blur. Do not shorten long compound terms — width and line breaks are the layout's job. No soft hyphens. Decimal numbers stay as in source (they are input values). Sentence-style headings.
- ja: です・ます調 for explanations, polite instructions (「〜を選択してください」) for operations; state mandatory conditions and prohibitions clearly (do not soften). Keep every explanatory sentence of the source; where a Japanese reader would lose the link between two sentences, choose a connective within the source's meaning — never reorder items. Standard IT terminology (フィールド, タブ, 保存, 発行, ログイン …). Full-width 、。 in Japanese sentences; Latin tokens half-width; no spaces between Japanese words, a space only around Latin tokens where natural.

## Procedure
1. Read `glossary/<lang>.json`, `template/fixed.json`, and the volume's `units_ko.json` (+ `data/model.json` only if you need more context).
2. Translate; write the three output files.
3. Run `python3 template/check_tr.py <VOL> <lang>` from the repository root and fix until it reports `문제 0`.
4. Build and check the HTML: `python3 -W ignore template/build.py <VOL> <lang>` then `python3 template/check.py <VOL> <lang>` (from the repository root; needs Chrome + Playwright, both installed). Report the page count and the check result line. If `no_overflow` or `header_position` fails, say so — do not change template files.
5. Report: check output, page count, 3–5 example translations, and the notes you wrote.
Do not edit anything under `template/`, `glossary/`, or another volume's folder.
