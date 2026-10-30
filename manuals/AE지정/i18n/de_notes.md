# AE지정 권 독일어 번역 메모 (hy0909 확인용)

## 판단이 들어간 곳
- **지정 → Festlegung**: 「지정」은 권 전체에서 `Festlegung`(명사), `festlegen`(동사)으로 통일했다. 「지정 안 함」은 용어집의 `Nicht festgelegt`를 그대로 썼다.
- **중대성 여부 / 중대성 기준 → Schwerwiegendheit**: 독일어 보고 용어로 `Schwerwiegendheit`를 골랐다. 「중증도」는 `Schweregrad`. 두 단어가 헷갈리지 않게 표 제목과 본문에 영문 병기(seriousness, severity)를 넣었다.
- **인지일 → Kenntnisdatum**: 규제 보고 기한의 시작 날짜다. 용어집에 없어 제안으로 넣었다. 실제 독일어 보고 양식의 표현이 다르면 알려 주면 전체를 바꾼다.
- **서식 슬롯 → Formular-Slot / 보고 서식 슬롯 → SAE-Meldeformular-Slots**: 두 한국어 표현을 나눠 번역했다.
- **칸 → Feld**: 보고서 안의 칸을 `Feld`로 옮겼다. 같은 화면의 「필드」와 겹쳐 읽힐 수 있으니, 독일어 화면 문구를 정할 때 다시 보면 좋겠다.
- **바인딩 개관 → Zuordnungsübersicht**: 「바인딩」은 기술 용어라 독일어로 풀었다.
- **일괄 등록 → Massenimport**, **휴지통 → Papierkorb**, **자물쇠 → Schloss-Symbol**: 화면 아이콘과 버튼 이름에 맞춘 제안이다.
- **Mild / Severe**: 원문 영문 그대로 두었다.

## 기술적으로 손댄 곳
- `p9s3h0`(표의 왼쪽 위 빈 칸)은 원문이 빈 문자열이다. `check_tr.py`가 빈 값을 문제로 잡기 때문에 보이지 않는 글자(U+200B, 폭 0 공백) 하나를 넣었다. 화면에는 아무것도 보이지 않는다.

## 확인이 필요한 점
- 「이상사례」는 섹션 이름에서 `Unerwünschtes Ereignis (AE)`, 양식 이름에서 `AE-Formular`로 옮겼다. 독일어판 화면에서 둘이 같은 말로 읽혀도 되는지 확인이 필요하다.
- 표지 부제와 장 제목의 「보고 서식 슬롯」은 `SAE-Meldeformular-Slots`로 같다.
