---
name: approval-board
description: "사용자가 후보 여러 개(디자인 시안, 상품, 캠페인, 이미지 등)를 한 화면에서 승인·보류·반려하고 메모를 남긴 뒤 결과를 JSON으로 돌려주게 할 때 호출한다. 로컬 HTML 보드 한 장을 만들고, 돌려받은 JSON을 프로젝트의 검토 기록으로 저장한다."
---

# approval-board: 승인용 HTML 보드

후보 100개를 채팅 문장으로 승인받으면 빠뜨리거나 잘못 알아듣는 항목이 생긴다. 이 스킬은 후보를 카드로 보여 주는 로컬 HTML 한 장을 만들고, 사용자가 판정을 마치면 "JSON 복사" 버튼으로 결과를 돌려받는다.

## 준비

- 보드 생성: Python 3.9 이상. 외부 패키지는 필요 없다.
- 화면 시험(선택): `pip install playwright && playwright install chromium`
- 스크립트 경로는 설치 방식에 따라 다르다. 플러그인으로 설치했다면 `${CLAUDE_PLUGIN_ROOT}/skills/approval-board/scripts/make_board.py`이고, 폴더를 직접 복사했다면 `~/.claude/skills/approval-board/scripts/make_board.py`이다. 아래 예시는 직접 복사한 경우의 경로다.

## 만들기

1. 후보 목록을 `items.json` 형식으로 만든다.

   ```json
   {
     "board_id": "design-review-20261007",
     "title": "로고 시안 12종 검토",
     "note": "마음에 드는 시안은 승인, 고칠 점이 있으면 메모를 남겨 주세요.",
     "items": [
       {"id": "001", "title": "시안 A", "subtitle": "둥근 글꼴",
        "image": "images/a.png", "fields": {"색상": "남색", "비율": "1:1"}, "group": "1차",
        "fingerprint": "3f9a1c0e"}
     ]
   }
   ```

   - `image`는 절대 경로, 상대 경로, https URL을 쓸 수 있다. 상대 경로는 `items.json`이 있는 폴더를 기준으로 한다.
   - `fingerprint`는 선택 항목이다. 이미지 sha256 앞자리처럼 내용이 바뀌면 함께 바뀌는 값을 넣으면, 같은 번호라도 내용이 바뀐 항목에는 옛 판정이 붙지 않는다.
   - `board_id`에는 날짜나 원본 파일 해시를 넣어서, 후보가 바뀌면 다른 보드로 구분되게 한다.

2. 보드를 만든다.

   ```bash
   python3 ~/.claude/skills/approval-board/scripts/make_board.py <items.json> <board.html> [--id 보드ID]
   ```

3. 사용자에게 보드 파일 경로를 알려 주고 "판정을 마치면 JSON 복사를 눌러 붙여 넣어 달라"고 안내한다.

## 보드의 동작

- 보드는 판정과 메모를 어디에도 보내지 않는다. 다만 이미지가 URL이면 그 서버에서 이미지를 불러온다.
- 판정과 메모는 그 브라우저의 `localStorage`에 보드 ID별로 저장되고, 항목은 `id`(그리고 `fingerprint`가 있으면 그 값까지)로 구분한다.
- 키보드로 판정할 수 있고(라디오 그룹 화살표), 집계·필터·검색을 지원하며, 밝은 화면과 어두운 화면을 모두 지원한다.
- "초기화"는 실수로 지우지 않도록 두 번 눌러야 동작한다.

## 돌려받은 결과 저장

- 결과 JSON을 프로젝트의 검토 기록 폴더에 날짜를 붙여 저장한다(예: `review/user-review-<날짜>.json`).
- 이 기록은 사용자의 검토 의견일 뿐이다. 외부 플랫폼 제출, 발행, 결제 같은 행동의 승인으로 쓰지 않는다. 그런 행동은 별도로 사용자의 확인을 받는다.

## 시험

```bash
python3 ~/.claude/skills/approval-board/tests/test_board.py <board.html> [스크린샷 폴더]
```

1440px·390px 너비와 밝은·어두운 화면에서 콘솔 오류 0, 가로 넘침 0, 키보드 판정, 집계, 필터, 새로 고침 뒤 유지, JSON 복사 내용을 확인한다.
