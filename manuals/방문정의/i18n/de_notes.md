# 방문정의 · 독일어(de) 번역 메모

## 판단한 곳
- **Latin 필드명·화면명은 그대로 둠**: Visit Type, Anchor Type, Offset Days, Repeating, Window Before/After, Study Arm, Visit Group, CRF Visit Matrix. 원문 화면에서 영문으로 적힌 이름이라 독일어로 옮기지 않았다. 화면 실물과 대조할 때 이 부분은 그대로 보이면 된다.
- **Visit-Code / Visit-Name / Visit Group-Code**: 원문 한글 "Visit 코드·Visit 명" 표기를 살려 "Visit" + 독일어 "-Code/-Name"으로 옮겼다. 실제 화면 라벨이 다르면 알려 주시면 바꾼다.
- **"선택"이 두 뜻으로 쓰임**: 버튼 "선택"(다중 선택 모드 켜기)은 "Auswählen", 연결 상태 "선택"(OPTIONAL)은 "Optional"로 옮겼다. 같은 한글 단어라 용어집에서도 따로 적었다.
- **"수정"과 "편집"**: 둘 다 "Bearbeiten"으로 통일했다.
- **"연결 조회" / "연결 수정"**: 모드 이름이라 "Verknüpfungen anzeigen" / "Verknüpfung bearbeiten"으로 옮겼다. 화면의 실제 독일어 라벨이 없어 번역자가 정한 말이다.
- **"매핑"은 "Zuordnung", "연결"은 "Verknüpfung"**으로 나눴다. 원문에서 두 말이 같은 뜻으로 섞여 쓰여서 독일어에서도 두 가지로 나눠 흔들리지 않게 했다.
- **"개정본"**: "überarbeitete Fassung"으로 옮겼다. 원문 카드 제목에 쓰인 말이다.
- **"Plan 미리보기"**: "Plan-Vorschau"로 옮기고 Plan은 영문을 그대로 뒀다.
- **연구책임자**: "Principal Investigator (PI)"로 옮기고 PI 약어를 그대로 썼다.
- **정렬값 겹침 경고**: "Sortierwerte überschneiden sich bei N Formularen"으로 옮겼다. 자주 쓰는 말이라 확인이 필요하면 알려 주시면 된다.

## 확인이 필요한 곳
- "구축 단계"와 "테스트 단계", "운영(ACTIVE)"은 독일어 프로젝트 단계 명칭이 따로 정해져 있지 않아 "Aufbauphase", "Testphase", "Betrieb (ACTIVE)"로 임시 번역했다.
- "DRAFT", "PUBLISHED", "SETUP", "ACTIVE"는 시스템 상태 값이라 원문대로 두었다.

## 검사 결과
- check_tr: 단위 135, 문제 0
- build: 21쪽
- check.py: 통과 (header_position, no_overflow, no_large_blank, short_last_line, refs, no_hangul 모두 true)
- build 로그는 "units 134"로 표시된다. 키는 135개인데 빌드가 134로 세는 이유는 확인하지 않았다. check.py는 전부 통과했다.
