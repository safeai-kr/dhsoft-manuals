# 검수 기록 — CRF 숫자 · 독일어(de)

작성: hy0909 · 2026-10-21 · 입력: `data/units_ko.json`(546) · `i18n/image_segments_ko.json`(595 / 22장)

출력: `glossary/de.json`(139항목, 전부 `status: "unconfirmed"`) · `template/i18n/fixed_de.json`(19) · `숫자/data/de.json`(527) · `숫자/i18n/image_de.json`(595)

자체 검사(키 개수·누락, 한글 0, `<b>`/`<code>`/엔티티 개수, 괄호 참조 `(N.N…)`·`(N장)→(Kap. N)`, 용어집–본문–이미지 일치): 전부 통과.

---

## A. 원문·화면 확인이 필요한 곳

1. **[확인 필요] s3_4_1 캡처의 BMI 계산식이 본문과 다름.** 화면 계산식은 `{weight} / ({height} * 100)^2`(100을 곱함)인데, 본문 s3.4.g2.i0 · s3.5.g2.i2는 `{height} / 100`(100으로 나눔)으로 설명함. 캡처의 식은 코드라 번역하지 않았음. 원본 캡처를 그대로 둘지, 매뉴얼 설명과 맞는 캡처로 바꿀지 결정 필요.
2. **[확인 필요] s6_2_1 캡처의 value가 `O`(영문자)인지 `0`(숫자)인지.** 본문 s6.2.g1.i2 · i3 · cap0은 `value = O`, 배지 `… eq O`로 설명하지만, 캡처의 입력란과 배지는 `0`처럼 보임(OCR도 `eq 0`). 번역문은 원문대로 `O`로 둠.
3. **[확인 필요] 글자 일부가 덩어리 상자 밖에 있는 곳.** 아래 덩어리는 한국어 글자가 상자 밖에 남아 있음. 번역문에는 빠진 뜻까지 넣었으니, 이미지에서 글자를 바꿀 때 지우는 영역을 넓혀 줘야 함(안 그러면 한글이 남음).
   - s1_1_1_021_0 · s1_1_1_034_0 `필드` → `Neues Feld`(앞의 `새`가 상자 밖)
   - s2_1_1_017_0 · s2_2_1_016_0 `자동 readonly.` → `automatisch readonly.`(앞의 `는`이 상자 밖)
   - s3_6_1_026_0 `… 는 후속 RF —` → `… folgen in späterem RF — dieser`(줄 끝 `본`이 상자 밖)
   - s4_2_1_037_0 · s4_3_1_039_0 `범위` → `Wertebereich`(앞의 `값`이 상자 밖)
   - s4_2_1_045_0 `값은 0~100 사이여야 합니다.` → `z. B.: Wert muss zwischen 0~100 liegen.`(앞의 `예:`가 상자 밖)
4. **[확인 필요] 화면 원문 판독이 불분명한 곳(note 기준).** s1_1_1_047_0 `통보·추출`의 구분 기호(`·`/`-`)는 `·`로 둠. s3_4_1_073_0 · s3_5_1_008_0 `1.888...`의 말줄임은 `...`로 둠.
5. **[확인 필요] `ACTIVE 이후 PUBLISHED 는 자동 readonly.`(fieldKey 안내)의 뜻.** “ACTIVE를 거친 뒤 PUBLISHED가 되면 읽기 전용”으로 읽고(본문 s2.1.g2.i3 기준) 화면 글자는 `Nach ACTIVE ist PUBLISHED automatisch readonly.`로 직역함. 실제 의미가 다르면 화면 글자와 s2.1.g2.i3을 함께 고쳐야 함.
6. **[확인 필요] `권위 평가`(조건부 탭 안내 앞머리, BE 표시 뒤).** 서버가 최종 판정한다는 뜻으로 보고 `Maßgebliche Auswertung`으로 번역함. 본문(s6.1.g1.i2)은 이 부분을 인용하지 않음.
7. **[확인 필요] s3.5.g1.i1 `(아래 ‘라.’ 참조)`.** 한국어 순서 기호 ‘라’(네 번째)를 `„D.“`로 옮김. 독일어 템플릿이 기타 영역(s3.5.g2.h „Verwendbare Elemente in Formeln“)에 실제로 어떤 순서 표기를 붙이는지 확인 필요. 표기가 다르면 이 문장만 고치면 됨.
8. **[확인 필요] 화면 표기 전체가 미확인.** 독일어 UI 화면 자료가 없어 버튼·탭·라벨·안내문·선택지를 모두 용어집 기준으로 새로 정했음(139항목 전부 `unconfirmed`). 실제 독일어 UI가 생기면 용어집을 먼저 고치고 본문·이미지에 다시 적용해야 함. 특히 확인할 것:
   - 탭: `Allgemein` · `Typeinstellungen` · `Validierung` · `UI` · `Bedingt`
   - 버튼: `Feld hinzufügen` · `Abschnitt hinzufügen` · `Regel hinzufügen` · `Speichern` · `Veröffentlichen` · `Bearbeiten` · `Vorschau` · `Feld löschen`
   - 라벨: `„Nicht gemessen“ zulassen` · `SDV-Verifizierung (CRA-Quelldatenabgleich)` · `Verifizierung erforderlich (unverifiziert: Qualität PENDING)` · `AE-Bedeutungsrolle` · `Anzeigelabel` · `Indikator` · `Schreibgeschützt (Eingabe gesperrt)` · `Ausblenden (kein UI-Rendering · Daten bleiben erhalten)` · `Layoutbreite`
   - 값: `Wertebereich` · `Speichern blockieren` · `Warnung` · `Voll / Halb (1/2) / Drittel (1/3) / Viertel (1/4)` · `Achtung (amber)` · `Keine` · `Unbekannt`
   - 경로: `CRF-Verwaltung › DataForm-Design › Formular bearbeiten › Feldeigenschaften › Tab „…“`
9. **[확인 필요] 이미지 글자 길이.** 독일어가 한국어보다 훨씬 길어서 595개 중 대부분이 원래 상자 폭을 넘음(글자 폭 대략 추정). 칸 안 줄바꿈 또는 85%까지 축소로 처리하고, 그래도 안 들어가는 덩어리는 글자 교체 단계에서 이미지별로 다시 기록해야 함. 특히 넘침이 심한 곳:
   - 좁은 칩·탭: `발행`→`Veröffentlichen`(22px), `편집`→`Bearbeiten`(20px), `신장`→`Körpergröße`(19~26px), `검증`→`Validierung`(17px), `기본`→`Allgemein`(17px), `개`→`Regeln`(8px), `예`→`z. B.`(10px), `범위`→`Wertebereich`(19px), `미측정`→`Nicht gemessen`(31px), `미상`→`Unbekannt`(21px)
   - 긴 안내: `자동 저장 실패 - 수동 저장 권장`(160px), `숨김 (UI 미렌더 · 데이터 보존)`(171px), `같은 폼 내 1개 형제 필드 자동완성 …`(250px), 줄 나뉜 안내문(`… 선언 시` / `값이 삭제되고 …`, `precision 미지정 …` 4줄, `여기 규칙은 …` 2줄)
   - 줄을 나눈 덩어리는 문장 전체를 번역한 뒤 원래 줄 수에 맞춰 나눴으므로, 줄바꿈 위치를 바꾸면 위아래 덩어리를 함께 조정해야 함.

## B. 번역 판단 기록

10. **[확인 필요] 「」의 독일어 따옴표.** 지침 규칙 5는 EN·DE에서 「」→ `“…”`라고 하지만 규칙 7(DE)은 독일어 따옴표 „…“를 쓰라고 함. 독일어 문서 안에서 따옴표를 하나로 맞추려고 「」와 “…” 모두 „…“로 옮김. `“…”`로 통일해야 하면 일괄 치환하면 됨. 화면 문구의 영문 큰따옴표 `"…"`는 화면 그대로 유지.
11. **[확인 필요] ‘검증’의 구분 번역.** 같은 ‘검증’을 뜻에 따라 나눔: 검증 탭·검증 규칙 = `Validierung(sregel)`, SDV 검증 = `Verifizierung`, 필수 검증·required 검증 = `Pflichtprüfung` / `required-Prüfung`. ‘SDV 검증 대상’은 `SDV-Verifizierung`(‘대상’은 라벨에서 생략, 본문에서는 „für SDV festlegen“ 식으로 풀어 씀).
12. **[확인 필요] `사전조사 정보 유무`.** `Voruntersuchungsdaten vorhanden`으로 번역함. ‘사전조사’가 스크리닝·사전 설문 중 무엇인지에 따라 단어가 달라질 수 있음.
13. **[확인 필요] 다른 분권과 맞춰야 할 이름.** `검사 패널 계열 필드` → `Feld der Untersuchungspanel-Familie`, `테이블형 · 필드 그룹` → `Tabellen und Feldgruppen`, `단일 행 텍스트` → `einzeiliger Text`, `임상 대상자 기본정보 및 건강상태 평가서`(화면 폼 이름) → `Probanden-Basisdaten und Gesundheitsbewertung`. 각 분권을 번역할 때 같은 용어집으로 맞춰야 함(잘린 제목 `건강상태 평가서` → `Gesundheitsbewertung`은 이 번역어의 뒷부분).
14. **[확인 필요] 고정 문구(16분권 공통).** `Überblick` · `Bildschirmbeschreibung` · `Zu beachten`(유의사항 탭) · `Einstellung`/`Ergebnis`/`Hinweis`(설정·결과·참고 안내) · `Unbedingt prüfen` · `Leicht missverständliches Verhalten` · `Hinweis`(참고 카드) · `Datenschäden · Formular nicht abschließbar` · `Pfad` · `Inhaltsverzeichnis` · `Titelseite` · 표지 `Elektronisches Datenerfassungssystem für klinische Studien` / `Benutzerhandbuch · Teilbände nach Formulartyp`. ‘참고’ 안내와 ‘참고’ 카드는 같은 `Hinweis`. 승인 필요.
15. 개수가 붙는 화면 글자는 숫자에 맞춰 단·복수를 나눔: 섹션 머리 `1 필드` → `Feld`, `2 필드` → `Felder`(s3_4_1_026_0 · s6_1_1_030_0 · s6_2_1_025_1); 규칙 수 배지 `0 개` → `Regeln`, `1 개` → `Regel`. 본문 `<code>0 개</code>` · `<code>1 개</code>`도 `0 Regeln` · `1 Regel`로 맞춤.
16. 숫자 형식은 바꾸지 않음: `36.8`, `2.00`, `10.00`, `0~200cm`, `0~100`(소수점 쉼표·범위 기호 현지화 안 함). `①~③`, `②~④`도 원문 기호 유지.
17. 화면 인용과 맞추려고 본문 인용을 소문자로 시작한 곳: s2.4.g2.i1 „bei Erklärung wird …“, s6.1.g1.i2 „ausgeblendete Felder …“(화면 문장의 중간부터 인용하기 때문).
18. 원문 대시 차이 유지: 본문은 “자동 저장 실패 — 수동 저장 권장”(—), 화면은 `-`. 각각 원문 기호를 따름(검사 스크립트는 대시를 무시하고 비교).
