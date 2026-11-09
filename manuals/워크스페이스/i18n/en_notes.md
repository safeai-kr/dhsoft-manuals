# 영문 번역 메모: 워크스페이스 권

2026-10-30 · 언어: en

산출물: `워크스페이스/data/en.json`(143개 키), `워크스페이스/i18n/glossary_en.json`(61개 항목).
자동 검사: `check_tr.py 워크스페이스 en` 결과 「문제 0」.

## 1. 확인 필요

### 1-1. 화면 메뉴와 버튼 영문 이름은 제안이다

참고할 영문 화면이 없어서 메뉴·버튼·탭 이름은 모두 제안입니다. 특히 아래 이름을 먼저 확인해 주세요.

- 메뉴: `Platform home` · `Workspace management` · `Workspace dashboard` · `Workspace details` · `User assignment management` · `Create new project`
- 버튼: `Assign users` · `Deactivate` · `Activate` · `Edit name and description` · `Shortcut` · `View all` · `Designate as administrator`
- 상태 값: `Setting up` · `Operation`

### 1-2. 「CRA」와 「모니터요원」

원문의 「모니터요원」을 `monitor`로 옮겼습니다. 공용 용어집에는 「임상연구모니터요원(CRA)」이 `clinical research associate (CRA)`로 되어 있습니다. 같은 사람을 가리키는지 확인이 필요합니다. 같다면 `CRA`로 바꾸겠습니다.

### 1-3. 기관 관리와 연구자 배정 메뉴 이름

「기관 관리」는 `Organization management`, 「연구자 배정」은 `Researcher assignment`로 옮겼습니다. 다른 권에서 쓰는 영문 메뉴 이름과 맞는지 확인해 주세요.

### 1-4. 「전체」 보기 버튼

「전체 보기」는 `View all`로 옮겼습니다. 공용 용어집의 「전체」(Full)와 다르게 쓴 것입니다. 용어집 충돌은 플랫폼관리 권 메모 1-3과 같습니다.

## 2. 뜻이 애매했거나 판단한 곳

- 「구성 현황」은 `Setup progress`로 옮겼습니다. 네 단계(워크스페이스 생성, 사용자 할당, 프로젝트 생성, 운영)를 보여 주는 패널이라 「진행 상황」의 뜻으로 골랐습니다.
- 「구축 단계」는 `setup stage`, 「설정 중」은 `Setting up`, 「운영」은 `Operation`으로 나눴습니다. 프로젝트 상태 이름인 「설정 중」과 「운영 상태」가 영문에서도 같은 말로 읽히도록 맞췄습니다.
- 「메타 편집」은 이름과 설명만 고치는 기능이라 `Edit name and description`으로 풀어 썼습니다. 짧은 이름이 필요하면 바꿀 수 있습니다.
- 「이어서」는 최근에 들어간 워크스페이스 목록이라 `Continue`로 옮겼습니다. 뜻이 더 분명한 `Recently entered`로 바꾸는 것도 가능합니다.
- 「활성 프로젝트」는 활성 상태 프로젝트만 세는 칸입니다. 설정 중인 프로젝트는 집계에서 빠진다는 원문 설명을 그대로 옮겼습니다.
- 「할당 사용자」 요약은 최대 5명만 보인다는 원문을 옮겼습니다. 숫자 5는 원문 그대로입니다.
- 「워크스페이스 ›」와 「워크스페이스 관리 /」 경로 표기는 기호를 그대로 두었습니다.
- 「※」, 「⋯」, 「›」, 「·」 기호는 원문과 같은 자리에 두었습니다.
- 「(변경 불가)」처럼 라벨에 붙는 안내는 `(Cannot be changed)`로 옮겼습니다.
- 「비활성 상태의 워크스페이스입니다.」 안내는 `This workspace is in an inactive state.`로 옮겼습니다.
- 「역할」은 워크스페이스 안의 지위를 가리킵니다. 프로젝트 역할(연구자, 모니터요원)과 구분해서 썼습니다.
- 원문에 없던 설명이나 단계는 추가하지 않았습니다.
