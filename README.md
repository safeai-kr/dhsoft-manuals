# DH Soft · SMART EDC 사용자 매뉴얼

SMART EDC CRF 필드 타입별 사용자 매뉴얼(16개 분권)의 A4 HTML과 디자인 기준 문서를 모아 두는 저장소입니다.

## 구성

```
prompt/
  SMART-EDC_매뉴얼_디자인_고정프롬프트.md   디자인·제작·검수 고정 규칙 (v105 기준)
manuals/
  <분권>/<언어>/
    SMART-EDC_사용자매뉴얼_CRF_<분권>_<언어>.html   A4 쪽 형태 HTML (PDF와 같은 템플릿)
    img/     화면 이미지 (300dpi 처리본), 헤더 이미지, 로고
    fonts/   Pretendard 고정 굵기 TTF (SIL OFL, fonts/LICENSE.txt)
```

## 현재 올라간 것

| 분권 | 한국어 | 영어 | 독일어 | 일본어 |
| --- | --- | --- | --- | --- |
| 숫자 | ✅ | 작업 중 | 작업 중 | 작업 중 |

## 보는 법

HTML 파일을 Chrome에서 열면 쪽 나눔 스크립트가 A4 쪽으로 배치합니다. `img/`, `fonts/` 폴더가 HTML과 같은 위치에 있어야 합니다. PDF는 같은 HTML을 Chrome으로 인쇄(A4, 여백 없음, 배경 그래픽 포함)해 만듭니다.
