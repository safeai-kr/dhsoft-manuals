# 데이터내보내기 독일어 번역 메모 (hy0909 확인용)

- **「추출」과 「내보내기」**: 원문에서 두 말이 섞여 쓰인다. 두 말 모두 `Export`(동사 exportieren)로 옮겼다. 「추출 화면」은 `Export-Bildschirm`, 「내보내기 이력」은 `Exportverlauf`.
- **「데이터 내보내기 허브」**: 독일어 화면 이름을 알 수 없어 `Export-Hub`로 옮겼다. AuditTrail 볼륨과 같은 말이다.
- **「범위」**: `Bereich`로 통일했다(예: 범위 지정 → Bereich festlegen, 자기 Site → Eigene Site). 독일어 화면에서 `Umfang`을 쓰면 용어 전부를 고쳐야 한다.
- **「프리셋」**: 독일어로 `Voreinstellungen`이다. 버튼이 화면에 그대로 있다면 독일어 라벨과 맞춰야 한다.
- **「확정 데이터 Export」「테스트 데이터 Export」**: 원문 배너 문구라서 Latin 표기를 그대로 두고 "Bestätigter Datenexport"만 우리말을 옮겼다. 배너 실제 문구가 다르면 알려 달라.
- **「1순위」「2순위」**: `Priorität 1`, `Priorität 2`. 표의 「1순위」 셀은 굵게 유지했다.
- **「N%」「N건」「N Warnungen」**: 숫자 자리 표시는 원문 그대로 두었다.
- **「-」「—」「~ 현재」「→」 기호**: 화면에 찍히는 기호라서 그대로 두고, 설명 글만 옮겼다.
- **「PI」 대신 「Hauptprüfer」**: 역할명(AuditTrail과 같다)을 쓰면서 원문에 없는 PI 표기를 넣지 않았다. 본문에 「연구책임자」는 나오지 않지만 `Hauptprüfer` 표기는 AuditTrail과 맞췄다.
- **「모니터요원」**: `Monitore`로 옮겼다(CRA 표기는 원문에 없어서 넣지 않았다).
- **「CRF 첨부 파일」**: `CRF-Anhänge`. 원문의 "첨부 원본은 별도 절차로" 문장은 `über ein gesondertes Verfahren`으로 옮겼다. 실제 절차가 있다면 용어를 맞춰야 한다.
- **「마스킹 해제 사유는 기록되지 않습니다」**: 원문 그대로 옮겼다. 독일어 화면 문구와 다르면 알려 달라.
- **`COLUMN_UNION`, `PER_VERSION`, `HARD_LOCK`, `OPEN + ANSWERED`, `CLOSED`, `ext_`, `entryRef`**: 코드 값은 모두 원문 그대로 두었다.
- **「회차」**: `Wiederholung`(열 이름 맥락). 원문에 "방문 회차"로 나와 있어 같은 뜻으로 판단했다.
- **「지문값」**: `Fingerabdruck`. SHA-256 해시 값을 가리킨다. 독일어 화면에서 `Prüfsumme`을 쓰면 여기도 바꿔야 한다.
