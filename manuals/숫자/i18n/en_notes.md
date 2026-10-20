# EN translation notes — Number volume (pilot)

Author: hy0909 · 2026-10-21 · Language: en

Outputs: `glossary/en.json` (146 entries, all `status: "unconfirmed"`), `template/i18n/fixed_en.json` (19), `숫자/data/en.json` (527), `숫자/i18n/image_en.json` (595).
Self-check: keys, Hangul = 0, `<b>`/`<code>`/entity counts, reference numbers `(N.N…)`/`(Ch. N)`/circled numbers, glossary consistency body ↔ image: all PASS.

## [확인 필요] list

### A. Screen terms with no localized UI available (whole glossary)

1. [확인 필요] No English UI was available for checking. Every term in `glossary/en.json` is a proposed standard UI wording. The terms that matter most to confirm: tabs `Basic` · `Type settings` · `Validation` · `UI` · `Conditional`; buttons `Add field` · `Add section` · `Add rule` · `Save` · `Publish` · `Delete field`; labels `SDV target (CRA source data check)` · `Verification required (if unverified, quality PENDING)` · `Allow not-measured declaration` · `Display label` · `Indicator` · `AE semantic role` · `Layout width` · `Read-only (input blocked)` · `Hidden (no UI render · data kept)` · `Enable conditional display (condition)`; values `Value range` · `Block save` · `Warning` · `Not measured` · `Unknown` · `Caution (amber)`.
2. [확인 필요] Capitalization: menu names follow the brief's example (`CRF Management`, `DataForm Design`, `Dashboard`), while other UI labels use sentence case (`Field properties`, `Edit form`, `Type settings tab`). Confirm which convention the real UI uses.
3. [확인 필요] The word "검증" is translated two ways on purpose: `Validation` for the Validation tab and its rules, and `verification` for SDV (`SDV target`, `Verification required`). Confirm this split matches the product.
4. [확인 필요] Sample data values in the captures were translated as screen text: the form title `Subject Baseline Info and Health Status Assessment` (and the trailing part `Health Status Assessment`), the section `Basic information`, the fields `Height` / `Weight` / `Pre-survey info available`, and descriptions such as `Enter the subject's height (cm).` `사전조사 정보 유무` was taken to mean "whether pre-survey information exists". Confirm the meaning.
5. [확인 필요] The rule-count badge `0 개` / `1 개` became `0 items` / `1 item` (body `<code>` and image). Confirm the actual badge text (it might be `0 rules`, for example).

### B. Image segments — boxes that do not cover the whole Korean text

6. [확인 필요] `s1_1_1_021_0`, `s1_1_1_034_0`: only `필드` is in the box and `새` sits outside it. The translation is `New field`, so the box needs to extend left to erase `새`. The structure-tree item `새 필드` in `s1_1_1.png` (around x=75, y=313) has **no segment**, so Korean will remain there.
7. [확인 필요] `s4_2_1_037_0`, `s4_3_1_039_0`: only `범위` is in the box and `값` sits outside it. The translation is `Value range`, so the box needs to extend left.
8. [확인 필요] `s4_2_1_045_0`: the placeholder `예: 값은 0~100 사이여야 합니다.` starts at x=939, but `예:` appears to lie outside the box. The translation includes the prefix (`Ex: The value must be between 0 and 100.`), so the box needs to extend left to erase `예:`.
9. [확인 필요] `s6_1_1.png`: the `value` placeholder `예: M` has **no segment**, so Korean `예` will remain there. Also check whether `s6_2_1.png` has the same placeholder.
10. [확인 필요] `s2_1_1_017_0`, `s2_2_1_016_0`: the note says `는` is on the line above and outside the crop. The segment is translated as `is automatically readonly.` Check that no `는` glyph remains.
11. [확인 필요] `s6_1_1_042_0`, `s6_2_1_040_0`: the leading `BE` is outside the segment, and `권위 평가` was translated as `authoritative evaluation`, so the full line reads `BE authoritative evaluation — hidden fields are exempt …`. The body (6.1 ③) says the system evaluates the condition. Confirm the wording.
12. [확인 필요] `s3_*` "NumberDataConfig 11필드 …" lines: the leading `BE` and the trailing `RF` were kept as-is (developer abbreviations). `후속 RF` was translated as `a follow-up RF`. Confirm the meaning (RF = refactor?).
13. [확인 필요] `s6_1_1_008_0`: the segment `ko` uses a hyphen (`자동 저장 실패 - 수동 저장 권장`), but the capture and the body (6.1) show an em dash. The translation uses `—` (`Auto-save failed — manual save recommended`) to match the body.
14. [확인 필요] Width risk: many translations are much longer than their boxes and probably need more than 85% shrink (rule 11). Main cases: `개` w8 → `items`/`item`; `규칙` w17 → `Rule`; `활성` w17 → `Active`; `검증` w17–18 → `Validation`; `기본` w17–18 → `Basic`; `숫자` chip w18–24 → `Number`; `참조` w18 → `References`; `범위` w19 → `Value range`; `필드` w20 → `field(s)`; `저장`/`발행` w22 → `Save`/`Publish`; `변경됨` w27 → `Modified`; `조건부` w27–28 → `Conditional`; `(같음)` w28 → `(equals)`; `연산자` w28 → `Operators`; `타입 설정` w37–38 → `Type settings`; `다.` w11 → `verification is required.`; `습니다.` w29 → `is added.`; plus the long multi-line help texts (`s1_1_1_045~049`, `s3_4_1_072~081`, `s3_5_1_007~016`). Check what `localize.py` reports.
15. [확인 필요] Multi-line sentences (`s1_1_1_045~049` AE help, `s2_4_*` display label/indicator help, `s3_4_1_072~075` precision warning, `s4_*` bottom notice, `s6_*` example) were translated as whole sentences and then split by line. Line breaks therefore fall at different words than in the Korean.
16. [확인 필요] `s1_1_1_047_0`: the mark between `통보` and `추출` is unclear (`·` or `-`). `·` was kept (`notification·extraction`).
17. [확인 필요] `s3_4_1_073_0`, `s3_5_1_008_0`: it is unclear whether the ellipsis after `1.888` is `...` or `…`. `...` was kept.
18. [확인 필요] Count words that depend on a number outside the box were set per image: `1` → `field`, `2`/`3` → `fields` (`s3_4_1_008_0` → `fields / 2 sections`).

### C. Body text decisions

19. [확인 필요] 3.5 ② `(아래 ‘라.’ 참조)` refers to a Korean list marker (라 = 4th). It became `(See ‘D.’ below)`. Confirm how the EN template labels the other areas (it might be the heading `What you can use in a formula`).
20. [확인 필요] 4.3 ⑤ (`s4.3.g1.i4`): to keep the original tag structure (3 `<b>`, 4 `<code>`) with English word order, the message is split as `<code>Height must be between</code><b><code> 0 and 200</code></b><code>cm</code><b><code>.</code></b>`. In the original, `cm` was inside the bold part; here it is not. In other places the message is `Height must be between 0 and 200cm` (the original `0~200cm` reads as "0 and 200cm").
21. [확인 필요] The Korean legend `참고` (`fixed.lg.ref`) and the card title `참고` (`fixed.card.note`) are both `Note`, because the same text must get the same translation within a document. Confirm the design accepts this.
22. [확인 필요] Tab and card fixed texts: `Overview` / `Screen guide` / `Precautions`; `Must check` / `Easily misunderstood behavior` / `Note`; legend `Setting` · `Where you operate` / `Result` · `What the setting above changes`. These are shared by all 16 volumes, so confirm them before translating the next volume.
23. [확인 필요] `s1.1.g2.i3` keeps `PUBLISH` from `발행(PUBLISH)`, and `s2.1.g2.i3` keeps `PUBLISHED`. Both are as in the original. Note the difference.
24. [확인 필요] `「…」` became `“…”` (`“Value range”`, `“Rule 1”`, `“Pre-survey info available = O”`, `“Project validation rules”`).
25. [확인 필요] Chapter references: `(6장)` → `(Ch. 6)` and `(3장)`/`(4장)` → `(Ch. 3)`/`(Ch. 4)`. Plain-text mentions became `in Chapter 2` and `Chapters 2–6`.
