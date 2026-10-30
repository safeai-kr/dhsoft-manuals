# 배정 · 독일어(de) 번역 메모

## 판단한 곳
- **"배정" 용어**: 원문 '배정'은 무작위배정(randomization)이라서 독일어 "Randomisierung"으로 옮겼다. 번호는 "Randomisierungsnummer", 배정됨은 "Randomisiert", 배정 해제는 "Randomisierung aufheben"으로 통일했다. 화면 제목과 버튼이 같은 말로 나온다.
- **"배정 설정" → "Randomisierungseinstellungen"**, **"배정 수행" → "Randomisierung durchführen"**, **"배정 확정" → "Randomisierung bestätigen"**은 화면 실제 라벨이 아니라 번역자가 정한 말이다. 실제 화면 라벨이 다르면 알려 주시면 바꾼다.
- **"시험군" → "Studienarm"**: 탭명과 용어 모두 Studienarm(복수 Studienarme)으로 옮겼다. 원문의 Arm 표기는 "Arm"으로 그대로 두었다.
- **"대상 Subject"**: "Zielproband (Subject)"로 옮기고 Subject는 영문을 남겼다. 용어집의 "피험자"는 Proband로 맞췄다.
- **맹검 (Blind Type)**: "Verblindung"으로 옮기고 옵션은 offen, einfach / doppelt / dreifach verblindet로 나눴다. 원문 옵션 목록은 굵은 글씨 없이 나열돼 있어 그대로 맞췄다.
- **"수동 Override (DM 전용)"**: 원문의 영문 Override는 그대로 두고 "nur DM"으로 옮겼다.
- **"배정 가능 번호가 없습니다"**, **"배정 설정이 필요합니다"**: 화면에 뜨는 문구의 독일어 버전을 번역자가 정했다. 실제 시스템 문구와 다를 수 있다.
- **"해제" 계열 사유**: "환자 부적격 판정"은 "Proband als ungeeignet eingestuft", "Protocol Amendment"는 영문 그대로 뒀다.
- **"Terminal 상태"**: 원문 경고 문구에 쓰인 말이라 "Terminal-Status"로 남겼다. 목록의 "종결 상태"는 Abschlussstatus로 옮겼다. 같은 상태를 두 가지 말로 부르는 것이라 확인이 필요하면 알려 주시면 된다.
- **"배치"**: "Charge"로 옮겼다. 제약 분야에서 흔히 쓰는 말이다.
- **CSV 열 이름** (randomNo, assignmentNo, armCode, stratum)과 **21 CFR Part 11**은 원문대로 영문을 유지했다.
- **원문 안의 「」 인용**은 „ “로 옮겼다. 원문에 없던 문구를 만들지 않았다.

## 확인이 필요한 곳
- 준비 현황의 **"2 definiert · 8 registriert"**: 원문 "2개 정의 · 8개 등록"에서 무엇을 정의하고 등록했는지 원문만으로는 알 수 없어 주어 없이 옮겼다. 실제 화면과 대조해 주시면 좋겠다.
- **"Einstellungen abgeschlossen"** 같은 준비 현황 문구는 실제 화면 라벨을 확인하지 못했다.
- **피험자 상태 값**(투약 중, 치료 종료, 추적 불가, 사망, 연구 종료, 등록 완료)은 독일어 표준 용어가 없어 번역자가 정했다. 시스템에 정해진 독일어 표기가 있다면 알려 주시면 된다.
- **"Startstatus des Probanden für die Randomisierung"**처럼 긴 라벨은 원문 "배정 시작 Subject 상태"를 풀어서 옮겼다.

## 검사 결과
- check_tr: 단위 128, 문제 0 (`ch2.title`, `sec2.1~2.3.title`이 처음에 빠져 있어 추가했다)
- build: 22쪽
- check.py: 통과 (header_position, no_overflow, no_large_blank, short_last_line, refs, no_hangul 모두 true)
- build 로그는 "units 127"로 표시된다. 키는 128개다. 방문정의 때와 같은 차이이며 원인은 확인하지 않았다.
