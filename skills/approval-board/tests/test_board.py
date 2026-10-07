#!/usr/bin/env python3
"""approval-board 화면 시험: python3 tests/test_board.py <board.html> [스크린샷 폴더]
1440·390px × 밝은·어두운 화면에서 콘솔 오류 0, 가로 넘침 0, 키보드 판정, 집계, 새로 고침 유지, JSON 복사를 확인한다."""
import json, sys

sys.dont_write_bytecode = True
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    board = Path(sys.argv[1]).resolve(); shots = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    url = board.as_uri(); problems = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for w, scheme in ((1440, "light"), (390, "dark"), (390, "light"), (1440, "dark")):
            ctx = b.new_context(viewport=dict(width=w, height=900), color_scheme=scheme, reduced_motion="reduce")
            ctx.grant_permissions(["clipboard-read", "clipboard-write"])
            pg = ctx.new_page(); errs = []
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url); pg.wait_for_timeout(500)
            tag = f"{w}px/{scheme}"
            over = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            if over > 1: problems.append(f"{tag}: 가로 넘침 {over}px")
            n = pg.evaluate("document.querySelectorAll('.card').length")
            # 키보드: 첫 카드 첫 판정 버튼에 초점을 두고 오른쪽 화살표로 '보류'로 옮긴다(라디오 그룹 기본 동작)
            pg.locator(".card").first.locator("input[value=approve]").focus()
            pg.keyboard.press("Space"); pg.keyboard.press("ArrowRight")
            d0 = pg.evaluate("document.querySelector('.card').dataset.d")
            if d0 != "hold": problems.append(f"{tag}: 키보드 판정 실패({d0})")
            pg.locator(".card").nth(1).locator("label.reject").click()
            pg.locator(".card").nth(1).locator("textarea").fill("메모 시험")
            counts = pg.inner_text("#counts")
            if "보류 1" not in counts or "반려 1" not in counts or f"미결정 {n - 2}" not in counts:
                problems.append(f"{tag}: 집계 오류 {counts!r}")
            pg.click("[data-f=reject]")
            vis = pg.evaluate("[...document.querySelectorAll('.card')].filter(c => !c.classList.contains('hidden')).length")
            if vis != 1: problems.append(f"{tag}: 반려 필터 결과 {vis}개(기대 1)")
            pg.click("[data-f=all]")
            if shots:
                shots.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(shots / f"board-{w}-{scheme}.png"))
            pg.reload(); pg.wait_for_timeout(300)
            kept = pg.evaluate("[document.querySelector('.card').dataset.d, document.querySelectorAll('.card')[1].dataset.d, document.querySelectorAll('.card')[1].querySelector('textarea').value]")
            if kept != ["hold", "reject", "메모 시험"]: problems.append(f"{tag}: 새로 고침 뒤 유지 안 됨 {kept}")
            pg.click("#copy"); pg.wait_for_timeout(300)
            try:
                res = json.loads(pg.evaluate("navigator.clipboard.readText()"))
                dec = {x["id"]: x for x in res["decisions"]}
                first = pg.evaluate("document.querySelector('.card').dataset.id")
                if res["kind"] != "user-review-record" or res.get("submission_approval") is not False or dec[first]["decision"] != "보류" or res["counts"].get("반려") != 1:
                    problems.append(f"{tag}: 복사한 JSON 내용 오류 {res['counts']}")
            except Exception as e:
                problems.append(f"{tag}: JSON 복사 확인 실패 {e}")
            if errs: problems.append(f"{tag}: 콘솔 오류 {errs[:2]}")
            ctx.close()
        b.close()
    for x in problems: print("문제:", x)
    print(f"카드 {n}개, 문제 {len(problems)}건")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
