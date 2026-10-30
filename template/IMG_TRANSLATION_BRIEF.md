# Translation brief — text inside screen captures (화면 캡처 속 글자)

Repository: /Users/khy/dhsoft_261016/dhsoft-manuals. Product: SMART EDC (clinical-trial EDC, Korean UI). Each volume's screenshots still show Korean UI text; we erase that text pixel-wise and redraw your translation in the same spot. So every string must be short enough to fit a UI widget and must match the body text of the same volume word for word.

## Input (all under `manuals/<VOL>/`)
- `img/loc/strings_ko.json` — array of {id, ko, role, lines, truncated}. `ko` is the exact Korean on screen. `role`: button · tab · badge (status chip) · header (table header) · status · label (field label / menu item) · placeholder (grey example text in an input) · title · breadcrumb · text (sentence / help text). `lines` > 1 means a wrapped paragraph that will be re-wrapped. `truncated` = ends with … or is cut by its box.
- `data/units_ko.json` + `data/<lang>.json` — the body text and its translation (same keys). When a screen string also appears in the body (a button name in `[ ]`, a status value, a tab, a screen title, a menu path item), use EXACTLY the body wording.
- `i18n/glossary_<lang>.json` — this volume's glossary ({ko, tr, type, note}). Mandatory.
- `glossary/<lang>.json` — repo-wide glossary from the CRF volumes ({ko, tr, type, status, where}). Use it when the volume glossary has no entry.

## Output
`manuals/<VOL>/i18n/image_<lang>.json` for `<lang>` = en, de, ja: a JSON object {ko: translation} with one entry for EVERY distinct `ko` in strings_ko.json (key must be byte-identical to `ko`). Then append any new UI term (not yet in `i18n/glossary_<lang>.json`) to that glossary file as {"ko","tr","type","note":"image"}; keep existing entries unchanged. Do not edit any other file.

## Rules
- Same Korean → same translation everywhere, in all three files and in the body.
- Keep code identifiers, enum values, Latin tokens, numbers, units, dates, e-mail addresses, UUIDs exactly (SCR-ACC-001, HARD_LOCK, OPEN, PI, CRA, DM, SDV, AE, SAE, CRF, Query, Lock, Audit Trail, Site, mg/dL, KoNECT…). Only the Korean words change: `5회 실패 시` → "after 5 failures". Proper names of institutions / people in the mock data: en/de transliterate (연세대학교 원주세브란스기독병원 → "Yonsei University Wonju Severance Christian Hospital"; 황민승 → "Minseung Hwang"), ja use katakana or common Japanese rendering (延世大学校 原州セブランス基督病院, ファン・ミンスン). Keep that mapping consistent.
- Length matters: for role button/tab/badge/header/status/label keep it as short as a real localized UI would (en "Save", de "Speichern", ja "保存"; en "Stay logged in", not "Keep me logged in on this device"). Standard UI words: en Log in / Log out / Search / Add / Edit / Delete / Cancel / Confirm / Save / Reset / Export; de Anmelden / Abmelden / Suchen / Hinzufügen / Bearbeiten / Löschen / Abbrechen / Bestätigen / Speichern / Zurücksetzen / Exportieren; ja ログイン / ログアウト / 検索 / 追加 / 編集 / 削除 / キャンセル / 確認 / 保存 / リセット / エクスポート. ja: ルール→規則, count badges フィールド→項目 (hy0909 decision). Do not invent abbreviations that are not standard; if a string cannot be short, translate it faithfully anyway (the renderer shrinks it and flags it).
- role placeholder / text: natural full sentence, same meaning, nothing added or dropped. Keep trailing punctuation as in source (`.`, `…`, `?`).
- Separators ` · `, ` — `, `/`, `→`, parentheses: keep as in the source.
- Output must contain no Hangul at all. No notes inside values. Valid JSON (escape quotes).
- en: sentence case for labels ("Project settings"), US spelling. de: Sie-form, nouns capitalized, no soft hyphens. ja: です・ます for sentences; labels as nouns; half-width Latin, full-width 、。 only in Japanese sentences.

## Check
From the repository root run:
`python3 template/check_img_tr.py <VOL>` — must report `문제 0` for all three languages. Fix and re-run until it does. Report in Korean, two or three lines: how many strings, what you could not decide (and why).
