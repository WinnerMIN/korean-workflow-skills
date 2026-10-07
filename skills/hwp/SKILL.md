---
name: hwp
description: 한글(HWP/HWPX/HML) 문서를 읽고·변환하고·수정할 때 사용한다. "hwp 읽어줘", "한글 파일 열어", "hwpx 템플릿 채워", "공고문/시행계획/기안문 요약", "표 markdown으로", "SVG/PNG/PDF로 내보내", "한글 파일 텍스트 추출", "누름틀/필드 채워", "표 셀 값 바꿔", "페이지네이션/조판부호 디버깅", "HWPX↔HWP 차이 비교" 등을 요청할 때 트리거한다. 서로 보완하는 두 도구를 쓴다. rhwp CLI(.hwp 읽기·쓰기, 렌더링·진단)와 kordoc MCP(HWPX 생성·서식 채움·서식 보존 텍스트 치환)다.
---

# HWP / HWPX 문서 작업

한컴오피스 없이 macOS·Linux·Windows에서 한글 문서를 읽고, 변환하고, 고친다. 모델이 "한글 파일은 열 수 없다"고 답하거나 내용을 추측하지 않게 하는 것이 이 스킬의 목적이다.

## 준비

| 도구 | 역할 | 설치 |
|---|---|---|
| [rhwp](https://github.com/edwardkim/rhwp) (MIT) | 기본 도구. `.hwp`/`.hwpx`/`.hml` 읽기, `.hwp` 직접 편집, SVG·PNG·PDF 렌더, 레이아웃 진단 | 원본 저장소 Releases의 플랫폼별 바이너리를 받아 `PATH`에 둔다 |
| [kordoc](https://github.com/chrisryugj/kordoc) (MIT) | MCP 서버. HWPX 생성, 서식 채움, 원본 서식을 보존하는 텍스트 치환, 렌더 | 원본 저장소 README의 MCP 등록 방법을 따른다 |

아래 명령 예시는 rhwp v0.8.2, kordoc 4.15 기준이다. 버전이 다르면 `rhwp --help`와 세션에 노출된 MCP 도구 스키마를 우선한다.

## 어느 쪽을 쓸까

| 상황 | 도구 |
|---|---|
| `.hwp` 읽기·쓰기 전부 | `rhwp` CLI |
| 텍스트·표·구조·검색을 JSON으로 대량 처리 | `rhwp ... --json`, `rhwp batch` |
| PNG·PDF·SVG 렌더 | `rhwp export-png/export-pdf/export-svg` 또는 kordoc `render_document` |
| 레이아웃 버그·페이지네이션 디버깅 | `rhwp dump-pages` / `dump` / `ir-diff` |
| 새 `.hwpx` 문서 생성 | kordoc `generate_document` |
| `.hwpx` 서식(누름틀·양식) 채우기 | kordoc `parse_form` → `fill_form` |
| 원본 서식을 보존한 텍스트 치환 | kordoc `patch_document` |

셸을 쓸 수 있으면 대부분 rhwp CLI가 낫다. 빠르고, `.hwp`도 쓸 수 있고, JSON 출력 형식이 명확하다. kordoc은 HWPX 생성, 양식 채움, 서식 보존 치환에 쓴다.

## rhwp CLI 핵심 명령

```bash
rhwp info <파일> --json                 # 포맷·구역·페이지·문단 수·폰트
rhwp export-text <파일> [--json]        # 페이지별 텍스트 (기본 output/)
rhwp export-markdown <파일>             # 페이지별 .md
rhwp export-tables <파일> --json        # 표 격자 JSON (rowSpan/colSpan·중첩 보존)
rhwp export-structure <파일> --json     # 편·장·절·조·항·호·목 계층 트리
rhwp search <파일> "검색어" --json      # 구역·문단·페이지·오프셋 포함 매치
rhwp fields <파일> --json               # 누름틀/필드 조사

rhwp export-svg <파일> [-p N] [-o 폴더] [--embed-fonts]
rhwp export-png <파일> [-p N] --vlm-target claude   # 비전 모델 입력용 자동 리사이즈
rhwp export-pdf <파일> [-o out.pdf]

# .hwp 직접 편집 (원본을 덮어쓰지 않도록 -o로 새 파일 지정)
rhwp edit replace-text <파일.hwp> --find A --replace B --json -o out.hwp [--dry-run]
rhwp edit fill-fields  <파일.hwp> --data '{"필드명":"값"}' -o out.hwp
rhwp edit set-cell     <파일> --table 0 --row 2 --col 1 --text "값" -o out.hwp

rhwp export-hwpx <입력.hwp> [출력.hwpx] --verify   # .hwp → .hwpx
rhwp convert <입력> <출력.hwp>                     # 배포용(읽기 전용) HWP → 편집 가능 HWP
```

여러 파일은 표준 입력으로 파일 목록을 넘기고 NDJSON으로 받는다.

```bash
ls *.hwp | rhwp batch export-text --json --threads 8
ls *.hwp | rhwp batch search --query "예산" --json
```

### 레이아웃 디버깅 순서

1. `rhwp export-svg <파일> --debug-overlay -p N`으로 문제 문단을 특정한다.
2. `rhwp dump-pages <파일> -p N`으로 페이지 배치와 높이를 본다.
3. `rhwp dump <파일> -s N -p M`으로 문단 모양·줄 정보·표·도형 속성을 본다.
4. `rhwp ir-diff a.hwpx b.hwp -s N -p M --json`으로 HWPX와 HWP의 차이를 본다(차이가 있으면 exit 3).
5. 좌표를 정밀하게 비교하려면 `rhwp export-render-tree <파일> -p N`의 bbox JSON을 쓴다.

### 주의

- 페이지 번호는 **0부터** 센다. 한컴·PDF 표기(1부터)와 헷갈리지 않는다.
- 단위: 1인치 = 7200 HWPUNIT = 96px, 1px = 75 HWPUNIT, 1mm ≈ 283.46 HWPUNIT.
- `--json`을 주면 표준 출력에는 순수 JSON만 나오고 진단은 표준 오류로 나온다.
- `export-png`는 native-skia 기능이 포함된 rhwp 빌드에서만 동작한다. 이 명령이 없으면 `export-svg`나 kordoc `render_document`로 렌더한다.
- 한컴 전용 폰트(HY견명조 등)가 없으면 `--font-path <폰트 폴더>`를 더한다.

## kordoc MCP 사용

- 주요 도구: `parse_document`, `parse_pages`, `parse_table`, `extract_tables`, `parse_form`, `fill_form`, `generate_document`, `patch_document`, `compare_documents`, `render_document`, `redact_document`
- 도구 이름과 인수는 세션에 노출된 도구 스키마를 따른다. 버전에 따라 이름이 바뀔 수 있다.
- `patch_document`는 텍스트 치환 전용이다. 블록 추가·삭제나 표 구조 변경을 지원하지 않으므로, 구조 변경을 텍스트 치환으로 흉내 내지 않는다.

## 처리 규칙

- `.hwp`·`.hwpx`·`.hml` 파일을 읽거나 고치라는 요청에는 **추측하거나 못 한다고 답하지 않고** 위 도구로 실제 처리한다.
- 읽기는 `rhwp info`·`export-markdown`, 표는 `export-tables`, `.hwp` 직접 편집은 `rhwp edit`를 쓴다.
- `.hwp`에 내용을 추가하거나 구조를 바꿔야 하면 `rhwp export-hwpx --verify` → HWPX 편집 → `rhwp convert out.hwpx final.hwp --verify --verify-pages` 순서로 처리하고, 변환 검증이 모두 exit 0인지 확인한다.
- 편집 결과는 **원본을 덮어쓰지 않고 새 파일로** 만든다. 편집 전에 원본을 읽어 내용을 파악하고, 편집 후에 다시 읽어 반영되었는지 확인한 뒤 보고한다.
- 생성하거나 수정한 뒤에는 `render_document` 또는 `rhwp export-png`로 깨짐과 잘림을 눈으로 확인한다.
- 치환 0건, 지원하지 않는 요소 같은 이유로 실패하면 추측으로 메우지 않고 실패 사실과 원인을 그대로 알린다.
- 중요한 산출물에는 "자체 검증 통과가 한컴오피스 호환을 보장하지는 않는다"는 점을 함께 알린다. 최종 확인은 한컴오피스에서 열어 보는 것이다.
- 도구 목록에 kordoc 도구가 없으면 `claude mcp list`로 등록 상태를 확인하고, 그래도 없으면 rhwp CLI로 처리한다.

## 전형적 시나리오

**공문·보고서 읽고 요약**

```bash
rhwp info doc.hwp --json && rhwp export-markdown doc.hwp -o out/
```

표 구조가 중요하면 `rhwp export-tables doc.hwp --json`을 쓰고, 시각 확인이 필요하면 `rhwp export-png doc.hwp -p 0 --vlm-target claude`로 만든 이미지를 직접 읽는다.

**양식 채우기**

- `.hwp`: `rhwp fields form.hwp --json`으로 필드를 확인한 뒤 `rhwp edit fill-fields form.hwp --data '{...}' -o 결과.hwp`
- `.hwpx`: kordoc `parse_form`으로 필드를 확인한 뒤 `fill_form`

**표 셀 수정**

- `.hwp`: `rhwp export-tables`로 좌표를 확인한 뒤 `rhwp edit set-cell --table N --row R --col C --text "값" -o out.hwp`

**대량 문서 색인**

```bash
find . -name '*.hwp' | rhwp batch export-text --json --threads 8 > corpus.ndjson
```
