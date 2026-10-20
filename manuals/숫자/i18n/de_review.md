# 교차 검수 기록 — CRF 숫자 · 독일어(de)

작성: hy0909 · 2026-10-21 · 기준: REVIEW_BRIEF.md, TRANSLATION_BRIEF.md, 고정프롬프트 1·9·11절
대상: `숫자/data/de.json`(527) · `template/i18n/fixed_de.json`(19) · `숫자/i18n/image_de.json`(600, 교정·추가분 포함) · `glossary/de.json`

결과: 본문 6건, 이미지 11건(같은 문구 반복 포함) 수정. 키 추가·삭제 없음. 한글 0자, `<b>`·`<code>`·엔티티·①~④·⛔/⚠·괄호 참조 개수 원문과 동일(스크립트 확인). 숫자 대조 차이는 `앞자리 0`→„führende Nullen“, `1차`→„primäre“뿐(의미 동일).
`python3 template/build.py 숫자 de` 오류 없음(units 546, refs 53). 이미지 글자 변경 반영을 위해 `template/localize.py 숫자 de`를 다시 실행함(스크립트 수정 없음). PDF는 다시 만들지 않음.

## 수정 표

| id | 원문 | 수정 전 | 수정 후 | 이유 |
| --- | --- | --- | --- | --- |
| s2.1.g1.i4 | 아래 유의사항을 반드시 확인하십시오 | beachten Sie unbedingt die Hinweise unten | prüfen Sie unbedingt den Abschnitt „Zu beachten“ unten | 용어(유의사항 탭 = „Zu beachten“, „Hinweis“는 참고 카드와 겹침) |
| s3.1.g1.i3 | (아래 유의사항 참조) | (Siehe Hinweise unten) | (Siehe „Zu beachten“ unten) | 용어(같은 이유) |
| s2.2.g2.i2 | 필수로 지정해도 필수 집계에서 자동 제외됩니다 | werden auch als Pflichtfeld automatisch aus der Pflichtfeldzählung ausgenommen | werden auch dann automatisch aus der Pflichtfeldzählung ausgenommen, wenn sie als Pflichtfeld festgelegt sind | 문체(‘지정해도’ 조건을 분명히) |
| s3.5.g3.i1 | 필수로 지정해도 필수 집계에서 자동 제외됩니다 | werden sie auch als Pflichtfeld automatisch … ausgenommen | werden sie auch dann automatisch … ausgenommen, wenn sie als Pflichtfeld festgelegt sind | 문체(같은 이유) |
| s3.4.g2.i1 | 폼은 그대로 저장됩니다 | das Formular wird unverändert gespeichert | das Formular wird trotzdem gespeichert | 오역(‘unverändert’는 내용이 안 바뀐다는 뜻으로 읽힘. 원문은 ‘계산 실패와 상관없이 저장됨’) |
| s3.6.g2.i0 | 확인되지 않은 수치가 그대로 저장됩니다 | wird ein Wert gespeichert, bei dem … | wird ein Wert unverändert gespeichert, bei dem … | 누락(‘그대로’) |
| s1_1_1_031_0 · s2_1_1_016_0 · s2_2_1_015_0 | … ACTIVE 이후 PUBLISHED (+ 다음 줄 ‘는 자동 readonly.’) | … Nach ACTIVE ist PUBLISHED | … Nach ACTIVE ab PUBLISHED | 오역(‘PUBLISHED가 readonly’로 읽힘. 본문 2.1 ④: ACTIVE 이후 PUBLISHED가 되면 fieldKey가 읽기 전용) |
| s1_1_1_047_0 | ‘SAE 여부’ | ‚SAE ja/nein‘ | „SAE ja/nein“ | 문체(따옴표 „…“ 통일) |
| s1_1_1_051_0 · s2_4_1_001_0 · s2_4_2_001_0 | "미측정" 체크박스 | die Checkbox "Nicht gemessen" | die Checkbox „Nicht gemessen“ | 문체(따옴표 통일, 본문 2.4 ①과 같은 글자) |
| s2_4_1_005_0 · s2_4_2_005_0 | 비워 두면 "미측정". | Leer = "Nicht gemessen". | Leer = „Nicht gemessen“. | 문체(따옴표 통일) |
| s3_4_1_075_0 · s3_5_1_010_0 | (의도한 자리수)가 있으면 지정하세요. | bitte festlegen. | ggf. festlegen. | 누락(‘있으면’ 조건) · 길이 |

코드 값의 영문 큰따옴표(`fieldKey="gender"` 등, s6_1_1_052_0 · s6_2_1_051_0, 본문 `&quot;`)는 코드라 그대로 둠.

## 길이(quality-manifest flags) 검토

flags 252개(재생성 후). 같은 뜻의 더 짧은 표준 UI 표현이 없어 그대로 둔 주요 항목: `Veröffentlichen`(발행, 22px) · `Bearbeiten`(편집) · `Abschnitt hinzufügen`(섹션 추가) · `Typeinstellungen` · `Wiederholungsformular` · `Körpergröße` · `Ausblenden (kein UI-Rendering · Daten bleiben erhalten)`. `Publizieren`·`Größe`는 더 짧지만 본문 전체(Veröffentlichung · Körpergröße)와 함께 바꿔야 하고 뜻이 덜 분명해 바꾸지 않음. 재생성 뒤 새로 생긴 flag(s*_000_2 `DataForm-Design` 0.808 등 12개)는 이번 수정과 무관한 덩어리임(스크립트 판정 변경으로 보임).

## [확인 필요]

1. **s3.5.g1.i1 `(아래 ‘라.’ 참조)`** — 원문 자체 문제. 현재 템플릿은 기타 영역 제목(s3.5.g2.h „Verwendbare Elemente in Formeln“)에 ‘라.’ 같은 순서 기호를 붙이지 않아 한국어판·독일어판 모두 가리키는 대상이 보이지 않음. 원문을 `(아래 ‘계산식에 쓸 수 있는 것’ 참조)`로 고칠지 결정 필요. 번역은 원문대로 „D.“ 유지.
2. **s3_4_1 캡처 BMI 식 `{weight} / ({height} * 100)^2`** — 본문 3.4·3.5의 `{height} / 100`과 반대(번역자 메모 1번과 같음). 원문·캡처 확인 필요.
3. **s6_2_1 캡처의 value `O`/`0`** — 번역자 메모 2번과 같음. 원문 확인 필요.
4. **`ACTIVE 이후 PUBLISHED 는 자동 readonly.`의 정확한 뜻** — „Nach ACTIVE ab PUBLISHED automatisch readonly.“로 고쳤으나 원래 화면 의도(ACTIVE와 PUBLISHED 둘 다인지)는 확인 필요.
5. **`미측정 선언` → „Erklärung“** — 독일어에서 ‘설명’으로도 읽힐 수 있음. 실제 독일어 UI가 생기면 „Markierung als ‚Nicht gemessen‘“ 등으로 본문·이미지·용어집을 함께 바꿀지 검토.
6. **`SDV 검증 대상` → „SDV-Verifizierung“** — ‘대상’이 라벨에서 빠짐(번역자 메모 11번). 화면 폭 때문에 유지.
7. **이미지 글자 넘침** — 위 길이 항목과 번역자 메모 9번. 65% 고정·넘침 덩어리는 글자 교체 단계에서 줄바꿈 처리 여부를 이미지별로 확인해야 함.
8. 번역자 메모 3번(상자 밖 한글 글자 — 덮어쓰기 영역 확장 필요)·6번(`권위 평가`)·12~14번(사전조사·분권 공통 이름·고정 문구)은 그대로 유효. 메모 10번(따옴표)은 이번 지시로 „…“ 통일 확정.
