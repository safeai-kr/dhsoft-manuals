# 영문 번역 메모: 플랫폼관리 권

2026-10-30 · 언어: en

산출물: `플랫폼관리/data/en.json`(156개 키), `플랫폼관리/i18n/glossary_en.json`(82개 항목).
자동 검사: `check_tr.py 플랫폼관리 en` 결과 「문제 0」.

## 1. 확인 필요

### 1-1. 화면 메뉴와 버튼 영문 이름은 제안이다

참고할 영문 화면이 없어서 메뉴·버튼·탭 이름은 모두 제안입니다. 특히 아래 이름을 먼저 확인해 주세요.

- 메뉴: `Platform menu` · `System settings` · `Code management` · `Access log` · `Operation history`
- 버튼: `Restore default` · `Cancel` · `Reset` · `Add` · `CSV export`
- 탭: `All` · `Security` · `Session` · `Notification` · `File` · `General`

### 1-2. 「접속 로그」 영문 이름

파일 이름이 `login-history_…csv`로 되어 있습니다. 메뉴 이름을 `Access log`로 썼는데, `Login history`가 맞는지 정해 주세요. 파일 이름 형식(`yyyymmddThhmm`)도 실제 파일과 맞는지 확인이 필요합니다.

### 1-3. 「전체」 탭 이름

공용 용어집(`glossary/en.json`)에서 「전체」는 「Full」(레이아웃 너비)로 정해져 있습니다. 이 권에서는 카테고리 탭 이름이라 `All`로 번역했습니다. 두 뜻을 같은 영문으로 쓸지, 용어집을 바꿀지 정해 주세요. 용어집 파일은 건드리지 않았습니다.

### 1-4. 「undefined」 표시

운영 이력의 「대상」 열 앞부분에 `undefined`가 나온다는 설명이 원문에 있습니다. 번역문에도 `undefined`를 그대로 두었습니다. 화면 결함을 설명하는 문장이라 원문을 지우면 안 된다고 판단했습니다. 실제 화면이 고쳐지면 이 문장도 바뀌어야 합니다.

## 2. 뜻이 애매했거나 판단한 곳

- 「화면 구성」은 모든 권에서 `Screen layout`으로 통일했습니다.
- 「설정값 편집」은 편집 창 제목이자 경로 이름이라 같은 영문을 씁니다.
- 「집계」는 합계보다 요약 카드 전체를 가리키는 말이라 `Summary`로 썼습니다.
- 「사용자 할당」 버튼은 `Assign users`, 「사용자 할당 관리」 화면 이름은 `User assignment management`로 나눴습니다.
- 「시각(KST)」과 「최종 수정(KST)」은 `Time (KST)`, `Last modified (KST)`로 썼습니다.
- 「※ …」로 시작하는 안내 문장은 원문 기호를 그대로 두었습니다.
- 「(확대)」는 `(enlarged)`로 옮겼습니다.
- 「전수 export 미지원」은 `full export not supported`로 옮겼습니다. 「전수」가 전체를 뜻하는 말이라 `full`을 골랐습니다.
- 「잠김」 항목 앞의 🔒 그림 기호는 원문 그대로 두었습니다.
- 「※ 임상 데이터 변경 이력(Audit Trail)」처럼 Latin 글자로 된 제품 용어는 그대로 두었습니다.
- 「Site 관리」의 Site도 원문대로 Latin 글자로 두었습니다.
- 「CSV/Excel 내보내기」와 「CSV 내보내기」는 원문이 다르므로 각각 다른 영문을 씁니다.
- 원문에 있던 「20건」, 「5명」, 「3장」 같은 숫자는 모두 그대로 옮겼습니다. 원문에 없는 숫자는 넣지 않았습니다.
- 원문에 없던 설명은 추가하지 않았습니다.
