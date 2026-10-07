# 사용 예시

## claim-check

[`claim-check/sample.md`](claim-check/sample.md)는 짧은 행사 안내문입니다. 아래 명령으로 주장 후보를 뽑으면 [`sample.claims/`](claim-check/sample.claims/)에 원장(`claims.json`)과 검토표(`claims-review.txt`)가 생깁니다.

```bash
python3 skills/claim-check/scripts/extract_claims.py examples/claim-check/sample.md
```

검토표에는 날짜, "1분이면 끝납니다" 같은 단정, "작년보다 두 배" 같은 비교, "지방자치법에 따라" 같은 규정 주장이 뽑혀 있고, "천천히 둘러보세요" 같은 일반 문장은 빠져 있습니다.

근거를 채우기 전에는 발행 전 검사가 실패(종료 코드 1)합니다. 주장마다 `evidence`와 `quote`를 채우고 별도 검토자가 판정해야 통과합니다.

```bash
python3 skills/claim-check/scripts/extract_claims.py --check examples/claim-check/sample.claims/claims.json examples/claim-check/sample.md
```

## approval-board

[`approval-board/items.json`](approval-board/items.json)으로 만든 보드가 [`approval-board/board.html`](approval-board/board.html)입니다. 파일을 내려받아 브라우저로 열면 시안마다 승인·보류·반려를 고르고 메모를 남긴 뒤, "JSON 복사"로 결과를 가져갈 수 있습니다.

```bash
python3 skills/approval-board/scripts/make_board.py examples/approval-board/items.json board.html
```
