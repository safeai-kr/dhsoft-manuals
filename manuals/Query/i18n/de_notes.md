# Query 권 독일어 번역 메모 (hy0909 확인용)

## 판단이 들어간 곳
- **취소**: 버튼은 `Abbrechen`, 상태 값(폐기된 Query)은 `Abgebrochen`으로 나눴다. 원문은 같은 낱말이라 용어집 규칙(한 낱말 한 번역)과 어긋난다. 한 가지로 통일하려면 상태를 `Verworfen`으로 바꾸면 된다.
- **종료 / 닫기 / 종결**: 동작 `종료`는 `abschließen`(Query abschließen), 상태 `종료`는 `Abgeschlossen`, 창 닫기 `닫기`는 `Schließen`, `종결`도 `Abschließen`으로 옮겼다. 종결과 종료가 같은 독일어가 된다.
- **재질의**: 상태는 `Erneut angefragt`, 동작 이름은 원문대로 `Reopen`을 쓰고 제목은 `Erneute Anfrage (Reopen)`.
- **미처리**: `Unbearbeitet`으로 옮겼다. 원문 `OPEN`은 영문 그대로 두었다.
- **경과(일)**: `Dauer (Tage)`. `Alter`도 가능하다.
- **해소**: `Klärung`으로 옮겼다. 해소 상태는 `Klärungsstatus`.
- **집계 / 집계 카드**: `Kennzahl` / `Kennzahlkarten`.
- **역할 이름**: 데이터 관리자는 `Datenmanager`, 모니터요원은 `Monitor`, 연구책임자는 `Prüfarzt`, 감사자는 `Auditor`, 등록자는 `Ersteller`로 옮겼다. 독일어 화면 용어가 따로 정해진 것이 없어서 제안이다.
- **Query 범위**: `Query-Umfang`. 열 이름인 `Scope`는 원문대로 둔다.

## 그대로 둔 Latin 표기
OPEN, ANSWERED, CLOSED, Reopen, Severity, Scope, Visit, Screening No, 화면 코드(SCR-QA-003 …), `(reopen #1)` 표시.

## 확인이 필요한 점
- 독일어판 실제 화면에 이 번역이 그대로 나오는지는 개발 쪽 용어와 맞춰 봐야 한다. 특히 버튼 이름(Abschließen, Antworten)과 상태 이름(Beantwortet, Abgeschlossen)은 화면 문구표와 한 번 대조하는 것이 좋다.
- 원문 `1.1`처럼 `<span class="ref">`가 없는 참조 번호는 원문 그대로 평문으로 두었다.
