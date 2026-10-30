# 프로젝트 권 독일어 번역 메모 (hy0909 검토용)

## 판단이 필요했던 곳
- **상태 이름**: 원문에 영문 공식 표기가 없어 독일어 상태명을 새로 정했다. 설정 중 = In Einrichtung, 테스트 = Test, 운영 중 = Im Betrieb, 종료 = Beendet, 보관 = Archiviert. 화면 실제 표기와 다르면 알려 주면 전체를 바꾼다. SETUP, ACTIVE, CLOSED, ARCHIVED, HARD 는 원문대로 영문으로 두었다.
- **연구자 → Forschungspersonal**: 참여기관 권과 맞추기 위해 쓴 말이다. 원문 "연구자 배정" 메뉴명은 "Zuweisung des Forschungspersonals"로 옮겼다.
- **부작용 배너 (p8s2i7)**: 임상 부작용과 섞이지 않도록 "Auswirkung"으로 옮겼다. 원문이 임상 이상반응이 아니라고 밝혀 둔 부분이다.
- **완전 잠금 → vollständige Sperre**: HARD_LOCK 과 연결되는 말이라 영문 코드는 그대로 두었다.
- **미처리 Query (p12s3i0)**: "offene Queries"로 옮겼다.
- **피험자 순번 → Probandennummerierung**: 전이 후 번호가 1번부터 다시 시작한다는 뜻으로 골랐다.
- **유의사항 참조 표기**: 고정 라벨 "유의사항 = Zu beachten"을 써서 "(siehe 3.1, Zu beachten)" 형태로 옮겼다.

## 화면 문구 (확인 창 제목, 배너, 안내문)
- 큰따옴표 안의 화면 문구는 한국어 원문을 옮긴 것이다. 실제 독일어 UI에 같은 문구가 있는지는 확인되지 않았다. 독일어 화면이 나오면 실제 문구로 맞춰야 한다.

## 원문에 대해 알아 둘 점
- p9s3i0: 원문이 "다음 데이터가"로 시작하지만 목록이 이어지지 않는다는 주의 문구다. 원문 그대로 옮겼다.
- p4s3i0 (보관 정책 미저장): 원문 그대로 옮겼다.

## 용어 정리
- 보관 만료일 = Ende der Aufbewahrungsfrist, 초기 역할 = Anfangsrolle, 집계 = Kennzahlen, 전자서명 = elektronische Signatur (21 CFR Part 11 은 그대로).
- 기관 주도(SIT) 등 연구 유형 코드(IIT · IND · SIT)는 원문대로 두고 풀이만 독일어로 옮겼다.
