# korean-workflow-skills

[![tests](https://github.com/WinnerMIN/korean-workflow-skills/actions/workflows/test.yml/badge.svg)](https://github.com/WinnerMIN/korean-workflow-skills/actions/workflows/test.yml)

한국에서 일하는 사람을 위한 Claude Code 스킬 모음입니다. 한글(HWP) 문서, 한국 법령 조회, 네이버·쿠팡 파트너스 운영처럼 범용 AI 에이전트가 자주 틀리거나 모르는 한국 실무를 다룹니다.

> **English summary**: A set of [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) (`SKILL.md`) for Korean workflows that general-purpose coding agents often get wrong: reading and editing Hangul (HWP/HWPX) documents, looking up Korean statutes and case law from primary sources, staying within Naver Search Advisor and Coupang Partners API limits, fact-checking marketing copy before publishing, and collecting bulk approvals through a local HTML board. The rules grew out of problems the author ran into while running Korean websites and documents with AI agents. The skills are written in Korean. MIT licensed.

## 스킬 목록

| 스킬 | 하는 일 | 필요한 것 |
|---|---|---|
| [`hwp`](skills/hwp/SKILL.md) | 한컴오피스 없이 `.hwp`·`.hwpx`·`.hml` 문서를 읽고, 표를 뽑고, 양식을 채우고, PDF·PNG로 렌더한다. 원본을 덮어쓰지 않고 검증까지 하게 한다. | [rhwp](https://github.com/edwardkim/rhwp), [kordoc](https://github.com/chrisryugj/kordoc) |
| [`korean-law-lookup`](skills/korean-law-lookup/SKILL.md) | 법령·판례 질문에 기억으로 답하지 않고 법제처 1차 출처를 조회한 뒤, 인용을 검증하고 시행일·현행 여부를 표기하게 한다. | [korean-law-mcp](https://github.com/chrisryugj/korean-law-mcp), 법제처 Open API 인증키 |
| [`claim-check`](skills/claim-check/SKILL.md) | 홍보문·블로그 글을 발행하기 전에 수치·날짜·규정·효과·비교·단정 문장을 주장 후보로 뽑고, 근거와 별도 검토자의 판정이 없으면 발행을 막는다. | Python 3.9+ |
| [`approval-board`](skills/approval-board/SKILL.md) | 후보 수십~수백 개를 한 화면에서 승인·보류·반려하고 메모를 남긴 뒤 JSON으로 돌려받는 로컬 HTML 보드를 만든다. | Python 3.9+ (화면 시험은 Playwright) |
| [`coupang-api-safety`](skills/coupang-api-safety/SKILL.md) | 쿠팡 파트너스 API 호출 코드를 만들 때 분당 피크 한도, 단일 throttle, 사이트 간 시간 분리, 403 즉시 정지 규칙을 지키게 한다. | 없음 |
| [`naver-searchadvisor-quota`](skills/naver-searchadvisor-quota/SKILL.md) | 네이버 서치어드바이저 수집 요청의 계정당 일일 한도를 넘기지 않도록 제출 우선순위와 이월 기준을 정한다. | 없음 |

## 설치

### 방법 1: 플러그인으로 한 번에 설치

Claude Code 안에서 다음 두 줄을 실행합니다. 스킬 6개가 함께 설치되고, `/korean-workflow-skills:hwp`처럼 플러그인 이름이 붙은 이름으로 불립니다.

```text
/plugin marketplace add WinnerMIN/korean-workflow-skills
/plugin install korean-workflow-skills@winnermin-skills
```

플러그인은 사용자 권한으로 스크립트를 실행할 수 있으니, 설치 전에 [플러그인 보안 안내](https://code.claude.com/docs/en/plugins/security)를 확인하세요.

### 방법 2: 필요한 스킬만 복사

쓰고 싶은 스킬 폴더만 `~/.claude/skills/` 아래에 복사합니다.

```bash
# 예: hwp와 claim-check만 설치
cp -R skills/hwp skills/claim-check ~/.claude/skills/
```

프로젝트에서만 쓰려면 그 프로젝트의 `.claude/skills/` 아래에 복사합니다. 설치한 뒤 Claude Code를 다시 시작하면 요청 내용에 맞는 스킬이 자동으로 불려 옵니다.

`hwp`와 `korean-law-lookup`은 외부 도구가 필요합니다. 각 도구의 설치 방법은 위 표의 원본 저장소를 따르세요. 이 저장소는 그 도구들을 포함하지 않습니다.

## 사용 예시

[`examples/`](examples/README.md)에 claim-check가 행사 안내문에서 뽑은 주장 검토표와, approval-board로 만든 승인 보드가 있습니다.

## 시험

GitHub Actions가 push와 PR마다 아래 시험을 실행합니다.

```bash
python3 skills/claim-check/tests/test_extract_claims.py
python3 skills/approval-board/scripts/make_board.py <items.json> board.html
python3 skills/approval-board/tests/test_board.py board.html
```

`items.json`의 형식은 [approval-board SKILL.md](skills/approval-board/SKILL.md)의 예시를 참고하세요. 화면 시험은 카드가 2장 이상인 보드로 실행합니다.

## 주의

- `coupang-api-safety`와 `naver-searchadvisor-quota`의 한도 수치는 작성자가 2026년에 운영하며 확인한 값입니다. 플랫폼 정책은 바뀔 수 있으니 공식 안내를 함께 확인하세요.
- `korean-law-lookup`은 1차 출처를 조회하게 하는 도구일 뿐 법률 자문이 아닙니다.
- 이 저장소는 Anthropic, 한컴, 네이버, 쿠팡과 관계가 없습니다.

## 기여

버그 제보, 다른 한국 실무 스킬 제안, 문서 개선 PR을 환영합니다. 플랫폼 한도나 정책 수치를 고칠 때는 확인한 날짜와 출처를 함께 적어 주세요.

## English

The skills are written in Korean because they target Korean documents, laws, and platforms, but they work in any Claude Code session.

| Skill | What it does |
|---|---|
| `hwp` | Read, fill, convert, and render Hangul `.hwp`/`.hwpx`/`.hml` files without Hancom Office, using [rhwp](https://github.com/edwardkim/rhwp) and [kordoc](https://github.com/chrisryugj/kordoc). Edits never overwrite the original and are checked by rendering. |
| `korean-law-lookup` | Answer questions about Korean statutes and case law only from primary sources via [korean-law-mcp](https://github.com/chrisryugj/korean-law-mcp), verify every citation, and state effective dates. |
| `claim-check` | Extract factual claims (numbers, dates, regulations, comparisons, absolute statements) from Korean copy and block publishing until each has a cited source and an independent reviewer's verdict. |
| `approval-board` | Build a single-file, accessible local HTML board for approving, holding, or rejecting many candidates, and export the decisions as JSON. |
| `coupang-api-safety` | Rules for code that calls the Coupang Partners API: per-minute peak limits, a single global throttle, staggered schedules, and a hard stop on 403 or warnings. |
| `naver-searchadvisor-quota` | Daily per-account quota and submission priority for Naver Search Advisor crawl requests. |

Install with `/plugin marketplace add WinnerMIN/korean-workflow-skills` and `/plugin install korean-workflow-skills@winnermin-skills`, or copy individual folders from `skills/` into `~/.claude/skills/`.

## 라이선스

[MIT](LICENSE)
